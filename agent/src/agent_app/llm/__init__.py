"""LiteLLM chat client with retained message sessions.

For local Ollama (especially Gemma 4), we call the native `/api/chat` endpoint
with `think=true` so the model's real scratchpad lands in `message.thinking`.
LiteLLM's OpenAI-compatible path often drops or mis-routes that channel.
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.request
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any

from agent_app.config import Settings, litellm_model_id

logger = logging.getLogger(__name__)

# Bound for the duration of one orchestrator run. Each LLM call appends an
# entry so thinking.md can be rewritten on every persist.
_thinking_trace: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "thinking_trace", default=None
)


def bind_thinking_trace(trace: list[dict[str, Any]]) -> Token:
    return _thinking_trace.set(trace)


def unbind_thinking_trace(token: Token) -> None:
    _thinking_trace.reset(token)


def _record_thinking(step: str | None, thinking: str) -> None:
    if not step:
        return
    trace = _thinking_trace.get()
    if trace is None:
        return
    text = (thinking or "").strip()
    trace.append(
        {
            "step": step,
            "at": datetime.now(timezone.utc).isoformat(),
            "thinking": text,
            "chars": len(text),
        }
    )


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

    def complete(self, *, temperature: float = 0.2, step: str = "judgement") -> str:
        return chat_completion(
            self.settings, self.messages, temperature=temperature, step=step
        )


def chat_completion(
    settings: Settings,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    step: str | None = None,
) -> str:
    provider = settings.llm_provider.strip().lower()
    prompt_chars = sum(len(m.get("content") or "") for m in messages)
    logger.info(
        "LLM complete model=%s messages=%d prompt_chars=%d timeout=%.0fs step=%s",
        litellm_model_id(settings) if provider != "ollama" else settings.llm_model,
        len(messages),
        prompt_chars,
        settings.llm_timeout_seconds,
        step or "-",
    )
    started = time.monotonic()
    if provider == "ollama":
        content, thinking = _ollama_chat(
            settings, messages, temperature=temperature
        )
    else:
        content, thinking = _litellm_chat(
            settings, messages, temperature=temperature
        )
    logger.info(
        "LLM responded in %.1fs (content=%d chars, thinking=%d chars)",
        time.monotonic() - started,
        len(content),
        len(thinking),
    )
    _record_thinking(step, thinking)
    return content.strip()


def _ollama_chat(
    settings: Settings,
    messages: list[dict[str, str]],
    *,
    temperature: float,
) -> tuple[str, str]:
    """Native Ollama chat with thinking enabled (Gemma 4 / MLX)."""
    url = settings.ollama_api_base.rstrip("/") + "/api/chat"
    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "stream": False,
        "think": True,
        "options": {"temperature": temperature},
    }
    body = json.dumps(payload).encode("utf-8")
    attempts = max(1, int(settings.llm_max_retries) + 1)
    last_err: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(
                req, timeout=settings.llm_timeout_seconds
            ) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            message = data.get("message") or {}
            content = str(message.get("content") or "")
            thinking = str(
                message.get("thinking")
                or message.get("reasoning")
                or ""
            )
            if not content and thinking:
                # Some builds occasionally put the answer in thinking only;
                # still surface it so JSON parsing has something to work with.
                logger.warning(
                    "Ollama returned empty content with thinking; using thinking as content"
                )
                content = thinking
                thinking = ""
            return content, thinking
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = e
            logger.warning(
                "Ollama chat failed (%d/%d): %s", attempt, attempts, e
            )
            if attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(f"Ollama chat failed after {attempts} attempts: {last_err}")


def _litellm_chat(
    settings: Settings,
    messages: list[dict[str, str]],
    *,
    temperature: float,
) -> tuple[str, str]:
    import litellm

    kwargs: dict[str, Any] = {
        "model": litellm_model_id(settings),
        "messages": messages,
        "temperature": temperature,
        "timeout": settings.llm_timeout_seconds,
        "num_retries": settings.llm_max_retries,
    }
    provider = settings.llm_provider.strip().lower()
    if provider == "bedrock" and settings.aws_region_name:
        kwargs["aws_region_name"] = settings.aws_region_name

    response = litellm.completion(**kwargs)
    message = response.choices[0].message
    content = message.content or ""
    thinking = ""
    for attr in ("reasoning_content", "thinking", "reasoning"):
        value = getattr(message, attr, None)
        if value:
            thinking = str(value)
            break
    if not thinking:
        provider_fields = getattr(message, "provider_specific_fields", None) or {}
        if isinstance(provider_fields, dict):
            for key in ("reasoning_content", "thinking", "reasoning"):
                if provider_fields.get(key):
                    thinking = str(provider_fields[key])
                    break
    return content, thinking


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
