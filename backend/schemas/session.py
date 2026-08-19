from typing import Any

from pydantic import BaseModel, Field

from schemas.critic import CriticResult
from schemas.execution import ExecutionResult, WorkflowBlueprint
from schemas.requirement import Requirement
from schemas.workflow import Workflow


class DemoRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)


class DemoResult(BaseModel):
    session_id: str
    outcome: str  # executed | blueprint | error
    requirement: Requirement | None = None
    workflow: Workflow | None = None
    critic: CriticResult | None = None
    critic_history: list[CriticResult] = Field(default_factory=list)
    execution: ExecutionResult | None = None
    blueprint: WorkflowBlueprint | None = None
    rejected_steps: list[dict[str, Any]] = Field(default_factory=list)
    mode: str = "fallback"  # live | fallback
    error: str | None = None
