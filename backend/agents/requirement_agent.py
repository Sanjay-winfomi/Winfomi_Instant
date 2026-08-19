"""Agent 1 — Requirement Analyzer.

Converts raw natural-language customer text into the structured Requirement
schema (spec §4). Tries the live LLM first; if unavailable, falls back to a
deterministic keyword-based extractor so the pipeline never dead-ends.
"""
from __future__ import annotations

from agents.llm_provider import LLMUnavailableError, get_llm_provider
from core.config import get_settings
from core.logging import get_logger
from schemas.requirement import Requirement
from tools.datasets import guess_dataset

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Requirement Analyzer for an AI workflow-generation platform.
Convert the customer's plain-English business problem into structured JSON. Do not include
any explanation, only the JSON object. Schema:
{
  "goal": "short description of what the customer wants automated",
  "input": "the kind of data/record this operates on, e.g. 'customer complaints', 'inventory levels'",
  "decision": "the yes/no or branching decision involved, or null if none",
  "condition": "the condition that triggers the decision, or null if none",
  "action": "the action taken once a decision is made",
  "expected_output": "what the customer should see as a result"
}
Respond with ONLY the JSON object, no markdown fences, no commentary."""


def _fallback_requirement(text: str) -> Requirement:
    """Deterministic extraction used when no LLM is configured or the live call fails."""
    dataset = guess_dataset(text) or "tickets"
    lowered = text.lower()

    dataset_input_map = {
        "tickets": "customer complaints/support tickets",
        "customers": "customer account activity",
        "employees": "employee attendance records",
        "inventory": "inventory stock levels",
        "invoices": "vendor invoices",
        "products": "product reviews",
    }
    has_condition = any(kw in lowered for kw in ["if", "below", "above", "when", "falls", "exceed", "urgent", "risk"])

    return Requirement(
        goal=text.strip()[:200],
        input=dataset_input_map.get(dataset, "business records"),
        decision="whether the record requires action" if has_condition else None,
        condition="record meets the specified threshold or keyword trigger" if has_condition else None,
        action="route/alert the relevant team" if has_condition else "summarize and report",
        expected_output="a list of flagged records with the recommended action",
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
