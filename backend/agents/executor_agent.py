"""Agent 4 — Executor.

Deterministic. Never calls an LLM and never generates its own data - it only ever
processes the sample dataset it's handed (synthesized ahead of time by
agents/data_synthesizer.py, based on whatever business problem the customer actually
described, not a fixed set of pre-built datasets).

If a step references a field that genuinely doesn't exist anywhere in the records it
was given, that's treated as a real capability gap - most often a live LLM Planner
referencing a field it invented rather than one from the Requirement's own `fields`.
Rather than silently returning a meaningless all-empty result, this raises
UnsupportedCapabilityError so the orchestrator can build a Workflow Blueprint instead
(the "no dead end" rule).
"""
from __future__ import annotations

import time
from typing import Any

from schemas.execution import ExecutionResult, StepResult
from schemas.workflow import Workflow, WorkflowStep
from tools.registry import run_tool

FIELD_REFERENCING_TOOLS = {"CHECK_CONDITION", "COMPARE", "CALCULATE"}


class UnsupportedCapabilityError(Exception):
    def __init__(self, step: WorkflowStep, field: str, record_label: str):
        self.step = step
        self.field = field
        self.record_label = record_label
        super().__init__(f"Field '{field}' not available on '{record_label}' records for tool '{step.tool}'.")


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
    workflow: Workflow,
    requirement_text: str,
    records: list[dict],
    record_label: str = "record",
    record_id: str | None = None,
) -> ExecutionResult:
    """`records` is the sample dataset already synthesized for this session. If
    `record_id` is given, only the one record whose "id" matches is processed - this
    is what powers the "try it live" single-record run in the mini-app, re-executing
    the same approved workflow against just that record rather than the whole batch."""
    dataset_records = records
    if record_id is not None:
        dataset_records = [r for r in records if str(r.get("id")) == str(record_id)]

    state: dict[str, Any] = {
        "data": None,
        "dataset_records": dataset_records,
        "requirement_text": requirement_text,
        "log": [],
    }
    step_results: list[StepResult] = []
    known_dynamic_fields: set[str] = set()

    for step in workflow.steps:
        start = time.perf_counter()

        if step.tool in FIELD_REFERENCING_TOOLS:
            field = step.params.get("field") or step.params.get("metric_field")
            if field and field not in known_dynamic_fields and not _field_exists(dataset_records, field):
                raise UnsupportedCapabilityError(step=step, field=field, record_label=record_label)

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
