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
