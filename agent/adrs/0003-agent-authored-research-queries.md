# ADR 0003: Agent-authored research queries + refine loop

## Status

Accepted

## Context

Qualitative research previously used fixed query templates. That removes
agency and may miss fixture-specific angles after scene is known.

## Decision

1. After scene, the LLM proposes 3–6 search queries (guardrails: no weather /
   venue / kickoff / officials — those come from scene).
2. `research_fixture_news` accepts optional `queries`; CLI keeps defaults when omitted.
3. Coverage gate (`research_ok`) may trigger **one** refine: fewer/sharper queries
   and one extra research call. Then continue even if still weak.
4. Cache key includes a hash of custom queries so agent runs do not collide with
   default-template cache entries.

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| Fixed queries only | No meaningful agency |
| Unlimited research loops | Cost / latency / flaky source thrashing |
| Betting-source success criteria | Unstable and off-mission |

## Consequences

Primary agency is query authorship. Research loop is ledgered (`research_loop`).
