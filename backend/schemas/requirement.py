from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """Structured output of Agent 1 — Requirement Analyzer.

    `record_label` and `fields` describe the shape of ONE record this workflow will
    process (e.g. record_label="sales visit", fields=["rep_name","customer","outcome"]).
    They exist because the platform never assumes a fixed set of business domains -
    the data synthesizer (agents/data_synthesizer.py) uses them to generate a small
    sample dataset tailored to whatever the customer actually described, instead of
    reading from a handful of pre-baked mock datasets.
    """

    goal: str
    input: str
    record_label: str = "record"
    fields: list[str] = Field(default_factory=lambda: ["name", "status", "value"])
    decision: str | None = None
    condition: str | None = None
    action: str
    expected_output: str
