"""Client-facing API - everything a visitor/prospect touches. No authentication:
clients are identified purely by an opaque `client_token` tied to a Lead (created the
moment they submit their email, see POST /session), sent back on every subsequent
request via the `X-Client-Token` header. Never exposes internal-only data (notes,
other leads, agent internals) - see api/company_routes.py for that."""
from __future__ import annotations

import json
import queue
import threading
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from agents.executor_agent import UnsupportedCapabilityError, run_workflow
from api.store import get as get_session
from api.store import (
    get_lead_by_token,
    get_or_create_lead,
    list_actions,
    list_demos_for_lead,
    log_event,
    save_action,
    save_record_run,
)
from api.store import save as save_session
from core.logging import get_logger
from database.models import Lead
from graph.orchestrator import PipelineState, run_pipeline
from schemas.client_session import (
    ClientEventRequest,
    ClientSessionRequest,
    ClientSessionResponse,
    DemoSummary,
    ModifyDemoRequest,
)
from schemas.execution import ExecutionResult
from schemas.miniapp import ActionLogEntry, RecordActionRequest
from schemas.session import DemoRequest, DemoResult
from services.file_import import FileParseError, UnsupportedFileTypeError, extract_from_file
from services.lead_scoring import recompute_lead_score
from tools.mini_app import allowed_actions, build_mini_app_info
from tools.ui_schema import build_ui_schema

logger = get_logger(__name__)
router = APIRouter(prefix="/api/client")

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


def _log(lead_id: int, event_type: str, session_id: str | None = None, metadata: dict | None = None) -> None:
    log_event(lead_id, event_type, session_id, metadata)
    recompute_lead_score(lead_id)


def get_current_lead(x_client_token: str | None = Header(default=None)) -> Lead:
    if not x_client_token:
        raise HTTPException(status_code=401, detail="Missing X-Client-Token header. Call POST /api/client/session first.")
    lead = get_lead_by_token(x_client_token)
    if lead is None:
        raise HTTPException(status_code=401, detail="Unknown or expired client session.")
    return lead


@router.post("/session", response_model=ClientSessionResponse)
def start_session(request: ClientSessionRequest) -> ClientSessionResponse:
    lead = get_or_create_lead(request.email)
    _log(lead.id, "EMAIL_SUBMITTED")
    return ClientSessionResponse(client_token=lead.client_token, email=lead.email)


def _build_result(
    session_id: str, state: PipelineState, lead_id: int | None, title: str | None = None
) -> DemoResult:
    mode = state.get("planner_mode") or state.get("requirement_mode") or "fallback"
    outcome = state.get("outcome", "error")
    requirement = state.get("requirement")
    dataset_records = state.get("dataset_records", [])
    execution = state.get("execution")

    return DemoResult(
        session_id=session_id,
        outcome=outcome,
        requirement=requirement,
        workflow=state.get("workflow"),
        critic=state.get("critic"),
        critic_history=state.get("critic_history", []),
        execution=execution,
        blueprint=state.get("blueprint"),
        rejected_steps=state.get("rejected_steps", []),
        mode=mode,
        mini_app=build_mini_app_info(dataset_records, requirement) if outcome == "executed" else None,
        ui_schema=build_ui_schema(requirement, dataset_records, execution) if outcome == "executed" else None,
        title=title or (requirement.goal[:80] if requirement else None),
        lead_id=lead_id,
        dataset_records=dataset_records,
    )


@router.post("/demo", response_model=DemoResult)
def create_demo(request: DemoRequest, lead: Lead = Depends(get_current_lead)) -> DemoResult:
    session_id = str(uuid.uuid4())
    _log(lead.id, "BUILD_STARTED", session_id)
    try:
        state = run_pipeline(request.text, session_id=session_id)
    except Exception as exc:  # last-resort guard - the pipeline should never raise past this point
        logger.exception("Pipeline crashed unexpectedly")
        result = DemoResult(session_id=session_id, outcome="error", error=str(exc), lead_id=lead.id)
        save_session(result)
        return result

    result = _build_result(session_id, state, lead.id)
    save_session(result)
    _log(lead.id, "DEMO_CREATED", session_id)
    _log(lead.id, "BUILD_COMPLETED", session_id, {"outcome": result.outcome})
    return result


@router.post("/demo/upload", response_model=DemoResult)
async def create_demo_from_file(
    file: UploadFile = File(...),
    instruction: str = Form(default=""),
    lead: Lead = Depends(get_current_lead),
) -> DemoResult:
    """Builds a demo from an uploaded document instead of typed text.

    .csv/.xlsx: the file's own rows become the REAL dataset - no data is synthesized.
    .docx/.pdf/.pptx: extracted text is treated like a typed problem description; a
    sample dataset is still synthesized, since there's no tabular ground truth here.
    """
    session_id = str(uuid.uuid4())
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large (max 5 MB).")

    try:
        extracted = extract_from_file(file.filename or "upload", content)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except FileParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - any parser-library failure
        logger.exception("File parsing failed for %s", file.filename)
        raise HTTPException(status_code=422, detail=f"Could not read this file: {exc}") from exc

    _log(lead.id, "BUILD_STARTED", session_id)
    try:
        if extracted.kind == "tabular":
            slug = extracted.record_label.replace(" ", "-") or "record"
            records = extracted.records
            for i, record in enumerate(records):
                record.setdefault("id", f"{slug}-{i + 1:03d}")

            prompt = f"Process {extracted.record_label} records with fields: {', '.join(extracted.fields)}."
            if instruction.strip():
                prompt += f" {instruction.strip()}"

            state = run_pipeline(
                prompt,
                override_records=records,
                override_fields=extracted.fields,
                override_record_label=extracted.record_label,
                session_id=session_id,
            )
        else:
            combined_text = extracted.text
            if instruction.strip():
                combined_text = f"{combined_text}\n\n{instruction.strip()}"
            state = run_pipeline(combined_text[:8000], session_id=session_id)
    except Exception as exc:  # last-resort guard - the pipeline should never raise past this point
        logger.exception("Pipeline crashed unexpectedly while processing an uploaded file")
        result = DemoResult(session_id=session_id, outcome="error", error=str(exc), lead_id=lead.id)
        save_session(result)
        return result

    result = _build_result(session_id, state, lead.id)
    save_session(result)
    _log(lead.id, "DEMO_CREATED", session_id)
    _log(lead.id, "BUILD_COMPLETED", session_id, {"outcome": result.outcome})
    return result


@router.post("/demo/stream")
def stream_demo_build(request: DemoRequest, lead: Lead = Depends(get_current_lead)):
    """SSE-style endpoint (spec §14): emits real stage-transition events as the graph
    actually moves through Requirement -> Planner -> Critic -> Executor, instead of a
    fixed fake timer. POST (not native EventSource) so the client token header and a
    long problem description both travel safely - the frontend reads the streamed
    body with fetch()'s ReadableStream rather than the EventSource API. The client
    then GETs /demo/{session_id} for the full payload once it sees the "done" event."""
    text = request.text
    session_id = str(uuid.uuid4())
    event_queue: queue.Queue = queue.Queue()

    def on_stage(stage: str) -> None:
        event_queue.put({"event": "stage", "stage": stage})

    def worker() -> None:
        _log(lead.id, "BUILD_STARTED", session_id)
        try:
            state = run_pipeline(text, session_id=session_id, on_stage=on_stage)
            result = _build_result(session_id, state, lead.id)
        except Exception as exc:  # noqa: BLE001 - the pipeline should never raise past this point
            logger.exception("Pipeline crashed unexpectedly")
            result = DemoResult(session_id=session_id, outcome="error", error=str(exc), lead_id=lead.id)
        save_session(result)
        _log(lead.id, "DEMO_CREATED", session_id)
        _log(lead.id, "BUILD_COMPLETED", session_id, {"outcome": result.outcome})
        event_queue.put({"event": "done", "session_id": session_id, "outcome": result.outcome})

    threading.Thread(target=worker, daemon=True).start()

    def event_stream():
        while True:
            item = event_queue.get()
            yield f"data: {json.dumps(item)}\n\n"
            if item.get("event") == "done":
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/demos", response_model=list[DemoSummary])
def list_my_demos(lead: Lead = Depends(get_current_lead)) -> list[DemoSummary]:
    records = list_demos_for_lead(lead.id)
    return [
        DemoSummary(
            session_id=r.session_id,
            title=r.title,
            outcome=r.outcome,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )
        for r in records
    ]


@router.get("/demo/{session_id}", response_model=DemoResult)
def get_demo(session_id: str) -> DemoResult:
    result = get_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Demo session not found.")
    return result


@router.post("/demo/{session_id}/modify", response_model=DemoResult)
def modify_demo(session_id: str, request: ModifyDemoRequest, lead: Lead = Depends(get_current_lead)) -> DemoResult:
    """Refines an existing demo in natural language (spec §20): re-enters the pipeline
    carrying the prior requirement's fields/decision forward as a hint, so a
    refinement doesn't discard a working shape, then rebuilds/re-persists the SAME
    session (not a new one)."""
    existing = get_session(session_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Demo session not found.")

    combined_text = f"{existing.requirement.goal if existing.requirement else ''}\n\nRefinement: {request.text}".strip()
    try:
        state = run_pipeline(
            combined_text,
            requirement_hint=existing.requirement,
            session_id=session_id,
        )
    except Exception as exc:  # last-resort guard
        logger.exception("Pipeline crashed unexpectedly during modification")
        result = DemoResult(session_id=session_id, outcome="error", error=str(exc), lead_id=lead.id, title=existing.title)
        save_session(result)
        return result

    result = _build_result(session_id, state, lead.id, title=existing.title)
    save_session(result)
    _log(lead.id, "DEMO_MODIFIED", session_id, {"modification": request.text[:200]})
    return result


@router.post("/demo/{session_id}/records/{record_id}/run", response_model=ExecutionResult)
def run_record(session_id: str, record_id: str, lead: Lead = Depends(get_current_lead)) -> ExecutionResult:
    """Re-executes the session's already-approved workflow against a single record -
    a real run of the same deterministic tools, over the same dataset (synthesized or
    uploaded), not a canned lookup."""
    result = get_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Demo session not found.")
    if result.outcome != "executed" or result.workflow is None:
        raise HTTPException(status_code=400, detail="This session has no executable workflow to run.")

    record_label = result.requirement.record_label if result.requirement else "record"
    try:
        execution = run_workflow(
            result.workflow,
            result.requirement.goal if result.requirement else "",
            records=result.dataset_records,
            record_label=record_label,
            record_id=record_id,
        )
    except UnsupportedCapabilityError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    save_record_run(session_id, record_id, execution)
    _log(lead.id, "WORKFLOW_EXECUTED", session_id, {"record_id": record_id})
    return execution


@router.post("/demo/{session_id}/records/{record_id}/actions", response_model=ActionLogEntry)
def take_action(
    session_id: str, record_id: str, request: RecordActionRequest, lead: Lead = Depends(get_current_lead)
) -> ActionLogEntry:
    """Persists a simulated action (approve/flag for review/...) the customer took on
    one record - written to PostgreSQL as proof the interaction is real."""
    result = get_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Demo session not found.")

    allowed = {a["action"] for a in allowed_actions(result.requirement)}
    if request.action not in allowed:
        raise HTTPException(status_code=422, detail=f"'{request.action}' is not a valid action for this session.")

    save_action(session_id, record_id, request.action)
    _log(lead.id, "MINI_APP_INTERACTION", session_id, {"record_id": record_id, "action": request.action})
    return ActionLogEntry(record_id=record_id, action=request.action, created_at=datetime.now(timezone.utc).isoformat())


@router.get("/demo/{session_id}/actions", response_model=list[ActionLogEntry])
def get_actions_log(session_id: str) -> list[ActionLogEntry]:
    if get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Demo session not found.")
    return [ActionLogEntry(**a) for a in list_actions(session_id)]


@router.post("/events")
def log_client_event(request: ClientEventRequest, lead: Lead = Depends(get_current_lead)) -> dict:
    """Generic sink for frontend-only events (DEMO_OPENED, MINI_APP_INTERACTION,
    FULL_SOLUTION_REQUESTED, ...) that don't correspond to a dedicated endpoint call."""
    _log(lead.id, request.event_type, request.session_id, request.metadata)
    return {"status": "ok"}
