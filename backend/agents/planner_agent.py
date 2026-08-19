"""Agent 2 — Workflow Planner.

Selects and sequences steps ONLY from the Tool Registry. The LLM is given the
exact tool list + descriptions and told never to invent a tool name; every
planned step is still re-validated against the registry downstream
(graph/validation.py) before it can reach the Critic.
"""
from __future__ import annotations

import json

from agents.llm_provider import LLMUnavailableError, get_llm_provider
from core.config import get_settings
from core.logging import get_logger
from schemas.requirement import Requirement
from schemas.workflow import Workflow, WorkflowStep
from tools.datasets import guess_dataset
from tools.registry import TOOL_DESCRIPTIONS

logger = get_logger(__name__)


def _system_prompt() -> str:
    tool_list = "\n".join(f"- {name}: {desc}" for name, desc in TOOL_DESCRIPTIONS.items())
    return f"""You are the Workflow Planner for an AI workflow-generation platform.
Given a structured requirement, produce a workflow as a JSON object with a "steps" array.
Each step is {{"tool": "<TOOL_NAME>", "params": {{...}}}}.

You may ONLY use these exact tool names - never invent a new one:
{tool_list}

Datasets available for the "dataset" param on READ_DATA: tickets, customers, employees, inventory, invoices, products.

Respond with ONLY the JSON object, no markdown fences, no commentary. Keep the workflow
between 3 and 8 steps, ending with GENERATE_REPORT."""


def _fallback_workflow(requirement: Requirement, feedback: list[str] | None = None) -> Workflow:
    dataset = guess_dataset(f"{requirement.goal} {requirement.input}") or "tickets"
    has_decision = bool(requirement.decision or requirement.condition)

    if dataset == "inventory":
        steps = [
            WorkflowStep(tool="READ_DATA", params={"dataset": "inventory"}),
            WorkflowStep(tool="ANALYZE", params={"method": "stock_percentage", "output_field": "stock_pct"}),
            WorkflowStep(tool="CHECK_CONDITION", params={"field": "stock_pct", "operator": "<", "value": 20}),
            WorkflowStep(tool="MAKE_DECISION", params={"true_branch": "alert_supplier", "false_branch": "continue_monitoring"}),
            WorkflowStep(tool="SEND_NOTIFICATION", params={"to": "supplier", "message": "Stock has fallen below the configured threshold."}),
            WorkflowStep(tool="GENERATE_REPORT", params={"title": "Inventory Monitoring Report"}),
        ]
    elif dataset == "customers":
        steps = [
            WorkflowStep(tool="READ_DATA", params={"dataset": "customers"}),
            WorkflowStep(tool="ANALYZE", params={"method": "risk_score", "output_field": "risk_score"}),
            WorkflowStep(tool="CHECK_CONDITION", params={"field": "risk_score", "operator": ">", "value": 50}),
            WorkflowStep(tool="MAKE_DECISION", params={"true_branch": "alert_sales_team", "false_branch": "no_action"}),
            WorkflowStep(tool="SEND_NOTIFICATION", params={"to": "sales-team", "message": "High-risk customers identified."}),
            WorkflowStep(tool="GENERATE_REPORT", params={"title": "Customer Retention Risk Report"}),
        ]
    elif dataset == "products":
        steps = [
            WorkflowStep(tool="READ_DATA", params={"dataset": "products"}),
            WorkflowStep(tool="COMPARE", params={"group_field": "product", "period_field": "period", "metric_field": "rating", "baseline": "last_month", "current": "this_month"}),
            WorkflowStep(tool="GENERATE_REPORT", params={"title": "Product Sentiment Trend Report"}),
        ]
    elif dataset == "invoices":
        steps = [
            WorkflowStep(tool="READ_DATA", params={"dataset": "invoices"}),
            WorkflowStep(tool="CHECK_CONDITION", params={"field": "vendor_known", "operator": "==", "value": False}),
            WorkflowStep(tool="MAKE_DECISION", params={"true_branch": "send_for_manual_review", "false_branch": "approve"}),
            WorkflowStep(tool="SEND_NOTIFICATION", params={"to": "finance-team", "message": "Suspicious invoices flagged for review."}),
            WorkflowStep(tool="GENERATE_REPORT", params={"title": "Invoice Verification Report"}),
        ]
    elif dataset == "employees":
        lowered = f"{requirement.goal} {requirement.input}".lower()
        if any(kw in lowered for kw in ["late", "attendance", "absent", "punctual"]):
            # Deliberately references a field the mock dataset doesn't have (attendance
            # tracking isn't part of employees.json) - the Executor will detect this
            # capability gap and the orchestrator will fall back to a Workflow Blueprint,
            # rather than the Planner special-casing "unsupported" itself.
            steps = [
                WorkflowStep(tool="READ_DATA", params={"dataset": "employees"}),
                WorkflowStep(tool="CHECK_CONDITION", params={"field": "days_late", "operator": ">", "value": 2}),
                WorkflowStep(tool="MAKE_DECISION", params={"true_branch": "flag_for_review", "false_branch": "no_action"}),
                WorkflowStep(tool="GENERATE_REPORT", params={"title": "Employee Attendance Report"}),
            ]
        else:
            steps = [
                WorkflowStep(tool="READ_DATA", params={"dataset": "employees"}),
                WorkflowStep(tool="EXTRACT", params={"fields": ["employee_id", "name", "team", "capacity"]}),
                WorkflowStep(tool="GENERATE_REPORT", params={"title": "Employee Overview Report"}),
            ]
    else:  # tickets / default
        steps = [
            WorkflowStep(tool="READ_DATA", params={"dataset": "tickets"}),
            WorkflowStep(tool="CLASSIFY", params={"field": "body", "category_field": "urgency", "categories": {"urgent": ["urgent", "immediately", "unacceptable", "blocking", "asap"], "normal": []}}),
            WorkflowStep(tool="CHECK_CONDITION", params={"field": "urgency", "operator": "==", "value": "urgent"}),
            WorkflowStep(tool="MAKE_DECISION", params={"true_branch": "escalate", "false_branch": "normal_queue"}),
            WorkflowStep(tool="ROUTE", params={"by": "urgency"}),
            WorkflowStep(tool="GENERATE_REPORT", params={"title": "Support Ticket Routing Report"}),
        ]

    if not has_decision:
        steps = [s for s in steps if s.tool not in ("CHECK_CONDITION", "MAKE_DECISION")]

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
