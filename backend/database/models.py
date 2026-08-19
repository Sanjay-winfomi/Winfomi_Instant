"""ORM schema for demo_sessions. Structured agent output (requirement, workflow,
critic, execution, blueprint) is stored as JSONB - it's already validated Pydantic
data by the time it reaches here, so a relational breakout isn't warranted for an
MVP sandbox that only ever reads a session back by id."""
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
    dataset: Mapped[str | None] = mapped_column(String(40), nullable=True)

    requirement: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    workflow: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    critic: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    critic_history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    execution: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    blueprint: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rejected_steps: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
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
