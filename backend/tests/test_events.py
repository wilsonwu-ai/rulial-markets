"""Tests for rulial.events. LANE-EVENTS owns this file.

Run:  cd backend && python -m pytest tests/test_events.py -q

The interesting tests are the de-duplication ones. Overlapping-window handling is
where an event detector silently lies to you: it either triple-counts one crash
or, if the de-dup is written as a naive forward chain scan, it deletes real
events. Both failure modes produce a plausible-looking ledger, so they are
tested explicitly rather than eyeballed.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rulial import events as E  # noqa: E402
from rulial.config import EMBARGO_DAYS, JUMP_THRESHOLD, TRAIN_END, WINDOW_DAYS  # noqa: E402
from rulial.types import Article, Event  # noqa: E402


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _frame(closes, start="2015-01-01", volume=1_000_000, colnames=("date", "close", "volume")):
    """Build a price frame on consecutive business days from a list of closes."""
    dates = pd.bdate_range(start=start, periods=len(closes))
    vols = volume if hasattr(volume, "__len__") else [volume] * len(closes)
    return pd.DataFrame(
        {colnames[0]: dates, colnames[1]: closes, colnames[2]: list(vols)}
    )


def _flat_then_jump(n_before, jump, n_after, base=100.0):
    """Flat prices, one single-bar jump, then flat again."""
    return [base] * n_before + [base * (1 + jump)] * n_after


# ---------------------------------------------------------------------------
# detect_events -- core threshold behaviour
# ---------------------------------------------------------------------------

def test_no_events_on_flat_prices():
    assert E.detect_events(_frame([100.0] * 60), "TEST") == []


def test_detects_a_single_down_jump():
    evs = E.detect_events(_frame(_flat_then_jump(30, -0.30, 30)), "TEST")
    assert len(evs) == 1
    assert evs[0].direction == "down"
    assert evs[0].move_pct == pytest.approx(-0.30, abs=1e-9)
    assert evs[0].ticker == "TEST"
    assert evs[0].window_days == WINDOW_DAYS


def test_detects_a_single_up_jump():
    evs = E.detect_events(_frame(_flat_then_jump(30, 0.42, 30)), "TEST")
    assert len(evs) == 1
    assert evs[0].direction == "up"
    assert evs[0].move_pct == pytest.approx(0.42, abs=1e-9)


def test_threshold_is_inclusive_and_respected():
    """A hair under the frozen detection floor must not fire; a hair over must.

    INTEGRATOR NOTE (test fixed, not code). This previously asserted that a jump
    of *exactly* ``JUMP_THRESHOLD`` fires, and its docstring said "frozen at 0.25".
    That assertion only ever passed by accident of binary floating point: at the
    old 0.25 floor ``100.0 * 1.25 == 125.0`` exactly, so the realised return was
    exactly 0.25. CONTRACT section 3 later moved the detection floor to
    ``TIER_SIGNIFICANT = 0.15``, and ``100.0 * 1.15 == 114.99999999999999``, whose
    realised return is 0.1499999999999999 -- genuinely BELOW the floor. The
    detector is correct to reject it; the test was asserting a float artifact.
    The boundary is now probed with an explicit epsilon on each side.
    """
    eps = 1e-9
    just_under = E.detect_events(_frame(_flat_then_jump(30, JUMP_THRESHOLD - 1e-3, 30)), "T")
    assert just_under == []
    just_over = E.detect_events(_frame(_flat_then_jump(30, JUMP_THRESHOLD + eps, 30)), "T")
    assert len(just_over) == 1


def test_gradual_drift_below_threshold_is_not_an_event():
    """A 20% move spread over 40 bars never clears 25% inside any 5-bar window."""
    closes = [100.0 * (1.20 ** (i / 40)) for i in range(60)]
    assert E.detect_events(_frame(closes), "T") == []


def test_event_date_is_the_window_end():
    closes = _flat_then_jump(30, -0.30, 30)
    df = _frame(closes, start="2015-01-01")
    evs = E.detect_events(df, "T")
    # the jump lands on bar 30; the window ending there is the first to clear
    assert evs[0].date == df["date"].iloc[30].strftime("%Y-%m-%d")


def test_move_pct_matches_the_window_return_definition():
    """move_pct == close[t]/close[t-WINDOW_DAYS] - 1, exactly."""
    rng = np.random.default_rng(7)
    closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.06, 400)))
    df = _frame(closes)
    for ev in E.detect_events(df, "T"):
        i = df.index[df["date"].dt.strftime("%Y-%m-%d") == ev.date][0]
        expected = closes[i] / closes[i - WINDOW_DAYS] - 1
        assert ev.move_pct == pytest.approx(expected, abs=1e-6)


def test_short_history_returns_empty_not_error():
    assert E.detect_events(_frame([100.0, 120.0, 150.0]), "T") == []
    assert E.detect_events(pd.DataFrame(columns=["date", "close", "volume"]), "T") == []


# ---------------------------------------------------------------------------
# de-duplication of overlapping windows  -- the part that matters
# ---------------------------------------------------------------------------

def test_one_crash_produces_exactly_one_event():
    """A single -35% step makes ~5 consecutive windows qualify. Only one survives."""
    df = _frame(_flat_then_jump(40, -0.35, 40))
    closes = df["close"].to_numpy()
    prev = np.concatenate([np.full(WINDOW_DAYS, np.nan), closes[:-WINDOW_DAYS]])
    n_qualifying = int(np.sum(np.abs(closes / prev - 1) >= JUMP_THRESHOLD))
    assert n_qualifying >= 5, "fixture should produce overlapping qualifying windows"
    assert len(E.detect_events(df, "T")) == 1


def test_selected_windows_never_overlap():
    rng = np.random.default_rng(11)
    closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.07, 1200)))
    df = _frame(closes)
    evs = E.detect_events(df, "T")
    idx = [df.index[df["date"].dt.strftime("%Y-%m-%d") == e.date][0] for e in evs]
    assert all(b - a >= WINDOW_DAYS for a, b in zip(idx, idx[1:])), (
        "two selected windows overlap; one crash is being counted twice"
    )


def test_dedupe_keeps_the_most_extreme_window():
    idx = np.array([10, 11, 12, 13])
    ret = np.array([0.26, 0.40, 0.28, 0.27])
    keep = E._dedupe_candidates(idx, ret, WINDOW_DAYS)
    assert len(keep) == 1
    assert idx[keep[0]] == 11  # the 40% window, not the first one


def test_dedupe_does_not_delete_a_distinct_earlier_event():
    """Regression test for the bug that collapsed 118 NVDA windows into 1.

    A chain where A overlaps B and B overlaps C, but A and C do not overlap, and
    the largest move is at C. A naive forward scan walks the whole chain, picks C,
    and throws A away even though A is a legitimate non-overlapping event.
    """
    idx = np.array([100, 104, 108])          # gaps of 4, so each overlaps its neighbour
    ret = np.array([0.30, 0.28, 0.55])       # peak at the far end
    keep = sorted(idx[k] for k in E._dedupe_candidates(idx, ret, WINDOW_DAYS))
    assert 108 in keep, "the largest window must survive"
    assert 100 in keep, "a non-overlapping earlier event must not be deleted"


def test_dedupe_splits_a_long_sustained_slide_into_multiple_events():
    """A 30-bar collapse contains several non-overlapping 5-bar windows."""
    closes = [100.0 * (0.93**i) for i in range(30)] + [100.0 * (0.93**29)] * 20
    evs = E.detect_events(_frame(closes), "T")
    assert len(evs) >= 3, f"expected a sustained slide to yield several events, got {len(evs)}"


def test_dedupe_is_deterministic_under_ties():
    idx = np.array([10, 40, 70])
    ret = np.array([0.30, 0.30, 0.30])
    assert E._dedupe_candidates(idx, ret, WINDOW_DAYS) == [0, 1, 2]
    # ties inside one neighbourhood resolve to the earlier bar
    assert E._dedupe_candidates(np.array([10, 11]), np.array([0.3, 0.3]), WINDOW_DAYS) == [0]


def test_dedupe_empty_input():
    assert E._dedupe_candidates(np.array([]), np.array([]), WINDOW_DAYS) == []


# ---------------------------------------------------------------------------
# price frame normalisation
# ---------------------------------------------------------------------------

def test_accepts_capitalised_columns_and_datetime_index():
    closes = _flat_then_jump(30, -0.30, 30)
    df = _frame(closes, colnames=("Date", "Close", "Volume"))
    assert len(E.detect_events(df, "T")) == 1

    indexed = _frame(closes).set_index("date")
    assert len(E.detect_events(indexed, "T")) == 1


def test_prefers_adjusted_close_over_raw_close():
    """adj_close must win. Raw close carrying an unadjusted split would fire falsely."""
    n = 60
    df = pd.DataFrame(
        {
            "date": pd.bdate_range("2015-01-01", periods=n),
            "close": [100.0] * 30 + [25.0] * 30,   # looks like a -75% crash (a 4:1 split)
            "adj_close": [100.0] * n,              # truth: nothing happened
            "volume": [1_000_000] * n,
        }
    )
    assert E.detect_events(df, "T") == [], "adjusted close was ignored"


def test_missing_close_column_raises_clearly():
    with pytest.raises(ValueError, match="close"):
        E.detect_events(pd.DataFrame({"date": ["2015-01-01"], "open": [1.0]}), "T")


def test_unsorted_and_duplicated_rows_are_handled():
    df = _frame(_flat_then_jump(30, -0.30, 30))
    shuffled = pd.concat([df.iloc[::-1], df.iloc[:5]]).reset_index(drop=True)
    assert len(E.detect_events(shuffled, "T")) == 1


def test_split_artifact_guard_flags_unadjusted_splits():
    closes = np.array([100.0] * 10 + [25.0] * 10)   # exact 4:1
    assert E._split_artifact_bars(closes) == [10]
    # a real -30% crash is not a common split ratio and must not be flagged
    assert E._split_artifact_bars(np.array([100.0] * 10 + [70.0] * 10)) == []


# ---------------------------------------------------------------------------
# ticker inference
# ---------------------------------------------------------------------------

def test_ticker_inferred_from_column_or_attrs():
    df = _frame(_flat_then_jump(30, -0.30, 30))
    df["ticker"] = "ZZZZ"
    assert E.detect_events(df)[0].ticker == "ZZZZ"

    df2 = _frame(_flat_then_jump(30, -0.30, 30))
    df2.attrs["ticker"] = "YYYY"
    assert E.detect_events(df2)[0].ticker == "YYYY"


# ---------------------------------------------------------------------------
# famous heuristic
# ---------------------------------------------------------------------------

def test_famous_requires_a_volume_spike():
    """Identical moves; only the one on heavy volume can be famous."""
    quiet = _frame(_flat_then_jump(80, -0.40, 20), volume=1_000_000)
    loud_vol = [1_000_000] * 76 + [20_000_000] * 5 + [1_000_000] * 19
    loud = _frame(_flat_then_jump(80, -0.40, 20), volume=loud_vol)

    evs = E.detect_events(quiet, "QUIET") + E.detect_events(loud, "LOUD")
    E._assign_famous(evs)
    by_ticker = {e.ticker: e.famous for e in evs}
    assert by_ticker["LOUD"] is True
    assert by_ticker["QUIET"] is False


def test_famous_is_a_bool_and_never_none():
    df = _frame(_flat_then_jump(80, -0.40, 20))
    evs = E.detect_events(df, "T")
    E._assign_famous(evs)
    assert all(isinstance(e.famous, bool) for e in evs)


def test_assign_famous_handles_empty_and_missing_volume():
    assert E._assign_famous([]) == []
    df = _frame(_flat_then_jump(80, -0.40, 20), volume=[np.nan] * 100)
    evs = E.detect_events(df, "NOVOL")
    E._assign_famous(evs)
    assert all(e.famous is False for e in evs)  # unknown attention -> obscure, not a crash


def test_famous_heuristic_is_documented():
    """CONTRACT s8.2 requires the split be reported; a silent heuristic is not enough."""
    doc = E.FAMOUS_HEURISTIC_DOC
    assert "HEURISTIC" in doc
    assert "LIMITATION" in doc.upper()
    assert str(E.FAMOUS_ATTENTION_RATIO_MIN) in doc


# ---------------------------------------------------------------------------
# ledger round trip
# ---------------------------------------------------------------------------

def test_build_load_round_trip(tmp_path):
    prices = tmp_path / "prices"
    prices.mkdir()
    for t, jump in [("AAA", -0.30), ("BBB", 0.45)]:
        _frame(_flat_then_jump(40, jump, 40)).to_csv(prices / f"{t}.csv", index=False)

    out = tmp_path / "events.jsonl"
    built = E.build_ledger(["AAA", "BBB"], out_path=out, prices_dir=prices, verbose=False)
    assert len(built) == 2

    loaded = E.load_ledger(out)
    assert len(loaded) == 2
    for a, b in zip(built, loaded):
        assert (a.ticker, a.date, a.direction, a.famous) == (b.ticker, b.date, b.direction, b.famous)
        assert a.move_pct == pytest.approx(b.move_pct)


def test_ledger_is_one_json_object_per_line(tmp_path):
    prices = tmp_path / "prices"
    prices.mkdir()
    _frame(_flat_then_jump(40, -0.30, 40)).to_csv(prices / "AAA.csv", index=False)
    out = tmp_path / "events.jsonl"
    E.build_ledger(["AAA"], out_path=out, prices_dir=prices, verbose=False)

    lines = [ln for ln in out.read_text().splitlines() if ln.strip()]
    assert len(lines) == 1
    row = json.loads(lines[0])
    for key in ("ticker", "date", "move_pct", "direction", "window_days", "famous", "articles"):
        assert key in row, f"ledger row missing {key}"


def test_missing_ticker_is_skipped_not_fatal(tmp_path):
    prices = tmp_path / "prices"
    prices.mkdir()
    _frame(_flat_then_jump(40, -0.30, 40)).to_csv(prices / "AAA.csv", index=False)
    out = tmp_path / "events.jsonl"
    built = E.build_ledger(["AAA", "NOPE"], out_path=out, prices_dir=prices, verbose=False)
    assert [e.ticker for e in built] == ["AAA"]


def test_load_ledger_missing_file_returns_empty(tmp_path):
    assert E.load_ledger(tmp_path / "nope.jsonl") == []


def test_load_ledger_preserves_articles(tmp_path):
    """LANE-NEWS enriches rows in place; a reload must not drop its work."""
    out = tmp_path / "events.jsonl"
    ev = Event(
        ticker="AAA", date="2015-03-04", move_pct=-0.31, direction="down", window_days=5,
        headline="h",
        articles=[Article(url="u", title="t", published="2015-03-03", source="reuters", snippet="s")],
        famous=True,
    )
    out.write_text(json.dumps(E._event_to_dict(ev)) + "\n")
    back = E.load_ledger(out)[0]
    assert back.headline == "h"
    assert back.famous is True
    assert len(back.articles) == 1
    assert back.articles[0].source == "reuters"
    assert back.articles[0].url == "u"


def test_load_ledger_tolerates_blank_lines_and_extra_keys(tmp_path):
    out = tmp_path / "events.jsonl"
    row = {"ticker": "AAA", "date": "2015-03-04", "move_pct": -0.31,
           "direction": "down", "window_days": 5, "unexpected_key": 1}
    out.write_text("\n" + json.dumps(row) + "\n\n")
    assert len(E.load_ledger(out)) == 1


# ---------------------------------------------------------------------------
# split_ledger -- the leak guard
# ---------------------------------------------------------------------------

def _ev(date, ticker="AAA"):
    return Event(ticker=ticker, date=date, move_pct=0.3, direction="up", window_days=5)


def test_split_respects_train_end():
    train, test = E.split_ledger([_ev("2015-06-01"), _ev("2021-06-01")])
    assert [e.date for e in train] == ["2015-06-01"]
    assert [e.date for e in test] == ["2021-06-01"]


def test_no_train_event_lands_after_train_end():
    train, _ = E.split_ledger([_ev("2019-12-30"), _ev("2019-06-01")])
    assert all(e.date <= TRAIN_END for e in train)


def test_embargo_purges_both_sides_of_the_boundary():
    """A train event 2 days before TRAIN_END has a 5-day outcome inside the test
    period; a test event 2 days after TEST_START has a 5-day lookback inside the
    train period. Both must be purged."""
    events = [_ev("2019-12-30"), _ev("2020-01-02"), _ev("2019-01-15"), _ev("2021-01-15")]
    train, test = E.split_ledger(events)
    dates = {e.date for e in train} | {e.date for e in test}
    assert "2019-12-30" not in dates
    assert "2020-01-02" not in dates
    assert "2019-01-15" in dates and "2021-01-15" in dates


def test_embargo_band_width_is_configurable_and_symmetric():
    train, test = E.split_ledger([_ev("2019-12-30")], embargo_days=0)
    assert len(train) == 1
    train, test = E.split_ledger([_ev("2019-12-30")], embargo_days=EMBARGO_DAYS)
    assert len(train) == 0


def test_train_and_test_are_disjoint_and_ordered():
    events = [_ev(d) for d in ("2011-01-05", "2015-07-07", "2019-01-01", "2021-03-03", "2023-09-09")]
    train, test = E.split_ledger(events)
    assert not ({e.date for e in train} & {e.date for e in test})
    assert max(e.date for e in train) < min(e.date for e in test)


def test_events_after_test_end_are_excluded():
    _, test = E.split_ledger([_ev("2030-01-01")])
    assert test == []
    _, test = E.split_ledger([_ev("2030-01-01")], test_end=None)
    assert len(test) == 1


def test_ledger_summary_accounts_for_every_event():
    events = [_ev(d) for d in ("2015-01-05", "2019-12-30", "2021-03-03")]
    s = E.ledger_summary(events)
    assert s["n_train"] + s["n_test"] + s["n_purged_by_embargo"] == s["n_total"] == 3
    assert s["n_purged_by_embargo"] == 1


# ---------------------------------------------------------------------------
# real-data integration (skipped when no prices are on disk yet)
# ---------------------------------------------------------------------------

def _real_prices_dir():
    import os
    from rulial.config import PRICES_DIR
    for d in (os.environ.get("RULIAL_TMP_PRICES"), PRICES_DIR):
        if d and any(Path(d).glob("*.csv")):
            return Path(d)
    return None


@pytest.mark.skipif(_real_prices_dir() is None, reason="no price CSVs on disk yet")
def test_real_prices_produce_a_sane_ledger(tmp_path):
    d = _real_prices_dir()
    out = tmp_path / "events.jsonl"
    evs = E.build_ledger(out_path=out, prices_dir=d, verbose=False)
    assert len(evs) > 0
    for e in evs:
        assert abs(e.move_pct) >= JUMP_THRESHOLD
        assert e.direction == ("up" if e.move_pct > 0 else "down")
        assert datetime.strptime(e.date, "%Y-%m-%d")
    # no ticker may have two overlapping windows
    for t in {e.ticker for e in evs}:
        ds = sorted(datetime.strptime(e.date, "%Y-%m-%d") for e in evs if e.ticker == t)
        assert all((b - a).days >= WINDOW_DAYS for a, b in zip(ds, ds[1:]))


def test_synthetic_cached_csv_is_never_used_as_real(tmp_path):
    """LANE-DATA writes a '# SYNTHETIC' marker into fallback CSVs. Building a jump
    ledger on random-walk prices would mint crashes that never happened, so a
    marked CSV must be refused even though it parses fine."""
    d = tmp_path / "prices"
    d.mkdir()
    body = _frame(_flat_then_jump(40, -0.30, 40)).to_csv(index=False)
    (d / "AAA.csv").write_text("# SYNTHETIC-FALLBACK-DATA: NOT REAL MARKET PRICES\n" + body)
    df, src = E._load_prices_for("AAA", d)
    assert df is None, f"synthetic CSV was accepted as real (src={src})"

    (d / "BBB.csv").write_text(body)
    df, src = E._load_prices_for("BBB", d)
    assert df is not None and len(df) > 0
