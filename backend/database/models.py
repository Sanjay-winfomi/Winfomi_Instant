"""ORM schema for demo_sessions. Structured agent output (requirement, workflow,
critic, execution, blueprint) is stored as JSONB - it's already validated Pydantic
data by the time it reaches here, so a relational breakout isn't warranted for an
MVP sandbox that only ever reads a session back by id."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DemoSessionRecord(Base):
    __tablename__ = "demo_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    problem_text: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="fallback")
    dataset: Mapped[str | None] = mapped_column(String(120), nullable=True)

    requirement: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dataset_records: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    workflow: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    critic: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    critic_history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    execution: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    blueprint: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rejected_steps: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    lead_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("leads.id"), nullable=True)
    ui_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class User(Base):
    """A Winfomi employee account - COMPANY_ADMIN portal login only. Clients never
    appear in this table; they're identified purely by email on Lead."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="Winfomi Admin")
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="COMPANY_ADMIN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class Lead(Base):
    """A prospective client, identified by email. Created the moment a visitor submits
    their email (before any demo exists) and enriched as they interact further."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    client_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NEW")
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="normal")
    score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class ClientEvent(Base):
    """Product-analytics event trail (EMAIL_SUBMITTED, DEMO_CREATED, ...) - feeds both
    lead scoring and the company Analytics funnel. Never stores more than a lead/session
    reference plus a small JSON metadata blob."""

    __tablename__ = "client_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    event_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class InternalNote(Base):
    """Employee-only note on a lead. Never returned by any /api/client/* route."""

    __tablename__ = "internal_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"), nullable=False)
    author_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class AgentExecution(Base):
    """One node-run of the 4-agent pipeline (requirement/planner/critic/executor) -
    safe operational metadata only (name, status, timing), never prompts or reasoning."""

    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class CompanySetting(Base):
    """Key/value overrides layered on top of core/config.py env defaults - never used
    for secrets (API keys stay env-only, see services/settings_service.py)."""

    __tablename__ = "company_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class SessionRecordRun(Base):
    """One "try it live" execution of a session's workflow against a single record -
    written every time the mini-app's Run button is used."""

    __tablename__ = "session_record_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("demo_sessions.session_id"), nullable=False)
    record_id: Mapped[str] = mapped_column(String(120), nullable=False)
    execution: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class SessionAction(Base):
    """A simulated action (approve/escalate/alert supplier/...) the customer took on a
    specific record from the mini-app - the persisted proof that the interaction is
    real, not decorative buttons."""

    __tablename__ = "session_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("demo_sessions.session_id"), nullable=False)
    record_id: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
