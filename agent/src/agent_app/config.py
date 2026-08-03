"""Agent configuration.

Settings come from four places. Later sources win:

    built-in defaults  <  <repo>/config.toml  <  agent/.env  <  environment

`config.toml` at the repo root holds everything non-secret and is the file a
human is expected to edit — switching from local Ollama to a hosted model is a
one-line change there. Secrets stay in `agent/.env`, which is git-ignored.
Environment variables win over both so a one-off override needs no file edits.

The TOML is nested by topic (`[llm]`, `[agent]`, `[paths]`) because a flat file
of twenty keys is not something anyone reads twice; `_flatten_toml` maps that
structure onto the flat field names below.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

AGENT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = AGENT_ROOT.parent
CONFIG_PATH = REPO_ROOT / "config.toml"

PROVIDERS = ("ollama", "openai", "anthropic", "gemini", "bedrock")


def _flatten_toml(path: Path) -> dict[str, Any]:
    """Read config.toml into the flat field names Settings expects.

    Only the selected provider's preset is applied, so the other presets can
    stay in the file as a documented menu of options.
    """
    if not path.is_file():
        return {}
    with path.open("rb") as fh:
        raw = tomllib.load(fh)

    llm = raw.get("llm") or {}
    agent = raw.get("agent") or {}
    paths = raw.get("paths") or {}
    flat: dict[str, Any] = {}

    provider = str(llm.get("provider", "")).strip().lower()
    if provider:
        flat["llm_provider"] = provider
    for key, field in (
        ("timeout_seconds", "llm_timeout_seconds"),
        ("max_retries", "llm_max_retries"),
    ):
        if key in llm:
            flat[field] = llm[key]

    preset = ((llm.get("presets") or {}).get(provider)) or {}
    if preset.get("model"):
        flat["llm_model"] = preset["model"]
    if preset.get("api_base"):
        flat["ollama_api_base"] = preset["api_base"]
    if preset.get("aws_region"):
        flat["aws_region_name"] = preset["aws_region"]

    for key in ("verifier_enabled", "max_research_loops", "max_verifier_loops",
                "max_agent_queries"):
        if key in agent:
            flat[key] = agent[key]

    if paths.get("runs_dir"):
        runs = Path(paths["runs_dir"])
        flat["agent_runs_dir"] = runs if runs.is_absolute() else REPO_ROOT / runs
    return flat


class _TomlSource(PydanticBaseSettingsSource):
    """Feeds config.toml in below .env and the environment."""

    def get_field_value(self, field, field_name):  # pragma: no cover - unused hook
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        return _flatten_toml(CONFIG_PATH)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", str(AGENT_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
        # Fields are declared with SCREAMING_CASE env aliases; without this,
        # in-process overrides by field name are silently discarded.
        populate_by_name=True,
    )

    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gemma4:31b", alias="LLM_MODEL")
    # Ollama OpenAI-compatible base (LiteLLM)
    ollama_api_base: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_API_BASE")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    aws_region_name: str | None = Field(default=None, alias="AWS_REGION_NAME")

    # A local Ollama server can drop a connection and leave the client waiting
    # forever, which stalls the whole run. Always bound the call.
    llm_timeout_seconds: float = Field(default=300.0, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=2, alias="LLM_MAX_RETRIES")

    verifier_enabled: bool = Field(default=True, alias="VERIFIER_ENABLED")
    max_research_loops: int = Field(default=1, alias="MAX_RESEARCH_LOOPS")
    max_verifier_loops: int = Field(default=1, alias="MAX_VERIFIER_LOOPS")
    max_agent_queries: int = Field(default=6, alias="MAX_AGENT_QUERIES")

    agent_runs_dir: Path = Field(
        default_factory=lambda: REPO_ROOT / "agent_runs",
        alias="AGENT_RUNS_DIR",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            _TomlSource(settings_cls),
            file_secret_settings,
        )


def _preset(provider: str) -> dict[str, Any]:
    """One provider's preset block from config.toml."""
    if not CONFIG_PATH.is_file():
        return {}
    with CONFIG_PATH.open("rb") as fh:
        raw = tomllib.load(fh)
    presets = ((raw.get("llm") or {}).get("presets") or {})
    return presets.get(provider) or {}


def get_settings(
    *,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    **overrides: Any,
) -> Settings:
    """Resolved settings. Keyword overrides beat every other source.

    Switching provider pulls that provider's preset (model, region, api_base)
    from config.toml, so `--provider bedrock` behaves the same as editing the
    file rather than leaving the previous provider's model in place.
    """
    if llm_provider:
        provider = llm_provider.strip().lower()
        preset = _preset(provider)
        overrides["llm_provider"] = provider
        if preset.get("model"):
            overrides["llm_model"] = preset["model"]
        if preset.get("api_base"):
            overrides["ollama_api_base"] = preset["api_base"]
        if preset.get("aws_region"):
            overrides["aws_region_name"] = preset["aws_region"]
    if llm_model:
        overrides["llm_model"] = llm_model
    return Settings(**overrides)


def missing_credentials(settings: Settings) -> str | None:
    """Human-readable warning if the selected provider has no credentials.

    Better to say so before a ten-minute run dies on its first LLM call.
    """
    provider = settings.llm_provider.strip().lower()
    needed = {
        "openai": ("OPENAI_API_KEY", settings.openai_api_key),
        "anthropic": ("ANTHROPIC_API_KEY", settings.anthropic_api_key),
        "gemini": ("GEMINI_API_KEY", settings.gemini_api_key),
    }.get(provider)
    if needed and not needed[1]:
        return (
            f"Provider '{provider}' is selected in config.toml but {needed[0]} "
            f"is not set. Add it to agent/.env (see agent/.env.example)."
        )
    if provider == "bedrock" and not settings.aws_region_name:
        return (
            "Provider 'bedrock' is selected but no AWS region is set. Add "
            "aws_region to [llm.presets.bedrock] in config.toml, and AWS "
            "credentials to agent/.env."
        )
    return None


def describe_settings(settings: Settings) -> str:
    """One-screen summary of what is actually in effect, secrets redacted."""
    def secret(value: str | None) -> str:
        return "set" if value else "-"

    lines = [
        f"config file      {CONFIG_PATH}"
        f"{'' if CONFIG_PATH.is_file() else '  (NOT FOUND — using defaults)'}",
        f"provider         {settings.llm_provider}",
        f"model            {settings.llm_model}",
        f"litellm model id {litellm_model_id(settings)}",
        f"timeout          {settings.llm_timeout_seconds:.0f}s, "
        f"{settings.llm_max_retries} retries",
        f"verifier         {'on' if settings.verifier_enabled else 'off'}",
        f"loops            research<={settings.max_research_loops}, "
        f"verifier<={settings.max_verifier_loops}, "
        f"queries<={settings.max_agent_queries}",
        f"runs dir         {settings.agent_runs_dir}",
        "credentials      "
        f"openai={secret(settings.openai_api_key)} "
        f"anthropic={secret(settings.anthropic_api_key)} "
        f"gemini={secret(settings.gemini_api_key)} "
        f"aws_region={settings.aws_region_name or '-'}",
    ]
    warning = missing_credentials(settings)
    if warning:
        lines.append(f"\nWARNING: {warning}")
    return "\n".join(lines)


def litellm_model_id(settings: Settings) -> str:
    """Map provider + model to a LiteLLM model string."""
    provider = settings.llm_provider.strip().lower()
    model = settings.llm_model.strip()
    if provider == "ollama":
        # litellm uses ollama/<name> for native ollama, or openai/ with api_base
        if "/" in model:
            return model
        return f"ollama/{model}"
    for name in ("openai", "anthropic", "gemini", "bedrock"):
        if provider == name:
            return model if model.startswith(f"{name}/") else f"{name}/{model}"
    return model
