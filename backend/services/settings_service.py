"""Company-configurable overrides on top of core/config.py env defaults. Only the 3
non-secret tuning values in the spec (critic threshold, max retries, token limit) are
DB-writable - API keys/provider/DB URL/CORS stay env-only, never persisted or exposed."""
from __future__ import annotations

from database.engine import get_db_session
from database.models import CompanySetting
from core.config import get_settings

_KEYS = ("critic_approval_threshold", "max_planner_retries", "llm_max_tokens")


class EffectiveSettings:
    def __init__(self, critic_approval_threshold: float, max_planner_retries: int, llm_max_tokens: int):
        self.critic_approval_threshold = critic_approval_threshold
        self.max_planner_retries = max_planner_retries
        self.llm_max_tokens = llm_max_tokens


def get_effective_settings() -> EffectiveSettings:
    env = get_settings()
    overrides: dict[str, object] = {}
    try:
        with get_db_session() as session:
            rows = session.query(CompanySetting).filter(CompanySetting.key.in_(_KEYS)).all()
            for row in rows:
                overrides[row.key] = row.value.get("value")
    except Exception:  # noqa: BLE001 - DB unreachable/table not yet created -> pure env defaults
        overrides = {}

    return EffectiveSettings(
        critic_approval_threshold=float(overrides.get("critic_approval_threshold", env.critic_approval_threshold)),
        max_planner_retries=int(overrides.get("max_planner_retries", env.max_planner_retries)),
        llm_max_tokens=int(overrides.get("llm_max_tokens", env.llm_max_tokens)),
    )


def update_settings(values: dict[str, float | int]) -> EffectiveSettings:
    with get_db_session() as session:
        for key, value in values.items():
            if key not in _KEYS or value is None:
                continue
            existing = session.query(CompanySetting).filter(CompanySetting.key == key).one_or_none()
            if existing:
                existing.value = {"value": value}
            else:
                session.add(CompanySetting(key=key, value={"value": value}))
        session.commit()
    return get_effective_settings()
