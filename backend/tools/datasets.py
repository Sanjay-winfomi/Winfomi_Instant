"""Loads mock datasets from backend/mock_data. Read-only, cached in memory."""
import json
import os
from functools import lru_cache

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mock_data")

AVAILABLE_DATASETS = {
    "tickets",
    "customers",
    "employees",
    "inventory",
    "invoices",
    "products",
}

_KEYWORD_MAP = {
    "tickets": ["ticket", "complaint", "support", "escalation"],
    "customers": ["customer", "churn", "at-risk", "at risk", "renewal", "retention"],
    "employees": ["employee", "attendance", "late", "staff", "team"],
    "inventory": ["inventory", "stock", "supplier", "warehouse", "reorder"],
    "invoices": ["invoice", "vendor", "billing amount", "payment"],
    "products": ["review", "sentiment", "product", "rating"],
}

# The natural per-record identifier and a human-readable label field for each dataset -
# what lets the "try it live" mini-app offer a "pick a record" dropdown generically,
# without hardcoding per-domain UI.
ID_FIELDS: dict[str, str] = {
    "tickets": "ticket_id",
    "customers": "customer_id",
    "employees": "employee_id",
    "inventory": "sku",
    "invoices": "invoice_number",
    "products": "review_id",
}

LABEL_FIELDS: dict[str, str] = {
    "tickets": "subject",
    "customers": "name",
    "employees": "name",
    "inventory": "product",
    "invoices": "vendor",
    "products": "product",
}

# The actions a customer can take on a single record once a workflow has run against
# it - simulated, deterministic, and persisted (api/routes.py + database/models.py),
# not arbitrary: each maps to a fixed, human-readable label only.
ACTIONS_BY_DATASET: dict[str, list[dict[str, str]]] = {
    "tickets": [
        {"action": "escalate", "label": "Escalate to team"},
        {"action": "mark_resolved", "label": "Mark resolved"},
    ],
    "customers": [
        {"action": "alert_sales_team", "label": "Alert sales team"},
        {"action": "mark_reviewed", "label": "Mark reviewed"},
    ],
    "inventory": [
        {"action": "alert_supplier", "label": "Alert supplier"},
        {"action": "mark_reviewed", "label": "Mark reviewed"},
    ],
    "invoices": [
        {"action": "approve", "label": "Approve"},
        {"action": "send_for_review", "label": "Send for manual review"},
    ],
    "products": [
        {"action": "flag_for_review", "label": "Flag for product review"},
    ],
    "employees": [],
}


def list_records(dataset: str) -> list[dict]:
    id_field = ID_FIELDS.get(dataset)
    label_field = LABEL_FIELDS.get(dataset)
    records = load_dataset(dataset)
    return [
        {"id": str(r.get(id_field)), "label": str(r.get(label_field, r.get(id_field)))}
        for r in records
        if id_field
    ]


def get_actions(dataset: str) -> list[dict[str, str]]:
    return ACTIONS_BY_DATASET.get(dataset, [])


@lru_cache
def load_dataset(name: str) -> list[dict]:
    if name not in AVAILABLE_DATASETS:
        raise ValueError(f"Unknown dataset '{name}'. Available: {sorted(AVAILABLE_DATASETS)}")
    path = os.path.join(_DATA_DIR, f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def guess_dataset(text: str) -> str | None:
    text_lower = text.lower()
    best, best_score = None, 0
    for dataset, keywords in _KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best, best_score = dataset, score
    return best
