"""Agent 2 — Workflow Planner.

Selects and sequences steps ONLY from the Tool Registry. The LLM is given the
exact tool list + descriptions and told never to invent a tool name; every
planned step is still re-validated against the registry downstream
(graph/validation.py) before it can reach the Critic.

Deliberately domain-agnostic: nothing here branches on "is this about tickets vs
invoices vs...". The Planner only ever looks at the Requirement's own
`record_label`/`fields`/`decision`/`condition`/`action`, so it composes the same way
for a business problem nobody anticipated as for a familiar one.
"""
from __future__ import annotations

from agents.data_synthesizer import is_numeric_field
from agents.llm_provider import LLMUnavailableError, get_llm_provider
from core.config import get_settings
from core.logging import get_logger
from schemas.requirement import Requirement
from schemas.workflow import Workflow, WorkflowStep
from tools.registry import TOOL_DESCRIPTIONS

logger = get_logger(__name__)


def _system_prompt() -> str:
    tool_list = "\n".join(f"- {name}: {desc}" for name, desc in TOOL_DESCRIPTIONS.items())
    return f"""You are the Workflow Planner for an AI workflow-generation platform.
Given a structured requirement, produce a workflow as a JSON object with a "steps" array.
Each step is {{"tool": "<TOOL_NAME>", "params": {{...}}}}.

You may ONLY use these exact tool names - never invent a new one:
{tool_list}

READ_DATA takes no params - it reads whatever sample dataset was generated for this
requirement's record_label/fields. Steps referencing a "field" must use one of the
requirement's own field names (or a field name introduced earlier by CLASSIFY/ANALYZE
via their category_field/output_field param).

Respond with ONLY the JSON object, no markdown fences, no commentary. Keep the workflow
between 3 and 7 steps, always starting with READ_DATA and ending with GENERATE_REPORT."""


def _pick_numeric_field(fields: list[str]) -> str | None:
    return next((f for f in fields if is_numeric_field(f)), None)


def _pick_operator(condition_text: str | None) -> str:
    text = (condition_text or "").lower()
    if any(kw in text for kw in ["below", "under", "less than", "falls", "drop"]):
        return "<"
    return ">"


def _fallback_workflow(requirement: Requirement, feedback: list[str] | None = None) -> Workflow:
    has_decision = bool(requirement.decision or requirement.condition)
    report_title = f"{requirement.record_label.title()} Report"

    steps = [WorkflowStep(tool="READ_DATA", params={})]

    if has_decision:
        numeric_field = _pick_numeric_field(requirement.fields)
        if numeric_field:
            operator = _pick_operator(requirement.condition)
            steps.append(
                WorkflowStep(tool="CHECK_CONDITION", params={"field": numeric_field, "operator": operator, "value": 50})
            )
        else:
            text_field = requirement.fields[0] if requirement.fields else "name"
            steps.append(
                WorkflowStep(
                    tool="CLASSIFY",
                    params={
                        "field": text_field,
                        "category_field": "flag",
                        "categories": {"flagged": ["urgent", "risk", "critical", "overdue"], "normal": []},
                    },
                )
            )
            steps.append(WorkflowStep(tool="CHECK_CONDITION", params={"field": "flag", "operator": "==", "value": "flagged"}))

        steps.append(WorkflowStep(tool="MAKE_DECISION", params={"true_branch": "flag_for_action", "false_branch": "no_action"}))
        steps.append(
            WorkflowStep(
                tool="ROUTE",
                params={"team": "Relevant team"},
            )
        )
        steps.append(WorkflowStep(tool="SEND_NOTIFICATION", params={"to": "relevant-team", "message": f"{requirement.record_label.title()} record(s) flagged for action."}))
    else:
        steps.append(WorkflowStep(tool="EXTRACT", params={"fields": requirement.fields or ["name", "status"]}))

    steps.append(WorkflowStep(tool="GENERATE_REPORT", params={"title": report_title}))
    return Workflow(steps=steps)


def plan_workflow(
    requirement: Requirement, feedback: list[str] | None = None, attempt: int = 1
) -> tuple[Workflow, str]:
    """Returns (workflow, mode). `feedback` carries Critic notes on retry attempts."""
    settings = get_settings()
    if settings.is_live:
        try:
            provider = get_llm_provider()
            user_prompt = f"Requirement:\n{requirement.model_dump_json(indent=2)}"
            if feedback:
                user_prompt += f"\n\nThe previous plan was rejected. Fix these issues:\n" + "\n".join(f"- {f}" for f in feedback)
            raw = provider.complete_json(_system_prompt(), user_prompt, settings.llm_max_tokens)
            steps = [WorkflowStep(**s) for s in raw.get("steps", [])]
            if not steps:
                raise ValueError("Planner returned zero steps")
            return Workflow(steps=steps), "live"
        except (LLMUnavailableError, Exception) as exc:  # noqa: BLE001
            logger.warning("Planner falling back to deterministic template: %s", exc)
    return _fallback_workflow(requirement, feedback), "fallback"
