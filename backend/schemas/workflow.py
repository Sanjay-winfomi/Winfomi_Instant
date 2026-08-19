from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    tool: str
    params: dict = Field(default_factory=dict)


class Workflow(BaseModel):
    """Structured output of Agent 2 — Workflow Planner. Matches spec §4."""

    steps: list[WorkflowStep]
