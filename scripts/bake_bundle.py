#!/usr/bin/env python3
"""Rebuild the precomputed bundle the static frontend serves.

WHY THIS EXISTS
---------------
`frontend/public/data/*.json` was originally produced by hand against a local
FastAPI and committed. Nothing recorded how. When the event ledger or the
backtest response shape changes, the bundle silently goes stale and the
deployed app serves numbers that no longer match the backend -- on a project
whose thesis is not fabricating numbers, that is the worst failure mode there
is. This script pins the procedure.

It drives the REAL app via TestClient rather than calling walk_forward
directly, so what lands on disk is exactly what `GET /api/...` would serve,
including Pydantic field filtering. If a field is missing from the bundle, it
is missing from the API too, and that is a bug worth seeing here.

    .venv/bin/python scripts/bake_bundle.py            # tickers, events, backtest
    .venv/bin/python scripts/bake_bundle.py --check    # verify only, write nothing

NOT REBAKED HERE: forecast_*.json, rulial_*.json, atlas.json, experiment.json.
Those are pinned single-event demos whose request text lives in the frontend,
not in the bundle. See --check output for their staleness warning.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
OUT = ROOT / "frontend" / "public" / "data"

from fastapi.testclient import TestClient          # noqa: E402
from rulial.api import app                         # noqa: E402
from rulial.config import UNIVERSE                 # noqa: E402


def write(path: Path, obj, check: bool) -> str:
    new = json.dumps(obj, separators=(",", ":"), sort_keys=True)
    old = path.read_text().strip() if path.exists() else None
    if old is not None:
        try:
            same = json.loads(old) == obj
        except Exception:
            same = False
    else:
        same = False
    if check:
        return "ok" if same else ("MISSING" if old is None else "STALE")
    if not same:
        path.write_text(json.dumps(obj, indent=1))
    return "ok" if same else "written"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    a = ap.parse_args()

    c = TestClient(app)
    rows = []

    r = c.get("/api/tickers")
    r.raise_for_status()
    rows.append(("tickers.json", write(OUT / "tickers.json", r.json(), a.check)))

    for t in UNIVERSE:
        e = c.get(f"/api/events?ticker={t}")
        e.raise_for_status()
        rows.append((f"events_{t}.json", write(OUT / f"events_{t}.json", e.json(), a.check)))

        b = c.get(f"/api/backtest?ticker={t}")
        b.raise_for_status()
        d = b.json()
        rows.append((f"backtest_{t}.json", write(OUT / f"backtest_{t}.json", d, a.check)))
        # the second baseline must survive the API's field filtering
        if d.get("n_tests") and d.get("mean_fhs_lift") is None:
            rows.append((f"  !! backtest_{t}: mean_fhs_lift is null with n_tests>0", "WARN"))

    width = max(len(n) for n, _ in rows)
    for n, s in rows:
        print(f"  {n:<{width}}  {s}")
    stale = [n for n, s in rows if s in ("STALE", "MISSING", "WARN")]
    print(f"\n{len(rows)} files  |  {'stale: ' + str(len(stale)) if stale else 'all current'}")
    if a.check and stale:
        print("\nRun without --check to rebake.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
