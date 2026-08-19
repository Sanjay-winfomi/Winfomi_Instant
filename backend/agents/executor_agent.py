"""Agent 4 — Executor.

Deterministic. Never calls an LLM. Walks the approved, validated workflow and runs
each step against the Tool Registry, accumulating results.

If a step references a data field that genuinely does not exist anywhere in the
underlying mock dataset (as opposed to existing-but-false), that's treated as a real
capability gap - e.g. "frequently late employees" needs an attendance/lateness field
that employees.json simply doesn't have. Rather than silently returning a meaningless
all-empty result, this raises UnsupportedCapabilityError so the orchestrator can build
a Workflow Blueprint instead (spec §8) - the "no dead end" rule.
"""
from __future__ import annotations

import time
from typing import Any

from schemas.execution import ExecutionResult, StepResult
from schemas.workflow import Workflow, WorkflowStep
from tools.datasets import ID_FIELDS
from tools.registry import run_tool

FIELD_REFERENCING_TOOLS = {"CHECK_CONDITION", "COMPARE", "CALCULATE"}


class UnsupportedCapabilityError(Exception):
    def __init__(self, step: WorkflowStep, field: str, dataset: str):
        self.step = step
        self.field = field
        self.dataset = dataset
        super().__init__(f"Field '{field}' not available in dataset '{dataset}' for tool '{step.tool}'.")


def _field_exists(records: list[dict], field: str) -> bool:
    return any(field in r for r in records)


def _introduced_fields_for(step: WorkflowStep) -> list[str]:
    if step.tool == "CLASSIFY":
        return [step.params.get("category_field", "category")]
    if step.tool == "ANALYZE":
        return [step.params.get("output_field", "score")]
    if step.tool == "EXTRACT":
        return list(step.params.get("fields", []))
    return []


def _json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    return str(value)


def run_workflow(
    workflow: Workflow, requirement_text: str, record_id: str | None = None
) -> ExecutionResult:
    """If `record_id` is given, the workflow runs against just that one record from
    the dataset (matched on that dataset's natural id field) instead of the whole
    dataset - this is what powers the "try it live" single-record run in the mini-app,
    and it's a real re-execution of the same approved workflow, not a lookup."""
    state: dict[str, Any] = {"data": None, "requirement_text": requirement_text, "log": []}
    step_results: list[StepResult] = []
    raw_records: list[dict] | None = None
    dataset_name: str | None = None
    known_dynamic_fields: set[str] = set()

    for step in workflow.steps:
        start = time.perf_counter()

        if step.tool == "READ_DATA":
            dataset_name = step.params.get("dataset")

        if step.tool in FIELD_REFERENCING_TOOLS and raw_records is not None:
            field = step.params.get("field") or step.params.get("metric_field")
            if field and field not in known_dynamic_fields and not _field_exists(raw_records, field):
                raise UnsupportedCapabilityError(step=step, field=field, dataset=dataset_name or "unknown")

        try:
            output = run_tool(step.tool, step.params, state)
        except UnsupportedCapabilityError:
            raise
        except Exception as exc:  # a genuine runtime failure in an otherwise valid tool
            duration_ms = int((time.perf_counter() - start) * 1000)
            step_results.append(
                StepResult(tool=step.tool, params=step.params, status="failed", error=str(exc), duration_ms=duration_ms)
            )
            state["data"] = None
            continue

        if step.tool == "READ_DATA" and raw_records is None:
            raw_records = output if isinstance(output, list) else [output]
            dataset_name = state.get("dataset_name", dataset_name)
            if record_id is not None:
                id_field = ID_FIELDS.get(dataset_name or "")
                if id_field:
                    output = [r for r in raw_records if str(r.get(id_field)) == str(record_id)]

        known_dynamic_fields.update(_introduced_fields_for(step))

        duration_ms = int((time.perf_counter() - start) * 1000)
        state["data"] = output
        step_results.append(
            StepResult(tool=step.tool, params=step.params, status="success", output=_json_safe(output), duration_ms=duration_ms)
        )

    any_failed = any(r.status == "failed" for r in step_results)
    final_output = step_results[-1].output if step_results else None

    return ExecutionResult(
        status="partial" if any_failed else "success",
        step_results=step_results,
        final_output=final_output,
    )
