from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from agents.executor_agent import UnsupportedCapabilityError, run_workflow
from api.store import get as get_session
from api.store import list_actions, save_action, save_record_run
from api.store import save as save_session
from core.logging import get_logger
from graph.orchestrator import run_pipeline
from schemas.execution import ExecutionResult
from schemas.miniapp import ActionLogEntry, RecordActionRequest
from schemas.session import DemoRequest, DemoResult
from tools.mini_app import allowed_actions, build_mini_app_info

logger = get_logger(__name__)
router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/demo", response_model=DemoResult)
def create_demo(request: DemoRequest) -> DemoResult:
    session_id = str(uuid.uuid4())
    try:
        state = run_pipeline(request.text)
    except Exception as exc:  # last-resort guard - the pipeline should never raise past this point
        logger.exception("Pipeline crashed unexpectedly")
        result = DemoResult(session_id=session_id, outcome="error", error=str(exc))
        save_session(result)
        return result

    mode = state.get("planner_mode") or state.get("requirement_mode") or "fallback"
    outcome = state.get("outcome", "error")
    requirement = state.get("requirement")
    dataset_records = state.get("dataset_records", [])

    result = DemoResult(
        session_id=session_id,
        outcome=outcome,
        requirement=requirement,
        workflow=state.get("workflow"),
        critic=state.get("critic"),
        critic_history=state.get("critic_history", []),
        execution=state.get("execution"),
        blueprint=state.get("blueprint"),
        rejected_steps=state.get("rejected_steps", []),
        mode=mode,
        mini_app=build_mini_app_info(dataset_records, requirement) if outcome == "executed" else None,
        dataset_records=dataset_records,
    )
    save_session(result)
    return result


@router.get("/demo/{session_id}", response_model=DemoResult)
def get_demo(session_id: str) -> DemoResult:
    result = get_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Demo session not found.")
    return result


@router.post("/demo/{session_id}/records/{record_id}/run", response_model=ExecutionResult)
def run_record(session_id: str, record_id: str) -> ExecutionResult:
    """Re-executes the session's already-approved workflow against a single record -
    a real run of the same deterministic tools, over the same synthesized dataset,
    not a canned lookup."""
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
    return execution


@router.post("/demo/{session_id}/records/{record_id}/actions", response_model=ActionLogEntry)
def take_action(session_id: str, record_id: str, request: RecordActionRequest) -> ActionLogEntry:
    """Persists a simulated action (approve/flag for review/...) the customer took on
    one record - written to PostgreSQL as proof the interaction is real."""
    result = get_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Demo session not found.")

    allowed = {a["action"] for a in allowed_actions(result.requirement)}
    if request.action not in allowed:
        raise HTTPException(status_code=422, detail=f"'{request.action}' is not a valid action for this session.")

    save_action(session_id, record_id, request.action)
    return ActionLogEntry(record_id=record_id, action=request.action, created_at=datetime.now(timezone.utc).isoformat())


@router.get("/demo/{session_id}/actions", response_model=list[ActionLogEntry])
def get_actions_log(session_id: str) -> list[ActionLogEntry]:
    if get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Demo session not found.")
    return [ActionLogEntry(**a) for a in list_actions(session_id)]
