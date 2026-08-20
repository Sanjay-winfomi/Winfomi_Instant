import re

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ClientSessionRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not _EMAIL_RE.match(cleaned):
            raise ValueError("Enter a valid email address.")
        return cleaned


class ClientSessionResponse(BaseModel):
    client_token: str
    email: str


class ClientEventRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=60)
    session_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class ModifyDemoRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)


class DemoSummary(BaseModel):
    session_id: str
    title: str | None = None
    outcome: str
    created_at: str
    updated_at: str
