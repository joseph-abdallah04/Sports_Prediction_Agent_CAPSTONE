"""Offline checks for research ranking / roundup drops (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.models import ResearchItem, item_id  # noqa: E402
from research.filter import (  # noqa: E402
    _apply_relevance,
    _is_other_fixture_preview,
    cap_league_roundups,
    refine_kept_after_bodies,
)


def _item(**kwargs) -> ResearchItem:
    title = kwargs.get("title", "x")
    url = kwargs.get("url", f"https://example.com/{title}")
    return ResearchItem(
        id=item_id(kwargs.get("channel", "nrl_news"), url),
        source_tier=kwargs.get("source_tier", "official"),
        channel=kwargs.get("channel", "nrl_news"),
        category=kwargs.get("category"),
        title=title,
        url=url,
        published_at=kwargs.get("published_at"),
        snippet=kwargs.get("snippet"),
        body_excerpt=kwargs.get("body_excerpt"),
        keep_reasons=list(kwargs.get("keep_reasons") or []),
        relevance_score=float(kwargs.get("relevance_score") or 0.0),
    )


def _check(label: str, cond: bool) -> int:
    print(f"  {'ok  ' if cond else 'FAIL'} {label}")
    return 0 if cond else 1


def main() -> int:
    fails = 0
    print("other-fixture titles")
    fails += _check(
        "other pairing dropped (Broncos vs Warriors in Eels packet)",
        _is_other_fixture_preview(
            "Broncos vs Warriors Tips, Odds – NRL Round 24", "Eels", "Cowboys"
        ),
    )
    fails += _check(
        "this fixture kept",
        not _is_other_fixture_preview(
            "Eels vs Cowboys NRL round 24 preview", "Eels", "Cowboys"
        ),
    )
    fails += _check(
        "one-club different opponent still dropped",
        _is_other_fixture_preview("Sharks v Raiders Late Mail", "Eels", "Cowboys"),
    )

    print("scoring: club list beats league Late Mail")
    club = _item(
        title="Updated Cowboys NRL team list: Round 23 v Titans",
        channel="nrl_news",
        source_tier="official",
        body_excerpt="Titans host Cowboys. Nanai out. Ilias returns.",
    )
    wrap = _item(
        title="NRL Late Mail: Round 23 - Rabbitohs lose Graham; Best sidelined",
        channel="nrl_news",
        source_tier="official",
        body_excerpt="Rabbitohs lose Graham. Knights: Best sidelined.",
    )
    r_club: list[str] = ["round_23_match"]
    club.relevance_score = 3.0
    _apply_relevance(
        club,
        text_blob=f"{club.title} {club.body_excerpt}",
        title_l=club.title.lower(),
        home_team="Titans",
        away_team="Cowboys",
        round_number=23,
        reasons=r_club,
    )
    r_wrap: list[str] = ["round_23_match"]
    wrap.relevance_score = 3.0
    _apply_relevance(
        wrap,
        text_blob=f"{wrap.title} {wrap.body_excerpt}",
        title_l=wrap.title.lower(),
        home_team="Titans",
        away_team="Cowboys",
        round_number=23,
        reasons=r_wrap,
    )
    fails += _check(
        f"club {club.relevance_score:.1f} > wrap {wrap.relevance_score:.1f}",
        club.relevance_score > wrap.relevance_score,
    )

    print("post-body prune")
    evergreen = _item(
        title="NRL Casualty Ward: Panthers' Yeo blow",
        url="https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/",
        body_excerpt="Yeo injury update. Titans not mentioned.",
        keep_reasons=["nrl_official_roundup"],
    )
    empty_wrap = _item(
        title="NRL Late Mail: Round 24 - Crossland back",
        body_excerpt="Knights and Sea Eagles Friday night. Best on hold.",
        keep_reasons=["nrl_official_roundup", "round_24_match"],
    )
    on_fixture = _item(
        title="NRL Late Mail: Round 23",
        body_excerpt="Titans: Ilias returns. Cowboys: Nanai hamstring.",
        keep_reasons=["nrl_official_roundup", "round_23_match"],
    )
    kept, dropped = refine_kept_after_bodies(
        [evergreen, empty_wrap, on_fixture],
        home_team="Titans",
        away_team="Cowboys",
        round_number=23,
    )
    reasons = {d["reason"] for d in dropped}
    fails += _check("evergreen casualty dropped", "dropped_evergreen_casualty_ward" in reasons)
    fails += _check("empty roundup dropped", "dropped_roundup_no_fixture_team" in reasons)
    fails += _check("on-fixture Late Mail kept", any("Ilias" in (i.body_excerpt or "") for i in kept))

    print("roundup cap")
    wraps = []
    for i in range(4):
        wraps.append(
            _item(
                title=f"NRL Late Mail extra {i} Titans Cowboys",
                url=f"https://www.nrl.com/news/late-mail-{i}",
                body_excerpt="Titans vs Cowboys late mail paragraph.",
                keep_reasons=["nrl_official_roundup"],
                relevance_score=10 - i,
            )
        )
    club_page = _item(
        title="Cowboys team list v Titans",
        url="https://www.cowboys.com.au/team-list",
        body_excerpt="Titans v Cowboys team list.",
        keep_reasons=["nrl_mentions_both", "mentions_both_teams"],
        relevance_score=12,
    )
    capped, cap_drops = cap_league_roundups([club_page, *wraps])
    fails += _check("club page survives cap", club_page in capped)
    fails += _check("at most 2 roundups", len(cap_drops) == 2)

    print("\nSMOKE_OK" if not fails else f"\n{fails} CHECK(S) FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
