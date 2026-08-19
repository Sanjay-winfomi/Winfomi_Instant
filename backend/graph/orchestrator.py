"""LangGraph orchestration of the 4-agent pipeline.

Requirement -> Planner -> Validate (Tool Registry safety layer) -> Critic
  -> (score < threshold and retries remain) -> back to Planner with feedback
  -> (score >= threshold) -> synthesize sample data -> Executor -> done
  -> (retries exhausted, still rejected) -> Workflow Blueprint
  -> (Executor hits a genuine capability gap) -> Workflow Blueprint

Sample data is generated fresh per requirement (agents/data_synthesizer.py) rather
than read from a fixed set of pre-built mock datasets - the Executor itself never
calls an LLM or generates data; it only ever processes records it's handed.

If the caller already has REAL data (e.g. an uploaded CSV/Excel file), pass it as
`override_records`/`override_fields`/`override_record_label` to run_pipeline() and
synthesis is skipped entirely - the workflow runs against the customer's actual data.
"""
from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from agents.critic_agent import critique_workflow
from agents.data_synthesizer import synthesize_dataset
from agents.executor_agent import UnsupportedCapabilityError, run_workflow
from agents.planner_agent import plan_workflow
from agents.requirement_agent import analyze_requirement
from core.config import get_settings
from core.logging import get_logger
from schemas.critic import CriticResult
from schemas.execution import ExecutionResult, WorkflowBlueprint
from schemas.requirement import Requirement
from schemas.workflow import Workflow
from graph.validation import validate_workflow

logger = get_logger(__name__)


class PipelineState(TypedDict, total=False):
    text: str
    override_records: list[dict[str, Any]] | None
    override_fields: list[str] | None
    override_record_label: str | None
    requirement: Requirement
    requirement_mode: str
    workflow: Workflow
    rejected_steps: list[dict[str, Any]]
    critic: CriticResult
    critic_history: list[CriticResult]
    critic_mode: str
    planner_mode: str
    attempt: int
    outcome: str  # executed | blueprint | error
    execution: ExecutionResult
    dataset_records: list[dict[str, Any]]
    dataset_mode: str
    blueprint: WorkflowBlueprint
    error: str | None


def _requirement_node(state: PipelineState) -> dict:
    requirement, mode = analyze_requirement(state["text"])
    # Real uploaded data always wins over a guessed/LLM-inferred shape - the file's
    # own columns ARE the ground truth for record_label/fields.
    if state.get("override_record_label"):
        requirement.record_label = state["override_record_label"]
    if state.get("override_fields"):
        requirement.fields = state["override_fields"]
    logger.info("Requirement analyzed (mode=%s): %s", mode, requirement.goal)
    return {"requirement": requirement, "requirement_mode": mode, "attempt": 0, "critic_history": []}


def _planner_node(state: PipelineState) -> dict:
    attempt = state.get("attempt", 0) + 1
    feedback = state.get("critic").feedback if state.get("critic") else None
    workflow, mode = plan_workflow(state["requirement"], feedback=feedback, attempt=attempt)
    logger.info("Planned workflow attempt %d (mode=%s): %d step(s)", attempt, mode, len(workflow.steps))
    return {"workflow": workflow, "planner_mode": mode, "attempt": attempt}


def _validate_node(state: PipelineState) -> dict:
    result = validate_workflow(state["workflow"])
    validated_workflow = Workflow(steps=result.valid_steps)
    return {"workflow": validated_workflow, "rejected_steps": result.rejected}


def _critic_node(state: PipelineState) -> dict:
    critic, mode = critique_workflow(
        requirement=state["requirement"],
        workflow=state["workflow"],
        rejected_count=len(state.get("rejected_steps", [])),
        total_proposed=len(state["workflow"].steps) + len(state.get("rejected_steps", [])),
        attempt=state.get("attempt", 1),
    )
    history = list(state.get("critic_history", [])) + [critic]
    logger.info("Critic score attempt %d: %.2f (approved=%s, mode=%s)", state.get("attempt", 1), critic.overall_score, critic.approved, mode)
    return {"critic": critic, "critic_history": history, "critic_mode": mode}


def _executor_node(state: PipelineState) -> dict:
    requirement: Requirement = state["requirement"]

    if state.get("override_records"):
        records, dataset_mode = state["override_records"], "uploaded_file"
        logger.info("Using %d uploaded '%s' record(s) - no synthesis.", len(records), requirement.record_label)
    else:
        records, dataset_mode = synthesize_dataset(requirement)
        logger.info("Synthesized %d sample '%s' record(s) (mode=%s)", len(records), requirement.record_label, dataset_mode)

    try:
        execution = run_workflow(state["workflow"], state["text"], records=records, record_label=requirement.record_label)
        return {"execution": execution, "outcome": "executed", "dataset_records": records, "dataset_mode": dataset_mode}
    except UnsupportedCapabilityError as exc:
        logger.info("Executor hit a capability gap: %s", exc)
        blueprint = _build_blueprint(state, integration_note=(
            f"This workflow needs a '{exc.field}' field that isn't part of the generated "
            f"sample data for '{exc.record_label}' records. Connecting a live data source "
            f"that actually provides this field (e.g. a CRM field, an internal system, or "
            f"a data warehouse column) would let this step run for real."
        ))
        return {"blueprint": blueprint, "outcome": "blueprint", "dataset_records": records, "dataset_mode": dataset_mode}


def _blueprint_node(state: PipelineState) -> dict:
    blueprint = _build_blueprint(
        state,
        integration_note=(
            "The generated workflow didn't reach the required quality bar after "
            f"{get_settings().max_planner_retries + 1} attempt(s). Below is the best "
            "workflow blueprint produced so far, along with what it would take to run it live."
        ),
    )
    return {"blueprint": blueprint, "outcome": "blueprint"}


def _build_blueprint(state: PipelineState, integration_note: str) -> WorkflowBlueprint:
    requirement: Requirement = state["requirement"]
    workflow: Workflow = state["workflow"]
    return WorkflowBlueprint(
        requirement_analysis=requirement.model_dump(),
        proposed_workflow=[s.model_dump() for s in workflow.steps],
        tools_required=sorted({s.tool for s in workflow.steps}),
        expected_output_description=requirement.expected_output,
        integration_note=integration_note,
    )


def _after_critic(state: PipelineState) -> str:
    critic: CriticResult = state["critic"]
    settings = get_settings()
    if critic.approved:
        return "executor"
    if state.get("attempt", 1) <= settings.max_planner_retries:
        return "planner"
    return "blueprint"


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("analyze_requirement", _requirement_node)
    graph.add_node("plan_workflow", _planner_node)
    graph.add_node("validate_workflow", _validate_node)
    graph.add_node("critic_review", _critic_node)
    graph.add_node("execute_workflow", _executor_node)
    graph.add_node("build_blueprint", _blueprint_node)

    graph.set_entry_point("analyze_requirement")
    graph.add_edge("analyze_requirement", "plan_workflow")
    graph.add_edge("plan_workflow", "validate_workflow")
    graph.add_edge("validate_workflow", "critic_review")
    graph.add_conditional_edges(
        "critic_review",
        _after_critic,
        {"planner": "plan_workflow", "executor": "execute_workflow", "blueprint": "build_blueprint"},
    )
    graph.add_edge("execute_workflow", END)
    graph.add_edge("build_blueprint", END)

    return graph.compile()


_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_pipeline(
    text: str,
    override_records: list[dict[str, Any]] | None = None,
    override_fields: list[str] | None = None,
    override_record_label: str | None = None,
) -> PipelineState:
    graph = get_compiled_graph()
    final_state = graph.invoke({
        "text": text,
        "override_records": override_records,
        "override_fields": override_fields,
        "override_record_label": override_record_label,
    })
    return final_state
