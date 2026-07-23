"""Shared item shapes for research channels."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ResearchItem:
    id: str
    source_tier: str  # official | mainstream_news | search_discovery | unverified_community
    channel: str
    category: str | None
    title: str
    url: str
    published_at: str | None
    snippet: str | None = None
    body_excerpt: str | None = None
    reliability: str = "medium"
    guidance: str | None = None
    age_hours: float | None = None
    relevance_score: float = 0.0
    keep_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChannelResult:
    name: str
    status: str  # ok | error | rate_limited | skipped
    items: list[ResearchItem] = field(default_factory=list)
    error: str | None = None
    queries: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        out: dict[str, Any] = {"status": self.status, "items_kept": len(self.items)}
        if self.error:
            out["error"] = self.error
        return out


def item_id(channel: str, url: str) -> str:
    import hashlib
    return hashlib.sha256(f"{channel}|{url}".encode()).hexdigest()[:16]


def hours_since(published_at: datetime | None, now: datetime) -> float | None:
    if published_at is None:
        return None
    return (now - published_at).total_seconds() / 3600.0
