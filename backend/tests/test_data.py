"""Tests for backend/rulial/data.py (LANE-DATA).

Run from the repo root::

    python3 -m pytest backend/tests/test_data.py -v

These tests are offline. They read the CSV cache that ``rulial.data`` built
under ``data/prices/``; nothing here hits the network. The one test that would
need a fetch (a cold-cache round-trip) writes into ``tmp_path`` with a
monkeypatched cache directory instead.
"""

from __future__ import annotations

import datetime as dt
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

# backend/ on sys.path so `from rulial import ...` resolves no matter where
# pytest is invoked from. (LANE-DATA owns no conftest.py.)
BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from rulial import config  # noqa: E402
from rulial import data as D  # noqa: E402


# --------------------------------------------------------------------------
# fixtures / helpers
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def cached_universe():
    """Every universe ticker that actually has a CSV on disk."""
    present = [t for t in config.UNIVERSE if D.cache_path(t).exists()]
    if not present:
        pytest.skip("no price cache on disk; run `python3 -m rulial.data` first")
    return present


# --------------------------------------------------------------------------
# schema / contract shape
# --------------------------------------------------------------------------


def test_price_columns_match_the_contract():
    """CONTRACT.md s4 freezes the column list and its order."""
    assert D.PRICE_COLUMNS == ["date", "open", "high", "low", "close", "volume"]


def test_load_prices_returns_contract_columns(cached_universe):
    df = D.load_prices(cached_universe[0])
    assert list(df.columns) == D.PRICE_COLUMNS


def test_load_prices_dates_are_iso_strings(cached_universe):
    df = D.load_prices(cached_universe[0])
    assert len(df) > 0
    for value in (df["date"].iloc[0], df["date"].iloc[-1]):
        assert isinstance(value, str), "date must be a plain ISO string, not a Timestamp"
        dt.date.fromisoformat(value)  # raises if malformed


def test_load_prices_is_sorted_ascending_and_unique(cached_universe):
    for ticker in cached_universe:
        df = D.load_prices(ticker)
        dates = df["date"].tolist()
        assert dates == sorted(dates), f"{ticker}: dates not ascending"
        assert len(dates) == len(set(dates)), f"{ticker}: duplicate dates"


def test_prices_are_positive_and_ohlc_is_coherent(cached_universe):
    for ticker in cached_universe:
        df = D.load_prices(ticker)
        assert (df["close"] > 0).all(), f"{ticker}: non-positive close"
        ok = df.dropna(subset=["open", "high", "low", "close"])
        assert (ok["high"] >= ok["low"] - 1e-9).all(), f"{ticker}: high < low"
        assert (ok["high"] >= ok["close"] - 1e-6).all(), f"{ticker}: close above high"
        assert (ok["low"] <= ok["close"] + 1e-6).all(), f"{ticker}: close below low"


def test_unknown_ticker_returns_empty_frame_not_an_exception():
    df = D.load_prices("ZZZZ_NOT_A_TICKER")
    assert list(df.columns) == D.PRICE_COLUMNS
    assert len(df) == 0


# --------------------------------------------------------------------------
# the cache round-trips
# --------------------------------------------------------------------------


def test_cache_round_trips_on_disk(cached_universe):
    """Read the CSV twice through the public API; must be byte-identical data."""
    ticker = cached_universe[0]
    first = D.load_prices(ticker)
    D._MEMO.pop(ticker.upper(), None)  # force a genuine re-read from disk
    second = D.load_prices(ticker)
    pd.testing.assert_frame_equal(first, second)


def test_cache_round_trips_through_write_then_read(tmp_path, monkeypatch):
    """Write a frame with _write_cache, read it back with load_prices: same data.

    Exercises the cold-cache path without any network by pointing PRICES_DIR at
    a temp dir and pre-seeding the CSV.
    """
    monkeypatch.setattr(config, "PRICES_DIR", tmp_path)
    D._MEMO.clear()

    original = D._normalise(
        pd.DataFrame(
            {
                "date": ["2018-01-02", "2018-01-03", "2018-01-04"],
                "open": [10.0, 11.0, 12.0],
                "high": [10.5, 11.5, 12.5],
                "low": [9.5, 10.5, 11.5],
                "close": [10.2, 11.2, 12.2],
                "volume": [1000.0, 2000.0, 3000.0],
            }
        )
    )
    D._write_cache("FAKE", original)
    assert (tmp_path / "FAKE.csv").exists()

    D._MEMO.clear()
    reloaded = D.load_prices("FAKE", start="1900-01-01")
    pd.testing.assert_frame_equal(original, reloaded)
    D._MEMO.clear()


def test_synthetic_cache_is_marked_and_detected(tmp_path, monkeypatch):
    """A synthetic CSV must announce itself so no lane reports it as real."""
    monkeypatch.setattr(config, "PRICES_DIR", tmp_path)
    D._MEMO.clear()
    D.SYNTHETIC_TICKERS.discard("SYNTH")

    fake = D._synthetic_prices("SYNTH", "2018-01-01", "2018-06-30")
    assert "SYNTH" in D.SYNTHETIC_TICKERS
    D._write_cache("SYNTH", fake)

    header = (tmp_path / "SYNTH.csv").read_text().splitlines()[0]
    assert "SYNTHETIC" in header

    D.SYNTHETIC_TICKERS.discard("SYNTH")
    D._MEMO.clear()
    df = D.load_prices("SYNTH", start="1900-01-01")
    assert len(df) > 0
    assert "SYNTH" in D.SYNTHETIC_TICKERS, "reading a synthetic cache must re-flag it"
    D.SYNTHETIC_TICKERS.discard("SYNTH")
    D._MEMO.clear()


# --------------------------------------------------------------------------
# date coverage -- the leak-guard window must actually be covered
# --------------------------------------------------------------------------


def test_history_covers_pre_2019_train_period(cached_universe):
    """Every ticker must supply real train-period rows at or before TRAIN_END.

    CONTRACT.md s2 lets the seed corpus and calibration use data <= 2019-12-31.
    If a ticker has no pre-2019 rows there is nothing to calibrate on.
    """
    for ticker in cached_universe:
        df = D.load_prices(ticker)
        assert len(df) > 0, f"{ticker}: no rows at all"
        first, last = df["date"].iloc[0], df["date"].iloc[-1]

        # every universe ticker was public well before the train window closed
        assert first <= "2012-06-01", f"{ticker}: history starts too late ({first})"
        # and genuinely reaches into the pre-2019 train window
        assert first < config.TRAIN_END, f"{ticker}: nothing before TRAIN_END"
        assert last > config.TEST_START, f"{ticker}: nothing in the test window"

        train = df[df["date"] <= config.TRAIN_END]
        assert len(train) > 250, (
            f"{ticker}: only {len(train)} train rows; need >250 for a 250d trailing vol"
        )


def test_default_window_honours_config_history_start(cached_universe):
    """load_prices() respects config.HISTORY_START, whatever the parent sets.

    It is currently ``None`` ("fetch from inception"), so the default call must
    return the full cached history rather than silently clipping it.
    """
    hs = getattr(config, "HISTORY_START", None)
    for ticker in cached_universe:
        default = D.load_prices(ticker)
        full = D.load_prices(ticker, start="1900-01-01")
        if hs:
            assert default["date"].iloc[0] >= hs
        else:
            pd.testing.assert_frame_equal(default, full)


def test_history_reaches_each_tickers_inception(cached_universe):
    """Depth check. config.HISTORY_START is None, so the cache must hold the
    ticker's whole life, not an arbitrarily truncated window.

    Inception dates independently confirmed by LANE-DATA-FEASIBILITY.
    """
    inception = {
        "XOM": "1962-01-02", "BA": "1962-01-02", "JPM": "1980-03-17",
        "AAPL": "1980-12-12", "MSFT": "1986-03-13", "AMZN": "1997-05-15",
        "NVDA": "1999-01-22", "GOOGL": "2004-08-19", "TSLA": "2010-06-29",
        "META": "2012-05-18",
    }
    if getattr(config, "HISTORY_START", None):
        pytest.skip("HISTORY_START is set; inception depth not expected")
    for ticker in cached_universe:
        first = D.load_prices(ticker)["date"].iloc[0]
        assert first == inception[ticker], f"{ticker}: starts {first}, expected {inception[ticker]}"


def test_history_extends_to_roughly_today(cached_universe):
    """A stale cache would quietly starve the test window."""
    cutoff = (dt.date.today() - dt.timedelta(days=10)).isoformat()
    for ticker in cached_universe:
        last = D.load_prices(ticker)["date"].iloc[-1]
        assert last >= cutoff, f"{ticker}: cache ends {last}, stale as of {cutoff}"


def test_train_test_windows_are_both_non_empty(cached_universe):
    for ticker in cached_universe:
        df = D.load_prices(ticker)
        train = df[df["date"] <= config.TRAIN_END]
        test = df[df["date"] >= config.TEST_START]
        assert len(train) > 0 and len(test) > 0, f"{ticker}: empty train or test window"


def test_start_and_end_filters_are_inclusive(cached_universe):
    df = D.load_prices(cached_universe[0], start="2015-01-01", end="2015-12-31")
    assert len(df) > 200
    assert df["date"].iloc[0] >= "2015-01-01"
    assert df["date"].iloc[-1] <= "2015-12-31"


# --------------------------------------------------------------------------
# the shipped cache is REAL data
# --------------------------------------------------------------------------


def test_shipped_cache_contains_no_synthetic_data(cached_universe):
    """Guard against a rate-limit fallback silently shipping fake prices."""
    for ticker in cached_universe:
        head = D.cache_path(ticker).read_text().splitlines()[0]
        assert "SYNTHETIC" not in head, f"{ticker}: cache is SYNTHETIC, re-fetch it"


def test_known_real_price_anchors():
    """Spot-check against values independently confirmed via the
    dubbs-research MCP equity_price_historical route (yfinance, splits_only)
    on 2026-09-06. If these drift, the cache is not the data we verified.
    """
    anchors = {
        "AAPL": ("2019-12-31", 73.4124984741211),
        "MSFT": ("2019-12-31", 157.6999969482422),
        "JPM": ("2019-12-31", 139.39999389648438),
        "XOM": ("2019-12-31", 69.77999877929688),
        "BA": ("2019-12-31", 325.760009765625),
        "NVDA": ("2019-12-31", 5.882500171661377),
        # the NVDA crypto-hangover jump window, CONTRACT.md s3 style event
        "NVDA_JUMP": ("2018-11-15", 5.059750080108643),
    }
    for key, (date, expected) in anchors.items():
        ticker = key.split("_")[0]
        if not D.cache_path(ticker).exists():
            pytest.skip(f"{ticker} not cached")
        df = D.load_prices(ticker, start="1900-01-01")
        row = df[df["date"] == date]
        assert len(row) == 1, f"{ticker}: missing bar for {date}"
        assert row["close"].iloc[0] == pytest.approx(expected, rel=1e-6), (
            f"{ticker} {date}: cache says {row['close'].iloc[0]}, verified value is {expected}"
        )


def test_prices_are_split_adjusted():
    """NVDA's 2021 4:1 and 2024 10:1 splits must NOT appear as -75%/-90% days.

    Unadjusted data would manufacture fake CONTRACT.md s3 events out of splits.
    """
    if not D.cache_path("NVDA").exists():
        pytest.skip("NVDA not cached")
    df = D.load_prices("NVDA")
    rets = df["close"].pct_change().dropna()
    assert rets.min() > -0.60, f"suspected unadjusted split, worst day {rets.min():.3f}"


# --------------------------------------------------------------------------
# load_all_prices
# --------------------------------------------------------------------------


def test_load_all_prices_covers_the_whole_universe():
    frames = D.load_all_prices()
    assert set(frames) == set(config.UNIVERSE), "must key on config.UNIVERSE, never a hardcoded list"
    for ticker, df in frames.items():
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == D.PRICE_COLUMNS, f"{ticker}: wrong columns"


def test_load_all_prices_accepts_a_subset():
    frames = D.load_all_prices(["NVDA", "AAPL"])
    assert set(frames) == {"NVDA", "AAPL"}


# --------------------------------------------------------------------------
# load_fundamentals
# --------------------------------------------------------------------------


def test_load_fundamentals_returns_a_dict_for_every_ticker():
    for ticker in config.UNIVERSE:
        rec = D.load_fundamentals(ticker)
        assert isinstance(rec, dict), f"{ticker}: fundamentals must be a dict (may be empty)"


def test_load_fundamentals_supplies_name_and_sector_for_the_tickers_endpoint():
    """GET /api/tickers needs symbol/name/sector (CONTRACT.md s6)."""
    for ticker in config.UNIVERSE:
        rec = D.load_fundamentals(ticker)
        if not rec:
            pytest.skip(f"{ticker}: fundamentals cache absent (documented as best-effort)")
        assert rec.get("symbol") == ticker
        assert rec.get("name")
        assert rec.get("sector")


def test_load_fundamentals_unknown_ticker_is_empty_not_an_error():
    assert D.load_fundamentals("ZZZZ_NOT_A_TICKER") == {}


# --------------------------------------------------------------------------
# trailing_vol -- LANE-EVAL and LANE-MODEL both depend on this convention
# --------------------------------------------------------------------------


def test_trailing_vol_returns_a_plausible_daily_sigma(cached_universe):
    for ticker in cached_universe:
        sigma = D.trailing_vol(D.load_prices(ticker), config.TRAIN_END)
        assert not math.isnan(sigma)
        # a daily sigma for a large-cap equity: ~0.5% to ~8%.
        assert 0.002 < sigma < 0.08, (
            f"{ticker}: sigma={sigma:.5f} is not a DAILY figure "
            "(annualised would be ~0.2-0.6, per-horizon ~0.03-0.15)"
        )


def test_trailing_vol_matches_a_hand_computed_value(cached_universe):
    """Pin the exact convention: std of daily pct_change, ddof=1, inclusive of asof."""
    ticker = cached_universe[0]
    df = D.load_prices(ticker)
    asof = config.TRAIN_END
    hist = df[df["date"] <= asof]["close"]
    expected = hist.pct_change().dropna().iloc[-250:].std(ddof=1)
    assert D.trailing_vol(df, asof, lookback=250) == pytest.approx(expected, rel=1e-12)


def test_trailing_vol_uses_simple_returns_not_log_returns(cached_universe):
    """Guards the units: Event.move_pct and Ensemble.paths are simple returns."""
    import numpy as np

    ticker = cached_universe[0]
    df = D.load_prices(ticker)
    hist = df[df["date"] <= config.TRAIN_END]["close"]
    simple = hist.pct_change().dropna().iloc[-250:].std(ddof=1)
    log = np.diff(np.log(hist.to_numpy()))[-250:].std(ddof=1)
    got = D.trailing_vol(df, config.TRAIN_END)
    assert abs(got - simple) < abs(got - log)


def test_trailing_vol_never_looks_ahead(cached_universe):
    """Rows after asof must not move the answer -- this is the leak guard."""
    ticker = cached_universe[0]
    full = D.load_prices(ticker)
    asof = "2015-06-30"
    truncated = full[full["date"] <= asof]
    assert len(truncated) < len(full)
    assert D.trailing_vol(full, asof) == pytest.approx(D.trailing_vol(truncated, asof))


def test_trailing_vol_includes_the_asof_day_itself(cached_universe):
    """Documented convention: the return realised ON asof is known at asof close."""
    ticker = cached_universe[0]
    df = D.load_prices(ticker)
    asof = "2015-06-30"
    up_to = df[df["date"] <= asof]
    before = df[df["date"] < asof]
    inclusive = up_to["close"].pct_change().dropna().iloc[-250:].std(ddof=1)
    exclusive = before["close"].pct_change().dropna().iloc[-250:].std(ddof=1)
    got = D.trailing_vol(df, asof)
    assert got == pytest.approx(inclusive, rel=1e-12)
    assert got != pytest.approx(exclusive, rel=1e-12)


def test_trailing_vol_respects_the_lookback_argument(cached_universe):
    df = D.load_prices(cached_universe[0])
    short = D.trailing_vol(df, config.TRAIN_END, lookback=30)
    long = D.trailing_vol(df, config.TRAIN_END, lookback=250)
    assert not math.isnan(short) and not math.isnan(long)
    assert short != long


def test_trailing_vol_default_lookback_is_the_config_value(cached_universe):
    df = D.load_prices(cached_universe[0])
    assert D.trailing_vol(df, config.TRAIN_END) == pytest.approx(
        D.trailing_vol(df, config.TRAIN_END, lookback=config.NULL_VOL_LOOKBACK)
    )


def test_trailing_vol_returns_nan_on_insufficient_history(cached_universe):
    df = D.load_prices(cached_universe[0])
    assert math.isnan(D.trailing_vol(df, "1990-01-01"))
    assert math.isnan(D.trailing_vol(df.head(5), config.TRAIN_END))
    assert math.isnan(D.trailing_vol(D.load_prices("ZZZZ_NOT_A_TICKER"), config.TRAIN_END))


def test_trailing_vol_horizon_scaling_is_documented_and_sane(cached_universe):
    """sigma_h = sigma_daily * sqrt(h) -- the CONTRACT.md s7 null model width."""
    df = D.load_prices(cached_universe[0])
    daily = D.trailing_vol(df, config.TRAIN_END)
    sigma_5d = daily * math.sqrt(config.DEFAULT_HORIZON_DAYS)
    assert 0.005 < sigma_5d < 0.30
    assert "DAILY sigma" in D.trailing_vol.__doc__


def test_trailing_vol_accepts_datetime_dates(cached_universe):
    """Robust to a caller handing over a frame with Timestamp dates."""
    df = D.load_prices(cached_universe[0]).copy()
    string_answer = D.trailing_vol(df, config.TRAIN_END)
    df["date"] = pd.to_datetime(df["date"])
    assert D.trailing_vol(df, config.TRAIN_END) == pytest.approx(string_answer)


def test_trailing_vol_expands_after_a_jump():
    """LANE-WOLFRAM measured ~1.78x. The null auto-widens post-event by design;
    LANE-MODEL must not assume a stale, narrow null."""
    if not D.cache_path("NVDA").exists():
        pytest.skip("NVDA not cached")
    df = D.load_prices("NVDA")
    calm = D.trailing_vol(df, "2018-10-01")
    after = D.trailing_vol(df, "2018-11-21")  # the crypto-hangover jump window
    assert after > calm


# --------------------------------------------------------------------------
# import hygiene (CONTRACT.md s9)
# --------------------------------------------------------------------------


def test_module_imports_without_network_access():
    """No fetch at import time. Re-import with urlopen sabotaged."""
    import importlib
    import urllib.request

    original = urllib.request.urlopen

    def boom(*a, **k):  # pragma: no cover
        raise AssertionError("data.py performed network I/O at import time")

    urllib.request.urlopen = boom
    try:
        importlib.reload(D)
    finally:
        urllib.request.urlopen = original
    assert hasattr(D, "load_prices")
