"""Synthesizes a small sample dataset tailored to whatever business problem the
customer described, instead of reading from a fixed set of pre-built mock datasets.

Live mode: asks the LLM for realistic sample records matching the Requirement's
`record_label`/`fields`. Fallback mode: a deterministic generator keyed off each
field's name (so it still works, at lower fidelity, with zero API key configured).

Either way, this runs BEFORE the Executor - the Executor itself never calls an LLM
and never generates data on its own; it only ever processes records it was handed.
"""
from __future__ import annotations

import re

from agents.llm_provider import LLMUnavailableError, get_llm_provider
from core.config import get_settings
from core.logging import get_logger
from schemas.requirement import Requirement

logger = get_logger(__name__)

RECORD_COUNT = 6

SYSTEM_PROMPT = """You generate small, realistic sample datasets for a workflow-automation
demo. Given a record label and a list of fields, produce a JSON object:
{"records": [ {field: value, ...}, ... ]}
Generate exactly 6 records. Make values varied and realistic for the given fields, and
make sure the values would produce a MIX of outcomes for any downstream numeric threshold
or category check (i.e. don't make every record identical or all on one side of a likely
threshold). Every record must include an "id" field with a short unique string id.
Respond with ONLY the JSON object, no commentary."""

_NUMERIC_HINTS = [
    "score", "amount", "price", "revenue", "spend", "percentage", "percent", "rating",
    "stock", "level", "days", "count", "age", "quantity", "qty", "total", "value",
]


def is_numeric_field(field_name: str) -> bool:
    lowered = field_name.lower()
    return any(hint in lowered for hint in _NUMERIC_HINTS)


def _slugify(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return slug or "record"


def _seed_value(field: str, index: int) -> object:
    lowered = field.lower()
    if lowered in ("id",):
        return None  # filled in separately
    if any(k in lowered for k in ("name", "title", "subject", "label", "customer", "vendor", "supplier", "rep")):
        return f"{field.replace('_', ' ').title()} {index + 1}"
    if any(k in lowered for k in ("date", "time")):
        return f"2026-0{(index % 9) + 1}-{(index % 27) + 1:02d}"
    if lowered.startswith(("is_", "has_")) or lowered in ("flag", "flagged"):
        return index % 2 == 0
    if any(k in lowered for k in ("amount", "price", "revenue", "spend", "total")):
        return round(100 + (index * 137) % 900 + ((index * 17) % 100) / 100, 2)
    if is_numeric_field(field):
        return (index * 23 + 7) % 100
    if lowered == "status":
        return ["new", "in_progress", "resolved", "flagged"][index % 4]
    return f"{field.replace('_', ' ').title()} value {index + 1}"


def _deterministic_synthesize(requirement: Requirement) -> list[dict]:
    slug = _slugify(requirement.record_label)
    records = []
    for i in range(RECORD_COUNT):
        record = {"id": f"{slug}-{i + 1:03d}"}
        for field in requirement.fields:
            if field.lower() == "id":
                continue
            record[field] = _seed_value(field, i)
        records.append(record)
    return records


def synthesize_dataset(requirement: Requirement) -> tuple[list[dict], str]:
    """Returns (records, mode) where mode is 'live' or 'fallback'."""
    settings = get_settings()
    if settings.is_live:
        try:
            provider = get_llm_provider()
            user_prompt = (
                f"Record label: {requirement.record_label}\n"
                f"Fields: {requirement.fields}\n"
                f"Context (what this data will be used for): {requirement.goal}"
            )
            raw = provider.complete_json(SYSTEM_PROMPT, user_prompt, settings.llm_max_tokens)
            records = raw.get("records", [])
            if isinstance(records, list) and records:
                slug = _slugify(requirement.record_label)
                for i, record in enumerate(records):
                    if not isinstance(record, dict):
                        raise ValueError("synthesizer returned a non-object record")
                    record.setdefault("id", f"{slug}-{i + 1:03d}")
                return records, "live"
            raise ValueError("synthesizer returned no records")
        except (LLMUnavailableError, Exception) as exc:  # noqa: BLE001
            logger.warning("Data synthesizer falling back to deterministic generation: %s", exc)
    return _deterministic_synthesize(requirement), "fallback"
