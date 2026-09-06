#!/usr/bin/env python3
"""Rebuild data/events.jsonl reproducibly. Written by the INTEGRATOR.

WHY THIS SCRIPT EXISTS
----------------------
`rulial.events.build_ledger()` detects events over whatever price history it is
handed. `data/prices/*.csv` now carries INCEPTION-depth history (XOM and BA from
1962), so calling build_ledger() with no arguments produces 799 events reaching
back to 1962-05-28 -- a strict superset of, but not equal to, the 329-event
ledger this repo actually ships and that the 329-file news corpus was harvested
against. A fresh clone that ran `build_ledger()` would therefore silently get a
different corpus from the one every measured number in docs/INTEGRATION.md was
produced on. This script pins that choice in one auditable place.

THE ONE CHOICE THIS SCRIPT MAKES, AND THE ARGUMENT FOR IT
---------------------------------------------------------
`LEDGER_HISTORY_START = "2008-01-01"` bounds how far back ANALOG RETRIEVAL may
reach. It is NOT a leak-guard constant and it does not touch one:
`TRAIN_END`, `TEST_START` and `EMBARGO_DAYS` (CONTRACT section 2) and the two
tier thresholds (section 3) are untouched and unread by this file except to
label tiers. Restricting history makes the model see LESS, never more.

Reasons, stated before the measurement rather than after it:
  1. REGIME. At inception depth, the large majority of pre-2019 events are
     dot-com-era AMZN and NVDA windows (1999-2002). LANE-DATA and LANE-WOLFRAM
     each flagged, independently and before any test run, that this is a
     different volatility regime from the 2020+ test window, and that analog
     retrieval would be dominated by it.
  2. CORPUS. The 329 harvested corpus files under data/corpus/ map 1:1 onto this
     ledger. The extra 470 inception-depth events carry no articles, so they
     dilute retrieval with unlabelled geometry.
  3. SOURCES. Programmatic news archives effectively do not exist before ~2005
     (LANE-NEWS measured this: money.cnn.com's 2000 archive 404s, Reuters 401s).
     A 1962 event can never be anything but a price shape.

MEASURED CONSEQUENCE, reported for completeness and NOT as the justification:
the inception-depth ledger scores WORSE out of sample (universe mean crps_lift
+1.41%, CI90 [-0.38%, +3.22%], median -0.37%) than this one (+1.93%, CI90
[+0.52%, +3.40%], median +1.34%). Both numbers are in docs/INTEGRATION.md.
Reproduce the comparison with `--history-start 1900-01-01`.

USAGE
-----
    python scripts/build_ledger.py                 # rebuild data/events.jsonl
    python scripts/build_ledger.py --dry-run       # print counts, write nothing
    python scripts/build_ledger.py --history-start 1900-01-01 --out /tmp/deep.jsonl
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

import pandas as pd  # noqa: E402

from rulial import data as D  # noqa: E402
from rulial import events as E  # noqa: E402
from rulial.config import EVENTS_PATH, TEST_END, TEST_START, TRAIN_END, UNIVERSE  # noqa: E402

#: Analog-retrieval history floor. See the module docstring for the argument.
#: This is an INTEGRATOR constant, not a frozen one -- it lives here, not in
#: config.py, precisely so that it is visibly a judgement call.
LEDGER_HISTORY_START = "2008-01-01"


#: Researched, human-sourced description of WHY each window moved. Produced by
#: the research pass that wrote docs/research/*.md. Keyed "TICKER|YYYY-MM-DD".
CONTEXT_PATH = Path(EVENTS_PATH).parent / "event_context.json"


def attach_context(events: list) -> int:
    """Populate Event.headline / .context / .category from event_context.json.

    WHY THIS EXISTS. Before this step the ledger shipped `headline: ""` on all
    329 rows, so (a) /api/events served a ledger with no story in it and the UI
    rendered blank rows, and (b) `generator._event_document` -- the TF-IDF
    document that a user's event text is matched against -- contained nothing
    but the ticker name and a canned direction phrase. The product's entire
    premise is CONDITIONING ON AN EVENT DESCRIPTION, and there was nothing on
    the other side of the join. This wires the two together.

    NOT A LEAK. Every row describes an analog's OWN window, whose outcome is
    already in `move_pct` and already in the ledger. It says nothing about any
    date after the event it describes. The as-of guard that actually matters --
    an analog's forward window must close on or before `as_of_date` -- lives in
    `generator._forward_window_closes_by` and is untouched by this.
    """
    try:
        blob = json.loads(CONTEXT_PATH.read_text())
    except Exception as exc:                       # optional enrichment, never fatal
        print(f"[build_ledger] no research context ({exc}); headlines stay blank",
              file=sys.stderr)
        return 0
    hits = 0
    for ev in events:
        row = blob.get(f"{ev.ticker}|{ev.date}")
        if not isinstance(row, dict):
            continue
        ev.headline = str(row.get("headline", "") or "")
        ev.context = str(row.get("cause", "") or "")
        ev.category = str(row.get("category", "") or "")
        hits += 1
    return hits


def build(history_start: str = LEDGER_HISTORY_START, out: Path | None = None,
          dry_run: bool = False) -> list:
    out = Path(out) if out is not None else Path(EVENTS_PATH)
    events = []
    provenance = {}

    for ticker in UNIVERSE:
        df = D.load_prices(ticker)
        if df is None or len(df) == 0:
            print(f"[build_ledger] WARNING no prices for {ticker}", file=sys.stderr)
            provenance[ticker] = "MISSING"
            continue
        if ticker in getattr(D, "SYNTHETIC_TICKERS", set()):
            print(
                f"[build_ledger] REFUSING {ticker}: data/prices/{ticker}.csv is "
                "LANE-DATA's labelled SYNTHETIC fallback. These events did not "
                "happen. Re-run the price fetch.",
                file=sys.stderr,
            )
            provenance[ticker] = "SYNTHETIC-REFUSED"
            continue
        n_all = len(df)
        df = df[df["date"] >= history_start].reset_index(drop=True)
        provenance[ticker] = f"data.load_prices[{n_all} rows -> {len(df)} from {history_start}]"
        events.extend(E.detect_events(df, ticker))

    events.sort(key=lambda e: (e.ticker, e.date))
    E._assign_famous(events)  # volume-attention salience label; CONTRACT s8.2
    n_ctx = attach_context(events)
    print(f"[build_ledger] research context attached to {n_ctx}/{len(events)} events"
          f"  (source: {CONTEXT_PATH.name})")

    train = [e for e in events if e.date <= TRAIN_END]
    test = [e for e in events if TEST_START <= e.date <= TEST_END]
    beyond = [e for e in events if e.date > TEST_END]

    print(f"[build_ledger] history_start={history_start}")
    print(f"[build_ledger] {len(events)} events total"
          f"  |  train(<= {TRAIN_END}) {len(train)}"
          f"  |  test({TEST_START}..{TEST_END}) {len(test)}"
          f"  |  beyond TEST_END {len(beyond)}")
    for label, rows in (("TRAIN", train), ("TEST ", test)):
        c = collections.Counter(e.ticker for e in rows)
        print(f"[build_ledger] {label} per ticker: "
              + "  ".join(f"{t}={c.get(t,0)}" for t in UNIVERSE))
    print(f"[build_ledger] famous: train {sum(1 for e in train if e.famous)}"
          f" / test {sum(1 for e in test if e.famous)}")
    print(f"[build_ledger] major tier: {sum(1 for e in events if e.tier=='major')}"
          f"  significant tier: {sum(1 for e in events if e.tier=='significant')}")

    if dry_run:
        print("[build_ledger] --dry-run: nothing written")
        return events

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for ev in events:
            f.write(json.dumps(E._event_to_dict(ev)) + "\n")
    print(f"[build_ledger] wrote {len(events)} events -> {out}")
    return events


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--history-start", default=LEDGER_HISTORY_START)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    build(a.history_start, a.out, a.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
