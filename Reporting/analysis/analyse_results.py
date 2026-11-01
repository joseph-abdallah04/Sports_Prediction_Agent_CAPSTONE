"""Score the Round 23 to grand final testing window and write every figure used in the report.

Run from anywhere with the mathematical engine's environment:

    tools/mathematical_engine/.venv/bin/python Reporting/analysis/analyse_results.py

Sources
    Results, control forecasts and agent picks: the operator workbook export
        Reporting/PREDICTIONS LOG_RESULTS - capstone.md
    Model probability, run timing and verifier records: the two run logs and run folders
        agent_runs/ (new system) and legacy/agent_runs/ (old system)
    Official results for cross-checking: tools/mathematical_engine/data_lake/raw_historical/2026
    Holdout metrics: tools/mathematical_engine/reports/holdout_metrics.json

Outputs
    Reporting/output/scored_matches.csv
    Reporting/output/results.json
    Reporting/output/results.md
    Reporting/figures/figure_4_cumulative_accuracy.png
    Reporting/figures/figure_5_confidence_vs_hit_rate.png
"""

import csv
import glob
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score

REPO = Path(__file__).resolve().parents[2]
WORKBOOK = REPO / "Reporting/PREDICTIONS LOG_RESULTS - capstone.md"
NEW_LOG = REPO / "agent_runs/predictions_log.csv"
OLD_LOG = REPO / "legacy/agent_runs/predictions_log.csv"
NEW_RUNS = REPO / "agent_runs/fixtures"
OLD_RUNS = REPO / "legacy/agent_runs/fixtures"
LAKE_2026 = REPO / "tools/mathematical_engine/data_lake/raw_historical/2026"
ETL_MANIFEST = REPO / "tools/mathematical_engine/data_lake/manifests/weekly_manifest.json"
HOLDOUT = REPO / "tools/mathematical_engine/reports/holdout_metrics.json"
OUT = REPO / "Reporting/output"
FIGURES = REPO / "Reporting/figures"

SEED = 20261008
BOOTSTRAP_DRAWS = 20000

ROUND_LABEL = {23: "Round 23", 24: "Round 24", 25: "Round 25", 26: "Round 26", 27: "Round 27",
               28: "Finals week 1", 29: "Finals week 2", 30: "Preliminary finals", 31: "Grand final"}

GEMINI_VERSION = {23: "3.6", 24: "3.6", 25: "3.7", 26: "3.7", 27: "3.8", 28: "3.8", 29: "3.8", 30: "3.8", 31: "3.8"}

# Workbook rows in order. Two Round 24 rows have a blank matchup cell, so the order is fixed here
# and every row is checked against the teams named in its cells.
FIXTURES = [
    (23, "Titans", "Cowboys"), (23, "Warriors", "Panthers"), (23, "Roosters", "Bulldogs"),
    (23, "Storm", "Sea Eagles"), (23, "Dolphins", "Broncos"), (23, "Rabbitohs", "Eels"),
    (23, "Raiders", "Knights"), (23, "Dragons", "Sharks"),
    (24, "Panthers", "Roosters"), (24, "Sea Eagles", "Dolphins"), (24, "Bulldogs", "Rabbitohs"),
    (24, "Sharks", "Raiders"), (24, "Eels", "Cowboys"), (24, "Broncos", "Warriors"),
    (24, "Knights", "Titans"), (24, "Wests Tigers", "Dragons"),
    (25, "Storm", "Panthers"), (25, "Raiders", "Broncos"), (25, "Dolphins", "Eels"),
    (25, "Knights", "Sea Eagles"), (25, "Rabbitohs", "Warriors"), (25, "Dragons", "Bulldogs"),
    (25, "Titans", "Sharks"), (25, "Roosters", "Wests Tigers"),
    (26, "Broncos", "Storm"), (26, "Sea Eagles", "Dragons"), (26, "Panthers", "Bulldogs"),
    (26, "Titans", "Rabbitohs"), (26, "Roosters", "Dolphins"), (26, "Cowboys", "Wests Tigers"),
    (26, "Warriors", "Knights"), (26, "Eels", "Sharks"),
    (27, "Bulldogs", "Broncos"), (27, "Titans", "Dolphins"), (27, "Rabbitohs", "Roosters"),
    (27, "Warriors", "Sea Eagles"), (27, "Cowboys", "Raiders"), (27, "Sharks", "Storm"),
    (27, "Dragons", "Eels"), (27, "Panthers", "Wests Tigers"),
    (28, "Rabbitohs", "Knights"), (28, "Warriors", "Dolphins"), (28, "Sharks", "Cowboys"),
    (28, "Panthers", "Roosters"),
    (29, "Roosters", "Sharks"), (29, "Warriors", "Knights"),
    (30, "Dolphins", "Roosters"), (30, "Panthers", "Knights"),
    (31, "Roosters", "Knights"),
]

TEAM_ALIASES = {
    "north queensland cowboys": "Cowboys", "penrith panthers": "Panthers", "sydney roosters": "Roosters",
    "melbourne storm": "Storm", "south sydney rabbitohs": "Rabbitohs", "newcastle knights": "Knights",
    "cronulla-sutherland sharks": "Sharks", "canberra raiders": "Raiders", "new zealand warriors": "Warriors",
    "canterbury-bankstown bulldogs": "Bulldogs", "st. george illawarra dragons": "Dragons",
    "manly-warringah sea eagles": "Sea Eagles", "parramatta eels": "Eels", "wests tigers": "Wests Tigers",
    "sea eagles": "Sea Eagles", "titans": "Titans", "cowboys": "Cowboys", "warriors": "Warriors",
    "panthers": "Panthers", "roosters": "Roosters", "bulldogs": "Bulldogs", "storm": "Storm",
    "dolphins": "Dolphins", "broncos": "Broncos", "rabbitohs": "Rabbitohs", "eels": "Eels",
    "raiders": "Raiders", "knights": "Knights", "dragons": "Dragons", "sharks": "Sharks",
    "tigers": "Wests Tigers",
}

AGENT_SERIES = ["agent", "old", "new"]
CONTROLS = ["model", "gemini", "statsinsider"]
PROBABILISTIC = AGENT_SERIES + CONTROLS
NAMES = {"agent": "Agent (overall)", "old": "Old system", "new": "New system", "model": "XGBoost model",
         "gemini": "Gemini", "statsinsider": "Stats Insider", "home": "Always pick home"}


# ----------------------------------------------------------------------------- loading

def first_team(text):
    lowered = text.lower()
    best = None
    for alias, team in TEAM_ALIASES.items():
        i = lowered.find(alias)
        if i != -1 and (best is None or i < best[0] or (i == best[0] and len(alias) > best[2])):
            best = (i, team, len(alias))
    if best is None:
        raise ValueError(f"No team named in {text!r}")
    return best[1]


def probability_in(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if m:
        return float(m.group(1)) / 100
    m = re.search(r"\b(0\.\d+)\b", text)
    if m:
        return float(m.group(1))
    raise ValueError(f"No probability in {text!r}")


def clean(cell):
    return re.sub(r"\s+", " ", cell.replace("**", "").replace("\\", "")).strip()


def load_workbook():
    # Cells contain Unicode line separators, so split on newlines only.
    lines = [l for l in WORKBOOK.read_text().split("\n") if l.startswith("|") and "Predicted Winner" in l]
    assert len(lines) == len(FIXTURES), (len(lines), len(FIXTURES))
    matches = []
    for (rnd, home, away), line in zip(FIXTURES, lines):
        cells = [clean(c) for c in line.strip().strip("|").split("|")]
        if cells[0]:
            label = cells[0].lower()
            assert home.split()[-1].lower()[:6] in label and away.split()[-1].lower()[:6] in label, (rnd, home, away, cells[0])
        gem = cells[1]
        gemini_pick = first_team(re.search(r"Predicted Winner:\s*(.*?)Confidence", gem).group(1))
        gemini_conf = float(re.search(r"Confidence Score:\s*(\d+)%", gem).group(1)) / 100
        si_pick, si_conf = first_team(cells[2]), probability_in(cells[2])
        if rnd <= 27:
            agent_pick, agent_conf = first_team(cells[3]), probability_in(cells[3])
            old = (agent_pick, agent_conf) if rnd <= 25 else None
            new = (agent_pick, agent_conf) if rnd >= 26 else None
            result = cells[5]
        else:
            old = (first_team(cells[3]), probability_in(cells[3]))
            new = (first_team(cells[4]), probability_in(cells[4]))
            result = cells[5]
        winner = first_team(result)
        score = [int(x) for x in re.search(r"(\d+)\s*-\s*(\d+)", result).groups()]
        for team in [gemini_pick, si_pick, winner] + [x[0] for x in (old, new) if x]:
            assert team in (home, away), (rnd, home, away, team)
        matches.append(dict(round=rnd, home=home, away=away, winner=winner, home_win=int(winner == home),
                            margin=abs(score[0] - score[1]), result_text=result,
                            gemini=(gemini_pick, gemini_conf), statsinsider=(si_pick, si_conf), old=old, new=new))
    return matches


def load_log(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def find_run_folder(base, run_id):
    stamp = run_id.split("-")[0]
    hits = [Path(p).parent for p in glob.glob(str(base / "**" / stamp / "record.json"), recursive=True)]
    assert len(hits) == 1, (run_id, hits)
    return hits[0]


def load_lake():
    lake = {}
    for p in glob.glob(str(LAKE_2026 / "*.json")):
        m = json.load(open(p))["match"]
        lake[(m["roundNumber"], m["homeTeam"]["nickName"], m["awayTeam"]["nickName"])] = dict(
            home_score=m["homeTeam"]["score"], away_score=m["awayTeam"]["score"], venue=m["venue"],
            start=datetime.fromisoformat(m["startTime"].replace("Z", "+00:00")), extra_time=m.get("hasExtraTime"))
    return lake


# ----------------------------------------------------------------------------- scoring helpers

def p_home(pick, conf, home):
    return conf if pick == home else 1 - conf


def correct(m, s):
    return int((m["P"][s] > 0.5) == bool(m["home_win"]))


def brier(m, s):
    return (m["P"][s] - m["home_win"]) ** 2


def log_loss(m, s):
    p = min(max(m["P"][s], 1e-6), 1 - 1e-6)
    return -(m["home_win"] * math.log(p) + (1 - m["home_win"]) * math.log(1 - p))


def wilson(k, n, z=1.96):
    ph = k / n
    d = 1 + z * z / n
    centre = (ph + z * z / (2 * n)) / d
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return centre - half, centre + half


def bootstrap_mean_ci(values, rng):
    v = np.asarray(values, dtype=float)
    means = v[rng.integers(0, len(v), size=(BOOTSTRAP_DRAWS, len(v)))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)


def has(m, s):
    return s in m["P"]


def summarise(matches, s, rng):
    ms = [m for m in matches if has(m, s)]
    hits = [correct(m, s) for m in ms]
    k, n = sum(hits), len(ms)
    lo, hi = wilson(k, n)
    out = dict(system=s, n=n, correct=k, accuracy=k / n, accuracy_ci=[lo, hi])
    if s != "home":
        b = [brier(m, s) for m in ms]
        out.update(brier=float(np.mean(b)), brier_ci=bootstrap_mean_ci(b, rng),
                   log_loss=float(np.mean([log_loss(m, s) for m in ms])),
                   brier_skill_vs_coin=1 - float(np.mean(b)) / 0.25)
        y = [m["home_win"] for m in ms]
        if len(set(y)) == 2:
            out["auc"] = float(roc_auc_score(y, [m["P"][s] for m in ms]))
    return out


def paired(matches, a, b, rng):
    ms = [m for m in matches if has(m, a) and has(m, b)]
    ca = [correct(m, a) for m in ms]
    cb = [correct(m, b) for m in ms]
    a_only = sum(x and not y for x, y in zip(ca, cb))
    b_only = sum(y and not x for x, y in zip(ca, cb))
    p_mcnemar = stats.binomtest(min(a_only, b_only), a_only + b_only, 0.5).pvalue if a_only + b_only else 1.0
    out = dict(a=a, b=b, n=len(ms), a_correct=sum(ca), b_correct=sum(cb), a_only=a_only, b_only=b_only,
               mcnemar_p=float(p_mcnemar))
    if b != "home":
        d = np.array([brier(m, a) - brier(m, b) for m in ms])
        signs = rng.choice([-1, 1], size=(BOOTSTRAP_DRAWS, len(d)))
        p_perm = float(np.mean(np.abs((signs * d).mean(axis=1)) >= abs(d.mean()) - 1e-12))
        out.update(brier_a=float(np.mean([brier(m, a) for m in ms])), brier_b=float(np.mean([brier(m, b) for m in ms])),
                   brier_diff=float(d.mean()), brier_diff_ci=bootstrap_mean_ci(d, rng), brier_perm_p=p_perm)
    return out


def calibration(matches, s):
    ms = [m for m in matches if has(m, s)]
    conf = np.array([max(m["P"][s], 1 - m["P"][s]) for m in ms])
    hit = np.array([correct(m, s) for m in ms])
    bands = {}
    for name, lo, hi in [("0.50-0.55", 0.5, 0.55), ("0.55-0.65", 0.55, 0.65), ("0.65-0.75", 0.65, 0.75), ("0.75+", 0.75, 1.01)]:
        mask = (conf >= lo) & (conf < hi)
        if mask.any():
            bands[name] = dict(n=int(mask.sum()), mean_conf=float(conf[mask].mean()), hit_rate=float(hit[mask].mean()))
    return dict(system=s, n=len(ms), mean_conf=float(conf.mean()), hit_rate=float(hit.mean()),
                gap=float(conf.mean() - hit.mean()),
                mean_conf_hits=float(conf[hit == 1].mean()), mean_conf_misses=float(conf[hit == 0].mean()),
                mean_p_home=float(np.mean([m["P"][s] for m in ms])),
                actual_home_rate=float(np.mean([m["home_win"] for m in ms])),
                picked_home=int(sum(m["P"][s] > 0.5 for m in ms)), bands=bands)


# ----------------------------------------------------------------------------- build the scored table

def build():
    matches = load_workbook()
    lake = load_lake()
    old_log = [r for r in load_log(OLD_LOG) if r["failed"] == "False"]
    new_log = [r for r in load_log(NEW_LOG) if r["failed"] == "False" and int(r["round"]) >= 26]
    old_failed = [r for r in load_log(OLD_LOG) if r["failed"] != "False"]
    new_failed = [r for r in load_log(NEW_LOG) if r["failed"] != "False"]

    # The new-system log repeats the Round 23-25 old-system runs. They must be identical copies.
    old_by_id = {r["run_id"]: r for r in old_log}
    for r in load_log(NEW_LOG):
        if int(r["round"]) <= 25:
            assert r["run_id"] in old_by_id and r["confidence"] == old_by_id[r["run_id"]]["confidence"]

    def index(log):
        out = {}
        for r in log:
            k = (int(r["round"]), r["home_team"], r["away_team"])
            assert k not in out, ("duplicate official run", k)
            out[k] = r
        return out

    old_idx, new_idx = index(old_log), index(new_log)
    checks = dict(lake_mismatches=[], not_in_lake=[], workbook_vs_log_mismatches=[], missing_run_records=[])

    for m in matches:
        k = (m["round"], m["home"], m["away"])
        if k in lake:
            o = lake[k]
            if (o["home_score"] > o["away_score"]) != bool(m["home_win"]):
                checks["lake_mismatches"].append(k)
            m["home_score"], m["away_score"], m["extra_time"] = o["home_score"], o["away_score"], o["extra_time"]
        else:
            checks["not_in_lake"].append(k)
        m["runs"] = {}
        for series, idx in (("old", old_idx), ("new", new_idx)):
            if not m[series]:
                continue
            run = idx.get(k)
            if run is None:
                checks["missing_run_records"].append((series, k))
                continue
            side = "home" if m[series][0] == m["home"] else "away"
            if run["predicted_side"] != side or abs(float(run["confidence"]) - m[series][1]) > 1e-9:
                checks["workbook_vs_log_mismatches"].append((series, k))
            m["runs"][series] = run
        model_values = {r["math_home_win_prob"] for r in m["runs"].values()}
        assert len(model_values) <= 1, (k, model_values)
        m["model_p_home"] = float(model_values.pop()) if model_values else None

        m["P"] = {"gemini": p_home(*m["gemini"], m["home"]), "statsinsider": p_home(*m["statsinsider"], m["home"]),
                  "home": 1.0}
        if m["old"]:
            m["P"]["old"] = p_home(*m["old"], m["home"])
        if m["new"]:
            m["P"]["new"] = p_home(*m["new"], m["home"])
        m["P"]["agent"] = m["P"]["old"] if m["round"] <= 25 else m["P"]["new"]
        if m["model_p_home"] is not None:
            m["P"]["model"] = m["model_p_home"]
    return matches, lake, checks, old_log, new_log, old_failed + new_failed


# ----------------------------------------------------------------------------- run-level evidence

def run_records(log, base):
    out = []
    for r in log:
        folder = find_run_folder(base, r["run_id"])
        out.append((r, json.load(open(folder / "record.json")), json.load(open(folder / "ledger.json"))))
    return out


def process_metrics(records, matches):
    by_key = {(m["round"], m["home"], m["away"]): m for m in matches}
    n = len(records)
    res = dict(n=n, same_side_as_model=0, copied_model_to_2dp=0, within_002_of_model=0, gaps=[],
               checklist_pass=0, audit_pass=0, recalibrated=0, pick_changed=0, confidence_changed=0,
               confidence_changes=[], refine_triggered=0, gate_passed=0, stance=Counter(), loss_reason_specific=Counter(),
               disagreements=[], wall_seconds=[], research_items=[], hours_before_kickoff=[])
    for r, rec, ledger in records:
        k = (int(r["round"]), r["home_team"], r["away_team"])
        m = by_key[k]
        mp = float(r["math_home_win_prob"])
        conf = float(r["confidence"])
        side = r["predicted_side"]
        model_side = "home" if mp > 0.5 else "away"
        mp_pick = mp if side == "home" else 1 - mp
        if side == model_side:
            res["same_side_as_model"] += 1
        else:
            pick = r["home_team"] if side == "home" else r["away_team"]
            res["disagreements"].append(dict(round=k[0], home=k[1], away=k[2], pick=pick, confidence=conf,
                                             model_p_home=mp, winner=m["winner"], won=pick == m["winner"]))
        res["copied_model_to_2dp"] += abs(round(mp_pick, 2) - conf) < 1e-9
        res["within_002_of_model"] += abs(conf - mp_pick) <= 0.02 + 1e-9
        res["gaps"].append(conf - mp_pick)
        v = ledger["verifier_loop"]
        res["checklist_pass"] += bool(v["checklist"]["pass"])
        res["audit_pass"] += bool(v["llm_audit"]["pass"])
        if v.get("recalibration_triggered"):
            res["recalibrated"] += 1
            before, after = v["judgement_before"], v["judgement_after"]
            res["pick_changed"] += before["winner"] != after["winner"]
            if abs(before["confidence"] - after["confidence"]) > 1e-9:
                res["confidence_changed"] += 1
                res["confidence_changes"].append(dict(round=k[0], home=k[1], away=k[2], before=before["confidence"],
                                                      after=after["confidence"]))
        res["refine_triggered"] += bool(rec["research"]["refine_triggered"])
        res["gate_passed"] += bool(rec["research"]["gate_passed"])
        reasoning = rec.get("reasoning", {})
        res["stance"][str(reasoning.get("research_stance"))] += 1
        res["loss_reason_specific"][str(reasoning.get("loss_reason_specific"))] += 1
        res["wall_seconds"].append(float(r["wall_seconds"]))
        res["research_items"].append(int(r["research_items_kept"]))
        res["hours_before_kickoff"].append(float(r["hours_before_kickoff"]))
    gaps = np.array(res.pop("gaps"))
    res["mean_abs_gap_to_model"] = float(np.abs(gaps).mean())
    res["stance"] = dict(res["stance"])
    res["loss_reason_specific"] = dict(res["loss_reason_specific"])
    w = res.pop("wall_seconds")
    res["wall_minutes_mean"], res["wall_minutes_max"] = float(np.mean(w) / 60), float(np.max(w) / 60)
    res["research_items_range"] = [min(res["research_items"]), max(res["research_items"])]
    res.pop("research_items")
    h = res.pop("hours_before_kickoff")
    res["finished_after_kickoff"] = int(sum(x < 0 for x in h))
    res["finished_under_one_hour"] = int(sum(0 <= x < 1 for x in h))
    return res


def verifier_effect(records, matches):
    by_key = {(m["round"], m["home"], m["away"]): m for m in matches}
    before, after = [], []
    for r, rec, ledger in records:
        m = by_key[(int(r["round"]), r["home_team"], r["away_team"])]
        v = ledger["verifier_loop"]
        conf_after = float(r["confidence"])
        conf_before = v["judgement_before"]["confidence"] if v.get("recalibration_triggered") else conf_after
        side_home = r["predicted_side"] == "home"
        for conf, bucket in ((conf_before, before), (conf_after, after)):
            ph = conf if side_home else 1 - conf
            bucket.append((ph - m["home_win"]) ** 2)
    return dict(n=len(before), brier_before=float(np.mean(before)), brier_after=float(np.mean(after)),
                change=float(np.mean(after) - np.mean(before)))


def rule_compliance(records):
    """New-system judgement rule: agreeing news keeps the side and does not climb without a shock,
    conflicting or mixed news comes down from the prior, a flip needs a named research fact."""
    rows = []
    for r, rec, ledger in records:
        mp = float(r["math_home_win_prob"])
        side = r["predicted_side"]
        mp_pick = mp if side == "home" else 1 - mp
        flipped = side != ("home" if mp > 0.5 else "away")
        rows.append(dict(round=int(r["round"]), home=r["home_team"], away=r["away_team"],
                         stance=rec["reasoning"]["research_stance"], flipped=flipped,
                         confidence=float(r["confidence"]), model_p_pick=round(mp_pick, 4),
                         change_from_prior=round(float(r["confidence"]) - mp_pick, 3)))
    summary = defaultdict(lambda: dict(n=0, at_or_below_prior=0, above_prior=[], flips=0))
    for x in rows:
        s = summary[x["stance"]]
        s["n"] += 1
        if x["flipped"]:
            s["flips"] += 1
        elif x["change_from_prior"] <= 0.005:  # rounding a prior to two decimals can add up to 0.005
            s["at_or_below_prior"] += 1
        else:
            s["above_prior"].append(x)
    return rows, {k: dict(v) for k, v in summary.items()}


def data_freshness(log, lake):
    """Was every earlier round in the data lake before the forecast ran (FR-10)?"""
    runs = json.load(open(ETL_MANIFEST))["runs"]
    etl = sorted((datetime.fromisoformat(r["completed_at"]), r["raw_json_count_season"]) for r in runs)
    stale = []
    for r in log:
        rnd = int(r["round"])
        needed = sum(1 for (lr, _, _) in lake if lr < rnd)
        at = datetime.fromisoformat(r["predicted_at_utc"])
        available = max([c for t, c in etl if t <= at], default=0)
        if available < needed:
            stale.append(dict(round=rnd, home=r["home_team"], away=r["away_team"], run_id=r["run_id"],
                              matches_needed=needed, matches_in_lake=available))
    return stale


# ----------------------------------------------------------------------------- Gemini rationale check

def gemini_claims(matches, lake):
    """Every 'Round N ... score' claim about an earlier 2026 match, checked against the official record."""
    cells = [l.split("|")[2].replace("\\", "").replace("**", "")
             for l in WORKBOOK.read_text().split("\n") if l.startswith("|") and "Predicted Winner" in l]
    by_round = defaultdict(list)
    for (rnd, h, a), o in lake.items():
        by_round[rnd].append(tuple(sorted((o["home_score"], o["away_score"]))))
    claims = {}
    for m, cell in zip(matches, cells):
        for sentence in re.split(r"(?<=[.;])\s+", cell):
            cited = [int(x) for x in re.findall(r"Round (\d+)", sentence)]
            scores = [tuple(sorted((int(a), int(b)))) for a, b in re.findall(r"(\d+)\s*[–-]\s*(\d+)", sentence)]
            for rn in cited:
                if rn >= m["round"] or not scores:
                    continue
                key = (m["round"], m["home"], m["away"], rn)
                ok = any(s in by_round.get(rn, []) for s in scores)
                claims[key] = claims.get(key, False) or ok
    return dict(claims=len(claims), matched=sum(claims.values()),
                unmatched=[list(k) for k, v in claims.items() if not v])


# ----------------------------------------------------------------------------- figures

def figure_cumulative(matches):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x_all = np.arange(1, len(matches) + 1)
    styles = {"agent": ("Agent (overall)", "-", 2.2, "black"), "gemini": ("Gemini", "--", 1.6, "#1f77b4"),
              "statsinsider": ("Stats Insider", "-.", 1.6, "#d62728"), "model": ("XGBoost model", ":", 1.8, "#2ca02c"),
              "home": ("Always pick home", "-", 1.0, "grey")}
    for s, (label, ls, lw, colour) in styles.items():
        xs, ys, k, n = [], [], 0, 0
        for i, m in enumerate(matches, start=1):
            if not has(m, s):
                continue
            n += 1
            k += correct(m, s)
            xs.append(i)
            ys.append(k / n)
        ax.plot(xs, ys, linestyle=ls, linewidth=lw, color=colour, label=label)
    boundaries = [i for i in range(1, len(matches)) if matches[i]["round"] != matches[i - 1]["round"]]
    for b in boundaries:
        ax.axvline(b + 0.5, color="lightgrey", linewidth=0.8, zorder=0)
    ax.axvline(24.5, color="black", linewidth=0.8, linestyle=(0, (4, 3)), zorder=0)
    ax.axvline(40.5, color="black", linewidth=0.8, linestyle=(0, (4, 3)), zorder=0)
    ax.text(25, 0.93, "New system from Round 26", fontsize=8)
    ax.text(41, 0.93, "Finals", fontsize=8)
    ax.set_xlim(1, len(matches))
    ax.set_ylim(0, 1)
    ax.set_xlabel("Match number in the testing window (chronological)")
    ax.set_ylabel("Cumulative proportion correct")
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure_4_cumulative_accuracy.png", dpi=200)
    plt.close(fig)


def figure_calibration(cal):
    order = ["old", "new", "agent", "model", "gemini", "statsinsider"]
    labels = ["Old\nsystem", "New\nsystem", "Agent\n(overall)", "XGBoost\nmodel", "Gemini", "Stats\nInsider"]
    conf = [cal[s]["mean_conf"] for s in order]
    hit = [cal[s]["hit_rate"] for s in order]
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x - 0.18, conf, width=0.36, color="#bbbbbb", edgecolor="black", label="Mean stated confidence")
    ax.bar(x + 0.18, hit, width=0.36, color="#444444", edgecolor="black", label="Proportion correct")
    for i, (c, h) in enumerate(zip(conf, hit)):
        ax.text(i - 0.18, c + 0.01, f"{c:.2f}", ha="center", fontsize=8)
        ax.text(i + 0.18, h + 0.01, f"{h:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x, labels, fontsize=9)
    ax.set_ylim(0, 0.85)
    ax.set_ylabel("Proportion")
    ax.legend(loc="upper left", fontsize=8, frameon=False, ncols=2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure_5_confidence_vs_hit_rate.png", dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------------- main

def main():
    rng = np.random.default_rng(SEED)
    matches, lake, checks, old_log, new_log, failed_runs = build()
    results = dict(checks=checks)
    unrecorded = {tuple(k) for _, k in checks["missing_run_records"]}

    late = [(r, "old") for r in old_log if float(r["hours_before_kickoff"]) < 0] + \
           [(r, "new") for r in new_log if float(r["hours_before_kickoff"]) < 0]
    after_kickoff = {(int(r["round"]), r["home_team"], r["away_team"]) for r, _ in late}
    results["after_kickoff_runs"] = [dict(round=int(r["round"]), home=r["home_team"], away=r["away_team"],
                                          system=system, predicted_at_local=r["predicted_at_local"],
                                          kickoff_local=r["kickoff_local"]) for r, system in late]
    results["failed_runs"] = [dict(run_id=r["run_id"], round=int(r["round"]), home=r["home_team"], away=r["away_team"])
                              for r in failed_runs]

    regular = [m for m in matches if m["round"] <= 27]
    finals = [m for m in matches if m["round"] >= 28]
    old_matches = [m for m in matches if has(m, "old")]
    new_matches = [m for m in matches if has(m, "new")]

    systems = AGENT_SERIES + CONTROLS + ["home"]
    results["base_rates"] = dict(
        home_wins=sum(m["home_win"] for m in matches), matches=len(matches),
        home_wins_regular=sum(m["home_win"] for m in regular), home_wins_finals=sum(m["home_win"] for m in finals),
        home_wins_r23_25=sum(m["home_win"] for m in matches if m["round"] <= 25),
        draws=0, one_point_games=[(m["round"], m["home"], m["away"], m["result_text"]) for m in matches if m["margin"] <= 1],
        all_systems_same_side_in_finals=all(len({m["P"][s] > 0.5 for s in PROBABILISTIC if has(m, s)}) == 1 for m in finals))

    results["window"] = {s: summarise(matches, s, rng) for s in systems}
    results["phases"] = {
        "r23_25": {s: summarise([m for m in matches if m["round"] <= 25], s, rng) for s in ["old", "model", "gemini", "statsinsider", "home"]},
        "r26_27": {s: summarise([m for m in matches if 26 <= m["round"] <= 27], s, rng) for s in ["new", "model", "gemini", "statsinsider", "home"]},
        "regular": {s: summarise(regular, s, rng) for s in ["agent", "model", "gemini", "statsinsider", "home"]},
        "finals": {s: summarise(finals, s, rng) for s in ["old", "new", "model", "gemini", "statsinsider", "home"]},
    }
    # Each agent series against the controls on exactly the matches that series forecast.
    results["own_matches"] = {
        series: {s: summarise(ms, s, rng) for s in [series] + CONTROLS + ["home"]}
        for series, ms in (("agent", matches), ("old", old_matches), ("new", new_matches))
    }

    per_round = []
    for rnd in sorted({m["round"] for m in matches}):
        rs = [m for m in matches if m["round"] == rnd]
        row = dict(round=rnd, label=ROUND_LABEL[rnd], n=len(rs))
        for s in systems:
            sub = [m for m in rs if has(m, s)]
            row[s] = [sum(correct(m, s) for m in sub), len(sub)] if sub else None
            if s != "home" and sub:
                row[f"{s}_brier"] = float(np.mean([brier(m, s) for m in sub]))
        per_round.append(row)
    results["per_round"] = per_round

    pairs = [("agent", "gemini"), ("agent", "statsinsider"), ("agent", "model"), ("agent", "home"),
             ("gemini", "statsinsider"), ("model", "statsinsider"), ("gemini", "home")]
    results["paired_window"] = [paired(matches, a, b, rng) for a, b in pairs]
    results["paired_old"] = [paired(old_matches, "old", b, rng) for b in ["gemini", "statsinsider", "model", "home"]]
    results["paired_new"] = [paired(new_matches, "new", b, rng) for b in ["gemini", "statsinsider", "model", "home"]]
    results["paired_finals_new_vs_old"] = paired(finals, "new", "old", rng)

    s47 = [m for m in matches if (m["round"], m["home"], m["away"]) not in unrecorded]
    s45 = [m for m in s47 if (m["round"], m["home"], m["away"]) not in after_kickoff]
    results["sensitivity"] = {
        label: dict(n=len(ms), summary={s: summarise(ms, s, rng) for s in ["agent", "model", "gemini", "statsinsider", "home"]},
                    paired=[paired(ms, "agent", b, rng) for b in ["gemini", "statsinsider", "model"]])
        for label, ms in (("all_recorded_47", s47), ("recorded_pre_kickoff_45", s45))
    }

    results["calibration"] = {s: calibration(matches, s) for s in PROBABILISTIC}

    results["finals_paired_confidence"] = [
        dict(round=m["round"], home=m["home"], away=m["away"], pick=m["old"][0], old=m["old"][1], new=m["new"][1],
             winner=m["winner"], old_brier=brier(m, "old"), new_brier=brier(m, "new")) for m in finals]

    results["gemini_by_version"] = {}
    for version in ["3.6", "3.7", "3.8"]:
        ms = [m for m in matches if GEMINI_VERSION[m["round"]] == version]
        results["gemini_by_version"][version] = dict(
            rounds=sorted({m["round"] for m in ms}),
            gemini=summarise(ms, "gemini", rng), statsinsider=summarise(ms, "statsinsider", rng))
    results["gemini_claims"] = gemini_claims(matches, lake)

    old_records = run_records(old_log, OLD_RUNS)
    new_records = run_records(new_log, NEW_RUNS)
    results["process"] = {
        "old_r23_25": process_metrics([x for x in old_records if int(x[0]["round"]) <= 25], matches),
        "old_finals": process_metrics([x for x in old_records if int(x[0]["round"]) >= 28], matches),
        "old_all": process_metrics(old_records, matches),
        "new_r26_27": process_metrics([x for x in new_records if int(x[0]["round"]) <= 27], matches),
        "new_finals": process_metrics([x for x in new_records if int(x[0]["round"]) >= 28], matches),
        "new_all": process_metrics(new_records, matches),
    }
    results["verifier_effect"] = {"old": verifier_effect(old_records, matches), "new": verifier_effect(new_records, matches)}
    compliance_rows, compliance_summary = rule_compliance(new_records)
    results["new_rule_compliance"] = dict(summary=compliance_summary, rows=compliance_rows)

    results["fixture_details_vs_official"] = []
    for r, rec, _ in old_records + new_records:
        f = rec["fixture"]
        o = lake.get((f["round"], f["home_team"], f["away_team"]))
        if o and (o["venue"] != f["venue"] or datetime.fromisoformat(f["kickoff"]).astimezone(timezone.utc) != o["start"]):
            results["fixture_details_vs_official"].append(r["run_id"])
    results["fixture_details_checked"] = sum(
        1 for r, rec, _ in old_records + new_records
        if (rec["fixture"]["round"], rec["fixture"]["home_team"], rec["fixture"]["away_team"]) in lake)

    finals_model = [(m["round"], m["home"], m["away"]) for m in finals]
    results["model_probability_identical_across_systems_in_finals"] = all(
        m["runs"]["old"]["math_home_win_prob"] == m["runs"]["new"]["math_home_win_prob"] for m in finals)
    results["llm_identity"] = sorted({(r["llm_provider"], r["llm_model"]) for r in old_log + new_log})
    results["manual_columns_empty"] = all(
        not r[c].strip() for r in load_log(OLD_LOG) + load_log(NEW_LOG)
        for c in ("actual_winner", "actual_home_score", "actual_away_score", "vanilla_llm_winner",
                  "vanilla_llm_confidence", "statsinsider_home_prob"))
    results["stale_data_forecasts"] = {"old": data_freshness(old_log, lake), "new": data_freshness(new_log, lake)}

    holdout = json.load(open(HOLDOUT))
    results["holdout"] = dict(metrics=holdout["holdout_metrics"]["sigmoid"],
                              always_home_accuracy=holdout["baselines"]["always_home_accuracy"],
                              base_rate_log_loss=holdout["baselines"]["base_rate_log_loss"])

    # Matches needed for 80% power to detect an accuracy gap d when a fraction p of matches are discordant.
    za, zb = 1.959964, 0.841621
    results["power"] = [dict(discordant=p, gap=d, matches=math.ceil(((za * math.sqrt(p) + zb * math.sqrt(p - d * d)) ** 2) / (d * d)))
                        for p in (0.10, 0.15) for d in (0.05, 0.08)]

    figure_cumulative(matches)
    figure_calibration(results["calibration"])
    write_appendix(matches, lake, results)
    write_outputs(matches, results)


SHORT_ROUND = {23: "R23", 24: "R24", 25: "R25", 26: "R26", 27: "R27", 28: "FW1", 29: "FW2", 30: "PF", 31: "GF"}
APPENDIX_MD = REPO / "Reporting/Appendix_results.md"
APPENDIX_JSON = OUT / "appendix_tables.json"

APPENDIX_INTRO = [
    "This appendix lists every forecast scored in the findings. Table A1 gives each match in the testing window, "
    "its result and the forecast from every source. Tables A2 to A8 then score each source separately, one match "
    "per row, with running totals. Table A9 lists the run record behind each agent forecast. Matches are numbered "
    "in kickoff order, and the same number is used in every table.",
    "Each row is calculated in the same way. P(home) is the probability given to the home side. If a source picked "
    "the home side, P(home) is its confidence. If it picked the away side, P(home) is one minus its confidence. The "
    "XGBoost model gives P(home) directly, and its pick is the side it gives more than 0.50. Home win is 1 if the "
    "home side won and 0 if it lost. Correct is 1 if the picked side won. The Brier term is (P(home) − home win)², "
    "and the Brier score for a set of matches is the mean of those terms. The running columns include every match "
    "up to and including that row.",
    "Round labels: R23 to R27 are Rounds 23 to 27, FW1 and FW2 are finals weeks 1 and 2, PF is the preliminary "
    "finals and GF is the grand final.",
]


def write_appendix(matches, lake, results):
    """Every forecast with its scoring and running totals, for the report appendix."""
    starts = [lake[(m["round"], m["home"], m["away"])]["start"] for m in matches
              if (m["round"], m["home"], m["away"]) in lake]
    assert starts == sorted(starts), "workbook rows are not in kickoff order"

    def fixture(m):
        return f"{m['home']} v {m['away']}"

    def result(m):
        a, b = (int(x) for x in re.search(r"(\d+)\s*-\s*(\d+)", m["result_text"]).groups())
        return f"{m['winner']} {max(a, b)}–{min(a, b)}"

    def pick_and_p(m, s):
        """Displayed pick, displayed P(home) and the decimals used to show it."""
        if s == "model":
            p = m["P"]["model"]
            pick = m["home"] if p > 0.5 else m["away"]
            return f"{pick} ({max(p, 1 - p):.4f})", p, 4
        if s == "home":
            return m["home"], None, None
        series = s if s in ("old", "new", "gemini", "statsinsider") else ("old" if m["round"] <= 25 else "new")
        team, conf = m[series]
        return f"{team} ({conf:.2f})", m["P"][s], 2

    tables = []
    rows = []
    for i, m in enumerate(matches, start=1):
        model_cell = f"{m['P']['model']:.4f}" if has(m, "model") else "No run record"
        rows.append([str(i), SHORT_ROUND[m["round"]], fixture(m), result(m), str(m["home_win"]),
                     pick_and_p(m, "gemini")[0], pick_and_p(m, "statsinsider")[0], model_cell,
                     pick_and_p(m, "old")[0] if m["old"] else "–", pick_and_p(m, "new")[0] if m["new"] else "–"])
    tables.append(dict(id="A1", title="All forecasts and results",
                       columns=["#", "Round", "Match (home v away)", "Result", "Home win", "Gemini", "Stats Insider",
                                "Model P(home)", "Old system", "New system"],
                       rows=rows,
                       note="Each forecast is shown as the picked team and the confidence given to it. The model "
                            "column is the model's home-win probability. A dash means the system did not forecast "
                            "that match. The model has no probability for two Round 27 matches because their run "
                            "records were not kept."))

    sources = [("A2", "agent", "The agent (old system in Rounds 23 to 25, new system from Round 26)"),
               ("A3", "old", "The old system"), ("A4", "new", "The new system"),
               ("A5", "model", "The XGBoost model"), ("A6", "gemini", "Gemini"),
               ("A7", "statsinsider", "Stats Insider"), ("A8", "home", "Always picking the home side")]
    for table_id, s, title in sources:
        rows, k, n, brier_sum, brier_n = [], 0, 0, 0.0, 0
        for i, m in enumerate(matches, start=1):
            if s in ("old", "new") and not has(m, s):
                continue
            base = [str(i), SHORT_ROUND[m["round"]], fixture(m)]
            if s == "agent":
                base.append("Old" if m["round"] <= 25 else "New")
            if s == "model" and not has(m, "model"):
                running = [f"{k}/{n}", f"{100 * k / n:.1f}%", f"{brier_sum / brier_n:.3f}"]
                rows.append(base + ["No run record", "–", str(m["home_win"]), "–", "–"] + running)
                continue
            pick, p, dp = pick_and_p(m, s)
            hit = correct(m, s)
            k += hit
            n += 1
            if s == "home":
                rows.append(base + [pick, str(m["home_win"]), str(hit), f"{k}/{n}", f"{100 * k / n:.1f}%"])
                continue
            term = (p - m["home_win"]) ** 2
            brier_sum += term
            brier_n += 1
            rows.append(base + [pick, f"{p:.{dp}f}", str(m["home_win"]), str(hit),
                                f"({p:.{dp}f} − {m['home_win']})² = {term:.4f}",
                                f"{k}/{n}", f"{100 * k / n:.1f}%", f"{brier_sum / brier_n:.3f}"])
        summary = results["window"][s]
        assert k == summary["correct"] and n == summary["n"], (s, k, n)
        if s == "home":
            columns = ["#", "Round", "Match", "Pick", "Home win", "Correct", "Running correct", "Running accuracy"]
            total = f"Total: {k} of {n} correct ({100 * k / n:.1f}%). This baseline gives no probability, so it has no Brier score."
        else:
            assert abs(brier_sum / brier_n - summary["brier"]) < 1e-12, s
            columns = ["#", "Round", "Match"] + (["System"] if s == "agent" else []) + \
                      ["Pick (confidence)", "P(home)", "Home win", "Correct", "Brier term",
                       "Running correct", "Running accuracy", "Running Brier score"]
            total = f"Total: {k} of {n} correct ({100 * k / n:.1f}%). Brier score {brier_sum / brier_n:.3f}."
        note = None
        if s == "model":
            note = ("The model's pick is the side it gives more than 0.50, and the confidence shown is the "
                    "probability of that side. Rows without a run record are not scored, so the running values "
                    "carry over unchanged.")
        tables.append(dict(id=table_id, title=f"Scoring of every forecast: {title}", columns=columns, rows=rows,
                           total=total, note=note))

    rows = []
    for i, m in enumerate(matches, start=1):
        for series in ("old", "new"):
            if not m[series]:
                continue
            run = m["runs"].get(series)
            pick = f"{m[series][0]} ({m[series][1]:.2f})"
            if run is None:
                rows.append([str(i), SHORT_ROUND[m["round"]], fixture(m), series.capitalize(), pick,
                             "Record not kept", "–", "–", "–"])
                continue
            done = datetime.fromisoformat(run["predicted_at_local"])
            ko = datetime.fromisoformat(run["kickoff_local"])
            minutes = round((ko - done).total_seconds() / 60)
            rows.append([str(i), SHORT_ROUND[m["round"]], fixture(m), series.capitalize(), pick, run["run_id"],
                         f"{done.day} {done:%b %H:%M}", f"{ko.day} {ko:%b %H:%M}",
                         str(minutes) if minutes >= 0 else f"−{abs(minutes)}"])
    tables.append(dict(id="A9", title="Agent run records", columns=["#", "Round", "Match", "System", "Pick (confidence)",
                                                                    "Run ID", "Finished (local time)", "Kickoff (local time)",
                                                                    "Minutes before kickoff"],
                       rows=rows,
                       note="The run ID names the run folder that holds the full record of tool outputs, rationale "
                            "and verification. Finished is the time the run was completed. A negative value means the "
                            "run finished after kickoff. In both such runs the research and the model probability "
                            "were collected before kickoff."))

    APPENDIX_JSON.parent.mkdir(parents=True, exist_ok=True)
    APPENDIX_JSON.write_text(json.dumps(dict(title="Appendix A: Testing-window results", intro=APPENDIX_INTRO,
                                             tables=tables), indent=1, ensure_ascii=False))

    lines = ["# Appendix A: Testing-window results", ""]
    for para in APPENDIX_INTRO:
        lines += [para, ""]
    for t in tables:
        lines += [f"**Table {t['id']}**", "", f"*{t['title']}*", "",
                  "| " + " | ".join(t["columns"]) + " |", "| " + " | ".join("---" for _ in t["columns"]) + " |"]
        lines += ["| " + " | ".join(r) + " |" for r in t["rows"]]
        lines.append("")
        if t.get("total"):
            lines += [t["total"], ""]
        if t.get("note"):
            lines += [f"*Note.* {t['note']}", ""]
    APPENDIX_MD.write_text("\n".join(lines))


def write_outputs(matches, results):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "scored_matches.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["round", "home", "away", "winner", "home_win", "margin", "gemini_version",
                    "p_home_agent", "p_home_old", "p_home_new", "p_home_model", "p_home_gemini", "p_home_statsinsider",
                    "old_run_id", "new_run_id"])
        for m in matches:
            P = m["P"]
            w.writerow([m["round"], m["home"], m["away"], m["winner"], m["home_win"], m["margin"], GEMINI_VERSION[m["round"]],
                        P.get("agent"), P.get("old"), P.get("new"), P.get("model"), P["gemini"], P["statsinsider"],
                        m["runs"].get("old", {}).get("run_id"), m["runs"].get("new", {}).get("run_id")])
    with open(OUT / "results.json", "w") as f:
        json.dump(results, f, indent=1, default=str)

    lines = ["# Testing-window results", "", "Generated by `Reporting/analysis/analyse_results.py`. Do not edit by hand.", ""]

    def fmt(s):
        x = s
        line = f"| {NAMES[x['system']]} | {x['n']} | {x['correct']} | {x['accuracy']:.3f} | {x['accuracy_ci'][0]:.3f}–{x['accuracy_ci'][1]:.3f} |"
        if "brier" in x:
            line += f" {x['brier']:.4f} | {x['brier_ci'][0]:.3f}–{x['brier_ci'][1]:.3f} | {x['log_loss']:.3f} | {x.get('auc', float('nan')):.3f} |"
        else:
            line += " – | – | – | – |"
        return line

    head = "| System | n | Correct | Accuracy | 95% CI | Brier | 95% CI | Log loss | AUC |\n|---|---|---|---|---|---|---|---|---|"
    lines += ["## Whole window", "", head] + [fmt(v) for v in results["window"].values()] + [""]
    for series in ("agent", "old", "new"):
        lines += [f"## {NAMES[series]} against the controls on its own matches", "", head] + \
                 [fmt(v) for v in results["own_matches"][series].values()] + [""]
    for phase, block in results["phases"].items():
        lines += [f"## Phase {phase}", "", head] + [fmt(v) for v in block.values()] + [""]

    lines += ["## Per round (correct/n)", "", "| Round | " + " | ".join(NAMES[s] for s in AGENT_SERIES + CONTROLS + ["home"]) + " |",
              "|---" * 8 + "|"]
    for r in results["per_round"]:
        cells = [f"{r[s][0]}/{r[s][1]}" if r[s] else "–" for s in AGENT_SERIES + CONTROLS + ["home"]]
        lines.append(f"| {r['label']} | " + " | ".join(cells) + " |")
    lines.append("")

    lines += ["## Paired comparisons", "", "| A | B | n | A correct | B correct | A only | B only | McNemar p | Brier A | Brier B | Diff | 95% CI | Perm p |",
              "|---" * 13 + "|"]
    for p in results["paired_window"] + results["paired_old"] + results["paired_new"] + [results["paired_finals_new_vs_old"]]:
        tail = (f" {p['brier_a']:.4f} | {p['brier_b']:.4f} | {p['brier_diff']:+.4f} | {p['brier_diff_ci'][0]:+.3f} to {p['brier_diff_ci'][1]:+.3f} | {p['brier_perm_p']:.3f} |"
                if "brier_diff" in p else " – | – | – | – | – |")
        lines.append(f"| {NAMES[p['a']]} | {NAMES[p['b']]} | {p['n']} | {p['a_correct']} | {p['b_correct']} | {p['a_only']} | {p['b_only']} | {p['mcnemar_p']:.3f} |" + tail)
    lines.append("")

    lines += ["## Calibration", "", "| System | n | Mean confidence | Proportion correct | Gap | Mean P(home) | Actual home rate |", "|---" * 7 + "|"]
    for c in results["calibration"].values():
        lines.append(f"| {NAMES[c['system']]} | {c['n']} | {c['mean_conf']:.3f} | {c['hit_rate']:.3f} | {c['gap']:+.3f} | {c['mean_p_home']:.3f} | {c['actual_home_rate']:.3f} |")
    lines.append("")
    (OUT / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print("\nChecks:", json.dumps(results["checks"], default=str))
    print("After kickoff:", results["after_kickoff_runs"])
    print("Stale data:", json.dumps(results["stale_data_forecasts"], default=str))
    print("Process:", json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ('disagreements', 'confidence_changes')} for k, v in results["process"].items()}, default=str, indent=1))
    print("Verifier effect:", results["verifier_effect"])
    print("Compliance:", json.dumps(results["new_rule_compliance"]["summary"], default=str, indent=1))
    print("Gemini by version:", {k: (v["gemini"]["correct"], v["gemini"]["n"], round(v["gemini"]["brier"], 4), v["statsinsider"]["correct"], round(v["statsinsider"]["brier"], 4)) for k, v in results["gemini_by_version"].items()})
    print("Gemini claims:", results["gemini_claims"])
    print("Fixture detail mismatches:", results["fixture_details_vs_official"], "checked", results["fixture_details_checked"])
    print("Model identical across systems in finals:", results["model_probability_identical_across_systems_in_finals"])
    print("LLM:", results["llm_identity"], "| manual columns empty:", results["manual_columns_empty"])
    print("Holdout:", results["holdout"])
    print("Power:", results["power"])
    print("Base rates:", results["base_rates"])
    print("Sensitivity:", {k: {s: (v['summary'][s]['correct'], v['summary'][s]['n'], round(v['summary'][s].get('brier', float('nan')), 4)) for s in v['summary']} for k, v in results["sensitivity"].items()})


if __name__ == "__main__":
    main()
