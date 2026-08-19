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
        WorkflowStep(tool="READ_DATA", params={}),
        WorkflowStep(tool="RUN_ARBITRARY_CODE", params={}),
        WorkflowStep(tool="GENERATE_REPORT", params={}),
    ])
    result = validate_workflow(workflow)
    assert [s.tool for s in result.valid_steps] == ["READ_DATA", "GENERATE_REPORT"]
    assert len(result.rejected) == 1
    assert result.rejected[0]["tool"] == "RUN_ARBITRARY_CODE"
    assert not result.is_clean


def test_validate_workflow_enforces_max_step_limit():
    steps = [WorkflowStep(tool="READ_DATA", params={}) for _ in range(MAX_WORKFLOW_STEPS + 3)]
    result = validate_workflow(Workflow(steps=steps))
    assert len(result.valid_steps) == MAX_WORKFLOW_STEPS
    assert any(r["tool"] is None for r in result.rejected)


def test_read_data_reads_from_injected_dataset_records():
    """READ_DATA never touches a fixed mock dataset - it reads whatever sample
    records were synthesized for this request (state["dataset_records"])."""
    synthetic_records = [
        {"id": "item-001", "stock_level": 14, "supplier": "ABC Co"},
        {"id": "item-002", "stock_level": 80, "supplier": "XYZ Co"},
    ]
    state = {"data": None, "dataset_records": synthetic_records, "requirement_text": "", "log": []}
    records = run_tool("READ_DATA", {}, state)
    assert records == synthetic_records

    state["data"] = records
    result = run_tool("CHECK_CONDITION", {"field": "stock_level", "operator": "<", "value": 20}, state)
    assert "matched" in result and "unmatched" in result
    assert all(r["stock_level"] < 20 for r in result["matched"])


def test_analyze_sums_numeric_fields_generically_without_weights():
    state = {"data": [{"id": "a", "amount": 10, "count": 5}], "requirement_text": "", "log": []}
    out = run_tool("ANALYZE", {"output_field": "total"}, state)
    assert out[0]["total"] == 15


def test_route_tags_records_with_planner_supplied_team_no_fixed_directory():
    state = {"data": [{"id": "a"}, {"id": "b"}], "requirement_text": "", "log": []}
    out = run_tool("ROUTE", {"team": "Escalation team"}, state)
    assert all(r["team"] == "Escalation team" for r in out)
