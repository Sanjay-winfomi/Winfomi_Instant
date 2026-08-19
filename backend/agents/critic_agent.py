"""Agent 3 — Critic.

Scores a validated workflow 0-10 on four equally-weighted (25% each) criteria and
gates whether it proceeds to the Executor. The `overall_score` is ALWAYS recomputed
deterministically in Python from the sub-scores (schemas/critic.py) — the model's own
claimed overall figure, if it supplies one, is discarded. This is what makes approval
deterministic even though the sub-scores may come from an LLM.
"""
from __future__ import annotations

from agents.llm_provider import LLMUnavailableError, get_llm_provider
from core.config import get_settings
from core.logging import get_logger
from schemas.critic import CriticResult, CriticScores, compute_overall_score
from schemas.requirement import Requirement
from schemas.workflow import Workflow

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Critic in an AI workflow-generation pipeline. You review a
proposed workflow against the original requirement and score it 0-10 (can use decimals) on:
- requirement_understanding: does the workflow actually address the stated goal?
- workflow_completeness: does it cover reading data, any needed decision, and a final output?
- logical_correctness: is the step order sensible (e.g. conditions checked before decisions/actions)?
- tool_feasibility: can every step realistically run against the described input with the given tools?

Respond with ONLY this JSON object, no commentary:
{"scores": {"requirement_understanding": <0-10>, "workflow_completeness": <0-10>, "logical_correctness": <0-10>, "tool_feasibility": <0-10>}, "feedback": ["short actionable note", ...]}
If the workflow is strong, feedback can be an empty list."""


def _fallback_critic(
    requirement: Requirement, workflow: Workflow, rejected_count: int, total_proposed: int
) -> tuple[CriticScores, list[str]]:
    feedback: list[str] = []
    tool_names = [s.tool for s in workflow.steps]

    # requirement_understanding: did the plan touch on the requirement's action/decision?
    req_score = 9.0
    if requirement.decision and "CHECK_CONDITION" not in tool_names and "MAKE_DECISION" not in tool_names:
        req_score = 6.5
        feedback.append("Requirement implies a decision but no CHECK_CONDITION/MAKE_DECISION step was planned.")

    # workflow_completeness
    completeness = 9.0
    if len(workflow.steps) < 3:
        completeness = 5.0
        feedback.append("Workflow has too few steps to be considered complete.")
    elif tool_names[-1] != "GENERATE_REPORT":
        completeness = 7.0
        feedback.append("Workflow should end with GENERATE_REPORT to produce a clear final result.")
    if "READ_DATA" not in tool_names:
        completeness -= 2
        feedback.append("Workflow never reads any data.")

    # logical_correctness: ordering sanity checks
    logical = 9.0
    if "READ_DATA" in tool_names and tool_names[0] != "READ_DATA":
        logical -= 1.5
        feedback.append("Data should be read before any other processing step.")
    if "CHECK_CONDITION" in tool_names and "MAKE_DECISION" in tool_names:
        if tool_names.index("CHECK_CONDITION") > tool_names.index("MAKE_DECISION"):
            logical -= 3
            feedback.append("MAKE_DECISION appears before its CHECK_CONDITION.")

    # tool_feasibility: penalize proportional to how many proposed steps were rejected
    feasibility = 10.0
    if total_proposed > 0 and rejected_count > 0:
        feasibility = max(0.0, 10.0 - (rejected_count / total_proposed) * 10)
        feedback.append(f"{rejected_count} of {total_proposed} proposed step(s) referenced tools outside the registry.")

    return (
        CriticScores(
            requirement_understanding=round(req_score, 2),
            workflow_completeness=round(max(completeness, 0), 2),
            logical_correctness=round(max(logical, 0), 2),
            tool_feasibility=round(feasibility, 2),
        ),
        feedback,
    )


def critique_workflow(
    requirement: Requirement,
    workflow: Workflow,
    rejected_count: int,
    total_proposed: int,
    attempt: int = 1,
) -> tuple[CriticResult, str]:
    settings = get_settings()
    scores: CriticScores | None = None
    feedback: list[str] = []
    mode = "fallback"

    if settings.is_live:
        try:
            provider = get_llm_provider()
            user_prompt = (
                f"Requirement:\n{requirement.model_dump_json(indent=2)}\n\n"
                f"Proposed workflow:\n{workflow.model_dump_json(indent=2)}"
            )
            raw = provider.complete_json(SYSTEM_PROMPT, user_prompt, settings.llm_max_tokens)
            scores = CriticScores(**raw["scores"])
            feedback = list(raw.get("feedback", []))
            mode = "live"
        except (LLMUnavailableError, Exception) as exc:  # noqa: BLE001
            logger.warning("Critic falling back to deterministic scoring: %s", exc)

    if scores is None:
        scores, feedback = _fallback_critic(requirement, workflow, rejected_count, total_proposed)

    overall = compute_overall_score(scores)
    approved = overall >= settings.critic_approval_threshold and rejected_count == 0

    return (
        CriticResult(scores=scores, overall_score=overall, approved=approved, feedback=feedback, attempt=attempt),
        mode,
    )
