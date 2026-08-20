from typing import Any

from pydantic import BaseModel, Field

from schemas.critic import CriticResult
from schemas.execution import ExecutionResult, WorkflowBlueprint
from schemas.miniapp import MiniAppInfo
from schemas.requirement import Requirement
from schemas.ui_schema import UiSchema
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
    mini_app: MiniAppInfo | None = None
    ui_schema: UiSchema | None = None
    title: str | None = None
    # The sample dataset synthesized for this session (agents/data_synthesizer.py).
    # Internal only - excluded from the API response; the frontend only ever sees it
    # indirectly via mini_app.records and execution.step_results.
    dataset_records: list[dict[str, Any]] = Field(default_factory=list, exclude=True)
    # Internal only - which Lead (if any) this session is tied to.
    lead_id: int | None = Field(default=None, exclude=True)
