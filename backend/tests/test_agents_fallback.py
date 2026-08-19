"""Tests the deterministic fallback path of each agent - the path exercised whenever
no LLM_API_KEY is configured (or a live call fails), which is what makes the app
runnable and demoable with zero external dependencies. None of this is dataset-
specific: every case here synthesizes its own sample data on the fly."""
from agents.critic_agent import critique_workflow
from agents.data_synthesizer import synthesize_dataset
from agents.executor_agent import UnsupportedCapabilityError, run_workflow
from agents.planner_agent import plan_workflow
from agents.requirement_agent import analyze_requirement


def test_requirement_agent_fallback_produces_valid_schema():
    requirement, mode = analyze_requirement("Alert suppliers when stock falls below 20%.")
    assert mode == "fallback"
    assert requirement.goal
    assert requirement.record_label
    assert requirement.fields
    assert requirement.expected_output


def test_requirement_agent_handles_a_completely_novel_domain():
    """No keyword in this sentence maps to any of the old fixed mock datasets -
    proves the engine isn't secretly tied to a handful of pre-built categories."""
    requirement, mode = analyze_requirement(
        "Track field sales rep visits and flag reps who haven't logged a visit in 14 days."
    )
    assert mode == "fallback"
    assert requirement.record_label  # some label was derived, even if generic
    assert len(requirement.fields) >= 2


def test_planner_fallback_only_uses_registry_tools():
    from tools.registry import is_valid_tool

    requirement, _ = analyze_requirement("Monitor inventory and alert suppliers when stock is low.")
    workflow, mode = plan_workflow(requirement)
    assert mode == "fallback"
    assert len(workflow.steps) >= 3
    for step in workflow.steps:
        assert is_valid_tool(step.tool)


def test_data_synthesizer_fallback_generates_requested_fields_plus_id():
    requirement, _ = analyze_requirement("Monitor inventory and alert suppliers when stock is low.")
    records, mode = synthesize_dataset(requirement)
    assert mode == "fallback"
    assert len(records) == 6
    for r in records:
        assert "id" in r
        for field in requirement.fields:
            assert field in r


def test_critic_fallback_approves_a_clean_workflow():
    requirement, _ = analyze_requirement("Route urgent complaints to escalation team.")
    workflow, _ = plan_workflow(requirement)
    critic, mode = critique_workflow(requirement, workflow, rejected_count=0, total_proposed=len(workflow.steps))
    assert mode == "fallback"
    assert critic.overall_score >= 8.0
    assert critic.approved is True


def test_critic_fallback_penalizes_rejected_steps():
    requirement, _ = analyze_requirement("Route urgent complaints to escalation team.")
    workflow, _ = plan_workflow(requirement)
    critic, _ = critique_workflow(requirement, workflow, rejected_count=2, total_proposed=len(workflow.steps) + 2)
    assert critic.scores.tool_feasibility < 10.0


def test_executor_runs_inventory_style_workflow_and_flags_low_stock():
    requirement, _ = analyze_requirement("Monitor inventory and alert suppliers when stock falls below 20%.")
    workflow, _ = plan_workflow(requirement)
    records, _ = synthesize_dataset(requirement)
    execution = run_workflow(workflow, requirement.goal, records=records, record_label=requirement.record_label)
    assert execution.status == "success"
    assert execution.final_output is not None


def test_executor_raises_capability_gap_for_field_missing_from_records():
    requirement, _ = analyze_requirement("Monitor inventory and alert suppliers when stock is low.")
    workflow, _ = plan_workflow(requirement)
    records, _ = synthesize_dataset(requirement)
    # simulate a Planner step referencing a field that was never synthesized
    from schemas.workflow import Workflow, WorkflowStep

    bad_workflow = Workflow(steps=[
        WorkflowStep(tool="READ_DATA", params={}),
        WorkflowStep(tool="CHECK_CONDITION", params={"field": "totally_made_up_field", "operator": ">", "value": 1}),
        WorkflowStep(tool="GENERATE_REPORT", params={"title": "x"}),
    ])
    try:
        run_workflow(bad_workflow, requirement.goal, records=records, record_label=requirement.record_label)
        assert False, "expected UnsupportedCapabilityError"
    except UnsupportedCapabilityError as exc:
        assert exc.field == "totally_made_up_field"
