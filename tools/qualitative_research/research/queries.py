"""Query templates and team slug helpers for a fixture."""

from __future__ import annotations

# nickName (as used elsewhere) -> nrl.com club slug
TEAM_SLUGS: dict[str, str] = {
    "broncos": "broncos",
    "bulldogs": "bulldogs",
    "cowboys": "cowboys",
    "dolphins": "dolphins",
    "dragons": "dragons",
    "eels": "eels",
    "knights": "knights",
    "panthers": "panthers",
    "rabbitohs": "rabbitohs",
    "raiders": "raiders",
    "roosters": "roosters",
    "sea eagles": "sea-eagles",
    "sharks": "sharks",
    "storm": "storm",
    "titans": "titans",
    "warriors": "warriors",
    "wests tigers": "wests-tigers",
}


def team_slug(name: str) -> str | None:
    return TEAM_SLUGS.get(name.strip().lower())


# nickName -> city/region names used in headlines ("Gold Coast Titans").
# Deliberately excludes ambiguous bare tokens like "sydney" (Roosters vs
# Rabbitohs) and "queensland" (Cowboys vs Broncos vs Titans).
TEAM_REGION_ALIASES: dict[str, tuple[str, ...]] = {
    "broncos": ("brisbane",),
    "bulldogs": ("canterbury", "canterbury-bankstown", "bankstown"),
    "cowboys": ("north queensland", "nth queensland"),
    "dolphins": ("redcliffe",),
    "dragons": ("st george", "st. george", "illawarra"),
    "eels": ("parramatta",),
    "knights": ("newcastle",),
    "panthers": ("penrith",),
    "rabbitohs": ("south sydney", "souths"),
    "raiders": ("canberra",),
    "roosters": ("sydney roosters", "easts"),
    "sea eagles": ("manly", "manly warringah", "eagles"),
    "sharks": ("cronulla", "cronulla-sutherland"),
    "storm": ("melbourne",),
    "titans": ("gold coast",),
    "warriors": ("new zealand", "nz warriors", "auckland"),
    "wests tigers": ("wests", "tigers"),
}

# Reverse lookup: any alias -> canonical nickName.
REGION_ALIAS_TO_NICKNAME: dict[str, str] = {
    alias: nickname
    for nickname, aliases in TEAM_REGION_ALIASES.items()
    for alias in aliases
}


def region_aliases(name: str) -> tuple[str, ...]:
    """City/region names a headline may use instead of the nickName."""
    return TEAM_REGION_ALIASES.get(name.strip().lower(), ())


MAX_CUSTOM_QUERIES = 6

# Cap on agent queries + default templates combined, to bound HTTP fan-out.
MAX_MERGED_QUERIES = 10


def sanitize_custom_queries(
    queries: list[str] | None,
    *,
    max_queries: int = MAX_CUSTOM_QUERIES,
) -> list[str] | None:
    """Normalize agent-authored queries; return None to use defaults."""
    if not queries:
        return None
    out: list[str] = []
    seen: set[str] = set()
    for q in queries:
        text = " ".join(str(q).split()).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= max_queries:
            break
    return out or None


def default_queries(
    home: str,
    away: str,
    round_number: int | None = None,
) -> list[str]:
    """Built-in OR-heavy templates tuned for availability coverage."""
    queries = [
        f"{home} {away} NRL",
        (
            f"{home} NRL injury OR sidelined OR suspension OR judiciary "
            f"OR \"team list\" OR \"late mail\""
        ),
        (
            f"{away} NRL injury OR sidelined OR suspension OR judiciary "
            f"OR \"team list\" OR \"late mail\""
        ),
        (
            f"{home} {away} NRL preview OR form OR motivation OR derby "
            f"OR \"must win\" OR bye"
        ),
    ]
    if round_number is not None:
        queries.append(f"NRL round {round_number} {home} OR {away}")
    return queries


def search_queries(
    home: str,
    away: str,
    round_number: int | None = None,
    custom_queries: list[str] | None = None,
) -> list[str]:
    """Wide-net query strings for DDG / Google News.

    Agent-authored queries are merged *with* the default templates rather than
    replacing them: the agent steers discovery toward whatever it finds
    interesting, while the templates guarantee the injury / Late Mail coverage
    the research gate depends on. Scope stays qualitative — weather, venue,
    kickoff, and match officials come from fixture_scene.
    """
    defaults = default_queries(home, away, round_number)
    custom = sanitize_custom_queries(custom_queries)
    if custom is None:
        return defaults

    merged: list[str] = []
    seen: set[str] = set()
    for q in [*custom, *defaults]:
        key = q.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(q)
        if len(merged) >= MAX_MERGED_QUERIES:
            break
    return merged


def reddit_queries(home: str, away: str, round_number: int | None = None) -> list[str]:
    queries = [f"{home} {away}", f"{home} injury", f"{away} injury"]
    if round_number is not None:
        queries.append(f"round {round_number} {home} OR {away}")
    return queries
