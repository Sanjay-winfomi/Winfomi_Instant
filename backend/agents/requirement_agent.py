"""Agent 1 — Requirement Analyzer.

Converts raw natural-language customer text into the structured Requirement
schema. Tries the live LLM first; if unavailable, falls back to a deterministic
keyword-based extractor so the pipeline never dead-ends.

Deliberately domain-agnostic: this never maps a request onto a fixed set of
pre-built business categories. `record_label`/`fields` just describe the shape of
one record for whatever the customer described - the actual sample data is
synthesized later (agents/data_synthesizer.py) to fit.
"""
from __future__ import annotations

from agents.llm_provider import LLMUnavailableError, get_llm_provider
from core.config import get_settings
from core.logging import get_logger
from schemas.requirement import Requirement

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Requirement Analyzer for an AI workflow-generation platform.
Convert the customer's plain-English business problem into structured JSON. The platform
is fully generic - never map the request onto a fixed set of pre-built business categories.
Do not include any explanation, only the JSON object. Schema:
{
  "goal": "short description of what the customer wants automated",
  "input": "the kind of data/record this operates on, e.g. 'customer complaints', 'field sales visits'",
  "record_label": "singular name of ONE record this workflow processes, e.g. 'support ticket', 'sales visit', 'invoice'",
  "fields": ["3-6 field names a single record of this type would realistically have, e.g. ['customer_name','visit_date','outcome','follow_up_needed']"],
  "decision": "the yes/no or branching decision involved, or null if none",
  "condition": "the condition that triggers the decision, or null if none",
  "action": "the action taken once a decision is made",
  "expected_output": "what the customer should see as a result"
}
Respond with ONLY the JSON object, no markdown fences, no commentary."""

# Cue words -> a synthetic field name to add when that cue appears in the customer's
# text. Used only by the deterministic fallback (no LLM configured / live call failed).
_FIELD_CUES: list[tuple[str, str]] = [
    ("stock", "stock_level"),
    ("inventory", "stock_level"),
    ("invoice", "amount"),
    ("bill", "amount"),
    ("payment", "amount"),
    ("price", "price"),
    ("revenue", "revenue"),
    ("spend", "spend"),
    ("risk", "risk_score"),
    ("churn", "risk_score"),
    ("renewal", "days_until_renewal"),
    ("sentiment", "rating"),
    ("review", "rating"),
    ("rating", "rating"),
    ("late", "days_late"),
    ("attendance", "days_late"),
    ("urgent", "priority"),
    ("priority", "priority"),
    ("percentage", "percentage"),
    ("percent", "percentage"),
    ("supplier", "supplier"),
    ("vendor", "vendor"),
    ("score", "score"),
]

# Cue words -> the singular label of one record, checked in order.
_RECORD_LABEL_CUES: list[tuple[str, str]] = [
    ("invoice", "invoice"),
    ("ticket", "support ticket"),
    ("complaint", "complaint"),
    ("customer", "customer"),
    ("employee", "employee"),
    ("resume", "candidate"),
    ("candidate", "candidate"),
    ("review", "review"),
    ("inventory", "inventory item"),
    ("stock", "inventory item"),
    ("lead", "lead"),
    ("order", "order"),
    ("visit", "visit"),
    ("appointment", "appointment"),
    ("claim", "claim"),
    ("application", "application"),
    ("shipment", "shipment"),
    ("transaction", "transaction"),
]

_CONDITION_KEYWORDS = ["if", "below", "above", "when", "falls", "exceed", "urgent", "risk", "over", "under", "more than", "less than"]


def _fallback_requirement(text: str) -> Requirement:
    """Deterministic extraction used when no LLM is configured or the live call fails.

    Lower fidelity than the live LLM (it can only react to keyword cues, not real
    understanding), but works for ANY input, not just a fixed set of domains - and is
    what makes the whole pipeline demoable with zero external dependencies.
    """
    lowered = text.lower()

    record_label = next((label for kw, label in _RECORD_LABEL_CUES if kw in lowered), "record")

    fields: list[str] = ["name"]
    for kw, field in _FIELD_CUES:
        if kw in lowered and field not in fields:
            fields.append(field)
    if len(fields) == 1:
        fields.append("value")
    fields.append("status")
    fields = fields[:6]

    has_condition = any(kw in lowered for kw in _CONDITION_KEYWORDS)
    direction = "falls below" if any(kw in lowered for kw in ["below", "under", "less than", "falls", "drop"]) else "exceeds"

    input_description = "general business records" if record_label == "record" else f"{record_label} records"

    return Requirement(
        goal=text.strip()[:200],
        input=input_description,
        record_label=record_label,
        fields=fields,
        decision="whether the record requires action" if has_condition else None,
        condition=f"the relevant field {direction} the specified threshold" if has_condition else None,
        action="route/alert the relevant team" if has_condition else "summarize and report",
        expected_output=(
            "a summarized report of the processed records"
            if record_label == "record"
            else f"a list of flagged {record_label} records with the recommended action"
        ),
    )


def analyze_requirement(text: str) -> tuple[Requirement, str]:
    """Returns (requirement, mode) where mode is 'live' or 'fallback'."""
    settings = get_settings()
    if settings.is_live:
        try:
            provider = get_llm_provider()
            raw = provider.complete_json(SYSTEM_PROMPT, text, settings.llm_max_tokens)
            return Requirement(**raw), "live"
        except (LLMUnavailableError, Exception) as exc:  # noqa: BLE001 - deliberate broad fallback
            logger.warning("Requirement agent falling back to deterministic mode: %s", exc)
    return _fallback_requirement(text), "fallback"
