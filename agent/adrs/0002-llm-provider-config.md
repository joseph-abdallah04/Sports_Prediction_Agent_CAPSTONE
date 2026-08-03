# ADR 0002: LLM provider configuration

## Status

Accepted

## Context

Development should use free local models (Ollama). Evaluation / demos may use
cloud providers (OpenAI, Anthropic, Gemini, Bedrock) without forking prompts.

## Decision

Use a single chat abstraction (**LiteLLM**) configured by env / config file:

- `LLM_PROVIDER`: `ollama` | `openai` | `anthropic` | `gemini` | `bedrock`
- `LLM_MODEL`: provider-specific model id
- API keys / Bedrock region via standard env vars

Same prompts and orchestrator code for all providers.

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| Hard-code one provider SDK | Painful eval switches |
| Separate code paths per provider | Drift and maintenance cost |

## Consequences

Operator switches provider without code changes. Ollama is the default for local
dev; cloud providers for collating results.
