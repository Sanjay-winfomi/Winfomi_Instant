from typing import Any

from pydantic import BaseModel, Field


class StepResult(BaseModel):
    tool: str
    params: dict = Field(default_factory=dict)
    status: str  # success | failed | blocked
    output: Any = None
    error: str | None = None
    duration_ms: int = 0


class ExecutionResult(BaseModel):
    status: str  # success | partial | blueprint
    step_results: list[StepResult] = Field(default_factory=list)
    final_output: Any = None


class WorkflowBlueprint(BaseModel):
    """Returned instead of an error when a request can't be fully executed. See spec §8."""

    requirement_analysis: dict
    proposed_workflow: list[dict]
    tools_required: list[str]
    expected_output_description: str
    integration_note: str
