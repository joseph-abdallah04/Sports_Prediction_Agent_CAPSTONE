# ADR 0001: Agent control loop

## Status

Accepted

## Context

The Capstone agent must call fact tools (scene, research, math) via MCP, then
produce a final match prediction. Free ReAct tool choice risks skipping scene
and weakens auditability.

## Decision

Use a **constrained fact pipeline** owned by orchestrator code:

1. `set_fixture_scene` first  
2. LLM authors research queries  
3. `research_fixture_news` (+ optional one refine if coverage gate fails)  
4. `predict_match` with args wired from scene (including weather label)  
5. LLM judgement in a retained chat session  
6. Verifier checklist + LLM audit; optional one **in-session** recalibrate (no new tools)

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| Free ReAct | May skip scene; harder Verifier; weak on local LLMs |
| Pure non-LLM workflow | Not an AI-agent Capstone |
| Multi-process multi-agent tool users | Cost/complexity |
| Verifier re-runs all tools | Rate limits; non-determinism |

## Consequences

Agency is concentrated in research query authorship (+ one research refine).
Judgement and verifier recalibrate do not call tools again.
