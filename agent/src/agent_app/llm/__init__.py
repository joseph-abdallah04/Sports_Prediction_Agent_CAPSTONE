"""LiteLLM chat client with retained message sessions."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from agent_app.config import Settings, litellm_model_id

logger = logging.getLogger(__name__)


class ChatSession:
    """Retained multi-turn chat for judgement (+ verifier recalibrate)."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.messages: list[dict[str, str]] = []

    def add_system(self, content: str) -> None:
        self.messages.append({"role": "system", "content": content})

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def complete(self, *, temperature: float = 0.2) -> str:
        return chat_completion(self.settings, self.messages, temperature=temperature)


def chat_completion(
    settings: Settings,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
) -> str:
    import litellm

    model = litellm_model_id(settings)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "timeout": settings.llm_timeout_seconds,
        "num_retries": settings.llm_max_retries,
    }
    provider = settings.llm_provider.strip().lower()
    if provider == "ollama":
        kwargs["api_base"] = settings.ollama_api_base
    elif provider == "bedrock" and settings.aws_region_name:
        kwargs["aws_region_name"] = settings.aws_region_name

    prompt_chars = sum(len(m.get("content") or "") for m in messages)
    logger.info(
        "LLM complete model=%s messages=%d prompt_chars=%d timeout=%.0fs",
        model,
        len(messages),
        prompt_chars,
        settings.llm_timeout_seconds,
    )
    started = time.monotonic()
    response = litellm.completion(**kwargs)
    content = response.choices[0].message.content or ""
    logger.info(
        "LLM responded in %.1fs (%d chars)", time.monotonic() - started, len(content)
    )
    return content.strip()


def parse_json_object(text: str) -> dict[str, Any]:
    """Extract a JSON object from model output (tolerant of fences)."""
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        try:
            data = json.loads(fence.group(1))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start : end + 1]
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    raise ValueError(f"No JSON object in model output: {text[:200]!r}")
