"""ORM schema for demo_sessions. Structured agent output (requirement, workflow,
critic, execution, blueprint) is stored as JSONB - it's already validated Pydantic
data by the time it reaches here, so a relational breakout isn't warranted for an
MVP sandbox that only ever reads a session back by id."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
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
