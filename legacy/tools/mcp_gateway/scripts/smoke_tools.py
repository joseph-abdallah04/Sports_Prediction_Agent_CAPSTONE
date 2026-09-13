#!/usr/bin/env python3
"""Smoke-test MCP tool wrappers via direct function calls (no MCP host required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Match server import path setup
_TOOLS = Path(__file__).resolve().parents[2]  # .../tools
sys.path[:0] = [
    str(_TOOLS / "mathematical_engine"),
    str(_TOOLS / "fixture_scene"),
    str(_TOOLS / "qualitative_research"),
    str(Path(__file__).resolve().parents[1]),
]

from gateway.server import (  # noqa: E402
    predict_match,
    research_fixture_news,
    set_fixture_scene,
    tools_health,
)


def _parse(s: str) -> dict:
    return json.loads(s)


def main() -> int:
    health = _parse(tools_health())
    print("health:", json.dumps(health, indent=2)[:500], "...")
    if health.get("tools", {}).get("predict_match", {}).get("model", {}).get("status") not in {
        "ok",
        "not_trained",
    }:
        print("WARN: unexpected model health", file=sys.stderr)

    scene = _parse(
        set_fixture_scene(home_team="Eels", away_team="Panthers", force_refresh=False)
    )
    if scene.get("error"):
        print("scene error:", scene)
        return 1
    fix = scene["fixture"]
    print(
        "scene ok:",
        fix.get("kickoff"),
        fix.get("venue"),
        scene.get("weather", {}).get("math_weather_label"),
    )

    # Research can be slow; use cache if present
    research = _parse(
        research_fixture_news(
            home_team=fix["home_team"],
            away_team=fix["away_team"],
            kickoff=fix["kickoff"],
            round_number=fix.get("round_number"),
            venue=fix.get("venue"),
            force_refresh=False,
        )
    )
    if research.get("error"):
        print("research error:", research)
        return 1
    print(
        "research ok: items=",
        len(research.get("items") or []),
        "cache_hit=",
        research.get("cache_hit"),
    )

    pred = _parse(
        predict_match(
            home_team=fix["home_team"],
            away_team=fix["away_team"],
            venue=fix["venue"],
            kickoff=fix["kickoff"],
            weather=scene.get("weather", {}).get("math_weather_label"),
        )
    )
    if pred.get("error"):
        print("predict error:", pred)
        return 1
    print(
        "predict ok: p_home=",
        pred.get("home_win_probability") or pred.get("probability") or pred.get("p_home_win"),
        "keys=",
        sorted(pred.keys())[:12],
    )
    print("SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
