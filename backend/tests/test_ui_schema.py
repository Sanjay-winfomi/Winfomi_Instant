"""The dynamic mini-app UI schema (tools/ui_schema.py) must generalize across
unrelated, previously-unseen business domains - the generalization test required by
spec §49. Nothing here is domain-specific application logic; both fixtures below are
deliberately novel and not referenced anywhere else in the codebase."""
from agents.data_synthesizer import synthesize_dataset
from agents.executor_agent import run_workflow
from agents.planner_agent import plan_workflow
from agents.requirement_agent import analyze_requirement
from tools.ui_schema import build_ui_schema

NOVEL_FIXTURES = [
    "Track gym membership renewals and flag members whose plan expires within 7 days.",
    "Monitor greenhouse soil moisture sensors and alert staff when a zone is too dry.",
]


def test_ui_schema_is_none_without_a_requirement():
    assert build_ui_schema(None, [], None) is None


def test_ui_schema_generalizes_across_unrelated_domains():
    seen_titles = set()
    for text in NOVEL_FIXTURES:
        requirement, _ = analyze_requirement(text)
        workflow, _ = plan_workflow(requirement)
        records, _ = synthesize_dataset(requirement)
        execution = run_workflow(workflow, requirement.goal, records=records, record_label=requirement.record_label)

        schema = build_ui_schema(requirement, records, execution)
        assert schema is not None
        assert schema.app["title"]
        seen_titles.add(schema.app["title"])
        assert len(schema.inputs) >= 1
        assert any(i.type == "record_picker" for i in schema.inputs)
        assert len(schema.results) >= 1
        assert any(r.type == "table" for r in schema.results)
        # every component reference must resolve to a real input/action/result id
        ids = {f"input:{i.id}" for i in schema.inputs} | {f"action:{a.id}" for a in schema.actions} | {
            f"result:{r.id}" for r in schema.results
        }
        assert all(c.ref in ids for c in schema.components)

    # the two unrelated domains must not have produced an identical schema title -
    # proof this isn't secretly one hardcoded template
    assert len(seen_titles) == len(NOVEL_FIXTURES)
