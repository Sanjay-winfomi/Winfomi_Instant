"""The dynamic mini-app UI schema — what the frontend's DynamicMiniAppRenderer
consumes instead of one fixed hardcoded template. See tools/ui_schema.py for how
this is deterministically derived from the Requirement/Workflow/ExecutionResult
already produced by the pipeline (no LLM, no per-domain hardcoding)."""
from typing import Any

from pydantic import BaseModel, Field


class UiInput(BaseModel):
    id: str
    type: str  # text | number | date | select | record_picker
    label: str
    field: str | None = None
    options: list[str] | None = None


class UiAction(BaseModel):
    id: str
    type: str  # run | record_action
    label: str
    action: str | None = None  # the action key posted to /records/{id}/actions, when type=record_action


class UiResult(BaseModel):
    id: str
    type: str  # table | card | status
    title: str
    columns: list[str] | None = None
    rows: list[dict[str, Any]] | None = None
    content: Any = None


class UiComponent(BaseModel):
    ref: str  # "input:<id>" | "action:<id>" | "result:<id>"


class UiSchema(BaseModel):
    app: dict  # {title, description}
    inputs: list[UiInput] = Field(default_factory=list)
    actions: list[UiAction] = Field(default_factory=list)
    results: list[UiResult] = Field(default_factory=list)
    components: list[UiComponent] = Field(default_factory=list)
