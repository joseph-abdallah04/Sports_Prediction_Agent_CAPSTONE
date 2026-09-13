"""Assemble multi-channel research into a ledger-friendly response."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from . import TOOL_NAME, TOOL_VERSION
from .article_fetch import attach_article_bodies
from .cache import cache_key, load as cache_load, save as cache_save
from .channels.duckduckgo import fetch_duckduckgo
from .channels.google_news_rss import fetch_google_news_rss
from .channels.nrl_news import fetch_nrl_news
from .channels.reddit import fetch_reddit
from .debug_log import write_dropped_sources
from .filter import (
    dedupe_by_canonical_url,
    dedupe_by_url,
    filter_items,
    promote_deferred_with_bodies,
    sort_key,
)
from .http_client import RateLimitedHttpClient
from .queries import sanitize_custom_queries
from .timestamps import parse_published

logger = logging.getLogger(__name__)


def _kickoff_datetime(kickoff: str) -> datetime:
    dt = parse_published(kickoff) or datetime.fromisoformat(
        kickoff.replace("Z", "+00:00")
    )
    if dt.tzinfo is None:
        from zoneinfo import ZoneInfo
        dt = dt.replace(tzinfo=ZoneInfo("Australia/Sydney"))
    return dt.astimezone(timezone.utc)


def _kickoff_date(kickoff: str) -> str:
    return _kickoff_datetime(kickoff).date().isoformat()


def research_fixture(
    home_team: str,
    away_team: str,
    kickoff: str,
    *,
    round_number: int | None = None,
    venue: str | None = None,
    force_refresh: bool = False,
    max_age_days: int = 10,
    max_items: int = 25,
    max_deferred_body_fetches: int = 15,
    queries: list[str] | None = None,
    include_reddit: bool = False,
) -> dict:
    """Run all channels, filter, optionally cache, return ResearchResponse dict.

    If ``queries`` is provided (agent path), DDG/Google News merge those strings
    with the default templates. CLI callers omit ``queries``.

    Relevance runs in two passes: a title/snippet pass, then a second pass over
    deferred items once article bodies have been fetched, so articles that only
    name the fixture in their body are recovered rather than dropped.

    Reddit is off by default (DD-34): it contributes ~0 usable items per fixture
    and its search endpoint is blocked to unauthenticated clients. Pass
    ``include_reddit=True`` to run it anyway.
    """
    custom = sanitize_custom_queries(queries)
    request = {
        "home_team": home_team,
        "away_team": away_team,
        "kickoff": kickoff,
        "round_number": round_number,
        "venue": venue,
        "queries": custom,
    }
    key = cache_key(
        home_team, away_team, _kickoff_date(kickoff), round_number, queries=custom
    )

    if not force_refresh:
        cached = cache_load(key)
        if cached is not None:
            cached = dict(cached)
            cached["cache_hit"] = True
            cached["retrieved_at"] = datetime.now(timezone.utc).isoformat()
            return cached

    client = RateLimitedHttpClient(delay_seconds=1.0)
    kickoff_dt = _kickoff_datetime(kickoff)
    now = datetime.now(timezone.utc)

    window_start = kickoff_dt - timedelta(days=max_age_days)

    nrl = fetch_nrl_news(
        client, home_team, away_team, now=now, window_start=window_start
    )
    ddg = fetch_duckduckgo(
        home_team,
        away_team,
        round_number=round_number,
        custom_queries=custom,
        now=now,
    )
    gnews = fetch_google_news_rss(
        client,
        home_team,
        away_team,
        round_number=round_number,
        custom_queries=custom,
        now=now,
    )
    channels = {
        "nrl_news": nrl,
        "duckduckgo": ddg,
        "google_news_rss": gnews,
    }
    if include_reddit:
        channels["reddit"] = fetch_reddit(
            client, home_team, away_team, round_number=round_number, now=now
        )

    all_items = []
    for ch in channels.values():
        all_items.extend(ch.items)
    all_items = dedupe_by_url(all_items)

    kept, filter_summary, dropped, deferred = filter_items(
        all_items,
        home_team=home_team,
        away_team=away_team,
        kickoff=kickoff_dt,
        round_number=round_number,
        max_age_days=max_age_days,
        now=now,
    )
    kept = kept[:max_items]

    # Second relevance pass: give the best deferred candidates a body, then
    # re-test them for fixture relevance.
    deferred = deferred[:max_deferred_body_fetches]
    attach_article_bodies(
        client, kept + deferred, max_unique_fetches=30 + len(deferred)
    )
    promoted, deferred_drops = promote_deferred_with_bodies(
        deferred,
        home_team=home_team,
        away_team=away_team,
        round_number=round_number,
    )
    dropped.extend(deferred_drops)
    filter_summary["promoted_after_body"] = len(promoted)
    filter_summary["dropped_irrelevant"] += len(deferred_drops)
    if promoted:
        kept = sorted([*kept, *promoted], key=sort_key)[:max_items]

    # Collapse identical publisher URLs (e.g. nrl_news + Google → same nrl.com)
    kept, dup_drops = dedupe_by_canonical_url(kept)
    dropped.extend(dup_drops)
    if dup_drops:
        filter_summary["dropped_duplicate_url"] = len(dup_drops)

    # Drop empty shells — no use to the Orchestrator / wastes tokens
    with_body: list = []
    for item in kept:
        if item.body_excerpt and item.body_excerpt.strip():
            with_body.append(item)
        else:
            dropped.append(
                {
                    "reason": "dropped_no_body",
                    "channel": item.channel,
                    "source_tier": item.source_tier,
                    "title": item.title,
                    "url": item.url,
                    "published_at": item.published_at,
                    "category": item.category,
                }
            )
            filter_summary["dropped_no_body"] = filter_summary.get("dropped_no_body", 0) + 1
    kept = with_body
    filter_summary["kept"] = len(kept)

    # Local audit only — never sent to LLM / API response / day cache
    write_dropped_sources(
        key,
        request=request,
        filter_summary=filter_summary,
        dropped=dropped,
    )

    # Recount items_kept after global filter + body requirement
    kept_urls = {i.url for i in kept}
    channel_summaries = {}
    for name, ch in channels.items():
        summary = ch.summary()
        summary["items_kept"] = sum(1 for i in ch.items if i.url in kept_urls)
        channel_summaries[name] = summary

    queries_run: list[str] = []
    seen_q: set[str] = set()
    for ch in channels.values():
        for q in ch.queries:
            if q in seen_q:
                continue
            seen_q.add(q)
            queries_run.append(q)

    response = {
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "request": request,
        "retrieved_at": now.isoformat(),
        "cache_hit": False,
        "channels": channel_summaries,
        "items": [i.to_dict() for i in kept],
        "queries_run": queries_run,
        "filter_summary": filter_summary,
    }
    cache_save(key, response)
    return response
