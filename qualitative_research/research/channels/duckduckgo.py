"""DuckDuckGo news discovery channel."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..models import ChannelResult, ResearchItem, item_id
from ..queries import search_queries
from ..timestamps import parse_published, to_iso

logger = logging.getLogger(__name__)


def fetch_duckduckgo(
    home_team: str,
    away_team: str,
    *,
    round_number: int | None = None,
    venue: str | None = None,
    max_results_per_query: int = 5,
    now: datetime | None = None,
) -> ChannelResult:
    now = now or datetime.now(timezone.utc)
    queries = search_queries(home_team, away_team, round_number, venue=venue)
    result = ChannelResult(name="duckduckgo", status="ok", queries=queries)
    items: list[ResearchItem] = []

    try:
        from ddgs import DDGS
    except ImportError as e:
        return ChannelResult(name="duckduckgo", status="error", error=str(e), queries=queries)

    try:
        with DDGS() as ddgs:
            for q in queries:
                try:
                    hits = list(
                        ddgs.news(
                            query=q,
                            region="au-en",
                            timelimit="w",
                            max_results=max_results_per_query,
                        )
                    )
                except Exception as e:
                    err = str(e).lower()
                    if "429" in err or "ratelimit" in err.replace(" ", ""):
                        result.status = "rate_limited"
                        result.error = str(e)
                        break
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

    result.items = items
    return result
