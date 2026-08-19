"""Session persistence, backed by PostgreSQL (database/models.py). Every access goes
through this module - nothing else in the app touches SQLAlchemy directly."""
from __future__ import annotations

from database.engine import get_db_session
from database.models import DemoSessionRecord, SessionAction, SessionRecordRun
from schemas.execution import ExecutionResult
from schemas.session import DemoResult
from tools.mini_app import build_mini_app_info


def _derive_dataset(result: DemoResult) -> str | None:
    steps = []
    if result.outcome == "blueprint" and result.blueprint:
        steps = result.blueprint.proposed_workflow
        for step in steps:
            if step.get("tool") == "READ_DATA":
                return step.get("params", {}).get("dataset")
        return None
    if result.workflow:
        for step in result.workflow.steps:
            if step.tool == "READ_DATA":
                return step.params.get("dataset")
    return None


def _to_record(result: DemoResult) -> DemoSessionRecord:
    return DemoSessionRecord(
        session_id=result.session_id,
        problem_text=result.requirement.goal if result.requirement else "",
        outcome=result.outcome,
        mode=result.mode,
        dataset=_derive_dataset(result),
        requirement=result.requirement.model_dump() if result.requirement else None,
        workflow=result.workflow.model_dump() if result.workflow else None,
        critic=result.critic.model_dump() if result.critic else None,
        critic_history=[c.model_dump() for c in result.critic_history],
        execution=result.execution.model_dump() if result.execution else None,
        blueprint=result.blueprint.model_dump() if result.blueprint else None,
        rejected_steps=result.rejected_steps,
        error=result.error,
    )


def _to_demo_result(record: DemoSessionRecord) -> DemoResult:
    return DemoResult(
        session_id=record.session_id,
        outcome=record.outcome,
        requirement=record.requirement,
        workflow=record.workflow,
        critic=record.critic,
        critic_history=record.critic_history or [],
        execution=record.execution,
        blueprint=record.blueprint,
        rejected_steps=record.rejected_steps or [],
        mode=record.mode,
        error=record.error,
        mini_app=build_mini_app_info(record.dataset) if record.outcome == "executed" else None,
    )


def save(result: DemoResult) -> None:
    with get_db_session() as session:
        existing = session.get(DemoSessionRecord, result.session_id)
        new_record = _to_record(result)
        if existing:
            for column in DemoSessionRecord.__table__.columns.keys():
                if column in ("session_id", "created_at"):
                    continue
                setattr(existing, column, getattr(new_record, column))
        else:
            session.add(new_record)
        session.commit()


def get(session_id: str) -> DemoResult | None:
    with get_db_session() as session:
        record = session.get(DemoSessionRecord, session_id)
        return _to_demo_result(record) if record else None


def get_dataset(session_id: str) -> str | None:
    with get_db_session() as session:
        record = session.get(DemoSessionRecord, session_id)
        return record.dataset if record else None


def save_record_run(session_id: str, record_id: str, execution: ExecutionResult) -> None:
    with get_db_session() as session:
        session.add(
            SessionRecordRun(session_id=session_id, record_id=record_id, execution=execution.model_dump())
        )
        session.commit()


def save_action(session_id: str, record_id: str, action: str) -> None:
    with get_db_session() as session:
        session.add(SessionAction(session_id=session_id, record_id=record_id, action=action))
        session.commit()


def list_actions(session_id: str) -> list[dict]:
    with get_db_session() as session:
        rows = (
            session.query(SessionAction)
            .filter(SessionAction.session_id == session_id)
            .order_by(SessionAction.created_at.desc())
            .all()
        )
        return [
            {"record_id": r.record_id, "action": r.action, "created_at": r.created_at.isoformat()}
            for r in rows
        ]
