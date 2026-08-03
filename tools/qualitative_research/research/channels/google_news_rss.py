"""Google News RSS discovery channel (no API key)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import quote_plus

import feedparser

from ..http_client import RateLimitedHttpClient
from ..models import ChannelResult, ResearchItem, item_id
from ..queries import search_queries
from ..timestamps import parse_published, to_iso
from ..article_fetch import strip_html

logger = logging.getLogger(__name__)


def _rss_url(query: str) -> str:
    return (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query)}&hl=en-AU&gl=AU&ceid=AU:en"
    )


def fetch_google_news_rss(
    client: RateLimitedHttpClient,
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
    result = ChannelResult(name="google_news_rss", status="ok", queries=queries)
    items: list[ResearchItem] = []

    try:
        for q in queries:
            url = _rss_url(q)
            try:
                xml = client.get_text(url)
            except Exception as e:
                status = getattr(getattr(e, "response", None), "status_code", None)
                if status == 429:
                    result.status = "rate_limited"
                    result.error = str(e)
                    break
                logger.warning("Google News RSS failed for '%s': %s", q, e)
                continue
            feed = feedparser.parse(xml)
            for entry in feed.entries[:max_results_per_query]:
                link = getattr(entry, "link", None) or ""
                if not link:
                    continue
                pub = parse_published(getattr(entry, "published", None), now=now)
                raw_summary = getattr(entry, "summary", None)
                items.append(
                    ResearchItem(
                        id=item_id("google_news_rss", link),
                        source_tier="search_discovery",
                        channel="google_news_rss",
                        category=None,
                        title=getattr(entry, "title", link),
                        url=link,
                        published_at=to_iso(pub),
                        snippet=strip_html(raw_summary),
                        reliability="medium",
                    )
                )
    except Exception as e:
        return ChannelResult(
            name="google_news_rss", status="error", error=str(e), queries=queries
        )

    result.items = items
    return result
