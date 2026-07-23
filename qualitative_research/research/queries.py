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


def search_queries(
    home: str,
    away: str,
    round_number: int | None = None,
    venue: str | None = None,
) -> list[str]:
    """Wide-net query strings for DDG / Google News.

    Keeps the proven match + injury templates; situational factors use two
    focused queries (form/preview vs officials/conditions) instead of one
    odds-heavy mega-OR that mostly returned tipster pages.
    """
    queries = [
        f"{home} {away} NRL",
        f"{home} NRL injury OR sidelined OR \"team list\" OR \"late mail\"",
        f"{away} NRL injury OR sidelined OR \"team list\" OR \"late mail\"",
        # Form / motivation / preview (proven useful colour)
        (
            f"{home} {away} NRL preview OR form OR motivation OR derby "
            f"OR \"must win\" OR bye"
        ),
        # Officials + playing conditions (replaces odds/line-movement query)
        (
            f"{home} {away} NRL referee OR bunker OR judiciary OR suspension "
            f"OR weather OR \"playing conditions\""
        ),
    ]
    if venue:
        queries.append(f"\"{venue}\" NRL weather OR rain OR forecast OR crowd")
    if round_number is not None:
        queries.append(f"NRL round {round_number} {home} OR {away}")
    return queries


def reddit_queries(home: str, away: str, round_number: int | None = None) -> list[str]:
    queries = [f"{home} {away}", f"{home} injury", f"{away} injury"]
    if round_number is not None:
        queries.append(f"round {round_number} {home} OR {away}")
    return queries
