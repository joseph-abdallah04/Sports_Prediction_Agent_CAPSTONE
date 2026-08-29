"""Offline checks for gate, market quotes, verifier skip, 0.85 ceiling."""

from __future__ import annotations

from agent_app.judgement import extract_market_mentions, price_quote
from agent_app.research_gate import research_ok
from agent_app.verifier import (
    CONFIDENCE_CEILING,
    _check_judgement_grounding,
    material_shap_drivers,
    omitted_math_signals_only,
    should_recalibrate,
)


def _check(label: str, cond: bool) -> int:
    print(f"  {'ok  ' if cond else 'FAIL'} {label}")
    return 0 if cond else 1


def main() -> int:
    fails = 0

    print("confidence ceiling")
    fails += _check("ceiling is 0.85", CONFIDENCE_CEILING == 0.85)
    fails += _check(
        "0.86 fails checklist",
        any(
            i.startswith("confidence_above_ceiling")
            for i in _check_judgement_grounding(
                {
                    "confidence": 0.86,
                    "key_factors": [{"source": "research", "detail": "x"}],
                },
                {"items": [{"title": "t"}]},
            )
        ),
    )
    fails += _check(
        "0.85 passes checklist bound",
        not any(
            i.startswith("confidence_above_ceiling")
            for i in _check_judgement_grounding(
                {
                    "confidence": 0.85,
                    "key_factors": [{"source": "research", "detail": "x"}],
                },
                {"items": [{"title": "t"}]},
            )
        ),
    )

    print("confidence vs math copy")
    roosters_math = {"home_win_probability": 0.8306}
    roosters_copy = {
        "winner": "home",
        "confidence": 0.83,
        "research_stance": "silent",
        "strongest_reason_could_lose": "Tedesco is out.",
        "key_factors": [{"source": "research", "detail": "Tedesco out (nrl.com)."}],
    }
    roosters_issues = _check_judgement_grounding(
        roosters_copy, {"items": [{"title": "t"}]}, roosters_math
    )
    fails += _check(
        "copying 0.83 without confirms is rejected",
        "confidence_copied_math_without_research_confirm" in roosters_issues,
    )
    fails += _check(
        "0.83 without confirms is above the clear-edge band",
        "confidence_above_clear_edge_without_research_confirm" in roosters_issues,
    )

    eagles_ok = {
        "winner": "home",
        "confidence": 0.75,
        "research_stance": "confirms",
        "strongest_reason_could_lose": "Any favourite can lose in the NRL.",
        "loss_reason_specific": False,
        "key_factors": [
            {"source": "research", "detail": "Trbojevic returns (seaeagles.com.au)."}
        ],
    }
    eagles_issues = _check_judgement_grounding(
        eagles_ok, {"items": [{"title": "t"}]}, {"home_win_probability": 0.7499, "prediction": "Home Win"}
    )
    fails += _check(
        "matching math is allowed when research confirms",
        eagles_issues == [],
    )

    storm_copy = {
        "winner": "away",
        "confidence": 0.61,
        "research_stance": "silent",
        "strongest_reason_could_lose": "Suncorp and a dead rubber.",
        "loss_reason_specific": True,
        "key_factors": [
            {"source": "research", "detail": "Neither side makes finals (sportingnews)."}
        ],
    }
    storm_issues = _check_judgement_grounding(
        storm_copy, {"items": [{"title": "t"}]}, {"home_win_probability": 0.3892, "prediction": "Away Win"}
    )
    fails += _check(
        "pasting 0.61 with silent research is a copy",
        "confidence_copied_math_without_research_confirm" in storm_issues,
    )
    storm_own = dict(storm_copy, confidence=0.58)
    storm_own_issues = _check_judgement_grounding(
        storm_own, {"items": [{"title": "t"}]}, {"home_win_probability": 0.3892, "prediction": "Away Win"}
    )
    fails += _check(
        "same pick at 0.58 with silent research is fine",
        storm_own_issues == [],
    )
    fake_confirm = dict(
        storm_copy,
        research_stance="confirms",
        confidence=0.61,
    )
    fake_issues = _check_judgement_grounding(
        fake_confirm, {"items": [{"title": "t"}]}, {"home_win_probability": 0.3892}
    )
    fails += _check(
        "cannot label dead-rubber stakes as confirms",
        "research_stance_confirms_without_team_news" in fake_issues,
    )

    hughes = {
        "winner": "away",
        "confidence": 0.68,
        "research_stance": "confirms",
        "strongest_reason_could_lose": "Last home game at Suncorp.",
        "loss_reason_specific": True,
        "key_factors": [
            {"source": "research", "detail": "Jahrome Hughes returns at halfback (Lone Scout)."}
        ],
    }
    hughes_issues = _check_judgement_grounding(
        hughes, {"items": [{"title": "t"}]}, {"home_win_probability": 0.3892, "prediction": "Away Win"}
    )
    fails += _check(
        "named loss reason does not force a 0.65 cap",
        hughes_issues == [],
    )
    hughes_ok = dict(hughes, confidence=0.61)
    hughes_ok_issues = _check_judgement_grounding(
        hughes_ok,
        {"items": [{"title": "t"}]},
        {"home_win_probability": 0.3892, "prediction": "Away Win"},
    )
    fails += _check(
        "same side at the 0.61 prior with Hughes confirm is fine",
        hughes_ok_issues == [],
    )
    climb_ok = {
        "winner": "away",
        "confidence": 0.70,
        "research_stance": "confirms",
        "strongest_reason_could_lose": "Upsets happen in the NRL.",
        "loss_reason_specific": False,
        "key_factors": [
            {"source": "research", "detail": "Late mail names an unexpected change (nrl.com)."}
        ],
    }
    climb_issues = _check_judgement_grounding(
        climb_ok,
        {"items": [{"title": "t"}]},
        {"home_win_probability": 0.3892, "prediction": "Away Win"},
    )
    fails += _check(
        "checklist does not ban a band climb",
        climb_issues == [],
    )
    conflict_kept = {
        "winner": "home",
        "confidence": 0.83,
        "research_stance": "conflicts",
        "strongest_reason_could_lose": "Tedesco is out.",
        "loss_reason_specific": True,
        "key_factors": [
            {"source": "research", "detail": "Tedesco is out (nrl.com)."}
        ],
    }
    conflict_issues = _check_judgement_grounding(
        conflict_kept,
        {"items": [{"title": "t"}]},
        {"home_win_probability": 0.8306, "prediction": "Home Win"},
    )
    fails += _check(
        "conflicts cannot keep the math number",
        "confidence_not_discounted_despite_research_conflict" in conflict_issues,
    )
    conflict_down = dict(conflict_kept, confidence=0.62)
    conflict_down_issues = _check_judgement_grounding(
        conflict_down,
        {"items": [{"title": "t"}]},
        {"home_win_probability": 0.8306, "prediction": "Home Win"},
    )
    fails += _check(
        "conflicts may keep the side if confidence comes down",
        conflict_down_issues == [],
    )

    print("research gate")
    thin = {
        "request": {"home_team": "Titans", "away_team": "Sharks"},
        "items": [
            {
                "title": "NRL Late Mail: Round 25 - Latrell on hold",
                "body_excerpt": "Rabbitohs: Latrell. Sea Eagles: Turbo.",
                "channel": "nrl_news",
                "source_tier": "official",
            },
            {
                "title": "Unrelated preview",
                "body_excerpt": "Finals race chatter.",
                "channel": "google_news_rss",
            },
            {
                "title": "Also unrelated",
                "body_excerpt": "More chatter.",
                "channel": "duckduckgo",
            },
        ],
        "channels": {
            "nrl_news": {"status": "ok", "items_kept": 1},
            "duckduckgo": {"status": "ok", "items_kept": 1},
            "google_news_rss": {"status": "ok", "items_kept": 1},
        },
    }
    ok, diag = research_ok(thin)
    fails += _check("league wrap alone does not pass gate", not ok)
    fails += _check(
        "fail reason names both-teams",
        "insufficient_items_mentioning_both_teams" in (diag.get("fail_reasons") or []),
    )

    fat = {
        "request": {"home_team": "Titans", "away_team": "Sharks"},
        "items": [
            {
                "title": "Titans v Sharks team list",
                "body_excerpt": "Titans team list. Sharks: Fonua-Blake returns from suspension.",
                "channel": "nrl_news",
                "source_tier": "official",
            },
            {
                "title": "Titans vs Sharks preview",
                "body_excerpt": "Titans host Sharks at Cbus.",
                "channel": "google_news_rss",
            },
            {
                "title": "Sharks late mail v Titans",
                "body_excerpt": "Sharks late mail against the Titans. Trindall out.",
                "channel": "duckduckgo",
            },
        ],
        "channels": {
            "nrl_news": {"status": "ok", "items_kept": 1},
            "duckduckgo": {"status": "ok", "items_kept": 1},
            "google_news_rss": {"status": "ok", "items_kept": 1},
        },
    }
    ok2, diag2 = research_ok(fat)
    fails += _check("on-fixture pack passes gate", ok2)
    fails += _check("three both-team items", diag2.get("items_mentioning_both_teams") == 3)
    fails += _check("fixture availability true", diag2.get("has_fixture_availability") is True)

    print("market mentions")
    research = {
        "request": {"home_team": "Titans", "away_team": "Sharks"},
        "items": [
            {
                "title": "Bulldogs vs Rabbitohs tips",
                "body_excerpt": "Bulldogs $" + "1.83 favourite over Rabbitohs.",
            },
            {
                "title": "Titans vs Sharks tips",
                "body_excerpt": (
                    "x" * 900
                    + " Titans $"
                    + "1.20 and Sharks $"
                    + "4.50 at Cbus."
                ),
            },
        ],
    }
    mentions = extract_market_mentions(research)
    fails += _check("foreign-game price dropped", len(mentions) == 1)
    fails += _check(
        "price_quote contains $1.20",
        bool(mentions and "$1.20" in (mentions[0].get("price_quote") or "")),
    )
    q = price_quote("padding " * 80 + "priced at $1.52 tonight " + "padding " * 80)
    fails += _check("price_quote is a short window", bool(q) and len(q) < 400 and "$1.52" in q)

    print("verifier skip")
    shap = {
        "favouring_Sharks_away_win": [
            "Elo rating advantage (-211 points) — contribution 0.324 (21% of total)",
            "Home travel to venue (0 km) — contribution 0.021 (1% of total)",
        ],
        "favouring_Titans_home_win": [
            "Bradley-Terry strength advantage — contribution 0.248 (16% of total)",
        ],
    }
    material = material_shap_drivers(shap)
    fails += _check("21% and 16% are material", len(material) == 2)
    fails += _check("1% travel is not material", not any("0 km" in x for x in material))

    audit_only = {
        "pass": False,
        "checks": [
            {"check": "sourced_claims", "verdict": "pass"},
            {"check": "omitted_math_signals", "verdict": "fail", "evidence": "travel"},
        ],
        "issues": ["Math drivers include travel"],
        "instruction": "please consider travel",
    }
    fail, _, _ = should_recalibrate({"pass": True, "issues": []}, audit_only)
    fails += _check("coverage-only does not recalibrate", fail is False)
    fails += _check("omitted_math_signals_only true", omitted_math_signals_only(audit_only))

    audit_real = {
        "pass": False,
        "checks": [
            {"check": "sourced_claims", "verdict": "fail"},
            {"check": "omitted_math_signals", "verdict": "fail"},
        ],
        "issues": ["unsourced $1.20"],
        "instruction": "drop the price",
    }
    fail2, _, _ = should_recalibrate({"pass": True, "issues": []}, audit_real)
    fails += _check("real sourced_claims fail still recalibrates", fail2 is True)

    print("\nSMOKE_OK" if not fails else f"\n{fails} CHECK(S) FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
