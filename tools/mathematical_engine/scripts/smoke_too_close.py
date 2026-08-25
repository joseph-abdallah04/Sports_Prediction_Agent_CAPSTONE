"""Offline checks for Too close math labels (no model load)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from model.explain import prediction_label  # noqa: E402


def _check(label: str, cond: bool) -> int:
    print(f"  {'ok  ' if cond else 'FAIL'} {label}")
    return 0 if cond else 1


def main() -> int:
    fails = 0
    cases = [
        (0.2703, "Away Win"),
        (0.4499, "Away Win"),
        (0.45, "Too close"),
        (0.4886, "Too close"),
        (0.5063, "Too close"),
        (0.5301, "Too close"),
        (0.5491, "Too close"),
        (0.55, "Too close"),
        (0.5584, "Home Win"),
        (0.8306, "Home Win"),
    ]
    for p, want in cases:
        got = prediction_label(p)
        fails += _check(f"P(home)={p} → {want}", got == want)
    print("\nSMOKE_OK" if not fails else f"\n{fails} CHECK(S) FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
