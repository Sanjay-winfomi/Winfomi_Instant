"""Builds the dynamic mini-app UI schema (schemas/ui_schema.py) that the frontend's
DynamicMiniAppRenderer consumes. Fully deterministic - derived only from data the
pipeline already computed (Requirement, Workflow, ExecutionResult, dataset_records),
never from an LLM and never hardcoded to a particular business domain. This is what
makes the mini-app a real generic renderer instead of one fixed template.
"""
from __future__ import annotations

from agents.data_synthesizer import is_numeric_field
from schemas.execution import ExecutionResult
from schemas.requirement import Requirement
from schemas.ui_schema import UiAction, UiComponent, UiInput, UiResult, UiSchema
from tools.mini_app import allowed_actions

_DATE_HINTS = ("date", "time")
_SELECT_HINTS = {
    "status": ["new", "in_progress", "resolved", "flagged"],
}


def _input_type_for(field: str) -> tuple[str, list[str] | None]:
    lowered = field.lower()
    if lowered in _SELECT_HINTS:
        return "select", _SELECT_HINTS[lowered]
    if any(h in lowered for h in _DATE_HINTS):
        return "date", None
    if is_numeric_field(field):
        return "number", None
    return "text", None


def build_ui_schema(
    requirement: Requirement | None,
    dataset_records: list[dict],
    execution: ExecutionResult | None,
) -> UiSchema | None:
    if not requirement:
        return None

    inputs: list[UiInput] = []
    for field in requirement.fields:
        if field.lower() == "id":
            continue
        input_type, options = _input_type_for(field)
        inputs.append(
            UiInput(id=f"field_{field}", type=input_type, label=field.replace("_", " ").title(), field=field, options=options)
        )
    if dataset_records:
        inputs.insert(
            0,
            UiInput(id="record_picker", type="record_picker", label=requirement.record_label.title(), field="id"),
        )

    actions: list[UiAction] = []
    if dataset_records:
        actions.append(UiAction(id="run", type="run", label=f"Run on selected {requirement.record_label}"))
    for option in allowed_actions(requirement):
        actions.append(UiAction(id=f"action_{option['action']}", type="record_action", label=option["label"], action=option["action"]))

    results: list[UiResult] = []
    if dataset_records:
        columns = [f for f in requirement.fields if f.lower() != "id"] or list(dataset_records[0].keys())
        results.append(
            UiResult(
                id="dataset_table",
                type="table",
                title=f"{requirement.record_label.title()} records",
                columns=columns,
                rows=dataset_records,
            )
        )
    if execution and execution.step_results:
        for i, step in enumerate(execution.step_results):
            results.append(
                UiResult(
                    id=f"step_{i}",
                    type="card",
                    title=step.tool.replace("_", " ").title(),
                    content=step.output if step.status == "success" else step.error,
                )
            )
    if requirement.decision:
        results.append(
            UiResult(
                id="decision_status",
                type="status",
                title=requirement.decision,
                content=execution.status if execution else "pending",
            )
        )

    components: list[UiComponent] = (
        [UiComponent(ref=f"input:{i.id}") for i in inputs]
        + [UiComponent(ref=f"action:{a.id}") for a in actions]
        + [UiComponent(ref=f"result:{r.id}") for r in results]
    )

    return UiSchema(
        app={"title": requirement.goal[:120] or "Your AI solution", "description": requirement.expected_output},
        inputs=inputs,
        actions=actions,
        results=results,
        components=components,
    )
