"""Deterministic lead scoring - a configurable weighted sum over event counts, never
an LLM call (spec §29). Recomputed whenever a new client_event is logged."""
from __future__ import annotations

from database.engine import get_db_session
from database.models import ClientEvent, Lead

EVENT_WEIGHTS: dict[str, float] = {
    "EMAIL_SUBMITTED": 5,
    "DEMO_CREATED": 10,
    "BUILD_COMPLETED": 5,
    "DEMO_OPENED": 5,
    "MINI_APP_INTERACTION": 3,
    "WORKFLOW_EXECUTED": 2,
    "DEMO_MODIFIED": 8,
    "FULL_SOLUTION_REQUESTED": 25,
}

MAX_SCORE = 100.0


def recompute_lead_score(lead_id: int) -> float:
    with get_db_session() as session:
        rows = session.query(ClientEvent).filter(ClientEvent.lead_id == lead_id).all()
        total = 0.0
        for row in rows:
            total += EVENT_WEIGHTS.get(row.event_type, 0)
        score = round(min(total, MAX_SCORE), 2)

        lead = session.get(Lead, lead_id)
        if lead:
            lead.score = score
            session.commit()
        return score
