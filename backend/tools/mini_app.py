"""Builds the deterministic "try it live" mini-app description for a session -
which records the customer can pick from and which actions are available for the
dataset the workflow reads. No LLM involved: this is a fixed lookup, not generated UI."""
from schemas.miniapp import ActionOption, MiniAppInfo, RecordSummary
from tools.datasets import get_actions, list_records


def build_mini_app_info(dataset: str | None) -> MiniAppInfo | None:
    if not dataset:
        return None
    records = [RecordSummary(**r) for r in list_records(dataset)]
    actions = [ActionOption(**a) for a in get_actions(dataset)]
    if not records:
        return None
    return MiniAppInfo(dataset=dataset, records=records, actions=actions)
