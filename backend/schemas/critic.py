from pydantic import BaseModel, Field


class CriticScores(BaseModel):
    requirement_understanding: float
    workflow_completeness: float
    logical_correctness: float
    tool_feasibility: float


class CriticResult(BaseModel):
    """Structured output of Agent 3 — Critic. overall_score is ALWAYS recomputed
    deterministically in Python from the four sub-scores; the LLM's own claimed
    overall value (if any) is discarded rather than trusted."""

    scores: CriticScores
    overall_score: float
    approved: bool
    feedback: list[str] = Field(default_factory=list)
    attempt: int = 1


def compute_overall_score(scores: CriticScores) -> float:
    total = (
        scores.requirement_understanding * 0.25
        + scores.workflow_completeness * 0.25
        + scores.logical_correctness * 0.25
        + scores.tool_feasibility * 0.25
    )
    return round(total, 2)
