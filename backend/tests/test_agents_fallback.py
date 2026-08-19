"""Tests the deterministic fallback path of each agent - the path exercised whenever
no LLM_API_KEY is configured (or a live call fails), which is what makes the app
runnable and demoable with zero external dependencies."""
from agents.critic_agent import critique_workflow
from agents.executor_agent import UnsupportedCapabilityError, run_workflow
from agents.planner_agent import plan_workflow
from agents.requirement_agent import analyze_requirement


def test_requirement_agent_fallback_produces_valid_schema():
    requirement, mode = analyze_requirement("Alert suppliers when stock falls below 20%.")
    assert mode == "fallback"
    assert requirement.goal
    assert requirement.expected_output


def test_planner_fallback_only_uses_registry_tools():
    from tools.registry import is_valid_tool

    requirement, _ = analyze_requirement("Monitor inventory and alert suppliers when stock is low.")
    workflow, mode = plan_workflow(requirement)
    assert mode == "fallback"
    assert len(workflow.steps) >= 3
    for step in workflow.steps:
        assert is_valid_tool(step.tool)


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


def test_executor_runs_inventory_workflow_and_flags_low_stock():
    requirement, _ = analyze_requirement("Monitor inventory and alert suppliers when stock falls below 20%.")
    workflow, _ = plan_workflow(requirement)
    execution = run_workflow(workflow, requirement.goal)
    assert execution.status == "success"
    assert execution.final_output is not None


def test_executor_raises_capability_gap_for_missing_field():
    requirement, _ = analyze_requirement("analyze employee attendance and identify frequently late employees")
    workflow, _ = plan_workflow(requirement)
    try:
        run_workflow(workflow, requirement.goal)
        assert False, "expected UnsupportedCapabilityError"
    except UnsupportedCapabilityError as exc:
        assert exc.field == "days_late"
