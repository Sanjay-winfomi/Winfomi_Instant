"""Session persistence, backed by PostgreSQL (database/models.py). Every access goes
through this module - nothing else in the app touches SQLAlchemy directly."""
from __future__ import annotations

from datetime import datetime, timezone

from database.engine import get_db_session
from database.models import (
    AgentExecution,
    ClientEvent,
    CompanySetting,
    DemoSessionRecord,
    InternalNote,
    Lead,
    SessionAction,
    SessionRecordRun,
    User,
)
from schemas.execution import ExecutionResult
from schemas.requirement import Requirement
from schemas.session import DemoResult
from schemas.ui_schema import UiSchema
from tools.mini_app import build_mini_app_info


def _to_record(result: DemoResult) -> DemoSessionRecord:
    return DemoSessionRecord(
        session_id=result.session_id,
        problem_text=result.requirement.goal if result.requirement else "",
        outcome=result.outcome,
        mode=result.mode,
        dataset=result.requirement.record_label if result.requirement else None,
        requirement=result.requirement.model_dump() if result.requirement else None,
        workflow=result.workflow.model_dump() if result.workflow else None,
        critic=result.critic.model_dump() if result.critic else None,
        critic_history=[c.model_dump() for c in result.critic_history],
        execution=result.execution.model_dump() if result.execution else None,
        blueprint=result.blueprint.model_dump() if result.blueprint else None,
        rejected_steps=result.rejected_steps,
        error=result.error,
        dataset_records=result.dataset_records,
        lead_id=result.lead_id,
        ui_schema=result.ui_schema.model_dump() if result.ui_schema else None,
        title=result.title,
    )


def _to_demo_result(record: DemoSessionRecord) -> DemoResult:
    requirement = Requirement(**record.requirement) if record.requirement else None
    return DemoResult(
        session_id=record.session_id,
        outcome=record.outcome,
        requirement=requirement,
        workflow=record.workflow,
        critic=record.critic,
        critic_history=record.critic_history or [],
        execution=record.execution,
        blueprint=record.blueprint,
        rejected_steps=record.rejected_steps or [],
        mode=record.mode,
        error=record.error,
        dataset_records=record.dataset_records or [],
        lead_id=record.lead_id,
        ui_schema=UiSchema(**record.ui_schema) if record.ui_schema else None,
        title=record.title,
        mini_app=(
            build_mini_app_info(record.dataset_records or [], requirement)
            if record.outcome == "executed"
            else None
        ),
    )


def save(result: DemoResult) -> None:
    with get_db_session() as session:
        existing = session.get(DemoSessionRecord, result.session_id)
        new_record = _to_record(result)
        if existing:
            for column in DemoSessionRecord.__table__.columns.keys():
                if column in ("session_id", "created_at", "updated_at"):
                    continue
                setattr(existing, column, getattr(new_record, column))
        else:
            session.add(new_record)
        session.commit()


def get(session_id: str) -> DemoResult | None:
    with get_db_session() as session:
        record = session.get(DemoSessionRecord, session_id)
        return _to_demo_result(record) if record else None


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


# ---------------------------------------------------------------------------
# Users (company auth)
# ---------------------------------------------------------------------------

def count_users() -> int:
    with get_db_session() as session:
        return session.query(User).count()


def create_user(email: str, password_hash: str, name: str = "Winfomi Admin", role: str = "COMPANY_ADMIN") -> User:
    with get_db_session() as session:
        user = User(email=email, password_hash=password_hash, name=name, role=role)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def get_user_by_email(email: str) -> User | None:
    with get_db_session() as session:
        return session.query(User).filter(User.email == email).one_or_none()


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

def get_or_create_lead(email: str) -> Lead:
    with get_db_session() as session:
        lead = session.query(Lead).filter(Lead.email == email).one_or_none()
        if lead:
            return lead
        lead = Lead(email=email)
        session.add(lead)
        session.commit()
        session.refresh(lead)
        return lead


def get_lead(lead_id: int) -> Lead | None:
    with get_db_session() as session:
        return session.get(Lead, lead_id)


def get_lead_by_token(client_token: str) -> Lead | None:
    with get_db_session() as session:
        return session.query(Lead).filter(Lead.client_token == client_token).one_or_none()


def list_leads(
    status: str | None = None,
    search: str | None = None,
    sort: str = "-created_at",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Lead], int]:
    with get_db_session() as session:
        query = session.query(Lead)
        if status:
            query = query.filter(Lead.status == status)
        if search:
            query = query.filter(Lead.email.ilike(f"%{search}%"))
        total = query.count()

        column = Lead.created_at
        if sort.lstrip("-") == "score":
            column = Lead.score
        elif sort.lstrip("-") == "email":
            column = Lead.email
        query = query.order_by(column.desc() if sort.startswith("-") else column.asc())

        rows = query.offset((page - 1) * page_size).limit(page_size).all()
        return rows, total


def update_lead(lead_id: int, status: str | None, priority: str | None) -> Lead | None:
    with get_db_session() as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            return None
        if status:
            lead.status = status
        if priority:
            lead.priority = priority
        session.commit()
        session.refresh(lead)
        return lead


def add_note(lead_id: int, author_user_id: int | None, note: str) -> InternalNote:
    with get_db_session() as session:
        row = InternalNote(lead_id=lead_id, author_user_id=author_user_id, note=note)
        session.add(row)
        session.commit()
        session.refresh(row)
        return row


def list_notes(lead_id: int) -> list[InternalNote]:
    with get_db_session() as session:
        return (
            session.query(InternalNote)
            .filter(InternalNote.lead_id == lead_id)
            .order_by(InternalNote.created_at.desc())
            .all()
        )


def list_demos_for_lead(lead_id: int) -> list[DemoSessionRecord]:
    with get_db_session() as session:
        return (
            session.query(DemoSessionRecord)
            .filter(DemoSessionRecord.lead_id == lead_id)
            .order_by(DemoSessionRecord.updated_at.desc())
            .all()
        )


# ---------------------------------------------------------------------------
# Client events
# ---------------------------------------------------------------------------

def log_event(lead_id: int, event_type: str, session_id: str | None = None, metadata: dict | None = None) -> None:
    with get_db_session() as session:
        session.add(
            ClientEvent(lead_id=lead_id, session_id=session_id, event_type=event_type, event_metadata=metadata or {})
        )
        session.commit()


def list_events_for_lead(lead_id: int) -> list[ClientEvent]:
    with get_db_session() as session:
        return (
            session.query(ClientEvent)
            .filter(ClientEvent.lead_id == lead_id)
            .order_by(ClientEvent.created_at.desc())
            .all()
        )


def list_all_events() -> list[ClientEvent]:
    with get_db_session() as session:
        return session.query(ClientEvent).order_by(ClientEvent.created_at.asc()).all()


# ---------------------------------------------------------------------------
# Agent execution instrumentation
# ---------------------------------------------------------------------------

def save_agent_execution(
    session_id: str, agent_name: str, status: str, duration_ms: int, attempt: int = 1, error_message: str | None = None
) -> None:
    with get_db_session() as session:
        session.add(
            AgentExecution(
                session_id=session_id,
                agent_name=agent_name,
                status=status,
                duration_ms=duration_ms,
                attempt=attempt,
                error_message=error_message,
            )
        )
        session.commit()


def list_agent_executions(agent_name: str | None = None, limit: int = 2000) -> list[AgentExecution]:
    with get_db_session() as session:
        query = session.query(AgentExecution)
        if agent_name:
            query = query.filter(AgentExecution.agent_name == agent_name)
        return query.order_by(AgentExecution.created_at.desc()).limit(limit).all()


# ---------------------------------------------------------------------------
# Company: dashboard / demos listing
# ---------------------------------------------------------------------------

def dashboard_counts() -> dict:
    with get_db_session() as session:
        total_leads = session.query(Lead).count()
        new_leads = session.query(Lead).filter(Lead.status == "NEW").count()
        qualified_leads = session.query(Lead).filter(Lead.status.in_(("QUALIFIED", "CONVERTED"))).count()
        total_demos = session.query(DemoSessionRecord).count()
        successful_demos = session.query(DemoSessionRecord).filter(DemoSessionRecord.outcome == "executed").count()
        active_demos = (
            session.query(DemoSessionRecord)
            .filter(DemoSessionRecord.outcome.in_(("executed", "blueprint")))
            .count()
        )
        recent_leads = session.query(Lead).order_by(Lead.created_at.desc()).limit(5).all()
        recent_demos = (
            session.query(DemoSessionRecord).order_by(DemoSessionRecord.created_at.desc()).limit(5).all()
        )
        return {
            "total_leads": total_leads,
            "new_leads": new_leads,
            "qualified_leads": qualified_leads,
            "total_demos": total_demos,
            "successful_demos": successful_demos,
            "active_demos": active_demos,
            "recent_leads": recent_leads,
            "recent_demos": recent_demos,
        }


def list_all_demos(
    outcome: str | None = None, search: str | None = None, page: int = 1, page_size: int = 20
) -> tuple[list[DemoSessionRecord], int]:
    with get_db_session() as session:
        query = session.query(DemoSessionRecord)
        if outcome:
            query = query.filter(DemoSessionRecord.outcome == outcome)
        if search:
            query = query.filter(DemoSessionRecord.problem_text.ilike(f"%{search}%"))
        total = query.count()
        rows = (
            query.order_by(DemoSessionRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return rows, total


def lead_email_for(lead_id: int | None) -> str | None:
    if lead_id is None:
        return None
    with get_db_session() as session:
        lead = session.get(Lead, lead_id)
        return lead.email if lead else None
