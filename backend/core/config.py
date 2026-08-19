"""Central, environment-driven configuration. No secrets ever hardcoded."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    llm_model: str = "claude-sonnet-5"
    llm_max_tokens: int = 1500

    critic_approval_threshold: float = 8.0
    max_planner_retries: int = 2

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def active_api_key(self) -> str:
        return {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
        }.get(self.llm_provider, "")

    @property
    def is_live(self) -> bool:
        return bool(self.active_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
