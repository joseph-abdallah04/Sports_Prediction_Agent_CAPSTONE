"""Resolve article URLs and fetch plain-text body excerpts for the LLM."""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .http_client import RateLimitedHttpClient
from .models import ResearchItem

logger = logging.getLogger(__name__)

_GOOGLE_HOSTS = {"news.google.com", "news.google.com.au"}

_BOILERPLATE = re.compile(
    r"(respect and honour the traditional|"
    r"acknowledg(?:e|ement) of country|"
    r"traditional custodians|"
    r"subscribe to our|"
    r"sign up for|"
    r"cookie (?:policy|settings)|"
    r"all rights reserved|"
    r"sponsored by|"
    r"^share (?:on|via)|"
    r"^share on social media)",
    re.I,
)


def strip_html(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def resolve_article_url(url: str) -> str:
    """Turn Google News RSS redirect URLs into publisher URLs when possible."""
    if not url:
        return url
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host not in _GOOGLE_HOSTS and "news.google." not in host:
        return url
    try:
        from googlenewsdecoder import new_decoderv1

        result = new_decoderv1(url)
        if isinstance(result, dict) and result.get("status") and result.get("decoded_url"):
            return str(result["decoded_url"])
        if isinstance(result, str) and result.startswith("http"):
            return result
    except Exception as e:
        logger.warning("Google News URL decode failed for %s: %s", url[:80], e)
    return url


def _clean_line(text: str) -> str | None:
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) < 2:
        return None
    if _BOILERPLATE.search(t) and len(t) < 280:
        return None
    return t


def _extract_from_soup(soup: BeautifulSoup, max_chars: int) -> str | None:
    """Pull readable text including team-list widgets (not only <p>)."""
    for tag in soup(
        ["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript"]
    ):
        tag.decompose()

    root = (
        soup.find("article")
        or soup.find("main")
        or soup.find(attrs={"role": "main"})
        or soup.find(class_=re.compile(r"(article|content|story|news-body)", re.I))
        or soup.body
        or soup
    )

    chunks: list[str] = []
    seen: set[str] = set()

    def _add(text: str | None) -> None:
        line = _clean_line(text or "")
        if not line:
            return
        key = line.lower()
        if key in seen:
            return
        seen.add(key)
        chunks.append(line)

    # Structured content first: headings, paragraphs, list/table cells (team widgets)
    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "figcaption"]):
        _add(el.get_text(" ", strip=True))

    # Div/span text that looks like jersey lines ("1. Name" / "BACKS") if still thin
    joined = "\n".join(chunks)
    if len(joined) < 400:
        for el in root.find_all(["div", "span", "section"]):
            # Skip huge containers; prefer leaf-ish nodes
            if el.find(["div", "p", "ul", "ol", "table"]):
                continue
            t = el.get_text(" ", strip=True)
            if len(t) < 3 or len(t) > 120:
                continue
            if re.search(
                r"(\b(?:backs|forwards|interchange|reserves|team lists?)\b)|(^\d{1,2}\.?\s+[A-Z])",
                t,
                re.I,
            ) or re.match(r"^\d{1,2}\b", t):
                _add(t)

    if not chunks:
        blob = root.get_text("\n", strip=True)
        for ln in blob.splitlines():
            _add(ln)

    if not chunks:
        return None

    # Drop leading acknowledgement-only runs if we have real content after
    filtered = [c for c in chunks if not (_BOILERPLATE.search(c) and "eel" not in c.lower())]
    if len("\n".join(filtered)) >= 80:
        chunks = filtered

    text = "\n".join(chunks)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < 60:
        return None
    return text[:max_chars]


def fetch_article_excerpt(
    client: RateLimitedHttpClient,
    url: str,
    *,
    max_chars: int = 4000,
) -> str | None:
    """Fetch a page and extract readable text including UI widgets (soft-fail)."""
    try:
        html = client.get_text(url)
    except Exception as e:
        logger.warning("Article fetch failed %s: %s", url, e)
        return None
    soup = BeautifulSoup(html, "html.parser")
    return _extract_from_soup(soup, max_chars)


def _body_priority(it: ResearchItem) -> float:
    t = (it.title or "").lower()
    score = float(it.relevance_score)
    if it.source_tier == "official" or "nrl.com" in (it.url or ""):
        score += 10.0
    if "late mail" in t:
        score += 5.0
    if "casualty" in t or "injury" in t:
        score += 4.0
    if "team list" in t:
        score += 5.0
    if "preview" in t:
        score += 1.0
    snip = it.snippet or ""
    if "<a href" in snip or "news.google.com" in snip or len(snip) < 80:
        score += 2.0
    return -score


def attach_article_bodies(
    client: RateLimitedHttpClient,
    items: list[ResearchItem],
    *,
    max_unique_fetches: int = 30,
) -> None:
    """Resolve URLs and attach body excerpts for kept items.

    Fetches up to ``max_unique_fetches`` distinct publisher URLs (deduped),
    prioritising official / team-list / injury pages. Soft-fail per URL.
    """
    for item in items:
        item.snippet = strip_html(item.snippet)
        resolved = resolve_article_url(item.url)
        if resolved != item.url:
            item.url = resolved

    by_url: dict[str, str] = {}
    for item in items:
        if item.body_excerpt:
            by_url[item.url] = item.body_excerpt
    for item in items:
        if not item.body_excerpt and item.url in by_url:
            item.body_excerpt = by_url[item.url]
            if not item.snippet or len(item.snippet) < 80:
                item.snippet = item.body_excerpt[:280]

    need_body = [i for i in items if not i.body_excerpt]
    need_body.sort(key=_body_priority)

    fetched_urls: set[str] = set(by_url.keys())
    fetches = 0

    for item in need_body:
        resolved = item.url
        if resolved in fetched_urls:
            excerpt = by_url.get(resolved)
            if excerpt:
                item.body_excerpt = excerpt
                if not item.snippet or len(item.snippet) < 80:
                    item.snippet = excerpt[:280]
            continue
        if fetches >= max_unique_fetches:
            break
        fetched_urls.add(resolved)
        fetches += 1
        excerpt = fetch_article_excerpt(client, resolved)
        if not excerpt:
            continue
        item.body_excerpt = excerpt
        by_url[resolved] = excerpt
        if not item.snippet or len(item.snippet) < 80:
            item.snippet = excerpt[:280]
        for sibling in items:
            if sibling is not item and sibling.url == resolved and not sibling.body_excerpt:
                sibling.body_excerpt = excerpt
                if not sibling.snippet or len(sibling.snippet) < 80:
                    sibling.snippet = excerpt[:280]
