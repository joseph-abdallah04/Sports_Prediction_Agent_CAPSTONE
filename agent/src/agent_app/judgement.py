"""Judgement session: non-agentic LLM synthesis over tool facts."""

from __future__ import annotations

import json
import re
from typing import Any

from agent_app.config import Settings
from agent_app.llm import ChatSession, parse_json_object
from agent_app.prompts import JUDGEMENT_SYSTEM, RECALIBRATE_USER_TEMPLATE

_PRICE_RE = re.compile(r"\$\d{1,2}\.\d{2}")
_PRICE_QUOTE_WINDOW = 180


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _team_aliases(team: str) -> set[str]:
    t = _norm(team)
    aliases = {t}
    parts = t.split()
    if parts:
        aliases.add(parts[-1])
    if t == "wests tigers":
        aliases.update({"tigers", "w.tigers"})
    return {a for a in aliases if len(a) > 2}


def mentions_team(text: str, team: str) -> bool:
    blob = _norm(text)
    return any(a in blob for a in _team_aliases(team))


def mentions_both_teams(text: str, home: str, away: str) -> bool:
    if not home or not away:
        return False
    return mentions_team(text, home) and mentions_team(text, away)


RESEARCH_STANCES = ("confirms", "conflicts", "mixed", "silent")
# Two-decimal match is how the model pastes P(win); independent 0.60 vs 0.6108
# is not treated as a copy.
_COPY_DECIMALS = 2
# Prompt band: above 0.65 needs several independent signals, including research.
CLEAR_EDGE_ABOVE = 0.65
_TEAM_NEWS_RE = re.compile(
    r"(return|returned|returning|comeback|named|sidelined|injur|"
    r"suspen|late mail|team list|hat-?trick|ruled out|\bout\b|"
    r"available|omitted|dropped|recalled)",
    re.I,
)


def normalize_research_stance(value: Any) -> str | None:
    raw = str(value or "").strip().lower()
    if raw in RESEARCH_STANCES:
        return raw
    aliases = {
        "confirm": "confirms",
        "confirmed": "confirms",
        "conflict": "conflicts",
        "neutral": "silent",
        "none": "silent",
        "n/a": "silent",
    }
    return aliases.get(raw)


def math_win_probability_for_side(math: dict[str, Any] | None, winner: str) -> float | None:
    """P(the judged side wins) from the model, or None if we cannot compute it."""
    if not math or winner not in ("home", "away"):
        return None
    p_home = math.get("home_win_probability")
    if not isinstance(p_home, (int, float)):
        return None
    p_home = float(p_home)
    if not 0.0 <= p_home <= 1.0:
        return None
    return p_home if winner == "home" else 1.0 - p_home


def confidence_copies_math(confidence: Any, math_p: float | None) -> bool:
    """True when the judge pasted the model's P(their side) to two decimals."""
    if math_p is None or not isinstance(confidence, (int, float)):
        return False
    return round(float(confidence), _COPY_DECIMALS) == round(float(math_p), _COPY_DECIMALS)


def loss_reason_specific_flag(judgement: dict[str, Any]) -> bool | None:
    """Parse loss_reason_specific; None if the judge omitted it."""
    raw = judgement.get("loss_reason_specific")
    if raw is None or raw == "":
        return None
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    if text in ("true", "yes", "1"):
        return True
    if text in ("false", "no", "0"):
        return False
    return None


def research_factors_cite_team_news(factors: list[dict[str, Any]]) -> bool:
    """True when a research key_factor names availability/form, not just stakes."""
    blob = " ".join(
        str(f.get("detail") or "")
        for f in factors
        if isinstance(f, dict) and f.get("source") == "research"
    )
    return bool(_TEAM_NEWS_RE.search(blob))


def price_quote(body: str, *, window: int = _PRICE_QUOTE_WINDOW) -> str | None:
    """Short window around the first $x.xx so the verifier can match a price."""
    if not body:
        return None
    m = _PRICE_RE.search(body)
    if not m:
        return None
    start = max(0, m.start() - window // 2)
    end = min(len(body), m.end() + window // 2)
    return body[start:end].strip()


def fixture_teams_from_research(research: dict[str, Any]) -> tuple[str, str]:
    req = research.get("request") or {}
    return str(req.get("home_team") or ""), str(req.get("away_team") or "")


def label_shap_drivers(
    shap: Any,
    home_team: str | None,
    away_team: str | None,
) -> Any:
    """Rename positive/negative driver groups to the club they actually favour.

    The math tool speaks in terms of the label: positive pushes P(home win) up.
    An LLM reads "positive_drivers" as "points my way" and, when the model picks
    the away side, cheerfully attributes home-favouring drivers to the away team
    (ADR 0008). Naming the club removes the ambiguity.
    """
    if not isinstance(shap, dict):
        return shap
    home = home_team or "home team"
    away = away_team or "away team"
    labelled = {
        f"favouring_{home}_home_win": shap.get("positive_drivers") or [],
        f"favouring_{away}_away_win": shap.get("negative_drivers") or [],
    }
    for key, value in shap.items():
        if key not in ("positive_drivers", "negative_drivers"):
            labelled[key] = value
    return labelled


def extract_market_mentions(
    research: dict[str, Any], *, limit: int = 6
) -> list[dict[str, Any]]:
    """Pull bookie-ish snippets + $prices from on-fixture excerpts (no new tools)."""
    home, away = fixture_teams_from_research(research)
    mentions: list[dict[str, Any]] = []
    for item in research.get("items") or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "")
        body = str(item.get("body_excerpt") or "")
        blob = f"{title}\n{body}"
        if home and away and not mentions_both_teams(blob, home, away):
            continue
        prices = _PRICE_RE.findall(blob)
        if not prices:
            continue
        quote = price_quote(body) or price_quote(blob)
        mentions.append(
            {
                "title": title,
                "url": item.get("url"),
                "source_tier": item.get("source_tier"),
                "prices_found": prices[:8],
                "price_quote": quote,
                "snippet": (quote or body)[:400],
            }
        )
        if len(mentions) >= limit:
            break
    return mentions


def _slim_research(research: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    home, away = fixture_teams_from_research(research)
    items = []
    for i in (research.get("items") or [])[:limit]:
        if not isinstance(i, dict):
            continue
        body = i.get("body_excerpt") or ""
        title = i.get("title") or ""
        blob = f"{title}\n{body}"
        quote = None
        if (not home or not away or mentions_both_teams(blob, home, away)) and _PRICE_RE.search(
            blob
        ):
            quote = price_quote(body) or price_quote(blob)
        slim = {
            "title": i.get("title"),
            "source_tier": i.get("source_tier"),
            "channel": i.get("channel"),
            "url": i.get("url"),
            "body_excerpt": body[:800],
        }
        if quote:
            slim["price_quote"] = quote
        items.append(slim)
    return items


def start_judgement_session(
    settings: Settings,
    *,
    scene: dict[str, Any],
    research: dict[str, Any],
    math: dict[str, Any],
    user_question: str,
) -> tuple[ChatSession, dict[str, Any]]:
    session = ChatSession(settings)
    session.add_system(JUDGEMENT_SYSTEM)
    fixture = scene.get("fixture") or {}
    weather = scene.get("weather") or {}
    standings = scene.get("standings")
    packet = {
        "user_question": user_question,
        "scene": {
            "fixture": {
                k: fixture.get(k)
                for k in (
                    "home_team",
                    "away_team",
                    "kickoff",
                    "venue",
                    "round_number",
                    "officials",
                    "team_lists",
                )
            },
            "math_weather_label": weather.get("math_weather_label"),
            # Official ladder rows for both clubs (from nrl.com). Lets the judge
            # sanity-check ladder SHAP drivers against readable PD / position.
            "standings": standings,
        },
        "math": {
            "prediction": math.get("prediction"),
            "home_win_probability": math.get("home_win_probability"),
            "probability": math.get("probability"),
            "shap_drivers": label_shap_drivers(
                math.get("shap_explanations"),
                fixture.get("home_team"),
                fixture.get("away_team"),
            ),
            "error": math.get("error"),
        },
        "research": {
            "error": research.get("error"),
            "queries_run": research.get("queries_run"),
            "filter_summary": research.get("filter_summary"),
            "items": _slim_research(research),
        },
        # Bookie pages often lose prices behind paywalls; when $x.xx survives in
        # an excerpt, surface it explicitly so the judge can compare without
        # hunting. Empty list is fine — then there is nothing to acknowledge.
        "market_mentions": extract_market_mentions(research),
    }
    session.add_user(
        "Produce your prediction JSON from this evidence:\n"
        + json.dumps(packet, default=str)
    )
    raw = session.complete(step="judgement")
    session.add_assistant(raw)
    judgement = parse_json_object(raw)
    return session, judgement


def recalibrate_judgement(
    session: ChatSession,
    *,
    issues: list[str],
    instruction: str,
) -> dict[str, Any]:
    session.add_user(
        RECALIBRATE_USER_TEMPLATE.format(
            issues="\n".join(f"- {x}" for x in issues) or "- (none listed)",
            instruction=instruction or "Reconsider weighting; re-output judgement JSON.",
        )
    )
    raw = session.complete(step="verifier_recalibrate")
    session.add_assistant(raw)
    return parse_json_object(raw)
