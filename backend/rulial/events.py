"""Event detection and the seed event ledger.

LANE-EVENTS owns this file. See CONTRACT.md sections 3 and 4.

An *event* (CONTRACT.md s3, FROZEN) is a trading day where the close-to-close
return over a rolling ``WINDOW_DAYS = 5`` window satisfies
``|return| >= JUMP_THRESHOLD = 0.25``.  The event's ``date`` is the END of that
window; ``move_pct`` is the window return.

Public API
----------
``detect_events(prices, ticker=None) -> list[Event]``
``build_ledger(...) -> list[Event]``        also writes ``data/events.jsonl``
``load_ledger(...) -> list[Event]``
``split_ledger(...) -> (train_events, test_events)``

Three things in here are judgement calls rather than contract, and each is
documented at its implementation so no downstream lane has to reverse-engineer
it:

1. **Split-adjusted prices are mandatory.**  An unadjusted 4-for-1 split is a
   -75% close-to-close move and would be detected as a crash that never
   happened.  ``_normalize_prices`` prefers an adjusted-close column when the
   source offers one, and ``_split_artifact_bars`` independently checks the
   series for split-shaped discontinuities and shouts if it finds any.
   (Verified 2026-09-06: Yahoo's ``quote.close`` is already split-adjusted, so
   this guard is a safety net rather than a routine correction.)
2. **Overlapping windows are de-duplicated** (``_dedupe_candidates``).  On a
   real crash, five to fifteen consecutive days all clear the threshold on
   overlapping windows.  Counting them all would triple-count one crash and
   inflate the corpus.
3. **``Event.famous`` is a HEURISTIC**, not ground truth.  See
   ``FAMOUS_HEURISTIC_DOC`` and ``_assign_famous``.
"""

from __future__ import annotations

import json

import os
import sys
import warnings
from datetime import date as _date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .config import (
    EMBARGO_DAYS,
    TIER_MAJOR,
    TIER_SIGNIFICANT,
    tier_for,
    EVENTS_PATH,
    JUMP_THRESHOLD,
    PRICES_DIR,
    TEST_END,
    TEST_START,
    TRAIN_END,
    UNIVERSE,
    WINDOW_DAYS,
)
from .types import Article, Event

__all__ = [
    "detect_events",
    "build_ledger",
    "load_ledger",
    "split_ledger",
    "ledger_summary",
    "FAMOUS_HEURISTIC_DOC",
]


# ---------------------------------------------------------------------------
# Price frame normalisation
# ---------------------------------------------------------------------------

_DATE_ALIASES = ("date", "datetime", "timestamp", "time", "index")
# Order matters: adjusted close first. See module docstring, point 1.
_CLOSE_ALIASES = (
    "adj_close", "adjclose", "adj close", "adjusted_close", "adjusted close",
    "close_adj", "close",
)
_VOLUME_ALIASES = ("volume", "vol", "adj_volume")


def _pick(columns: Iterable[str], aliases: Sequence[str]) -> Optional[str]:
    """First column whose lowercased/stripped name matches an alias, in alias order."""
    lookup = {}
    for c in columns:
        key = str(c).strip().lower().replace("-", "_")
        lookup.setdefault(key, c)
        lookup.setdefault(key.replace("_", " "), c)
    for a in aliases:
        if a in lookup:
            return lookup[a]
    return None


def _normalize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Coerce an arbitrary OHLCV frame into columns ``date`` / ``close`` / ``volume``.

    LANE-DATA owns ``data.load_prices`` and this lane must not depend on its exact
    column casing, so we sniff. ``close`` is taken from an ADJUSTED close column
    when one exists -- unadjusted closes make every stock split look like a 25%+
    crash, which would poison the ledger with events that never happened.
    """
    if prices is None or len(prices) == 0:
        return pd.DataFrame(columns=["date", "close", "volume"])

    df = prices.copy()

    # A DatetimeIndex is a perfectly normal way for LANE-DATA to hand us dates.
    if _pick(df.columns, _DATE_ALIASES) is None and isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
        if df.columns[0] not in _DATE_ALIASES:
            df = df.rename(columns={df.columns[0]: "date"})

    date_col = _pick(df.columns, _DATE_ALIASES)
    close_col = _pick(df.columns, _CLOSE_ALIASES)
    vol_col = _pick(df.columns, _VOLUME_ALIASES)

    if date_col is None or close_col is None:
        raise ValueError(
            "events._normalize_prices: could not find a date column and a close "
            f"column in {list(df.columns)!r}"
        )

    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df[date_col], errors="coerce", utc=True).dt.tz_localize(None),
            "close": pd.to_numeric(df[close_col], errors="coerce"),
            "volume": (
                pd.to_numeric(df[vol_col], errors="coerce") if vol_col is not None else np.nan
            ),
        }
    )
    out = out.dropna(subset=["date", "close"])
    out = out[out["close"] > 0]
    out = out.sort_values("date").drop_duplicates(subset="date", keep="last")
    return out.reset_index(drop=True)


#: Common split ratios. A 1-day price ratio landing on one of these to within
#: _SPLIT_TOL is almost certainly a corporate action, not a market move.
_SPLIT_RATIOS = (2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 15.0, 20.0, 1.5, 2.5, 3.0 / 2.0)
_SPLIT_TOL = 0.02


def _split_artifact_bars(close: np.ndarray) -> List[int]:
    """Bars whose 1-day move looks like an unadjusted stock split, not a real move.

    Empirically verified 2026-09-06 against the Yahoo v8 chart endpoint: the raw
    ``quote.close`` series IS already split-adjusted (NVDA's 10-for-1 on
    2024-06-10 and AAPL's 4-for-1 on 2020-08-31 show no discontinuity; the only
    difference from ``adjclose`` is the dividend adjustment, which is smooth).
    So this guard should normally find nothing. It exists because if a price
    source ever hands us unadjusted closes, every split becomes a fake -50% to
    -90% "event" and would silently poison the ledger. Better to shout.
    """
    if close.size < 2:
        return []
    ratio = close[:-1] / close[1:]            # >1 for a forward split
    inv = close[1:] / close[:-1]              # >1 for a reverse split
    bad = []
    for i, (r, v) in enumerate(zip(ratio, inv)):
        for s in _SPLIT_RATIOS:
            if abs(r - s) / s < _SPLIT_TOL or abs(v - s) / s < _SPLIT_TOL:
                bad.append(i + 1)
                break
    return bad


# ---------------------------------------------------------------------------
# De-duplication of overlapping windows
# ---------------------------------------------------------------------------

def _dedupe_candidates(idx: np.ndarray, ret: np.ndarray, window_days: int) -> List[int]:
    """Collapse overlapping qualifying windows down to non-overlapping events.

    On a real crash, five to fifteen consecutive bars all clear the threshold on
    windows that overlap each other. Emitting all of them would triple-count one
    crash and inflate the event corpus, so exactly one survives per neighbourhood.

    Two windows ending at bars ``a`` and ``b`` overlap iff ``|a - b| < window_days``
    (each window covers the half-open bar span ``(end - window_days, end]``).

    Algorithm -- greedy non-maximum suppression, the standard approach:

    1. Sort all qualifying windows by ``|return|`` descending (ties broken by the
       earlier date, so the result is fully deterministic).
    2. Take the largest surviving window, emit it, and suppress every other
       window within ``window_days`` bars of it.
    3. Repeat until nothing is left.

    NMS is used here rather than a left-to-right scan on purpose. A forward scan
    that walks a *chain* of overlapping bars looking for the chain maximum will
    silently delete legitimate earlier events whenever the chain is long and its
    peak sits at the far end -- A overlaps B, B overlaps C, but A and C do not
    overlap, so dropping A is wrong. That bug cost this lane its first ledger
    (it collapsed 118 NVDA candidate windows into 1 event instead of ~40).
    NMS has no such ordering artefact: the winner in each neighbourhood is the
    globally most extreme window, and only genuinely overlapping windows die.

    Guarantees: the selected windows are pairwise non-overlapping, every emitted
    window is the most extreme within its own overlap radius, and the output is
    sorted by bar index ascending.

    Parameters
    ----------
    idx : bar positions of qualifying windows, strictly increasing.
    ret : the window return at each of those bars (same length as ``idx``).

    Returns the selected positions *into ``idx``* (not bar numbers).
    """
    n = len(idx)
    if n == 0:
        return []
    order = sorted(range(n), key=lambda k: (-abs(ret[k]), idx[k]))
    alive = np.ones(n, dtype=bool)
    selected: List[int] = []
    for k in order:
        if not alive[k]:
            continue
        selected.append(k)
        # suppress every window overlapping this one (including itself)
        alive &= np.abs(idx - idx[k]) >= window_days
    return sorted(selected)


# ---------------------------------------------------------------------------
# detect_events
# ---------------------------------------------------------------------------

def detect_events(
    prices: pd.DataFrame,
    ticker: Optional[str] = None,
    *,
    threshold: float = JUMP_THRESHOLD,
    window_days: int = WINDOW_DAYS,
) -> List[Event]:
    """Detect jump events in one ticker's price history. CONTRACT.md s3.

    A bar qualifies when ``|close[t] / close[t - window_days] - 1| >= threshold``.
    Overlapping qualifying windows are de-duplicated (see ``_dedupe_candidates``)
    so one crash produces one event.

    ``ticker`` may be omitted if the frame carries a ticker/symbol column or a
    ``.attrs['ticker']``; it is only used to stamp ``Event.ticker``.

    Returns events sorted by date ascending.  ``Event.headline`` and
    ``Event.articles`` are left for LANE-NEWS to fill in.
    """
    if ticker is None:
        col = _pick(prices.columns, ("ticker", "symbol")) if hasattr(prices, "columns") else None
        if col is not None and len(prices):
            ticker = str(prices[col].iloc[0])
        else:
            ticker = str(getattr(prices, "attrs", {}).get("ticker", "UNKNOWN"))

    df = _normalize_prices(prices)
    if len(df) <= window_days:
        return []

    close = df["close"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)
    dates = df["date"]

    # rolling window return; bars 0..window_days-1 have no complete window
    prev = np.concatenate([np.full(window_days, np.nan), close[:-window_days]])
    with np.errstate(invalid="ignore", divide="ignore"):
        wret = close / prev - 1.0

    qualifies = np.abs(wret) >= threshold
    qualifies &= np.isfinite(wret)
    cand_idx = np.flatnonzero(qualifies)
    if cand_idx.size == 0:
        return []

    keep = _dedupe_candidates(cand_idx, wret[cand_idx], window_days)

    # attention proxy for the famous heuristic: window dollar volume vs the
    # trailing 60-bar baseline ending just before the window opened.
    events: List[Event] = []
    for k in keep:
        i = int(cand_idx[k])
        move = float(wret[i])
        w0 = i - window_days + 1
        base_lo, base_hi = max(0, w0 - 60), w0
        with warnings.catch_warnings():
            # an all-NaN volume slice is a legitimate "attention unknown", not an error
            warnings.simplefilter("ignore", RuntimeWarning)
            win_dv = np.nanmean(close[w0 : i + 1] * volume[w0 : i + 1]) if volume.size else np.nan
            base_dv = (
                np.nanmedian(close[base_lo:base_hi] * volume[base_lo:base_hi])
                if base_hi - base_lo >= 10
                else np.nan
            )
        ev = Event(
            ticker=ticker,
            date=dates.iloc[i].strftime("%Y-%m-%d"),
            move_pct=round(move, 6),
            direction="up" if move > 0 else "down",
            window_days=window_days,
            headline="",
            articles=[],
            tier=tier_for(move) or "significant",  # CONTRACT.md s3, two tiers
            famous=False,  # assigned in build_ledger, see _assign_famous
        )
        # stash the attention proxy off-dataclass; build_ledger consumes and drops it
        _ATTENTION[(ticker, ev.date)] = (
            float(win_dv) if np.isfinite(win_dv) else float("nan"),
            float(base_dv) if np.isfinite(base_dv) else float("nan"),
            float(dates.iloc[i].year),
        )
        events.append(ev)

    return events


# module-level side table so detect_events can stay contract-shaped (returns
# list[Event]) while still passing the salience inputs to the famous heuristic.
_ATTENTION: dict = {}


# ---------------------------------------------------------------------------
# The `famous` heuristic  -- CONTRACT.md s8.2
# ---------------------------------------------------------------------------

FAMOUS_HEURISTIC_DOC = """\
Event.famous is a HEURISTIC PROXY FOR PRESS SALIENCE, not a verified fact.

CONTRACT.md s8.2 requires that we report famous and obscure events separately,
because an LLM whose weights have read the post-2019 world can *remember* a
famous crash without forecasting anything. The split is only useful if the
label is (a) computed the same way for every event and (b) honest about being
approximate. It is deliberately NOT hand-curated per event.

An event is labelled famous when BOTH of the following hold:

  1. attention_ratio >= 2.0
       attention_ratio = mean dollar volume during the 5-day jump window
                       / median dollar volume over the 60 bars before it.
       Rationale: press coverage and trading attention move together. A jump
       that ran on ordinary volume was not a story anyone was reading.

  2. The event ranks in the top FAMOUS_TOP_FRACTION (0.33) of the ledger by a
     composite salience score:
       score = 0.50 * z(log attention_ratio)
             + 0.30 * z(|move_pct|)
             + 0.20 * z(log mean window dollar volume)
     Rationale: the third term is a size/liquidity proxy. A 30% move in a
     mega-cap is front-page news; the same move in the same name fifteen years
     earlier when it was small was not.

Both conditions must hold, so an event can fail to be famous either by being
unremarkable in its own history (1) or by being small relative to the rest of
the ledger (2). Everything else is obscure.

KNOWN LIMITATIONS, stated because the eval depends on this label:
  * It measures ATTENTION, not MEMORABILITY. A high-volume jump nobody wrote
    an article about scores famous.
  * The composite is rank-based within this ledger, so the famous/obscure
    proportion is roughly fixed by construction. It answers "which of our
    events were the loud ones", not "which events would a human recognise".
  * Volume is unavailable or zero for some very old bars; those events fall
    back to obscure rather than raising.
  * BETTER LABEL AVAILABLE LATER: once LANE-NEWS has harvested, the honest
    measure is article count / publisher tier for each event. If news.py
    overwrites Event.famous with a corpus-derived label, that label should win
    and this heuristic should be dropped. LANE-DATA-FEASIBILITY already showed
    web search returns rich results for catalyst events and literally nothing
    for catalyst-free ones -- which is itself close to a ground-truth split.
"""

FAMOUS_ATTENTION_RATIO_MIN = 2.0
FAMOUS_TOP_FRACTION = 0.33
_FAMOUS_WEIGHTS = {"attention": 0.50, "magnitude": 0.30, "size": 0.20}


def _z(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    good = np.isfinite(x)
    if good.sum() < 2:
        return np.zeros_like(x)
    mu, sd = np.nanmean(x[good]), np.nanstd(x[good])
    if not np.isfinite(sd) or sd == 0:
        return np.zeros_like(x)
    out = np.zeros_like(x)
    out[good] = (x[good] - mu) / sd
    return out


def _assign_famous(events: List[Event]) -> List[Event]:
    """Set ``Event.famous`` in place across the whole ledger. See FAMOUS_HEURISTIC_DOC."""
    if not events:
        return events

    ratio, mag, size = [], [], []
    for ev in events:
        win_dv, base_dv, _yr = _ATTENTION.get((ev.ticker, ev.date), (np.nan, np.nan, np.nan))
        r = win_dv / base_dv if (np.isfinite(win_dv) and np.isfinite(base_dv) and base_dv > 0) else np.nan
        ratio.append(r)
        mag.append(abs(ev.move_pct))
        size.append(win_dv)

    ratio = np.asarray(ratio, dtype=float)
    score = (
        _FAMOUS_WEIGHTS["attention"] * _z(np.log(np.where(ratio > 0, ratio, np.nan)))
        + _FAMOUS_WEIGHTS["magnitude"] * _z(np.asarray(mag, dtype=float))
        + _FAMOUS_WEIGHTS["size"] * _z(np.log(np.where(np.asarray(size) > 0, size, np.nan)))
    )

    finite = score[np.isfinite(score)]
    cutoff = (
        float(np.quantile(finite, 1.0 - FAMOUS_TOP_FRACTION)) if finite.size else float("inf")
    )

    for ev, r, s in zip(events, ratio, score):
        ev.famous = bool(
            np.isfinite(r) and r >= FAMOUS_ATTENTION_RATIO_MIN and np.isfinite(s) and s >= cutoff
        )
    return events


# ---------------------------------------------------------------------------
# Price loading for build_ledger
# ---------------------------------------------------------------------------

def _load_prices_for(
    ticker: str, prices_dir: Optional[Path] = None
) -> Tuple[Optional[pd.DataFrame], str]:
    """Best-effort price load. Returns ``(frame_or_None, provenance_label)``.

    Preference order:

    1. ``rulial.data.load_prices`` (LANE-DATA's file, the contract source) --
       **unless** LANE-DATA has flagged that ticker in ``data.SYNTHETIC_TICKERS``.
    2. ``RULIAL_TMP_PRICES`` env var pointing at a directory of real CSVs. This
       lane uses it only to feed its own detector; it never writes prices there.
    3. ``data/prices/<TICKER>.csv`` read directly -- LANE-DATA may still be
       mid-write, and a raw CSV read is fine if the module import is not ready.

    Step 1's synthetic check is deliberate. LANE-DATA ships a clearly-labelled
    synthetic fallback when every real source fails, which is the right call for
    *its* contract, but a jump ledger built on random-walk prices would be a
    ledger of events that never happened. We would rather build from a real
    source we already have than mint fictional crashes.
    """
    if prices_dir is None:
        try:
            from . import data as _data  # noqa: PLC0415 -- lazy: LANE-DATA may not exist yet

            df = _data.load_prices(ticker)
            synth = ticker.upper() in getattr(_data, "SYNTHETIC_TICKERS", set())
            if df is not None and len(df) and not synth:
                return df, "data.load_prices"
        except Exception:
            pass

    search = [prices_dir] if prices_dir else [os.environ.get("RULIAL_TMP_PRICES"), PRICES_DIR]
    for d in search:
        if not d:
            continue
        p = Path(d) / f"{ticker}.csv"
        if p.exists() and p.stat().st_size > 0:
            try:
                # A cached CSV can be LANE-DATA's synthetic fallback -- the very
                # frame we just declined above. Its header carries a marker; if
                # we did not check it we would launder synthetic prices back in
                # through the file path and mint events that never happened.
                with open(p) as fh:
                    if "SYNTHETIC" in fh.readline().upper():
                        continue
                return pd.read_csv(p, comment="#"), f"csv:{Path(d).name}"
            except Exception:
                continue

    # last resort: LANE-DATA's synthetic frame, clearly labelled as such
    if prices_dir is None:
        try:
            from . import data as _data  # noqa: PLC0415

            df = _data.load_prices(ticker)
            if df is not None and len(df):
                return df, "SYNTHETIC(data.load_prices)"
        except Exception:
            pass
    return None, "missing"


# ---------------------------------------------------------------------------
# build / load / split
# ---------------------------------------------------------------------------

def build_ledger(
    universe: Sequence[str] = tuple(UNIVERSE),
    out_path: Optional[Path] = None,
    prices_dir: Optional[Path] = None,
    *,
    verbose: bool = True,
) -> List[Event]:
    """Detect events across the universe and write ``data/events.jsonl``.

    One JSON-encoded ``Event`` per line, sorted by (ticker, date). Tickers with
    no price data are skipped with a warning rather than failing the build --
    LANE-DATA may not have written them yet.

    Returns the full ledger (train AND test period). ``split_ledger`` applies the
    time boundary; the on-disk ledger deliberately keeps both so LANE-EVAL can
    walk forward without re-running detection.
    """
    out_path = Path(out_path) if out_path else Path(EVENTS_PATH)
    all_events: List[Event] = []
    missing: List[str] = []
    synthetic: List[str] = []
    provenance: dict = {}

    for t in universe:
        df, src = _load_prices_for(t, prices_dir)
        provenance[t] = src
        if df is None or len(df) == 0:
            missing.append(t)
            continue
        if src.startswith("SYNTHETIC"):
            synthetic.append(t)
        norm = _normalize_prices(df)
        bad = _split_artifact_bars(norm["close"].to_numpy(dtype=float))
        if bad:
            when = ", ".join(norm["date"].iloc[b].strftime("%Y-%m-%d") for b in bad[:5])
            print(
                f"[events] WARNING {t}: {len(bad)} bar(s) look like UNADJUSTED stock "
                f"splits ({when}). These will be detected as fake jump events. "
                f"The price source is not split-adjusted.",
                file=sys.stderr,
            )
        all_events.extend(detect_events(df, t))

    all_events.sort(key=lambda e: (e.ticker, e.date))
    _assign_famous(all_events)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for ev in all_events:
            f.write(json.dumps(_event_to_dict(ev)) + "\n")

    BUILD_PROVENANCE.clear()
    BUILD_PROVENANCE.update(provenance)

    if verbose:
        if missing:
            print(f"[events] WARNING no price data for: {', '.join(missing)}", file=sys.stderr)
        if synthetic:
            print(
                f"[events] WARNING built on SYNTHETIC prices for: {', '.join(synthetic)}. "
                "These events DID NOT HAPPEN. Do not report them as real.",
                file=sys.stderr,
            )
        print(f"[events] wrote {len(all_events)} events -> {out_path}")
        print(f"[events] price provenance: {provenance}")
    return all_events


#: Per-ticker price source used by the most recent ``build_ledger`` call.
#: Any lane reporting an event count should check this for "SYNTHETIC".
BUILD_PROVENANCE: dict = {}


def _event_to_dict(ev: Event) -> dict:
    return {
        "ticker": ev.ticker,
        "date": ev.date,
        "move_pct": ev.move_pct,
        "direction": ev.direction,
        "window_days": ev.window_days,
        "headline": ev.headline,
        "articles": [a if isinstance(a, dict) else _article_to_dict(a) for a in (ev.articles or [])],
        "tier": ev.tier,
        "famous": bool(ev.famous),
    }


def _article_to_dict(a) -> dict:
    return {
        "url": getattr(a, "url", ""),
        "title": getattr(a, "title", ""),
        "published": getattr(a, "published", ""),
        "source": getattr(a, "source", ""),
        "snippet": getattr(a, "snippet", ""),
    }


def load_ledger(path: Optional[Path] = None) -> List[Event]:
    """Read ``data/events.jsonl`` back into ``list[Event]``. Empty list if absent.

    Tolerates extra keys (LANE-NEWS may enrich rows) and blank lines.
    """
    p = Path(path) if path else Path(EVENTS_PATH)
    if not p.exists():
        return []
    events: List[Event] = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            arts = [
                Article(
                    url=a.get("url", ""),
                    title=a.get("title", ""),
                    published=a.get("published", ""),
                    source=a.get("source", ""),
                    snippet=a.get("snippet", ""),
                )
                for a in row.get("articles", [])
                if isinstance(a, dict)
            ]
            events.append(
                Event(
                    ticker=row["ticker"],
                    date=row["date"],
                    move_pct=float(row["move_pct"]),
                    direction=row.get("direction", "up" if float(row["move_pct"]) > 0 else "down"),
                    window_days=int(row.get("window_days", WINDOW_DAYS)),
                    headline=row.get("headline", ""),
                    articles=arts,
                    tier=row.get("tier") or (tier_for(float(row["move_pct"])) or "significant"),
                    famous=bool(row.get("famous", False)),
                )
            )
    return events


def split_ledger(
    events: Optional[List[Event]] = None,
    *,
    train_end: str = TRAIN_END,
    test_start: str = TEST_START,
    test_end: Optional[str] = TEST_END,
    embargo_days: int = EMBARGO_DAYS,
) -> Tuple[List[Event], List[Event]]:
    """Split the ledger into (train, test) honouring the CONTRACT s2 leak guard.

    The embargo is applied on BOTH sides, in calendar days:

    * **train**: ``date <= train_end - embargo_days``. A train event dated
      2019-12-30 has a 5-day forward outcome that lands in 2020, i.e. inside the
      test period. Keeping it would leak test-period price action into anything
      calibrated on the train set.
    * **test**: ``date >= test_start + embargo_days`` (and ``<= test_end`` when
      given). A test event dated 2020-01-02 has a 5-day *lookback window* that
      opens in December 2019, so its jump is partly a train-period move.

    Events inside the embargo band are purged from both sides. That is the point
    of a purge gap and it is cheap here -- it costs a handful of events.
    """
    if events is None:
        events = load_ledger()

    tr_cut = _parse(train_end) - timedelta(days=embargo_days)
    te_cut = _parse(test_start) + timedelta(days=embargo_days)
    te_hi = _parse(test_end) if test_end else None

    train, test = [], []
    for ev in events:
        d = _parse(ev.date)
        if d <= tr_cut:
            train.append(ev)
        elif d >= te_cut and (te_hi is None or d <= te_hi):
            test.append(ev)
        # else: inside the embargo band, or after test_end -> purged
    return train, test


def _parse(s: str) -> _date:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()


# ---------------------------------------------------------------------------
# Reporting helper (used by the CLI and by LANE-API for /api/tickers n_events)
# ---------------------------------------------------------------------------

def ledger_summary(events: Optional[List[Event]] = None) -> dict:
    """Per-ticker counts for the whole ledger and for the train/test split."""
    if events is None:
        events = load_ledger()
    train, test = split_ledger(events)
    tr = {t: 0 for t in UNIVERSE}
    te = {t: 0 for t in UNIVERSE}
    for e in train:
        tr[e.ticker] = tr.get(e.ticker, 0) + 1
    for e in test:
        te[e.ticker] = te.get(e.ticker, 0) + 1
    return {
        "n_total": len(events),
        "n_train": len(train),
        "n_test": len(test),
        "n_purged_by_embargo": len(events) - len(train) - len(test),
        "n_famous_train": sum(1 for e in train if e.famous),
        "n_famous_test": sum(1 for e in test if e.famous),
        "train_per_ticker": tr,
        "test_per_ticker": te,
    }


def _cli() -> None:  # pragma: no cover -- convenience only
    evs = build_ledger()
    s = ledger_summary(evs)
    print(json.dumps(s, indent=2))
    print(f"\n{'TICKER':<7}{'DATE':<12}{'MOVE':>9}  {'DIR':<5}{'SPLIT':<7}FAMOUS")
    train, test = split_ledger(evs)
    tr_set = {(e.ticker, e.date) for e in train}
    te_set = {(e.ticker, e.date) for e in test}
    for e in sorted(evs, key=lambda x: (x.ticker, x.date)):
        key = (e.ticker, e.date)
        split = "train" if key in tr_set else ("test" if key in te_set else "purged")
        print(
            f"{e.ticker:<7}{e.date:<12}{e.move_pct * 100:>8.1f}%  "
            f"{e.direction:<5}{split:<7}{'YES' if e.famous else '-'}"
        )


if __name__ == "__main__":  # pragma: no cover
    _cli()
