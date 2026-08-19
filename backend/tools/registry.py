"""The Tool Registry — the ONLY execution surface the Executor is allowed to touch.

Every tool is a small, independently-testable, deterministic Python function with a
fixed (params, state) -> output contract. The Planner LLM may only ever reference a
tool by the exact names in TOOL_REGISTRY; anything else is rejected before it reaches
the Critic (see graph/validation.py).

`state` is a plain dict threaded through the whole workflow execution:
  - state["data"]        current working value (list of records, one record, or a scalar)
  - state["requirement_text"]  original customer text, used as a fallback signal
  - state["log"]         list of human-readable notes appended by tools (for the demo trace)
"""
from __future__ import annotations

import time
from typing import Any, Callable

from tools.datasets import AVAILABLE_DATASETS, guess_dataset, load_dataset

ToolFn = Callable[[dict, dict], Any]


def _resolve_dataset(params: dict, state: dict) -> tuple[str, list[dict]]:
    name = params.get("dataset")
    if name in AVAILABLE_DATASETS:
        return name, list(load_dataset(name))
    guessed = guess_dataset(state.get("requirement_text", "")) or "tickets"
    return guessed, list(load_dataset(guessed))


def _as_records(data: Any) -> list[dict]:
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


# ---------------------------------------------------------------------------
# Data tools
# ---------------------------------------------------------------------------

def read_data(params: dict, state: dict) -> Any:
    name, records = _resolve_dataset(params, state)
    state["log"].append(f"Read {len(records)} record(s) from '{name}'.")
    state["dataset_name"] = name
    return records


def search_data(params: dict, state: dict) -> Any:
    records = _as_records(state.get("data"))
    field = params.get("field")
    contains = str(params.get("contains", "")).lower()
    if not field or not contains:
        return records
    matched = [r for r in records if contains in str(r.get(field, "")).lower()]
    state["log"].append(f"Searched for '{contains}' in '{field}': {len(matched)} match(es).")
    return matched


def write_data(params: dict, state: dict) -> Any:
    """Simulated write — MVP never persists to real external systems, only logs."""
    records = _as_records(state.get("data"))
    state["log"].append(f"Simulated write of {len(records)} record(s) (no external system connected in MVP).")
    return records


# ---------------------------------------------------------------------------
# AI tools — deterministic, rule-based (no LLM calls at execution time, so the
# customer-facing sandbox never depends on live API latency/cost per record)
# ---------------------------------------------------------------------------

_URGENT_KEYWORDS = ["urgent", "immediately", "unacceptable", "asap", "blocking", "production down", "escalat"]
_NEGATIVE_KEYWORDS = ["bad", "disappoint", "overheat", "stopped working", "broken", "worse", "outage", "fail"]
_POSITIVE_KEYWORDS = ["great", "love", "happy", "reliable", "smooth", "solid", "good"]


def classify(params: dict, state: dict) -> Any:
    records = _as_records(state.get("data"))
    field = params.get("field", "body")
    category_field = params.get("category_field", "category")
    categories: dict[str, list[str]] = params.get("categories") or {
        "urgent": _URGENT_KEYWORDS,
        "normal": [],
    }
    out = []
    for r in records:
        text = f"{r.get('subject', '')} {r.get(field, '')}".lower()
        assigned = "normal"
        for cat, keywords in categories.items():
            if keywords and any(kw in text for kw in keywords):
                assigned = cat
                break
        new_r = {**r, category_field: assigned}
        out.append(new_r)
    state["log"].append(f"Classified {len(out)} record(s) using keyword rules.")
    return out


def extract(params: dict, state: dict) -> Any:
    records = _as_records(state.get("data"))
    fields = params.get("fields") or (list(records[0].keys()) if records else [])
    out = [{f: r.get(f) for f in fields} for r in records]
    state["log"].append(f"Extracted fields {fields} from {len(out)} record(s).")
    return out


def summarize(params: dict, state: dict) -> Any:
    records = _as_records(state.get("data"))
    field = params.get("field", "text")
    summaries = []
    for r in records:
        text = str(r.get(field, ""))
        summaries.append({**r, "summary": (text[:80] + "...") if len(text) > 80 else text})
    state["log"].append(f"Summarized {len(summaries)} record(s).")
    return summaries


def analyze(params: dict, state: dict) -> Any:
    """Computes a weighted numeric score per record — used for risk scoring, sentiment
    scoring, etc. Falls back to sensible defaults when the Planner doesn't supply weights."""
    records = _as_records(state.get("data"))
    method = params.get("method", "risk_score")
    output_field = params.get("output_field", "score")

    if method == "sentiment":
        out = []
        for r in records:
            text = str(r.get("text", "")).lower()
            pos = sum(1 for kw in _POSITIVE_KEYWORDS if kw in text)
            neg = sum(1 for kw in _NEGATIVE_KEYWORDS if kw in text)
            rating = r.get("rating", 3)
            score = round(rating - neg * 1.5 + pos * 0.5, 2)
            out.append({**r, output_field: score})
        state["log"].append(f"Computed sentiment scores for {len(out)} record(s).")
        return out

    if method == "stock_percentage":
        out = []
        for r in records:
            current = r.get("current_stock", 0)
            max_stock = r.get("max_stock") or 1
            pct = round((current / max_stock) * 100, 2)
            out.append({**r, output_field: pct})
        state["log"].append(f"Computed stock percentage for {len(out)} record(s).")
        return out

    if method == "risk_score" and not params.get("weights"):
        # Purpose-built customer-health formula (not a generic linear blend): recent
        # support load and low satisfaction dominate, with an urgency bonus when the
        # renewal window is closing - this gives clean separation on the sample data
        # instead of one field (e.g. renewal_days' wide range) drowning out the rest.
        out = []
        for r in records:
            tickets = r.get("support_tickets_last_30d", 0)
            logins = r.get("logins_last_30d", 0)
            nps = r.get("nps_score", 5)
            renewal_days = r.get("contract_renewal_days", 999)
            urgency_bonus = 50 if renewal_days < 30 else 0
            score = tickets * 5 + (10 - nps) * 4 + urgency_bonus - logins * 1
            out.append({**r, output_field: round(score, 2)})
        state["log"].append(f"Computed customer risk scores for {len(out)} record(s).")
        return out

    # Generic weighted blend, used when the Planner supplies explicit weights.
    weights: dict[str, float] = params.get("weights") or {
        "support_tickets_last_30d": 0.35,
        "logins_last_30d": -0.25,
        "contract_renewal_days": -0.2,
        "nps_score": -0.2,
    }
    out = []
    for r in records:
        score = 0.0
        for field, weight in weights.items():
            value = r.get(field)
            if isinstance(value, (int, float)):
                score += value * weight
        out.append({**r, output_field: round(score, 2)})
    state["log"].append(f"Computed '{method}' for {len(out)} record(s) using weighted signals.")
    return out


def generate(params: dict, state: dict) -> Any:
    template = params.get("template", "Result: {data}")
    try:
        text = template.format(data=state.get("data"))
    except Exception:
        text = template
    state["log"].append("Generated output text from template.")
    return text


# ---------------------------------------------------------------------------
# Logic tools
# ---------------------------------------------------------------------------

_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "contains": lambda a, b: str(b).lower() in str(a).lower(),
}


def check_condition(params: dict, state: dict) -> Any:
    records = _as_records(state.get("data"))
    field = params.get("field", "score")
    operator = params.get("operator", ">")
    value = params.get("value", 0)
    op_fn = _OPERATORS.get(operator, _OPERATORS[">"])

    matched, unmatched = [], []
    for r in records:
        field_value = r.get(field)
        if field_value is None:
            unmatched.append(r)
            continue
        try:
            passed = op_fn(field_value, value)
        except TypeError:
            passed = False
        (matched if passed else unmatched).append({**r, "_condition_met": passed})

    state["log"].append(
        f"Checked condition '{field} {operator} {value}': {len(matched)} matched, {len(unmatched)} did not."
    )
    return {"matched": matched, "unmatched": unmatched}


def compare(params: dict, state: dict) -> Any:
    """Compares a metric across two groups/periods — used for trend analysis (e.g.
    declining sentiment for products.json, whose reviews carry a 'period' tag)."""
    records = _as_records(state.get("data"))
    group_field = params.get("group_field", "product")
    period_field = params.get("period_field", "period")
    metric_field = params.get("metric_field", "rating")
    baseline = params.get("baseline", "last_month")
    current = params.get("current", "this_month")

    grouped: dict[str, dict[str, list[float]]] = {}
    for r in records:
        group = r.get(group_field, "unknown")
        period = r.get(period_field)
        value = r.get(metric_field)
        if period not in (baseline, current) or value is None:
            continue
        grouped.setdefault(group, {baseline: [], current: []}).setdefault(period, []).append(value)

    results = []
    for group, periods in grouped.items():
        base_vals = periods.get(baseline, [])
        cur_vals = periods.get(current, [])
        base_avg = round(sum(base_vals) / len(base_vals), 2) if base_vals else None
        cur_avg = round(sum(cur_vals) / len(cur_vals), 2) if cur_vals else None
        delta = round(cur_avg - base_avg, 2) if (base_avg is not None and cur_avg is not None) else None
        results.append({
            group_field: group,
            f"{baseline}_avg": base_avg,
            f"{current}_avg": cur_avg,
            "delta": delta,
            "declining": bool(delta is not None and delta < 0),
        })
    state["log"].append(f"Compared '{metric_field}' across {len(results)} group(s).")
    return results


def calculate(params: dict, state: dict) -> Any:
    operation = params.get("operation", "count")
    records = _as_records(state.get("data"))
    field = params.get("field")

    if operation == "count":
        result = len(records)
    elif operation == "percentage" and field:
        numerator = params.get("numerator", len(records))
        denominator = params.get("denominator") or len(records) or 1
        result = round((numerator / denominator) * 100, 2)
    elif operation == "average" and field:
        values = [r.get(field) for r in records if isinstance(r.get(field), (int, float))]
        result = round(sum(values) / len(values), 2) if values else 0
    else:
        result = len(records)
    state["log"].append(f"Calculated '{operation}' -> {result}.")
    return result


def make_decision(params: dict, state: dict) -> Any:
    data = state.get("data")
    true_branch = params.get("true_branch", "proceed")
    false_branch = params.get("false_branch", "no_action")

    if isinstance(data, dict) and "matched" in data:
        decided = true_branch if data["matched"] else false_branch
        subject = data["matched"] if data["matched"] else data.get("unmatched", [])
    else:
        records = _as_records(data)
        decided = true_branch if records else false_branch
        subject = records
    state["log"].append(f"Decision: '{decided}'.")
    return {"decision": decided, "subject": subject}


# ---------------------------------------------------------------------------
# Action tools — all simulated in MVP. No real external system is contacted;
# each returns a structured record of what WOULD have been sent, for the demo.
# ---------------------------------------------------------------------------

def send_email(params: dict, state: dict) -> Any:
    to = params.get("to", "sales@company.com")
    subject = params.get("subject", "Automated notification")
    body = params.get("body") or str(state.get("data"))[:300]
    state["log"].append(f"[SIMULATED] Email queued to {to}: '{subject}'.")
    return {"channel": "email", "to": to, "subject": subject, "body": body, "triggered_by": state.get("data"), "simulated": True}


def send_notification(params: dict, state: dict) -> Any:
    to = params.get("to", "team-channel")
    message = params.get("message") or f"Automated alert: {str(state.get('data'))[:200]}"
    state["log"].append(f"[SIMULATED] Notification sent to {to}.")
    return {"channel": "notification", "to": to, "message": message, "triggered_by": state.get("data"), "simulated": True}


def create_ticket(params: dict, state: dict) -> Any:
    subject = params.get("subject", "Auto-generated ticket")
    priority = params.get("priority", "normal")
    new_id = f"AUTO-{int(time.time()) % 100000}"
    state["log"].append(f"[SIMULATED] Created ticket {new_id} (priority={priority}).")
    return {"ticket_id": new_id, "subject": subject, "priority": priority, "simulated": True}


def update_record(params: dict, state: dict) -> Any:
    updates = params.get("updates", {})
    records = _as_records(state.get("data"))
    updated = [{**r, **updates} for r in records]
    state["log"].append(f"[SIMULATED] Updated {len(updated)} record(s) with {updates}.")
    return updated


def generate_report(params: dict, state: dict) -> Any:
    title = params.get("title", "Workflow Report")
    report = {
        "title": title,
        "result": state.get("data"),
        "trace": list(state.get("log", [])),
    }
    state["log"].append("Generated final report.")
    return report


def route(params: dict, state: dict) -> Any:
    """Assigns a team based on keyword overlap with employees.json specialties."""
    employees = load_dataset("employees")
    data = state.get("data")
    records = _as_records(data)
    by_field = params.get("by", "category")

    def best_team(record: dict) -> dict:
        text = " ".join(str(record.get(f, "")) for f in (by_field, "subject", "body", "category")).lower()
        best, best_score = employees[0], -1
        for emp in employees:
            score = sum(1 for kw in emp.get("specialty", []) if kw in text)
            if score > best_score:
                best, best_score = emp, score
        return {"team": best["team"], "assigned_to": best["name"]}

    if records:
        routed = [{**r, **best_team(r)} for r in records]
    else:
        routed = best_team(data if isinstance(data, dict) else {})
    state["log"].append("Routed record(s) to the best-matching team.")
    return routed


TOOL_REGISTRY: dict[str, ToolFn] = {
    "READ_DATA": read_data,
    "SEARCH_DATA": search_data,
    "WRITE_DATA": write_data,
    "CLASSIFY": classify,
    "EXTRACT": extract,
    "SUMMARIZE": summarize,
    "ANALYZE": analyze,
    "GENERATE": generate,
    "CHECK_CONDITION": check_condition,
    "COMPARE": compare,
    "CALCULATE": calculate,
    "MAKE_DECISION": make_decision,
    "SEND_EMAIL": send_email,
    "SEND_NOTIFICATION": send_notification,
    "CREATE_TICKET": create_ticket,
    "UPDATE_RECORD": update_record,
    "GENERATE_REPORT": generate_report,
    "ROUTE": route,
}

TOOL_DESCRIPTIONS: dict[str, str] = {
    "READ_DATA": "Load a mock dataset. params: {dataset: one of tickets|customers|employees|inventory|invoices|products}",
    "SEARCH_DATA": "Filter the current records where a field contains a substring. params: {field, contains}",
    "WRITE_DATA": "Simulated write-back of the current records (no external system in MVP). params: {}",
    "CLASSIFY": "Assign each record a category using keyword rules. params: {field, category_field, categories: {name: [keywords]}}",
    "EXTRACT": "Keep only the given fields on each record. params: {fields: [list of field names]}",
    "SUMMARIZE": "Add a short 'summary' of a text field to each record. params: {field}",
    "ANALYZE": "Compute a numeric score per record. params: {method: risk_score|sentiment|stock_percentage, output_field, weights}",
    "GENERATE": "Fill a text template with the current data. params: {template}",
    "CHECK_CONDITION": "Split current records into matched/unmatched by a field/operator/value. params: {field, operator: <|<=|>|>=|==|!=|contains, value}",
    "COMPARE": "Compare a metric between two periods per group, flags declining groups. params: {group_field, period_field, metric_field, baseline, current}",
    "CALCULATE": "Compute count/average/percentage over current records. params: {operation: count|average|percentage, field}",
    "MAKE_DECISION": "Choose a branch label based on the previous CHECK_CONDITION result. params: {true_branch, false_branch}",
    "SEND_EMAIL": "Simulated email send. params: {to, subject, body}",
    "SEND_NOTIFICATION": "Simulated notification/alert. params: {to, message}",
    "CREATE_TICKET": "Simulated ticket creation. params: {subject, priority}",
    "UPDATE_RECORD": "Simulated in-memory update of current records. params: {updates: {field: value}}",
    "GENERATE_REPORT": "Compile the final report from accumulated state. params: {title}",
    "ROUTE": "Assign the best-matching internal team from employees.json. params: {by}",
}


def is_valid_tool(name: str) -> bool:
    return name in TOOL_REGISTRY


def run_tool(name: str, params: dict, state: dict) -> Any:
    fn = TOOL_REGISTRY[name]
    return fn(params or {}, state)
