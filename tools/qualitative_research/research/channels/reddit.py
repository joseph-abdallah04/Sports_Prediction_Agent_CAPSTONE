"""Reddit r/nrl channel — unverified community tier.

Reddit blocks unauthenticated `.json` scraping with HTTP 403 (bot wall).
The public Atom RSS feed (`/r/nrl/new/.rss`) still works without OAuth, so
we use that and filter posts locally for the fixture keywords.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from ..http_client import RateLimitedHttpClient
from ..models import ChannelResult, ResearchItem, item_id
from ..queries import reddit_queries
from ..timestamps import to_iso

logger = logging.getLogger(__name__)

REDDIT_GUIDANCE = (
    "Treat as rumour unless corroborated by official or mainstream_news items."
)

# Prefer RSS — JSON endpoints are routinely 403'd without OAuth.
RSS_NEW = "https://www.reddit.com/r/nrl/new/.rss"


def _parse_entry_published(entry) -> datetime | None:
    for key in ("published", "updated"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError, IndexError):
            pass
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def _entry_link(entry) -> str | None:
    link = entry.get("link")
    if link:
        return link
    for alt in entry.get("links") or []:
        href = alt.get("href")
        if href:
            return href
    return None


def _entry_to_item(entry) -> ResearchItem | None:
    link = _entry_link(entry)
    if not link:
        return None
    title = (entry.get("title") or link).strip()
    # RSS summary often wraps HTML; strip tags lightly
    summary = entry.get("summary") or entry.get("description") or ""
    snippet = re.sub(r"<[^>]+>", " ", summary)
    snippet = re.sub(r"\s+", " ", snippet).strip()[:400] or None
    pub = _parse_entry_published(entry)
    return ResearchItem(
        id=item_id("reddit", link),
        source_tier="unverified_community",
        channel="reddit",
        category="reddit_post",
        title=title,
        url=link,
        published_at=to_iso(pub),
        snippet=snippet,
        reliability="low",
        guidance=REDDIT_GUIDANCE,
    )


def _keywords_from_queries(queries: list[str]) -> set[str]:
    stop = {"and", "the", "for", "nrl", "or", "round"}
    words: set[str] = set()
    for q in queries:
        for w in re.findall(r"[A-Za-z0-9']+", q.lower()):
            if len(w) > 2 and w not in stop:
                words.add(w)
    return words


def fetch_reddit(
    client: RateLimitedHttpClient,
    home_team: str,
    away_team: str,
    *,
    round_number: int | None = None,
    max_posts_per_query: int = 5,
    now: datetime | None = None,
) -> ChannelResult:
    _ = now  # reserved for parity with other channels
    queries = reddit_queries(home_team, away_team, round_number)
    result = ChannelResult(name="reddit", status="ok", queries=queries)
    items: list[ResearchItem] = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml, */*",
    }

    feeds_ok = 0
    try:
        # Single RSS listing — Reddit rate-limits aggressively; avoid search.rss extras.
        try:
            xml = client.get_text(RSS_NEW, headers=headers)
            feed = feedparser.parse(xml)
            for entry in feed.entries or []:
                item = _entry_to_item(entry)
                if item:
                    items.append(item)
            feeds_ok += 1
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status == 429:
                result.status = "rate_limited"
                result.error = str(e)
            else:
                result.status = "error"
                result.error = str(e)
            logger.warning("Reddit RSS listing failed: %s", e)
    except Exception as e:
        status = "rate_limited" if "429" in str(e) else "error"
        return ChannelResult(name="reddit", status=status, error=str(e), queries=queries)

    keywords = _keywords_from_queries(queries)
    filtered: list[ResearchItem] = []
    seen: set[str] = set()
    for item in items:
        key = item.url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        blob = f"{item.title} {item.snippet or ''}".lower()
        if keywords and not any(k in blob for k in keywords):
            continue
        filtered.append(item)

    result.items = filtered[: max_posts_per_query * max(1, len(queries))]
    if result.items:
        result.status = "ok"
        result.error = None
    elif feeds_ok == 0 and result.status == "ok":
        result.status = "error"
        result.error = result.error or "Reddit RSS unavailable"
    return result
