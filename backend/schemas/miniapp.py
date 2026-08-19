from pydantic import BaseModel


class RecordSummary(BaseModel):
    id: str
    label: str


class ActionOption(BaseModel):
    action: str
    label: str


class MiniAppInfo(BaseModel):
    """What the frontend needs to render the "try it live" panel for a session -
    which records exist to pick from and which actions are available - derived
    deterministically from the dataset the workflow reads, never LLM-generated."""

    dataset: str | None
    records: list[RecordSummary]
    actions: list[ActionOption]


class RecordActionRequest(BaseModel):
    action: str


class ActionLogEntry(BaseModel):
    record_id: str
    action: str
    created_at: str
