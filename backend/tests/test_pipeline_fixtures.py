"""End-to-end fixtures from the master prompt (spec §10), run through the SAME
generic pipeline - no per-case branching in the test or in the app itself. Case 5
is the critical one: it proves the engine isn't a set of hardcoded demos, because
a genuinely novel domain correctly produces a Workflow Blueprint instead of either
crashing or faking a result."""
import pytest

from graph.orchestrator import run_pipeline

FIXTURES = [
    ("I want an AI agent that checks customer complaints and automatically sends urgent complaints to the escalation team.", "executed"),
    ("I want an AI system that monitors inventory and alerts suppliers when stock falls below 20%.", "executed"),
    ("Analyze customer reviews and identify products whose sentiment is declining.", "executed"),
    ("I want an agent that identifies customers at risk of leaving and alerts the sales team.", "executed"),
    ("analyze employee attendance and identify frequently late employees", "blueprint"),
]


@pytest.mark.parametrize("text,expected_outcome", FIXTURES)
def test_fixture_reaches_expected_outcome(text, expected_outcome):
    state = run_pipeline(text)
    assert state["outcome"] == expected_outcome
    assert state["critic"].overall_score >= 0
    if expected_outcome == "executed":
        assert state["execution"].status in ("success", "partial")
    else:
        assert state["blueprint"] is not None
        assert state["blueprint"].integration_note


def test_pipeline_never_raises_on_empty_ish_input():
    state = run_pipeline("automate stuff")
    assert state["outcome"] in ("executed", "blueprint")


def test_pipeline_never_raises_on_very_long_input():
    state = run_pipeline("I want to automate this. " * 100)
    assert state["outcome"] in ("executed", "blueprint")
