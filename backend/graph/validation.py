"""Safety / validation layer — sits between the Planner's raw output and the Critic.

Pipeline (spec §7): LLM output -> Structured Workflow JSON -> JSON Schema Validation
(handled by Pydantic in schemas/workflow.py) -> Allowed Tool Registry check (here) ->
Critic -> Executor.

Never let an unregistered tool name reach the Critic or the Executor. Every rejection
is logged with a reason so it can be shown on the demo as "here's what we blocked and why".
"""
from __future__ import annotations

from core.logging import get_logger
from schemas.workflow import Workflow, WorkflowStep
from tools.registry import is_valid_tool

logger = get_logger(__name__)

MAX_WORKFLOW_STEPS = 10


class ValidationResult:
    def __init__(self, valid_steps: list[WorkflowStep], rejected: list[dict]):
        self.valid_steps = valid_steps
        self.rejected = rejected

    @property
    def is_clean(self) -> bool:
        return not self.rejected


def validate_workflow(workflow: Workflow) -> ValidationResult:
    valid_steps: list[WorkflowStep] = []
    rejected: list[dict] = []

    steps = workflow.steps[:MAX_WORKFLOW_STEPS]
    if len(workflow.steps) > MAX_WORKFLOW_STEPS:
        rejected.append({
            "tool": None,
            "reason": f"Workflow exceeded max step limit of {MAX_WORKFLOW_STEPS}; extra steps dropped.",
        })

    for step in steps:
        if not is_valid_tool(step.tool):
            reason = f"Tool '{step.tool}' is not in the approved Tool Registry."
            logger.warning("Rejected workflow step: %s", reason)
            rejected.append({"tool": step.tool, "reason": reason})
            continue
        valid_steps.append(step)

    return ValidationResult(valid_steps=valid_steps, rejected=rejected)
