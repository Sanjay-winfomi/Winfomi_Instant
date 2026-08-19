"""Thin, swappable LLM provider abstraction.

Only Anthropic is wired for the MVP, but every call site depends only on
`LLMProvider.complete_json`, so adding OpenAI/Gemini later means implementing
one more subclass and switching LLM_PROVIDER - no agent code changes.

If no API key is configured, `get_llm_provider()` returns a `NullLLMProvider`
that always raises `LLMUnavailableError`, which callers treat identically to
a live-call failure. This is what pushes the whole app into fallback/deterministic
mode rather than crashing when a judge runs it with no key set.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)


class LLMUnavailableError(Exception):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def complete_json(self, system_prompt: str, user_prompt: str, max_tokens: int) -> dict:
        """Call the model and parse its response as JSON. Raises LLMUnavailableError on any failure."""


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete_json(self, system_prompt: str, user_prompt: str, max_tokens: int) -> dict:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                timeout=20.0,
            )
            text = "".join(block.text for block in response.content if hasattr(block, "text"))
            return _extract_json(text)
        except Exception as exc:  # network, auth, parsing, rate limit - all treated the same
            logger.warning("Anthropic call failed: %s", exc)
            raise LLMUnavailableError(str(exc)) from exc


class NullLLMProvider(LLMProvider):
    def complete_json(self, system_prompt: str, user_prompt: str, max_tokens: int) -> dict:
        raise LLMUnavailableError("No LLM provider configured (missing API key).")


def _extract_json(text: str) -> dict:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model output: {text[:200]}")
    return json.loads(text[start : end + 1])


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if not settings.is_live:
        return NullLLMProvider()
    if settings.llm_provider == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key, settings.llm_model)
    # Stretch: openai / gemini providers would be added here behind the same interface.
    logger.warning("LLM_PROVIDER=%s not yet implemented, falling back to null provider.", settings.llm_provider)
    return NullLLMProvider()
