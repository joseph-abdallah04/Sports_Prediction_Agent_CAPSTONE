"""Agent configuration (LLM provider + loop flags)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AGENT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = AGENT_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", str(AGENT_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gemma4:31b", alias="LLM_MODEL")
    # Ollama OpenAI-compatible base (LiteLLM)
    ollama_api_base: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_API_BASE")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    aws_region_name: str | None = Field(default=None, alias="AWS_REGION_NAME")

    verifier_enabled: bool = Field(default=True, alias="VERIFIER_ENABLED")
    max_research_loops: int = Field(default=1, alias="MAX_RESEARCH_LOOPS")
    max_verifier_loops: int = Field(default=1, alias="MAX_VERIFIER_LOOPS")
    max_agent_queries: int = Field(default=6, alias="MAX_AGENT_QUERIES")

    agent_runs_dir: Path = Field(
        default_factory=lambda: REPO_ROOT / "agent_runs",
        alias="AGENT_RUNS_DIR",
    )


def get_settings() -> Settings:
    return Settings()


def litellm_model_id(settings: Settings) -> str:
    """Map provider + model to a LiteLLM model string."""
    provider = settings.llm_provider.strip().lower()
    model = settings.llm_model.strip()
    if provider == "ollama":
        # litellm uses ollama/<name> for native ollama, or openai/ with api_base
        if "/" in model:
            return model
        return f"ollama/{model}"
    if provider == "openai":
        return model if model.startswith("openai/") else f"openai/{model}"
    if provider == "anthropic":
        return model if model.startswith("anthropic/") else f"anthropic/{model}"
    if provider == "gemini":
        return model if model.startswith("gemini/") else f"gemini/{model}"
    if provider == "bedrock":
        return model if model.startswith("bedrock/") else f"bedrock/{model}"
    return model
