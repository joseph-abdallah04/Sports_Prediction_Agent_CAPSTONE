"""Reddit r/nrl channel — unverified community tier.

Reddit blocks unauthenticated `.json` scraping with HTTP 403 (bot wall). The
public Atom feeds still work without OAuth, so we read two kinds:

- `/r/nrl/new/.rss` — the 25 most recent posts, for anything breaking.
- `/r/nrl/search.rss?q=...` — targeted at this fixture, because a specific
  match is rarely in the newest 25 posts.

Search is rate-limited hard and unpredictably, so each feed is optional: a 429
skips that feed rather than failing the channel, and no feed is retried more
than once (the backoff costs more than the content is worth at this tier).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser

from ..http_client import RateLimitedHttpClient
from ..models import ChannelResult, ResearchItem, item_id
from ..queries import reddit_queries, region_aliases
from ..timestamps import to_iso

logger = logging.getLogger(__name__)

REDDIT_GUIDANCE = (
    "Treat as rumour unless corroborated by official or mainstream_news items."
)

# Prefer RSS — JSON endpoints are routinely 403'd without OAuth.
RSS_NEW = "https://www.reddit.com/r/nrl/new/.rss"
RSS_SEARCH = (
    "https://www.reddit.com/r/nrl/search.rss"
    "?q={query}&restrict_sr=1&sort=new&t=week"
)

# Recurring r/nrl threads that carry availability news without naming a club in
# the title. Dropping these on a team-name test is how the channel ended up
# returning nothing useful.
_AVAILABILITY_TITLE = re.compile(
    r"\b(team list|late mail|injur|judiciary|suspend|casualty|line[- ]?up)\b",
    re.I,
)


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


def _team_terms(home_team: str, away_team: str) -> set[str]:
    """Club nickNames plus their city/region aliases, lowercased."""
    terms: set[str] = set()
    for team in (home_team, away_team):
        t = team.strip().lower()
        if not t:
            continue
        terms.add(t)
        terms.update(region_aliases(t))
        parts = t.split()
        if parts:
            terms.add(parts[-1])
    return terms


def _is_relevant(item: ResearchItem, team_terms: set[str]) -> bool:
    """Keep a post if it names either club, or is an availability thread.

    The second arm matters: r/nrl's "Team List Tuesday" and Late Mail threads
    carry exactly the availability detail this tool exists to find, and none of
    them mention a club in the title. Anything kept here still has to clear the
    main relevance filter afterwards, so being generous is cheap.
    """
    blob = f"{item.title} {item.snippet or ''}".lower()
    if any(term in blob for term in team_terms):
        return True
    return bool(_AVAILABILITY_TITLE.search(item.title))


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

    feed_urls = [RSS_NEW]
    for team in (home_team, away_team):
        feed_urls.append(RSS_SEARCH.format(query=quote_plus(f"{team} NRL")))

    feeds_ok = 0
    last_error: str | None = None
    rate_limited = False
    for url in feed_urls:
        try:
            # One attempt only: reddit's 429 backoff costs more time than this
            # low-reliability tier is worth, and the other feeds may still work.
            xml = client.get_text(url, headers=headers, max_retries=1)
            feed = feedparser.parse(xml)
            for entry in feed.entries or []:
                item = _entry_to_item(entry)
                if item:
                    items.append(item)
            feeds_ok += 1
        except Exception as e:
            last_error = str(e)
            if "429" in last_error:
                rate_limited = True
            logger.info("Reddit feed unavailable (%s): %s", url, e)

    team_terms = _team_terms(home_team, away_team)
    filtered: list[ResearchItem] = []
    seen: set[str] = set()
    for item in items:
        key = item.url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        if not _is_relevant(item, team_terms):
            continue
        filtered.append(item)

    result.items = filtered[: max_posts_per_query * max(1, len(queries))]
    if result.items:
        result.status = "ok"
        result.error = None
    elif feeds_ok == 0:
        result.status = "rate_limited" if rate_limited else "error"
        result.error = last_error or "Reddit RSS unavailable"
    logger.info(
        "Reddit: %d/%d feeds ok, %d posts seen, %d kept",
        feeds_ok, len(feed_urls), len(items), len(result.items),
    )
    return result
