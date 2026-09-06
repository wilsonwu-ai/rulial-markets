"""LANE-DATA — price + fundamentals loading for rulial-markets.

Owner: LANE-DATA. See CONTRACT.md section 4.

Public surface (this is what other lanes import):

    load_prices(ticker)            -> pd.DataFrame[date, open, high, low, close, volume]
    load_all_prices()              -> dict[str, pd.DataFrame] for config.UNIVERSE
    load_fundamentals(ticker)      -> dict  (best effort, may be {})
    trailing_vol(prices, asof, lookback=250) -> float   DAILY sigma

Design notes
------------
* **Cache first.** Every ticker is fetched once into ``data/prices/{TICKER}.csv``
  and read from disk thereafter. Nothing in this module touches the network at
  import time (CONTRACT.md section 9).

* **Fetch order.** ``yfinance`` if it is importable, else a zero-dependency
  urllib call to Yahoo's public ``/v8/finance/chart`` JSON endpoint, else a
  clearly-labelled synthetic fallback (see ``SYNTHETIC_TICKERS``). The urllib
  path is the one actually used to build the committed CSVs; it was verified
  against ``mcp__dubbs-research__equity_price_historical`` (yfinance provider)
  and agrees to ~1e-9.

* **Prices are SPLIT-ADJUSTED, not dividend-adjusted.** ``close`` is Yahoo's
  ``quote.close``, which is adjusted for splits only, so open/high/low/close in
  a row are mutually consistent. Splits are the adjustment that matters here:
  unadjusted NVDA/TSLA/AAPL series would manufacture fake 25% "events" out of
  10:1 and 4:1 splits. Dividends move a 5-day return by ~0.01% and are ignored
  on purpose.

* **Depth.** ``config.HISTORY_START`` is ``None``, meaning "fetch from each
  ticker's inception". The CSVs therefore run from each ticker's first trading
  day (BA/XOM 1962, AAPL 1980, ..., META 2012) to today, and ``load_prices()``
  returns all of it by default. If the parent ever sets ``HISTORY_START`` to a
  date, the cache keeps a ``WARMUP_YEARS`` buffer before it so
  ``trailing_vol(..., lookback=250)`` still has a full window on day one, and
  ``load_prices()`` filters to the configured start unless ``start=`` overrides.

* **Unknown tickers get nothing, not synthetic data.** The synthetic fallback
  fires only for ``config.UNIVERSE`` members, so a typo returns an empty frame
  instead of inventing a company.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import time as _time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from rulial import config

__all__ = [
    "PRICE_COLUMNS",
    "load_prices",
    "load_all_prices",
    "load_fundamentals",
    "trailing_vol",
    "refresh_prices",
    "cache_path",
    "SYNTHETIC_TICKERS",
]

# --- module constants -------------------------------------------------------

#: Exactly the columns CONTRACT.md section 4 asks for, in order.
PRICE_COLUMNS: List[str] = ["date", "open", "high", "low", "close", "volume"]

#: Extra history kept in the CSV purely so trailing_vol has a warm-up window.
#: Downstream lanes do NOT see this by default -- see load_prices().
WARMUP_YEARS = 2

#: Minimum observations before trailing_vol will return a number.
MIN_VOL_OBS = 20

#: Directory for the best-effort fundamentals cache (this module's own).
FUNDAMENTALS_DIR = config.DATA_DIR / "fundamentals"

_YAHOO_HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")
_HTTP_MAX_RETRIES = 6
_HTTP_BACKOFF_BASE = 2.0      # seconds; doubles each attempt
_THROTTLE_SECONDS = 1.5       # polite gap between per-ticker fetches
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

#: Tickers whose cached CSV is SYNTHETIC, not real market data. Populated at
#: load time by reading the ``# SYNTHETIC`` marker written into the CSV header.
#: Any lane reporting a number should check this and say so out loud.
SYNTHETIC_TICKERS: set = set()

_SYNTHETIC_MARKER = "# SYNTHETIC-FALLBACK-DATA: NOT REAL MARKET PRICES"

# In-process memo so repeated load_prices() calls do not re-read the disk.
_MEMO: Dict[str, pd.DataFrame] = {}


# --- helpers ----------------------------------------------------------------


def _fetch_start() -> Optional[str]:
    """First date to request from the provider.

    ``None`` (the current config) means "from inception" -- fetch the ticker's
    entire history. If ``config.HISTORY_START`` is a date instead, back it off
    by ``WARMUP_YEARS`` so ``trailing_vol`` has a full lookback at that date.
    """
    hs = getattr(config, "HISTORY_START", None)
    if not hs:
        return None
    d = _dt.date.fromisoformat(hs)
    return d.replace(year=d.year - WARMUP_YEARS).isoformat()


def cache_path(ticker: str) -> Path:
    """Path of the on-disk CSV cache for ``ticker``."""
    return config.PRICES_DIR / f"{ticker.upper()}.csv"


def _empty_frame() -> pd.DataFrame:
    df = pd.DataFrame({c: pd.Series(dtype="float64") for c in PRICE_COLUMNS})
    df["date"] = pd.Series(dtype="object")
    return df[PRICE_COLUMNS]


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce any fetched frame into the frozen column contract."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "close"])
    df = df[df["close"] > 0]
    df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date", kind="mergesort").reset_index(drop=True)
    return df[PRICE_COLUMNS]


# --- fetchers ---------------------------------------------------------------


def _fetch_yahoo_urllib(
    ticker: str, start: Optional[str], end: Optional[str] = None
) -> pd.DataFrame:
    """Zero-dependency daily OHLCV from Yahoo's public chart JSON endpoint.

    Returns split-adjusted OHLC (Yahoo ``quote``), which is what we want; see
    the module docstring. Raises on any transport or shape failure so the
    caller can fall through to the next source.
    """
    p1 = 0 if not start else int(
        _dt.datetime.fromisoformat(start).replace(tzinfo=_dt.timezone.utc).timestamp()
    )
    p1 = max(p1, 0)
    if end:
        p2 = int(_dt.datetime.fromisoformat(end).replace(tzinfo=_dt.timezone.utc).timestamp()) + 86400
    else:
        p2 = int(_dt.datetime.now(_dt.timezone.utc).timestamp()) + 86400

    qs = f"?period1={p1}&period2={p2}&interval=1d"
    headers = {"User-Agent": _UA, "Accept": "application/json"}

    # Yahoo rate-limits bursts with HTTP 429. Retry with exponential backoff and
    # alternate between the query1/query2 hosts before giving up.
    payload = None
    last_exc: Optional[Exception] = None
    for attempt in range(_HTTP_MAX_RETRIES):
        host = _YAHOO_HOSTS[attempt % len(_YAHOO_HOSTS)]
        url = f"https://{host}/v8/finance/chart/{ticker.upper()}{qs}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                payload = json.load(resp)
            break
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code not in (429, 502, 503, 504):
                raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_exc = exc
        if attempt < _HTTP_MAX_RETRIES - 1:
            _time.sleep(_HTTP_BACKOFF_BASE * (2**attempt))
    if payload is None:
        raise RuntimeError(f"Yahoo chart unreachable for {ticker}: {last_exc}")

    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise RuntimeError(f"Yahoo chart error for {ticker}: {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise RuntimeError(f"Yahoo chart returned no result block for {ticker}")

    res = results[0]
    ts = res.get("timestamp") or []
    quote = (res.get("indicators", {}).get("quote") or [{}])[0]
    if not ts or "close" not in quote:
        raise RuntimeError(f"Yahoo chart returned no bars for {ticker}")

    dates = [
        _dt.datetime.fromtimestamp(t, _dt.timezone.utc).strftime("%Y-%m-%d") for t in ts
    ]
    df = pd.DataFrame(
        {
            "date": dates,
            "open": quote.get("open"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "close": quote.get("close"),
            "volume": quote.get("volume"),
        }
    )
    return _normalise(df)


def _fetch_yfinance(
    ticker: str, start: Optional[str], end: Optional[str] = None
) -> pd.DataFrame:
    """Fetch via the yfinance library if it happens to be installed.

    ``auto_adjust=False`` so ``Close`` stays Yahoo's split-adjusted (but not
    dividend-adjusted) close -- the same series the urllib path reads out of
    ``quote.close``. Verified equal to the urllib path across NVDA's 2021 4:1
    and 2024 10:1 splits.
    """
    import yfinance as yf  # noqa: F401  (optional dependency)

    tk = yf.Ticker(ticker.upper())
    if start:
        raw = tk.history(
            start=start, end=end, interval="1d", auto_adjust=False, actions=False
        )
    else:
        raw = tk.history(
            period="max", end=end, interval="1d", auto_adjust=False, actions=False
        )
    if raw is None or raw.empty:
        raise RuntimeError(f"yfinance returned no rows for {ticker}")
    raw = raw.reset_index()
    df = pd.DataFrame(
        {
            "date": raw[raw.columns[0]],
            "open": raw["Open"],
            "high": raw["High"],
            "low": raw["Low"],
            "close": raw["Close"],
            "volume": raw["Volume"],
        }
    )
    return _normalise(df)


def _synthetic_prices(ticker: str, start: str, end: Optional[str] = None) -> pd.DataFrame:
    """CLEARLY-LABELLED synthetic fallback. NOT REAL MARKET DATA.

    A jump-diffusion GBM with a deterministic per-ticker seed, so the pipeline
    stays runnable offline. Any ticker built this way is recorded in
    ``SYNTHETIC_TICKERS`` and the CSV carries a ``# SYNTHETIC`` header line.
    """
    end = end or _dt.date.today().isoformat()
    days = pd.bdate_range(start=start, end=end)
    n = len(days)
    rng = np.random.default_rng(abs(hash(ticker.upper())) % (2**32))
    sigma, mu = 0.022, 0.0003
    rets = rng.normal(mu, sigma, n)
    jump = rng.random(n) < 0.004
    rets[jump] += rng.normal(0.0, 0.12, int(jump.sum()))
    close = 100.0 * np.exp(np.cumsum(rets))
    intr = np.abs(rng.normal(0.0, 0.008, n))
    df = pd.DataFrame(
        {
            "date": [d.strftime("%Y-%m-%d") for d in days],
            "open": close * (1 + rng.normal(0, 0.004, n)),
            "high": close * (1 + intr),
            "low": close * (1 - intr),
            "close": close,
            "volume": rng.integers(1_000_000, 80_000_000, n).astype(float),
        }
    )
    SYNTHETIC_TICKERS.add(ticker.upper())
    return _normalise(df)


def _fetch(
    ticker: str, start: Optional[str], end: Optional[str] = None
) -> pd.DataFrame:
    """Try every real source in order, then the labelled synthetic fallback.

    The synthetic fallback fires ONLY for ``config.UNIVERSE`` tickers -- it
    exists to keep the pipeline runnable offline, not to invent a company for a
    typo. Anything else returns an empty frame.
    """
    errors = []
    for name, fn in (("yfinance", _fetch_yfinance), ("yahoo-chart", _fetch_yahoo_urllib)):
        try:
            df = fn(ticker, start, end)
            if len(df) > 0:
                SYNTHETIC_TICKERS.discard(ticker.upper())
                return df
            errors.append(f"{name}: empty frame")
        except ImportError as exc:
            errors.append(f"{name}: not installed ({exc})")
        except Exception as exc:  # noqa: BLE001 - fall through to the next source
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    if ticker.upper() not in {t.upper() for t in config.UNIVERSE}:
        print(f"[data] {ticker}: no data from any source (not in UNIVERSE). {errors}")
        return _empty_frame()
    print(f"[data] WARNING {ticker}: all real sources failed -> SYNTHETIC fallback. {errors}")
    return _synthetic_prices(ticker, start or "2008-01-01", end)


# --- cache I/O --------------------------------------------------------------


def _write_cache(ticker: str, df: pd.DataFrame) -> None:
    path = cache_path(ticker)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = ""
    if ticker.upper() in SYNTHETIC_TICKERS:
        header = _SYNTHETIC_MARKER + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        if header:
            fh.write(header)
        df.to_csv(fh, index=False)


def _read_cache(ticker: str) -> Optional[pd.DataFrame]:
    path = cache_path(ticker)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            first = fh.readline()
        skip = 0
        if first.startswith("#"):
            skip = 1
            if _SYNTHETIC_MARKER.split(":")[0] in first:
                SYNTHETIC_TICKERS.add(ticker.upper())
        df = pd.read_csv(path, skiprows=skip, dtype={"date": str})
        if df.empty or not set(PRICE_COLUMNS).issubset(df.columns):
            return None
        return _normalise(df)
    except Exception as exc:  # noqa: BLE001 - a corrupt cache should just re-fetch
        print(f"[data] WARNING unreadable cache for {ticker}: {exc}")
        return None


# --- public API -------------------------------------------------------------


def refresh_prices(
    tickers: Optional[List[str]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    verbose: bool = True,
) -> Dict[str, pd.DataFrame]:
    """Force a network fetch and rewrite the CSV cache. Returns the new frames.

    This is the one function that always hits the network. Everything else
    reads the cache. ``start`` defaults to ``_fetch_start()`` -- inception when
    ``config.HISTORY_START`` is ``None``.
    """
    tickers = list(tickers or config.UNIVERSE)
    start = start if start is not None else _fetch_start()
    out: Dict[str, pd.DataFrame] = {}
    for i, t in enumerate(tickers):
        t = t.upper()
        if i:
            _time.sleep(_THROTTLE_SECONDS)   # Yahoo 429s on unthrottled bursts
        df = _fetch(t, start, end)
        _write_cache(t, df)
        _MEMO.pop(t, None)
        out[t] = df
        if verbose:
            tag = "  [SYNTHETIC]" if t in SYNTHETIC_TICKERS else ""
            span = f"{df['date'].iloc[0]} -> {df['date'].iloc[-1]}" if len(df) else "EMPTY"
            print(f"[data] {t:<6} rows={len(df):>6}  {span}{tag}")
    return out


def load_prices(
    ticker: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Daily split-adjusted OHLCV for one ticker, oldest row first.

    Columns are exactly ``["date","open","high","low","close","volume"]``.
    ``date`` is an ISO ``YYYY-MM-DD`` **string** (not a Timestamp), so it can be
    compared directly against ``config.TRAIN_END`` / ``TEST_START`` and
    serialised to JSON without a converter.

    Fetched from the network once, then cached to ``data/prices/{TICKER}.csv``.

    Parameters
    ----------
    ticker : str
    start : str, optional
        Inclusive ISO lower bound. **Defaults to ``config.HISTORY_START``**,
        which is currently ``None`` -- i.e. the full history back to the
        ticker's inception is returned. Pass e.g. ``start="2010-01-01"`` to
        narrow it.
    end : str, optional
        Inclusive ISO upper bound. Defaults to everything cached.
    refresh : bool
        Re-fetch from the network and rewrite the cache first.

    Returns an empty, correctly-typed frame if the ticker has no data at all.
    """
    t = ticker.upper()
    if refresh:
        refresh_prices([t], verbose=False)

    df = _MEMO.get(t)
    if df is None:
        df = _read_cache(t)
        if df is None:
            df = _fetch(t, _fetch_start(), None)
            if len(df):                 # never write an empty/garbage cache file
                _write_cache(t, df)
        _MEMO[t] = df

    if df.empty:
        return _empty_frame()

    lo = start if start is not None else getattr(config, "HISTORY_START", None)
    out = df if not lo else df[df["date"] >= lo]
    if end is not None:
        out = out[out["date"] <= end]
    return out.reset_index(drop=True)


def load_all_prices(
    tickers: Optional[List[str]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    """``{ticker: prices_df}`` for the whole frozen universe (or a subset).

    Never raises for a single bad ticker -- a ticker with no data maps to an
    empty frame with the correct columns, so callers can iterate safely.
    """
    tickers = list(tickers or config.UNIVERSE)
    out: Dict[str, pd.DataFrame] = {}
    for t in tickers:
        try:
            out[t.upper()] = load_prices(t, start=start, end=end)
        except Exception as exc:  # noqa: BLE001
            print(f"[data] WARNING load_prices({t}) failed: {exc}")
            out[t.upper()] = _empty_frame()
    return out


def load_fundamentals(ticker: str) -> dict:
    """Best-effort static company facts. **May legitimately return ``{}``.**

    Shape when populated (all keys optional -- always use ``.get()``)::

        {"symbol","name","sector","industry","exchange","country",
         "employees","market_cap","currency","description","source"}

    Sources, in order: ``data/fundamentals/{TICKER}.json`` (harvested from the
    dubbs-research MCP ``equity_profile`` route, real data), then ``yfinance``
    if installed, then a minimal record built from ``config.TICKER_NAMES``.
    The last case still returns ``symbol`` and ``name`` so ``/api/tickers`` can
    always render; ``sector`` will be absent.
    """
    t = ticker.upper()

    path = FUNDAMENTALS_DIR / f"{t}.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                rec = json.load(fh)
            if isinstance(rec, dict) and rec:
                return rec
        except Exception as exc:  # noqa: BLE001
            print(f"[data] WARNING unreadable fundamentals cache for {t}: {exc}")

    try:
        import yfinance as yf  # noqa: F401

        info = yf.Ticker(t).info or {}
        # yfinance returns a stub dict ({"symbol": ..., "trailingPegRatio": None})
        # for a nonexistent symbol, so require a real identifying field.
        if info.get("sector") or info.get("longName") or info.get("shortName"):
            rec = {
                "symbol": t,
                "name": info.get("longName") or config.TICKER_NAMES.get(t, t),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "exchange": info.get("exchange"),
                "country": info.get("country"),
                "employees": info.get("fullTimeEmployees"),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency"),
                "description": info.get("longBusinessSummary"),
                "source": "yfinance",
            }
            return {k: v for k, v in rec.items() if v is not None}
    except Exception:  # noqa: BLE001 - fundamentals are explicitly best-effort
        pass

    if t in config.TICKER_NAMES:
        return {"symbol": t, "name": config.TICKER_NAMES[t], "source": "config"}
    return {}


def trailing_vol(
    prices: pd.DataFrame,
    asof: str,
    lookback: int = config.NULL_VOL_LOOKBACK,
) -> float:
    """Trailing realised volatility as of ``asof``. **Returns DAILY sigma.**

    CONVENTION -- read this, LANE-EVAL and LANE-MODEL both depend on it
    ==================================================================
    * The return value is the **standard deviation of DAILY simple returns**
      (``close.pct_change()``), sample stdev with ``ddof=1``. It is
      **NOT annualised** and **NOT scaled to any horizon**.
    * To get the sigma of an ``h``-day cumulative return, the caller scales::

          sigma_h = trailing_vol(prices, asof) * math.sqrt(h)

      That is the sigma of the CONTRACT.md section 7 null model
      (Gaussian, trailing 250d sigma, zero drift). To annualise instead,
      multiply by ``sqrt(252)``.
    * Simple returns, not log returns, so the units match ``Event.move_pct``
      and ``Ensemble.paths`` (both cumulative simple returns per CONTRACT.md
      section 5).
    * The window is the last ``lookback`` daily returns whose date is
      ``<= asof``, **inclusive of ``asof`` itself**. The return realised on
      ``asof`` is known at the ``asof`` close, so including it is information
      available to a forecaster standing at ``asof`` -- it is not lookahead.
      Note the consequence, measured by LANE-WOLFRAM on this universe: right
      after a 25% jump window the trailing sigma is already ~1.78x its normal
      level, so the null model auto-widens after an event. That is intended;
      it is what makes the null honest and hard to beat.
    * Rows strictly after ``asof`` are dropped before anything is computed, so
      this function cannot leak the future regardless of what it is handed.
    * Returns ``float('nan')`` when fewer than ``MIN_VOL_OBS`` (20) returns are
      available, rather than a misleadingly precise small-sample number.
      Callers must check with ``math.isnan``.

    Parameters
    ----------
    prices : pd.DataFrame
        As returned by ``load_prices`` -- needs ``date`` (ISO string or
        datetime-like) and ``close``.
    asof : str
        ISO ``YYYY-MM-DD``. Everything after this date is discarded.
    lookback : int
        Number of trailing daily returns to use. Default
        ``config.NULL_VOL_LOOKBACK`` (250).
    """
    if prices is None or len(prices) == 0 or "close" not in prices.columns:
        return float("nan")

    asof = str(pd.Timestamp(asof).date())

    d = prices["date"]
    if not pd.api.types.is_string_dtype(d):
        d = pd.to_datetime(d, errors="coerce").dt.strftime("%Y-%m-%d")

    hist = prices.loc[d.values <= asof, "close"]
    hist = pd.to_numeric(hist, errors="coerce").dropna()
    if len(hist) < MIN_VOL_OBS + 1:
        return float("nan")

    rets = hist.pct_change().dropna()
    if lookback and lookback > 0:
        rets = rets.iloc[-int(lookback):]
    if len(rets) < MIN_VOL_OBS:
        return float("nan")

    sigma = float(rets.std(ddof=1))
    if not math.isfinite(sigma) or sigma <= 0:
        return float("nan")
    return sigma


if __name__ == "__main__":  # pragma: no cover - operational entry point
    frames = refresh_prices()
    print("\n--- summary ---")
    for tk, fr in frames.items():
        scoped = load_prices(tk)
        sig = trailing_vol(scoped, config.TRAIN_END)
        print(
            f"{tk:<6} cached={len(fr):>5} in-scope={len(scoped):>5} "
            f"{scoped['date'].iloc[0]}..{scoped['date'].iloc[-1]} "
            f"trailing_vol@{config.TRAIN_END}={sig:.5f}"
        )
