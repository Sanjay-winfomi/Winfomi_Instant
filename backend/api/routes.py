from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from api.store import get as get_session
from api.store import save as save_session
from core.logging import get_logger
from graph.orchestrator import run_pipeline
from schemas.session import DemoRequest, DemoResult

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
    result = DemoResult(
        session_id=session_id,
        outcome=state.get("outcome", "error"),
        requirement=state.get("requirement"),
        workflow=state.get("workflow"),
        critic=state.get("critic"),
        critic_history=state.get("critic_history", []),
        execution=state.get("execution"),
        blueprint=state.get("blueprint"),
        rejected_steps=state.get("rejected_steps", []),
        mode=mode,
    )
    save_session(result)
    return result


@router.get("/demo/{session_id}", response_model=DemoResult)
def get_demo(session_id: str) -> DemoResult:
    result = get_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Demo session not found.")
    return result
