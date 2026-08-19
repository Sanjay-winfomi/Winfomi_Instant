"""Builds the deterministic "try it live" mini-app description for a session -
which records the customer can pick from and which actions are available.

Fully generic: derived from the synthesized records + the Requirement itself, never
from a per-dataset lookup table. No LLM involved - this is a fixed, predictable
derivation, not generated UI.
"""
from schemas.miniapp import ActionOption, MiniAppInfo, RecordSummary
from schemas.requirement import Requirement

# Fixed, generic action set offered whenever the requirement involves a decision.
# Deliberately not domain-specific (no "alert supplier" vs "escalate to team") since
# the domain isn't known in advance - these two cover any decision-shaped workflow.
GENERIC_ACTIONS: list[dict[str, str]] = [
    {"action": "approve", "label": "Approve"},
    {"action": "flag_for_review", "label": "Flag for review"},
]


def allowed_actions(requirement: Requirement | None) -> list[dict[str, str]]:
    if requirement and (requirement.decision or requirement.condition):
        return GENERIC_ACTIONS
    return []


def build_mini_app_info(records: list[dict], requirement: Requirement | None) -> MiniAppInfo | None:
    if not records:
        return None

    label_field = requirement.fields[0] if requirement and requirement.fields else None

    summaries = [
        RecordSummary(
            id=str(r.get("id")),
            label=str(r.get(label_field)) if label_field and r.get(label_field) is not None else str(r.get("id")),
        )
        for r in records
    ]
    actions = [ActionOption(**a) for a in allowed_actions(requirement)]
    dataset_label = requirement.record_label if requirement else None
    return MiniAppInfo(dataset=dataset_label, records=summaries, actions=actions)
