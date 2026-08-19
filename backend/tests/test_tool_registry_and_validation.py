from graph.validation import MAX_WORKFLOW_STEPS, validate_workflow
from schemas.workflow import Workflow, WorkflowStep
from tools.registry import TOOL_REGISTRY, is_valid_tool, run_tool


def test_all_registry_tools_are_callable():
    for name, fn in TOOL_REGISTRY.items():
        assert callable(fn), f"{name} is not callable"


def test_is_valid_tool_rejects_hallucinated_name():
    assert is_valid_tool("READ_DATA") is True
    assert is_valid_tool("DELETE_EVERYTHING") is False
    assert is_valid_tool("") is False


def test_validate_workflow_strips_unregistered_tool_and_logs_reason():
    workflow = Workflow(steps=[
        WorkflowStep(tool="READ_DATA", params={"dataset": "tickets"}),
        WorkflowStep(tool="RUN_ARBITRARY_CODE", params={}),
        WorkflowStep(tool="GENERATE_REPORT", params={}),
    ])
    result = validate_workflow(workflow)
    assert [s.tool for s in result.valid_steps] == ["READ_DATA", "GENERATE_REPORT"]
    assert len(result.rejected) == 1
    assert result.rejected[0]["tool"] == "RUN_ARBITRARY_CODE"
    assert not result.is_clean


def test_validate_workflow_enforces_max_step_limit():
    steps = [WorkflowStep(tool="READ_DATA", params={"dataset": "tickets"}) for _ in range(MAX_WORKFLOW_STEPS + 3)]
    result = validate_workflow(Workflow(steps=steps))
    assert len(result.valid_steps) == MAX_WORKFLOW_STEPS
    assert any(r["tool"] is None for r in result.rejected)


def test_read_data_then_check_condition_execution():
    state = {"data": None, "requirement_text": "", "log": []}
    records = run_tool("READ_DATA", {"dataset": "inventory"}, state)
    state["data"] = records
    scored = run_tool("ANALYZE", {"method": "stock_percentage", "output_field": "stock_pct"}, state)
    state["data"] = scored
    result = run_tool("CHECK_CONDITION", {"field": "stock_pct", "operator": "<", "value": 20}, state)
    assert "matched" in result and "unmatched" in result
    assert all(r["stock_pct"] < 20 for r in result["matched"])
