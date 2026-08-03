"""nrl.com news channel — official Team Lists, Injuries, Match Preview, club hubs."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..http_client import RateLimitedHttpClient
from ..models import ChannelResult, ResearchItem, item_id
from ..queries import team_slug
from ..timestamps import parse_published, to_iso

# Re-export for callers that imported from this module previously
from ..article_fetch import fetch_article_excerpt  # noqa: F401

logger = logging.getLogger(__name__)

NRL_BASE = "https://www.nrl.com"

TOPIC_URLS = {
    "team_lists": f"{NRL_BASE}/news/topic/team-lists/",
    "injuries": f"{NRL_BASE}/news/topic/injuries/",
    "match_preview": f"{NRL_BASE}/news/topic/match-preview/",
}

SKIP_CATEGORIES = {"fantasy", "tipping", "match highlights"}


def _absolute(href: str) -> str:
    return urljoin(NRL_BASE, href)


def _extract_cards(html: str) -> list[dict]:
    """Parse news cards from an nrl.com listing page."""
    soup = BeautifulSoup(html, "html.parser")
    cards: list[dict] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/news/20" not in href and not re.search(r"/news/\d{4}/", href):
            continue
        url = _absolute(href.split("?")[0])
        if url in seen:
            continue
        # Prefer meaningful titles
        title = a.get_text(" ", strip=True)
        if len(title) < 12:
            continue
        # Skip video highlight / duration-prefixed cards early
        if re.match(r"^\d{1,2}:\d{2}\b", title) or "match highlights" in title.lower():
            continue
        if re.search(r"/news/\d{4}/\d{2}/\d{2}/[^/]*highlight", url, re.I):
            continue
        # Category often sits in a sibling/parent label
        category = None
        parent = a.parent
        for _ in range(4):
            if parent is None:
                break
            label = parent.find(class_=re.compile(r"label|tag|topic|category", re.I))
            if label:
                category = label.get_text(" ", strip=True)
                break
            # o-card__category style
            cat_el = parent.select_one("[class*='category'], [class*='topic'], .u-t-color-tint")
            if cat_el and cat_el != a:
                category = cat_el.get_text(" ", strip=True)
                break
            parent = parent.parent

        if category and category.strip().lower() in SKIP_CATEGORIES:
            continue

        # Timestamp: look for time element or "ago" / Yesterday text near card
        published_raw = None
        time_el = a.find("time")
        if time_el:
            published_raw = time_el.get("datetime") or time_el.get_text(strip=True)
        if not published_raw:
            card_root = a
            for _ in range(5):
                if card_root.parent is None:
                    break
                card_root = card_root.parent
                text = card_root.get_text(" ", strip=True)
                m = re.search(
                    r"(\d+\s+(?:second|minute|hour|day|week)s?\s+ago|Yesterday|\d{4}-\d{2}-\d{2}T[^\s]+)",
                    text,
                    re.I,
                )
                if m:
                    published_raw = m.group(1)
                    break

        # Clean title: often includes category + timestamp + sponsor mash
        clean_title = title
        if category and clean_title.upper().startswith(category.upper()):
            clean_title = clean_title[len(category):].strip()
        clean_title = re.sub(
            r"\s+(\d+\s+(?:second|minute|hour|day|week)s?\s+ago|Yesterday)\s*$",
            "",
            clean_title,
            flags=re.I,
        ).strip()
        clean_title = re.sub(r"\s*Presented by\s*$", "", clean_title, flags=re.I).strip()

        seen.add(url)
        cards.append(
            {
                "title": clean_title or title,
                "url": url,
                "category": category,
                "published_raw": published_raw,
            }
        )
    return cards


def fetch_nrl_news(
    client: RateLimitedHttpClient,
    home_team: str,
    away_team: str,
    *,
    max_list_items: int = 60,
    now: datetime | None = None,
    window_start: datetime | None = None,
) -> ChannelResult:
    """List official nrl.com cards (bodies attached later after filtering).

    ``window_start`` drops dated cards published before the fixture's recency
    window at the channel boundary. Topic and club hubs surface months of
    archive; without this the downstream filter spends its budget rejecting
    stale cards and genuinely recent items get crowded out of the listing cap.
    """
    now = now or datetime.now(timezone.utc)
    result = ChannelResult(name="nrl_news", status="ok")
    raw_cards: list[dict] = []

    urls = list(TOPIC_URLS.values())
    for team in (home_team, away_team):
        slug = team_slug(team)
        if slug:
            urls.append(f"{NRL_BASE}/news/club/{slug}/")

    try:
        for url in urls:
            try:
                html = client.get_text(url)
                raw_cards.extend(_extract_cards(html))
            except Exception as e:
                logger.warning("nrl listing failed %s: %s", url, e)
    except Exception as e:
        return ChannelResult(name="nrl_news", status="error", error=str(e))

    by_url: dict[str, dict] = {}
    for card in raw_cards:
        by_url[card["url"]] = card

    items: list[ResearchItem] = []
    for card in by_url.values():
        cat = (card.get("category") or "").strip()
        if cat.lower() in SKIP_CATEGORIES:
            continue
        # Prefer current-calendar-year URLs (stale Late Mail paths often keep old years)
        year_m = re.search(r"/news/(\d{4})/", card["url"])
        if year_m and int(year_m.group(1)) < now.year:
            continue
        pub = parse_published(card.get("published_raw"), now=now)
        # Undated cards survive here; the main filter decides those on title.
        if pub is not None and window_start is not None and pub < window_start:
            continue
        # Never store ISO durations / unparseable junk as published_at
        published_at = to_iso(pub)
        items.append(
            ResearchItem(
                id=item_id("nrl_news", card["url"]),
                source_tier="official",
                channel="nrl_news",
                category=cat or None,
                title=card["title"],
                url=card["url"],
                published_at=published_at,
                snippet=None,
                reliability="high",
                guidance=None,
            )
        )

    # Prefer dated cards; undated go last (do not let empty strings sort ahead)
    def _sort_key(it: ResearchItem) -> tuple:
        return (0 if it.published_at else 1, -(
            parse_published(it.published_at, now=now).timestamp()
            if it.published_at and parse_published(it.published_at, now=now)
            else 0.0
        ))

    items.sort(key=_sort_key)
    result.items = items[:max_list_items]
    return result
