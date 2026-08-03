"""DuckDuckGo news discovery channel."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from ..models import ChannelResult, ResearchItem, item_id
from ..queries import search_queries
from ..timestamps import parse_published, to_iso

logger = logging.getLogger(__name__)

# DuckDuckGo intermittently 403s its news endpoint. A short backoff recovers
# most of these; without it a whole query silently contributes zero items.
_RETRY_BACKOFF_SECONDS = (1.0, 3.0)


def _news_with_retry(ddgs, query: str, max_results: int) -> list[dict]:
    attempts = len(_RETRY_BACKOFF_SECONDS) + 1
    for attempt in range(attempts):
        try:
            return list(
                ddgs.news(
                    query=query,
                    region="au-en",
                    timelimit="w",
                    max_results=max_results,
                )
            )
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "ratelimit" in err.replace(" ", ""):
                raise
            if attempt == attempts - 1:
                raise
            delay = _RETRY_BACKOFF_SECONDS[attempt]
            logger.debug("DDG retry %d for '%s' after %s (%.1fs)", attempt + 1, query, e, delay)
            time.sleep(delay)
    return []


def fetch_duckduckgo(
    home_team: str,
    away_team: str,
    *,
    round_number: int | None = None,
    custom_queries: list[str] | None = None,
    max_results_per_query: int = 12,
    now: datetime | None = None,
) -> ChannelResult:
    now = now or datetime.now(timezone.utc)
    queries = search_queries(
        home_team, away_team, round_number, custom_queries=custom_queries
    )
    result = ChannelResult(name="duckduckgo", status="ok", queries=queries)
    items: list[ResearchItem] = []

    try:
        from ddgs import DDGS
    except ImportError as e:
        return ChannelResult(name="duckduckgo", status="error", error=str(e), queries=queries)

    failed_queries = 0
    last_error: str | None = None
    try:
        with DDGS() as ddgs:
            for q in queries:
                try:
                    hits = _news_with_retry(ddgs, q, max_results_per_query)
                except Exception as e:
                    err = str(e).lower()
                    if "429" in err or "ratelimit" in err.replace(" ", ""):
                        result.status = "rate_limited"
                        result.error = str(e)
                        break
                    failed_queries += 1
                    last_error = str(e)
                    logger.warning("DDG query failed '%s': %s", q, e)
                    continue
                for hit in hits:
                    url = hit.get("url") or hit.get("href") or ""
                    if not url:
                        continue
                    pub = parse_published(hit.get("date"), now=now)
                    items.append(
                        ResearchItem(
                            id=item_id("duckduckgo", url),
                            source_tier="mainstream_news",
                            channel="duckduckgo",
                            category=None,
                            title=hit.get("title") or url,
                            url=url,
                            published_at=to_iso(pub) or hit.get("date"),
                            snippet=hit.get("body"),
                            reliability="medium",
                        )
                    )
    except Exception as e:
        err = str(e).lower()
        status = "rate_limited" if "429" in err else "error"
        return ChannelResult(name="duckduckgo", status=status, error=str(e), queries=queries)

    # Every query erroring is a channel failure, not a clean empty result.
    if result.status == "ok" and failed_queries and failed_queries == len(queries):
        result.status = "error"
        result.error = last_error

    result.items = items
    return result
