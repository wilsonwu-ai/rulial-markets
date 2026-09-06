"""
LANE-API  --  FastAPI surface for rulial-markets.

Implements EXACTLY the five routes frozen in CONTRACT.md section 6:

    GET  /api/health
    GET  /api/tickers
    GET  /api/events?ticker=NVDA
    POST /api/forecast
    GET  /api/backtest?ticker=NVDA

Design rules this module obeys (they matter on a hackathon stage):

1.  **Nothing sibling-owned is imported at module scope.** `rulial.data`,
    `rulial.events`, `rulial.news`, `rulial.generator` and `rulial.evaluate` are
    imported lazily *inside* the route handlers and wrapped in try/except, so
    this app boots -- and `/api/health` answers -- even while another lane is
    mid-write or outright broken.

2.  **No route raises to the client.** Every handler degrades to a clearly
    flagged empty/`unavailable` payload with HTTP 200. An empty state on stage
    beats a stack trace on stage. The only shape-preserving exception: the two
    list routes (`/api/tickers`, `/api/events`) still return a JSON *array*, as
    the contract requires, and signal degradation via the
    `X-Rulial-Unavailable` / `X-Rulial-Reason` response headers so the frontend
    never has to type-check `Array.isArray`.

3.  **Synthetic fallbacks are labelled in the payload, never silent.**
    If `rulial.generator` is unavailable, `/api/forecast` returns a Gaussian
    placeholder ensemble with `fallback=true` and a narrative that says so in
    capital letters. It is never presented as a model output.
"""
from __future__ import annotations

import dataclasses
import importlib
import logging
import math
import statistics
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

# --- frozen, parent-owned modules: safe to import at module scope ------------
try:  # pragma: no cover - trivial path selection
    from . import config as cfg
    from . import types as rtypes
    _PKG = __package__ or "rulial"
except ImportError:  # pragma: no cover - executed only when run as a loose script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from rulial import config as cfg  # type: ignore
    from rulial import types as rtypes  # type: ignore
    _PKG = "rulial"

log = logging.getLogger("rulial.api")

API_VERSION = "0.1.0"
MAX_N_PATHS = 20000          # stage guard: never let a body DoS the demo
SIBLINGS = ("data", "events", "news", "generator", "evaluate")

# Static sector labels (public, factual classification -- used only when
# LANE-DATA's load_fundamentals() cannot supply one).
_SECTORS = {
    "NVDA": "Information Technology", "AAPL": "Information Technology",
    "MSFT": "Information Technology", "AMZN": "Consumer Discretionary",
    "TSLA": "Consumer Discretionary", "META": "Communication Services",
    "GOOGL": "Communication Services", "JPM": "Financials",
    "XOM": "Energy", "BA": "Industrials",
}


# ===========================================================================
# Response models (CONTRACT.md section 5 / 6)
# ===========================================================================
class _Lenient(BaseModel):
    model_config = ConfigDict(extra="ignore")


class ArticleModel(_Lenient):
    url: str = ""
    title: str = ""
    published: str = ""
    source: str = ""
    snippet: str = ""


class EventModel(_Lenient):
    ticker: str = ""
    date: str = ""
    move_pct: float = 0.0
    direction: str = ""
    window_days: int = cfg.WINDOW_DAYS
    headline: str = ""
    articles: List[ArticleModel] = Field(default_factory=list)
    tier: str = "significant"   # CONTRACT.md s3: "major" (>=25%) | "significant" (>=15%)
    famous: bool = False
    # INTEGRATOR, additive: researched cause text + category for this window.
    # Empty string when the event was never researched (96 of 329).
    context: str = ""
    category: str = ""


class TickerModel(_Lenient):
    symbol: str
    name: str = ""
    sector: str = ""
    has_data: bool = False
    n_events: int = 0


class EnsembleModel(_Lenient):
    ticker: str = ""
    as_of_date: str = ""
    horizon_days: int = cfg.DEFAULT_HORIZON_DAYS
    paths: List[float] = Field(default_factory=list)
    quantiles: Dict[str, float] = Field(default_factory=dict)
    mean: float = 0.0
    std: float = 0.0
    analogs: List[EventModel] = Field(default_factory=list)
    narrative: str = ""


class ScoreModel(_Lenient):
    crps: float
    crps_null: float
    crps_lift: float
    pit: float
    actual_return: float
    z_score: float


class ForecastRequestModel(_Lenient):
    ticker: str
    event_text: str = ""
    as_of_date: str = cfg.TRAIN_END
    horizon_days: int = cfg.DEFAULT_HORIZON_DAYS
    n_paths: int = cfg.DEFAULT_N_PATHS


class ForecastResponse(_Lenient):
    ensemble: Optional[EnsembleModel] = None
    score: Optional[ScoreModel] = None
    unavailable: bool = False
    fallback: bool = False
    error: Optional[str] = None
    notes: List[str] = Field(default_factory=list)
    leakage_disclosure: str = ""


class PerEventModel(_Lenient):
    date: str = ""
    crps: Optional[float] = None
    crps_null: Optional[float] = None
    crps_lift: Optional[float] = None
    z_score: Optional[float] = None
    tier: Optional[str] = None
    famous: Optional[bool] = None


class BacktestResponse(_Lenient):
    ticker: str = ""
    n_tests: int = 0
    mean_crps_lift: Optional[float] = None
    pit_histogram: List[int] = Field(default_factory=lambda: [0] * 10)
    calibration_ok: Optional[bool] = None
    per_event: List[PerEventModel] = Field(default_factory=list)
    unavailable: bool = False
    error: Optional[str] = None
    notes: List[str] = Field(default_factory=list)


class HealthResponse(_Lenient):
    ok: bool = True
    version: str = API_VERSION
    modules: Dict[str, bool] = Field(default_factory=dict)
    module_errors: Dict[str, str] = Field(default_factory=dict)


LEAKAGE_DISCLOSURE = (
    "Any LLM in this pipeline has read the post-2019 world. Cutting input data at "
    f"{cfg.TRAIN_END} does not cut the weights. We therefore report lift over a null "
    "model rather than raw accuracy, test obscure events alongside famous ones and "
    "report them separately, and say so here, in the product. See CONTRACT.md s8."
)


# ===========================================================================
# Lazy sibling import + defensive coercion helpers
# ===========================================================================
def _safe_import(name: str):
    """Import a sibling lane module. Returns (module | None, error_str | None)."""
    try:
        return importlib.import_module(f"{_PKG}.{name}"), None
    except Exception as exc:  # noqa: BLE001 - deliberately catching everything
        log.warning("lazy import of %s.%s failed: %s", _PKG, name, exc)
        return None, f"{type(exc).__name__}: {exc}"


def _to_dict(obj: Any) -> Optional[dict]:
    """Coerce a dataclass / pydantic model / dict / plain object into a dict."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return dict(obj)
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        try:
            return dataclasses.asdict(obj)
        except Exception:  # noqa: BLE001
            pass
    for attr in ("model_dump", "dict", "to_dict", "_asdict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                out = fn()
                if isinstance(out, dict):
                    return out
            except Exception:  # noqa: BLE001
                continue
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return None


def _try_call(fn: Callable, arg_variants: List[tuple]) -> tuple[Any, Optional[str]]:
    """Call fn with the first argument tuple that does not raise TypeError.

    Sibling lanes are being written concurrently; their exact signatures are
    only pinned by the contract's export list, not by keyword name. We try a
    few shapes rather than hard-failing the whole route.
    """
    last_err = None
    for args in arg_variants:
        try:
            return fn(*args), None
        except TypeError as exc:
            last_err = f"TypeError: {exc}"
            continue
        except Exception as exc:  # noqa: BLE001
            return None, f"{type(exc).__name__}: {exc}"
    return None, last_err or "no signature matched"


def _flatten_paths(raw: Any) -> List[float]:
    """Contract says paths is list[float] of cumulative returns. Tolerate a
    list of trajectories by taking each trajectory's terminal value."""
    out: List[float] = []
    if raw is None:
        return out
    try:
        seq = list(raw)
    except TypeError:
        return out
    for item in seq:
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            v = float(item)
            if math.isfinite(v):
                out.append(v)
        else:
            try:
                sub = [float(x) for x in item]
            except (TypeError, ValueError):
                continue
            if sub and math.isfinite(sub[-1]):
                out.append(sub[-1])
    return out


def _quantiles(paths: List[float]) -> Dict[str, float]:
    if not paths:
        return {}
    s = sorted(paths)
    n = len(s)

    def q(p: float) -> float:
        idx = min(n - 1, max(0, int(round(p * (n - 1)))))
        return float(s[idx])

    return {"p5": q(0.05), "p25": q(0.25), "p50": q(0.50), "p75": q(0.75), "p95": q(0.95)}


def _coerce_ensemble(obj: Any, req: ForecastRequestModel) -> Optional[EnsembleModel]:
    d = _to_dict(obj)
    if d is None:
        return None
    paths = _flatten_paths(d.get("paths"))
    quant = d.get("quantiles") or {}
    if not isinstance(quant, dict) or not quant:
        quant = _quantiles(paths)
    quant = {str(k): float(v) for k, v in quant.items()
             if isinstance(v, (int, float)) and math.isfinite(float(v))}
    mean = d.get("mean")
    std = d.get("std")
    if mean is None or not isinstance(mean, (int, float)) or not math.isfinite(float(mean)):
        mean = statistics.fmean(paths) if paths else 0.0
    if std is None or not isinstance(std, (int, float)) or not math.isfinite(float(std)):
        std = statistics.pstdev(paths) if len(paths) > 1 else 0.0
    analogs: List[EventModel] = []
    for a in (d.get("analogs") or []):
        ad = _to_dict(a)
        if not ad:
            continue
        ad["articles"] = [x for x in (_to_dict(y) for y in (ad.get("articles") or [])) if x]
        try:
            analogs.append(EventModel(**ad))
        except Exception:  # noqa: BLE001 - drop an unparseable analog, keep the rest
            continue
    try:
        return EnsembleModel(
            ticker=str(d.get("ticker") or req.ticker),
            as_of_date=str(d.get("as_of_date") or req.as_of_date),
            horizon_days=int(d.get("horizon_days") or req.horizon_days),
            paths=paths,
            quantiles=quant,
            mean=float(mean),
            std=float(std),
            analogs=analogs,
            narrative=str(d.get("narrative") or ""),
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("ensemble coercion failed: %s", exc)
        return None


def _coerce_event(obj: Any) -> Optional[EventModel]:
    d = _to_dict(obj)
    if not d:
        return None
    d = dict(d)
    arts = []
    for a in (d.get("articles") or []):
        ad = _to_dict(a)
        if ad:
            try:
                arts.append(ArticleModel(**ad))
            except Exception:  # noqa: BLE001
                continue
    d["articles"] = arts
    try:
        return EventModel(**d)
    except Exception:  # noqa: BLE001
        return None


# ===========================================================================
# Price helpers (read-only use of LANE-DATA; degrade to None, never raise)
# ===========================================================================
_PRICE_MEMO: Dict[str, Any] = {}


def _price_cache_exists(ticker: str) -> bool:
    return any((cfg.PRICES_DIR / f"{ticker}{ext}").exists()
               for ext in (".csv", ".parquet", ".pkl"))


_DF_MEMO: Dict[str, Any] = {}


def _prices_df(ticker: str):
    """Return (price DataFrame, None) or (None, reason).

    CACHE ONLY by default. `rulial.data.load_prices()` falls back to a live
    Yahoo fetch with retry/backoff when its CSV cache is cold, which can block a
    request for a minute or more -- unacceptable inside an HTTP handler during a
    live demo. So we refuse to call it unless the ticker is already cached on
    disk. Set RULIAL_ALLOW_FETCH=1 to permit network loads (dev only).
    """
    if ticker in _DF_MEMO:
        return _DF_MEMO[ticker]

    import os
    allow_fetch = os.environ.get("RULIAL_ALLOW_FETCH", "").lower() in ("1", "true", "yes")
    if not _price_cache_exists(ticker) and not allow_fetch:
        return None, (f"no cached price file for {ticker} in {cfg.PRICES_DIR}; refusing a "
                      "live fetch inside a request handler (run the LANE-DATA build, or "
                      "set RULIAL_ALLOW_FETCH=1)")

    data_mod, err = _safe_import("data")
    if data_mod is None:
        return None, f"rulial.data unavailable ({err})"
    loader = getattr(data_mod, "load_prices", None)
    if not callable(loader):
        return None, "rulial.data.load_prices missing"
    df, err = _try_call(loader, [(ticker,)])
    if df is None:
        return None, f"load_prices('{ticker}') failed: {err}"
    _DF_MEMO[ticker] = (df, None)
    return _DF_MEMO[ticker]


def _closes(ticker: str):
    """Return ((dates, closes), None) or (None, reason). Cache-only, memoized."""
    if ticker in _PRICE_MEMO:
        return _PRICE_MEMO[ticker]
    df, err = _prices_df(ticker)
    if df is None:
        return None, err
    try:
        cols = {str(c).lower(): c for c in df.columns}
        close_col = next((cols[k] for k in ("close", "adj_close", "adjclose", "adj close")
                          if k in cols), None)
        if close_col is None:
            return None, "no close column in price frame"
        if "date" in cols:
            dates = [str(x)[:10] for x in df[cols["date"]].tolist()]
        else:
            dates = [str(x)[:10] for x in df.index.tolist()]
        closes = [float(x) for x in df[close_col].tolist()]
        if not dates or len(dates) != len(closes):
            return None, "price frame malformed"
        _PRICE_MEMO[ticker] = ((dates, closes), None)
        return _PRICE_MEMO[ticker]
    except Exception as exc:  # noqa: BLE001
        return None, f"price frame parse failed: {type(exc).__name__}: {exc}"


def _index_asof(dates: List[str], as_of: str) -> Optional[int]:
    idx = None
    for i, d in enumerate(dates):
        if d <= as_of:
            idx = i
        else:
            break
    return idx


def _actual_forward_return(ticker: str, as_of: str, horizon: int):
    """Realized cumulative return over `horizon` trading days after as_of."""
    got, err = _closes(ticker)
    if got is None:
        return None, err
    dates, closes = got
    i = _index_asof(dates, as_of)
    if i is None:
        return None, f"no price on or before {as_of}"
    j = i + int(horizon)
    if j >= len(closes):
        return None, "horizon extends past available price history (future date)"
    if closes[i] == 0:
        return None, "zero base price"
    return (closes[j] / closes[i] - 1.0), None


def _trailing_sigma(ticker: str, as_of: str, horizon: int):
    """Trailing-250d daily sigma scaled to the horizon (CONTRACT s7 null shape)."""
    got, err = _closes(ticker)
    if got is None:
        return None, err
    dates, closes = got
    i = _index_asof(dates, as_of)
    if i is None or i < 20:
        return None, "insufficient history for trailing sigma"
    lb = cfg.NULL_VOL_LOOKBACK
    win = closes[max(0, i - lb): i + 1]
    rets = [win[k] / win[k - 1] - 1.0 for k in range(1, len(win)) if win[k - 1]]
    if len(rets) < 20:
        return None, "insufficient returns for trailing sigma"
    return statistics.pstdev(rets) * math.sqrt(max(1, int(horizon))), None


# ===========================================================================
# App
# ===========================================================================
app = FastAPI(
    title="rulial-markets API",
    version=API_VERSION,
    description="Conditional event -> ensemble of forward return paths, scored by "
                "CRPS against a trailing-volatility null. See CONTRACT.md.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _degrade(response: Response, reason: str) -> None:
    response.headers["X-Rulial-Unavailable"] = "true"
    response.headers["X-Rulial-Reason"] = reason[:400].replace("\n", " ")


# --------------------------------------------------------------------------
# GET /api/health
# --------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Always 200, always ok:true. Reports sibling-module status as a bonus."""
    mods: Dict[str, bool] = {}
    errs: Dict[str, str] = {}
    for name in SIBLINGS:
        mod, err = _safe_import(name)
        mods[name] = mod is not None
        if err:
            errs[name] = err[:300]
    return HealthResponse(ok=True, version=API_VERSION, modules=mods, module_errors=errs)


# --------------------------------------------------------------------------
# GET /api/tickers
# --------------------------------------------------------------------------
@app.get("/api/tickers", response_model=List[TickerModel])
def tickers(response: Response) -> List[TickerModel]:
    """The frozen 10-ticker universe, annotated with data/event availability.

    Never empty: the universe comes from the frozen config, so this route
    answers correctly even with every sibling lane broken.
    """
    counts, cerr = _event_counts()
    if cerr:
        _degrade(response, cerr)

    # load_fundamentals() may hit the network on a cold cache; only call it for
    # tickers whose profile is already on disk.
    fundamentals = None
    fund_dir = cfg.DATA_DIR / "fundamentals"
    data_mod, _ = _safe_import("data")
    if data_mod is not None:
        fundamentals = getattr(data_mod, "load_fundamentals", None)

    out: List[TickerModel] = []
    for sym in cfg.UNIVERSE:
        sector = _SECTORS.get(sym, "")
        name = cfg.TICKER_NAMES.get(sym, sym)
        has_data = (cfg.PRICES_DIR / f"{sym}.csv").exists() or \
                   (cfg.PRICES_DIR / f"{sym}.parquet").exists()
        if callable(fundamentals) and (fund_dir / f"{sym}.json").exists():
            f, _ = _try_call(fundamentals, [(sym,)])
            fd = _to_dict(f) or {}
            sector = str(fd.get("sector") or sector)
            name = str(fd.get("name") or fd.get("long_name") or name)
        if not has_data:
            got, _ = _closes(sym)
            has_data = got is not None
        out.append(TickerModel(
            symbol=sym, name=name, sector=sector,
            has_data=bool(has_data), n_events=int(counts.get(sym, 0)),
        ))
    return out


# --------------------------------------------------------------------------
# GET /api/events
# --------------------------------------------------------------------------
def _load_ledger() -> tuple[List[dict], Optional[str]]:
    """Train-period event ledger. Prefers the on-disk jsonl the LANE-EVENTS
    build step writes; falls back to calling detect_events() live."""
    rows: List[dict] = []
    path = cfg.EVENTS_PATH
    if path.exists():
        try:
            import json
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:  # noqa: BLE001 - skip a bad line, keep the file
                        continue
                    if isinstance(obj, list):
                        rows.extend([o for o in obj if isinstance(o, dict)])
                    elif isinstance(obj, dict):
                        rows.append(obj)
            if rows:
                return rows, None
        except Exception as exc:  # noqa: BLE001
            return [], f"ledger read failed: {type(exc).__name__}: {exc}"
    return [], f"event ledger not found at {path} (LANE-EVENTS has not built it yet)"


def _event_counts() -> tuple[Dict[str, int], Optional[str]]:
    rows, err = _load_ledger()
    counts: Dict[str, int] = {}
    for r in rows:
        d = str(r.get("date", ""))[:10]
        if d and d > cfg.TRAIN_END:
            continue
        t = str(r.get("ticker", ""))
        if t:
            counts[t] = counts.get(t, 0) + 1
    return counts, err


@app.get("/api/events", response_model=List[EventModel])
def events(response: Response, ticker: str = Query(..., description="e.g. NVDA")) -> List[EventModel]:
    """Seed ledger for one ticker, TRAIN PERIOD ONLY (date <= TRAIN_END).

    Returns `[]` (never an error object) so the frontend can render an empty
    state; degradation is signalled in X-Rulial-Unavailable / X-Rulial-Reason.
    Six of ten universe tickers legitimately have zero train events at the
    frozen 25%/5d threshold -- an empty list here is a real answer, not a bug.
    """
    sym = (ticker or "").strip().upper()
    if sym not in cfg.UNIVERSE:
        _degrade(response, f"'{sym}' is not in the frozen universe {cfg.UNIVERSE}")
        return []

    rows, err = _load_ledger()
    if err and not rows:
        # Fallback: build this ticker's events live from prices.
        ev_mod, ev_err = _safe_import("events")
        det = getattr(ev_mod, "detect_events", None) if ev_mod else None
        if callable(det):
            data_mod, _ = _safe_import("data")
            loader = getattr(data_mod, "load_prices", None) if data_mod else None
            if callable(loader):
                df, lerr = _try_call(loader, [(sym,)])
                if df is not None:
                    live, derr = _try_call(det, [(df,), (df, sym), (sym, df)])
                    if live:
                        rows = [d for d in (_to_dict(x) for x in live) if d]
                        for r in rows:
                            r.setdefault("ticker", sym)
                        err = None
                    else:
                        err = f"{err}; live detect_events failed: {derr}"
                else:
                    err = f"{err}; load_prices failed: {lerr}"
            else:
                err = f"{err}; rulial.data.load_prices unavailable"
        else:
            err = f"{err}; rulial.events unavailable ({ev_err})"

    if err:
        _degrade(response, err)

    out: List[EventModel] = []
    for r in rows:
        if str(r.get("ticker", "")).upper() != sym:
            continue
        d = str(r.get("date", ""))[:10]
        if not d or d > cfg.TRAIN_END:      # FROZEN leak guard, CONTRACT s2
            continue
        m = _coerce_event(r)
        if m is not None:
            out.append(m)
    out.sort(key=lambda e: e.date)
    return out


# --------------------------------------------------------------------------
# POST /api/forecast
# --------------------------------------------------------------------------
def _fallback_ensemble(req: ForecastRequestModel, notes: List[str]) -> EnsembleModel:
    """CLEARLY LABELLED synthetic placeholder. Not a model output.

    Used only when rulial.generator cannot be imported or called. Draws a
    zero-drift Gaussian at the trailing-250d sigma -- i.e. deliberately the
    NULL model itself, so it can never look better than the null it is scored
    against.
    """
    import random
    sigma, serr = _trailing_sigma(req.ticker, req.as_of_date, req.horizon_days)
    if sigma is None:
        sigma = 0.40 / math.sqrt(252) * math.sqrt(max(1, req.horizon_days))
        notes.append(f"trailing sigma unavailable ({serr}); used a hardcoded 40% "
                     "annualized placeholder volatility")
    rng = random.Random(f"{req.ticker}|{req.as_of_date}|{req.horizon_days}")
    n = max(100, min(int(req.n_paths or cfg.DEFAULT_N_PATHS), MAX_N_PATHS))
    paths = [rng.gauss(0.0, sigma) for _ in range(n)]
    return EnsembleModel(
        ticker=req.ticker, as_of_date=req.as_of_date, horizon_days=req.horizon_days,
        paths=paths, quantiles=_quantiles(paths),
        mean=statistics.fmean(paths), std=statistics.pstdev(paths), analogs=[],
        narrative=("SYNTHETIC FALLBACK -- NOT A MODEL OUTPUT. rulial.generator is "
                   "unavailable, so this is a zero-drift Gaussian at trailing-250d "
                   "volatility (the null model itself), shown purely so the interface "
                   "has a shape to render. It reads no event text and carries no "
                   "forecasting content."),
    )


def _score(ens: EnsembleModel, req: ForecastRequestModel,
           notes: List[str]) -> Optional[ScoreModel]:
    """Score the ensemble iff the actual is already known. Never raises."""
    actual, aerr = _actual_forward_return(req.ticker, req.as_of_date, req.horizon_days)
    if actual is None:
        notes.append(f"score omitted: {aerr}")
        return None

    ev_mod, ev_err = _safe_import("evaluate")
    if ev_mod is None:
        notes.append(f"score omitted: rulial.evaluate unavailable ({ev_err})")
        return None

    df, derr = _prices_df(req.ticker)
    if df is None:
        notes.append(f"null baseline needs prices: {derr}")

    # 1) preferred: the lane exposes a one-shot scorer that also builds the null
    for nm in ("score_event", "score_ensemble", "score"):
        fn = getattr(ev_mod, nm, None)
        if not callable(fn):
            continue
        variants = []
        if df is not None:
            variants += [
                (ens.paths, actual, df, req.as_of_date, req.horizon_days),
                (ens, actual, df, req.as_of_date, req.horizon_days),
                (ens.paths, actual, df),
                (ens, actual, df),
            ]
        variants += [(ens.paths, actual), (ens, actual)]
        res, serr = _try_call(fn, variants)
        d = _to_dict(res)
        if d and d.get("crps") is not None and d.get("crps_null") is not None:
            try:
                d.setdefault("crps_lift", (d["crps_null"] - d["crps"]) / d["crps_null"]
                             if d["crps_null"] else 0.0)
                d.setdefault("actual_return", actual)
                d.setdefault("pit", 0.5)
                d.setdefault("z_score",
                             (actual - ens.mean) / ens.std if ens.std else 0.0)
                return ScoreModel(**{k: d[k] for k in
                                     ("crps", "crps_null", "crps_lift", "pit",
                                      "actual_return", "z_score")})
            except Exception as exc:  # noqa: BLE001
                notes.append(f"{nm}() result not coercible: {exc}")
        elif serr:
            notes.append(f"{nm}() failed: {serr}")

    # 2) assemble from the contract's primitives
    crps_fn = getattr(ev_mod, "crps", None)
    if not callable(crps_fn):
        notes.append("score omitted: rulial.evaluate.crps missing")
        return None
    crps_model, cerr = _try_call(crps_fn, [(ens, actual), (ens.paths, actual)])
    if crps_model is None:
        notes.append(f"score omitted: crps() failed ({cerr})")
        return None

    crps_null = None
    null_fn = getattr(ev_mod, "null_ensemble", None)
    if callable(null_fn):
        null_variants = []
        if df is not None:
            null_variants += [
                (df, req.as_of_date, req.horizon_days, len(ens.paths) or req.n_paths),
                (df, req.as_of_date, req.horizon_days),
                (df, req.as_of_date),
            ]
        null_variants += [
            (req.ticker, req.as_of_date, req.horizon_days),
            (req.ticker, req.as_of_date),
        ]
        null_obj, nerr = _try_call(null_fn, null_variants)
        if null_obj is not None:
            null_paths = _flatten_paths((_to_dict(null_obj) or {}).get("paths")) \
                if _to_dict(null_obj) else _flatten_paths(null_obj)
            crps_null, _ = _try_call(crps_fn, [(null_obj, actual), (null_paths, actual)])
        else:
            notes.append(f"null_ensemble() failed ({nerr})")
    if crps_null is None:
        notes.append("score omitted: crps_null could not be computed and CONTRACT s7 "
                     "forbids reporting CRPS without the null baseline")
        return None

    pit_val = 0.5
    pit_fn = getattr(ev_mod, "pit", None)
    if callable(pit_fn):
        p, _ = _try_call(pit_fn, [(ens, actual), (ens.paths, actual)])
        if isinstance(p, (int, float)) and math.isfinite(float(p)):
            pit_val = float(p)
    elif ens.paths:
        pit_val = sum(1 for x in ens.paths if x < actual) / len(ens.paths)

    try:
        crps_model = float(crps_model)
        crps_null = float(crps_null)
        lift = (crps_null - crps_model) / crps_null if crps_null else 0.0
        z = (actual - ens.mean) / ens.std if ens.std else 0.0
        return ScoreModel(crps=crps_model, crps_null=crps_null, crps_lift=lift,
                          pit=pit_val, actual_return=float(actual), z_score=float(z))
    except Exception as exc:  # noqa: BLE001
        notes.append(f"score omitted: assembly failed ({type(exc).__name__}: {exc})")
        return None


@app.post("/api/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequestModel) -> ForecastResponse:
    """Conditional event text -> ensemble of forward return paths (+ score when
    the actual is already known). Degrades to a labelled synthetic ensemble
    rather than erroring."""
    notes: List[str] = []
    req = ForecastRequestModel(
        ticker=(req.ticker or "").strip().upper(),
        event_text=req.event_text or "",
        as_of_date=(req.as_of_date or cfg.TRAIN_END)[:10],
        horizon_days=max(1, min(int(req.horizon_days or cfg.DEFAULT_HORIZON_DAYS), 60)),
        n_paths=max(100, min(int(req.n_paths or cfg.DEFAULT_N_PATHS), MAX_N_PATHS)),
    )
    if req.ticker not in cfg.UNIVERSE:
        return ForecastResponse(
            unavailable=True,
            error=f"'{req.ticker}' is not in the frozen universe {cfg.UNIVERSE}",
            leakage_disclosure=LEAKAGE_DISCLOSURE,
        )

    ens: Optional[EnsembleModel] = None
    fallback = False
    gen_mod, gerr = _safe_import("generator")
    gen_fn = getattr(gen_mod, "generate_ensemble", None) if gen_mod else None
    if callable(gen_fn):
        native = None
        try:
            native = rtypes.ForecastRequest(
                ticker=req.ticker, event_text=req.event_text, as_of_date=req.as_of_date,
                horizon_days=req.horizon_days, n_paths=req.n_paths,
            )
        except Exception as exc:  # noqa: BLE001
            notes.append(f"could not build native ForecastRequest: {exc}")
        variants = [(native,)] if native is not None else []
        variants.append((req.model_dump(),))
        raw, rerr = _try_call(gen_fn, variants)
        if raw is not None:
            ens = _coerce_ensemble(raw, req)
            if ens is None:
                notes.append("generator returned an object this API could not coerce "
                             "into the contract Ensemble shape")
        else:
            notes.append(f"generate_ensemble() failed: {rerr}")
    else:
        notes.append(f"rulial.generator unavailable ({gerr or 'generate_ensemble missing'})")

    if ens is None or not ens.paths:
        ens = _fallback_ensemble(req, notes)
        fallback = True

    score = None
    try:
        score = _score(ens, req, notes)
    except Exception as exc:  # noqa: BLE001 - scoring must never kill a demo
        notes.append(f"score omitted: unexpected {type(exc).__name__}: {exc}")
        log.warning("scoring blew up:\n%s", traceback.format_exc())

    return ForecastResponse(
        ensemble=ens, score=score, unavailable=False, fallback=fallback,
        error=None, notes=notes, leakage_disclosure=LEAKAGE_DISCLOSURE,
    )


# --------------------------------------------------------------------------
# GET /api/backtest
# --------------------------------------------------------------------------
def _hist10(values: List[float]) -> List[int]:
    h = [0] * 10
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(f):
            continue
        b = min(9, max(0, int(f * 10)))
        h[b] += 1
    return h


@app.get("/api/backtest", response_model=BacktestResponse)
def backtest(response: Response, ticker: str = Query(..., description="e.g. NVDA")) -> BacktestResponse:
    """Walk-forward evaluation over the TEST window. n_tests == 0 is a real,
    expected answer for several tickers at the frozen threshold -- it is
    returned as an empty result, not an error."""
    sym = (ticker or "").strip().upper()
    notes: List[str] = []
    if sym not in cfg.UNIVERSE:
        return BacktestResponse(ticker=sym, unavailable=True,
                                error=f"'{sym}' is not in the frozen universe {cfg.UNIVERSE}")

    ev_mod, ev_err = _safe_import("evaluate")
    wf = getattr(ev_mod, "walk_forward", None) if ev_mod else None
    if not callable(wf):
        _degrade(response, ev_err or "walk_forward missing")
        return BacktestResponse(
            ticker=sym, unavailable=True,
            error=f"rulial.evaluate.walk_forward unavailable ({ev_err or 'not exported yet'})",
            notes=["backtest will populate once LANE-EVAL lands walk_forward()"],
        )

    raw, rerr = _try_call(wf, [(sym,), (), (sym, cfg.TEST_START)])
    if raw is None:
        _degrade(response, rerr or "walk_forward failed")
        return BacktestResponse(ticker=sym, unavailable=True,
                                error=f"walk_forward('{sym}') failed: {rerr}")

    d = _to_dict(raw)
    if d is None and isinstance(raw, (list, tuple)):
        d = {"per_event": list(raw)}
    if d is None:
        return BacktestResponse(ticker=sym, unavailable=True,
                                error="walk_forward returned an uncoercible object")

    # walk_forward may return a universe-wide dict keyed by ticker
    if sym in d and isinstance(d.get(sym), dict):
        d = d[sym]

    per_raw = d.get("per_event") or d.get("per_events") or d.get("events") or []
    per: List[PerEventModel] = []
    for r in per_raw:
        rd = _to_dict(r)
        if not rd:
            continue
        if rd.get("ticker") and str(rd["ticker"]).upper() != sym:
            continue
        rd["date"] = str(rd.get("date", ""))[:10]
        try:
            per.append(PerEventModel(**rd))
        except Exception:  # noqa: BLE001
            continue

    n_tests = d.get("n_tests")
    if not isinstance(n_tests, int):
        n_tests = len(per)

    lift = d.get("mean_crps_lift")
    if not isinstance(lift, (int, float)) or (isinstance(lift, float) and not math.isfinite(lift)):
        lifts = [p.crps_lift for p in per if isinstance(p.crps_lift, (int, float))]
        lift = statistics.fmean(lifts) if lifts else None

    hist = d.get("pit_histogram")
    if not (isinstance(hist, (list, tuple)) and len(hist) == 10):
        pits: List[float] = []
        for r in per_raw:
            rd = _to_dict(r) or {}
            if isinstance(rd.get("pit"), (int, float)):
                pits.append(float(rd["pit"]))
        hist = _hist10(pits)
    hist = [int(x) for x in hist]

    calib = d.get("calibration_ok")
    if not isinstance(calib, bool):
        calib = None
        notes.append("calibration_ok not supplied by walk_forward()")
    if n_tests == 0:
        notes.append(f"{sym} has zero test-window events at the frozen "
                     f"{cfg.JUMP_THRESHOLD:.0%}/{cfg.WINDOW_DAYS}d definition. "
                     "This is an empty result, not a failure.")
    if 0 < n_tests < 30:
        notes.append(f"n_tests={n_tests}: per-ticker PIT calibration is statistically "
                     "underpowered at this sample size; treat calibration_ok as "
                     "indicative and prefer the pooled universe verdict.")
    for k in ("mean_crps_lift_demeaned", "notes", "warning"):
        if d.get(k) is not None and k != "notes":
            notes.append(f"{k}={d[k]}")
    if isinstance(d.get("notes"), list):
        notes.extend(str(x) for x in d["notes"])

    return BacktestResponse(ticker=sym, n_tests=int(n_tests), mean_crps_lift=lift,
                            pit_histogram=hist, calibration_ok=calib, per_event=per,
                            unavailable=False, error=None, notes=notes)


# ===========================================================================
# POST /api/scenario  -- the inverse (CONTRACT.md s6b, "Pavel's inversion")
# ===========================================================================
#
# Owned by LANE-INVERSE. This is the ONLY block this lane added to api.py.
#
# The endpoint's whole reason to exist is that `achieved_prob` is COMPUTED --
# `rulial.inverse` runs each candidate event text back through
# `generator.generate_ensemble` and measures the fraction of paths moving in
# the requested direction. This route does no probability arithmetic of its
# own; it serialises what the solver measured. `verified` is never set here.
# If the solver returns nothing, the response carries an empty `scenarios`
# list, a null `best_error`, and a `note` explaining why -- never a filled-in
# placeholder number.
class ScenarioRequestModel(_Lenient):
    ticker: str
    direction: str = "down"                        # "up" | "down"
    target_prob: float = 0.75                      # clamped to 0.50 .. 0.95
    as_of_date: str = cfg.TRAIN_END
    horizon_days: int = cfg.DEFAULT_HORIZON_DAYS
    n_candidates: int = 3


class ScenarioModel(_Lenient):
    event_text: str = ""
    achieved_prob: float = 0.0     # COMPUTED by the forward model, never asserted
    error: float = 0.0             # |achieved - target|
    quantiles: Dict[str, float] = Field(default_factory=dict)
    analogs_used: List[EventModel] = Field(default_factory=list)
    narrative: str = ""
    verified: bool = False         # true ONLY when generate_ensemble actually ran


class ScenarioResponse(_Lenient):
    target_prob: float = 0.0
    direction: str = "down"
    ticker: str = ""
    scenarios: List[ScenarioModel] = Field(default_factory=list)
    # CONTRACT.md s6b types this `float`. It is Optional here so that "nothing
    # was verified" can be reported as null instead of a fabricated 0.0 or 1.0.
    best_error: Optional[float] = None
    search_iterations: int = 0
    note: str = ""
    unavailable: bool = False
    error: Optional[str] = None
    leakage_disclosure: str = ""


@app.post("/api/scenario", response_model=ScenarioResponse)
def scenario(req: ScenarioRequestModel) -> ScenarioResponse:
    """Target probability -> candidate events that produce it, each VERIFIED.

    Degrades to a well-formed empty result with an explanatory `note` rather
    than raising, exactly like /api/forecast.
    """
    ticker = (req.ticker or "").strip().upper()
    direction = (req.direction or "down").strip().lower()
    as_of = (req.as_of_date or cfg.TRAIN_END)[:10]
    horizon = max(1, min(int(req.horizon_days or cfg.DEFAULT_HORIZON_DAYS), 60))
    n_cand = max(1, min(int(req.n_candidates or 3), 8))

    if ticker not in cfg.UNIVERSE:
        return ScenarioResponse(
            target_prob=float(req.target_prob or 0.0), direction=direction, ticker=ticker,
            unavailable=True,
            error=f"'{ticker}' is not in the frozen universe {cfg.UNIVERSE}",
            note="No scenarios generated: ticker outside the frozen universe.",
            leakage_disclosure=LEAKAGE_DISCLOSURE,
        )

    inv_mod, ierr = _safe_import("inverse")
    solve = getattr(inv_mod, "solve_inverse", None) if inv_mod else None
    if not callable(solve):
        return ScenarioResponse(
            target_prob=float(req.target_prob or 0.0), direction=direction, ticker=ticker,
            unavailable=True,
            error=f"rulial.inverse unavailable ({ierr or 'solve_inverse missing'})",
            note="The inverse solver could not be imported, so nothing was verified and no "
                 "probability is reported.",
            leakage_disclosure=LEAKAGE_DISCLOSURE,
        )

    try:
        native = inv_mod.ScenarioRequest(          # type: ignore[attr-defined]
            ticker=ticker, direction=direction, target_prob=float(req.target_prob),
            as_of_date=as_of, horizon_days=horizon, n_candidates=n_cand,
        )
        result = solve(native)
    except Exception as exc:  # noqa: BLE001 - a demo must degrade, not 500
        log.warning("solve_inverse blew up:\n%s", traceback.format_exc())
        return ScenarioResponse(
            target_prob=float(req.target_prob or 0.0), direction=direction, ticker=ticker,
            unavailable=False,
            error=f"solve_inverse() failed: {type(exc).__name__}: {exc}",
            note="The inverse search raised, so no candidate was verified and no probability "
                 "is reported. `scenarios` is empty rather than filled with a placeholder.",
            leakage_disclosure=LEAKAGE_DISCLOSURE,
        )

    d = _to_dict(result) or {}
    scen: List[ScenarioModel] = []
    for raw in (d.get("scenarios") or []):
        sd = _to_dict(raw) or {}
        analogs = [a for a in (_coerce_event(x) for x in (sd.get("analogs_used") or []))
                   if a is not None]
        try:
            achieved = float(sd.get("achieved_prob"))
            err = float(sd.get("error"))
        except (TypeError, ValueError):
            continue                     # a candidate with no measured number is dropped
        scen.append(ScenarioModel(
            event_text=str(sd.get("event_text", "")),
            achieved_prob=achieved,
            error=err,
            quantiles={str(k): float(v) for k, v in (sd.get("quantiles") or {}).items()
                       if isinstance(v, (int, float))},
            analogs_used=analogs,
            narrative=str(sd.get("narrative", "")),
            verified=bool(sd.get("verified", False)),
        ))

    best = d.get("best_error")
    best = float(best) if isinstance(best, (int, float)) else None

    return ScenarioResponse(
        target_prob=float(d.get("target_prob", req.target_prob or 0.0)),
        direction=str(d.get("direction", direction)),
        ticker=str(d.get("ticker", ticker)),
        scenarios=scen,
        best_error=best,
        search_iterations=int(d.get("search_iterations", 0) or 0),
        note=str(d.get("note", "")),
        unavailable=False,
        error=None,
        leakage_disclosure=LEAKAGE_DISCLOSURE,
    )
