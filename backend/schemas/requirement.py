from pydantic import BaseModel


class Requirement(BaseModel):
    """Structured output of Agent 1 — Requirement Analyzer. Matches spec §4 exactly."""

    goal: str
    input: str
    decision: str | None = None
    condition: str | None = None
    action: str
    expected_output: str
