"""Session persistence, backed by PostgreSQL (database/models.py). Every access goes
through this module - nothing else in the app touches SQLAlchemy directly."""
from __future__ import annotations

from database.engine import get_db_session
from database.models import DemoSessionRecord
from schemas.session import DemoResult


def _to_record(result: DemoResult) -> DemoSessionRecord:
    return DemoSessionRecord(
        session_id=result.session_id,
        problem_text=result.requirement.goal if result.requirement else "",
        outcome=result.outcome,
        mode=result.mode,
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
