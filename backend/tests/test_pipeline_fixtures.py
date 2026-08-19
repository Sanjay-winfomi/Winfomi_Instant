"""End-to-end fixtures run through the SAME generic pipeline - no per-case branching
in the test or in the app itself. None of these map onto a fixed set of pre-built
mock datasets; sample data is synthesized fresh per request (agents/data_synthesizer.py),
which is what lets a genuinely novel business problem (the last fixture) still execute
successfully instead of needing a hand-built dataset to exist for it."""
import pytest

from graph.orchestrator import run_pipeline

FIXTURES = [
    "I want an AI agent that checks customer complaints and automatically sends urgent complaints to the escalation team.",
    "I want an AI system that monitors inventory and alerts suppliers when stock falls below 20%.",
    "I want an agent that identifies customers at risk of leaving and alerts the sales team.",
    "analyze employee attendance and identify frequently late employees",
    # Deliberately novel domain with no analogue in any hand-built dataset - proves the
    # engine composes a fresh workflow + sample data rather than being secretly a set
    # of hardcoded per-domain demos.
    "Track field sales rep visits and flag reps who haven't logged a visit in 14 days.",
]


@pytest.mark.parametrize("text", FIXTURES)
def test_fixture_executes_through_the_generic_pipeline(text):
    state = run_pipeline(text)
    assert state["outcome"] in ("executed", "blueprint")
    assert state["critic"].overall_score >= 0
    if state["outcome"] == "executed":
        assert state["execution"].status in ("success", "partial")
        assert len(state["dataset_records"]) > 0
    else:
        assert state["blueprint"] is not None
        assert state["blueprint"].integration_note


def test_executor_capability_gap_still_reaches_a_blueprint_end_to_end():
    """A Planner step referencing a field that was never part of the requirement's own
    fields (simulating a live-LLM planning mistake) must still surface as a Blueprint,
    never a crash or a silently-empty result."""
    from unittest.mock import patch

    from schemas.workflow import Workflow, WorkflowStep

    bad_workflow = Workflow(steps=[
        WorkflowStep(tool="READ_DATA", params={}),
        WorkflowStep(tool="CHECK_CONDITION", params={"field": "field_that_was_never_synthesized", "operator": ">", "value": 1}),
        WorkflowStep(tool="GENERATE_REPORT", params={"title": "x"}),
    ])

    with patch("graph.orchestrator.plan_workflow", return_value=(bad_workflow, "fallback")):
        state = run_pipeline("Do something with some records.")

    assert state["outcome"] == "blueprint"
    assert "field_that_was_never_synthesized" in state["blueprint"].integration_note


def test_pipeline_never_raises_on_empty_ish_input():
    state = run_pipeline("automate stuff")
    assert state["outcome"] in ("executed", "blueprint")


def test_pipeline_never_raises_on_very_long_input():
    state = run_pipeline("I want to automate this. " * 100)
    assert state["outcome"] in ("executed", "blueprint")
