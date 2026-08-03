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


MAX_CUSTOM_QUERIES = 6


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


def search_queries(
    home: str,
    away: str,
    round_number: int | None = None,
    custom_queries: list[str] | None = None,
) -> list[str]:
    """Wide-net query strings for DDG / Google News.

    If custom_queries is provided (agent path), use those. Otherwise use the
    default templates. Scope is qualitative only: injuries / Late Mail / form.
    Weather, venue, kickoff, and match officials come from fixture_scene.
    """
    custom = sanitize_custom_queries(custom_queries)
    if custom is not None:
        return custom

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


def reddit_queries(home: str, away: str, round_number: int | None = None) -> list[str]:
    queries = [f"{home} {away}", f"{home} injury", f"{away} injury"]
    if round_number is not None:
        queries.append(f"round {round_number} {home} OR {away}")
    return queries
