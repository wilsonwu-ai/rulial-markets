"""
backend/rulial/evaluate.py -- LANE-EVAL.

Scoring and calibration. This module is the defensibility argument of the whole
project, so every number it produces is either (a) checkable against a closed
form, or (b) explicitly labelled as unverified / synthetic.

Frozen commitments honoured here (CONTRACT.md sections 7 and 8):

  * CRPS is the primary metric.
  * ``crps_null`` (Gaussian, trailing NULL_VOL_LOOKBACK daily sigma, zero drift)
    is computed and returned on EVERY scored event and in EVERY aggregate.
    There is no code path that removes it.
  * ``crps_lift`` is the headline.
  * Directional hit-rate is computed only by
    :func:`appendix_directional_hit_rate` and is filed in walk_forward's output
    under the key ``appendix``. It is never promoted to a top-level field.
  * Leakage disclosure: walk_forward always returns famous/obscure breakdowns
    and a ``disclosures`` block for the UI and PRD to render.

Estimator notes (these matter -- getting them wrong invalidates every number):

  * The ensemble CRPS uses the FAIR (unbiased, Ferro 2014) estimator by
    default::

        CRPS = mean_i |x_i - y|  -  1/(2 m (m-1)) * sum_i sum_j |x_i - x_j|

    The commonly-seen NRG plug-in divides the pairwise term by 2 m^2 instead
    and is badly biased at small m (it is *upward* biased, i.e. it makes an
    ensemble look worse than it is).  ``crps(..., fair=False)`` gives the NRG
    form; ``test_evaluate.py`` measures the bias of both against the analytic
    Gaussian CRPS.
  * The pairwise term is evaluated in O(m log m) via the sorted identity
        sum_i sum_j |x_i - x_j| = 2 * sum_{i=1..m} (2i - m - 1) * x_(i)
    (1-indexed, x sorted ascending).  At n_paths=2000 the naive double loop is
    a 4,000,000-element matrix per event.
  * ``crps_null`` is computed from the CLOSED FORM Gaussian CRPS, not by
    sampling the null.  Sampling both sides with a finite m introduces an
    estimator asymmetry that shows up directly in ``crps_lift``.
  * PIT inside walk_forward is the RANDOMIZED PIT, ``(#{x < y} + U) / (m + 1)``,
    with U drawn from a seed derived deterministically from (ticker, date).
    The mid-rank convention puts a spurious spike in the histogram because the
    discrete PIT grid does not align with 10 equal bins.  Randomized is flat at
    any m and is still fully reproducible.

Dependencies on other lanes are LATE-BOUND and OPTIONAL.  ``data.load_prices``,
``events.detect_events`` and ``generator.generate_ensemble`` are imported inside
functions, and every one of them has a labelled fallback so this module runs and
is testable on its own.  Nothing here touches the network at import time.
"""

from __future__ import annotations

import hashlib
import math
import warnings
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .config import (
    DEFAULT_HORIZON_DAYS,
    DEFAULT_N_PATHS,
    EMBARGO_DAYS,
    JUMP_THRESHOLD,
    NULL_VOL_LOOKBACK,
    TEST_END,
    TEST_START,
    TIER_MAJOR,
    TIER_SIGNIFICANT,
    TRAIN_END,
    WINDOW_DAYS,
    tier_for,
)
from .types import Ensemble, Event, ForecastRequest, Score

__all__ = [
    "crps",
    "crps_nrg",
    "crps_gaussian",
    "null_sigma",
    "null_ensemble",
    "pit",
    "pit_histogram",
    "calibration_test",
    "z_score",
    "score_event",
    "walk_forward",
    "walk_forward_universe",
    "appendix_directional_hit_rate",
    "MIN_CALIBRATION_N",
    "PIT_BINS",
]

# A per-ticker walk-forward has roughly a dozen test events.  A KS test on 12
# PIT values rejects a 2x-too-narrow ensemble only ~30% of the time, so a
# per-ticker `calibration_ok = true` at that n is close to meaningless.  We
# still report it (the API shape is per-ticker) but we flag it as underpowered
# and expose walk_forward_universe() for the pooled verdict.
MIN_CALIBRATION_N = 30
PIT_BINS = 10

_EPS = 1e-12


# --------------------------------------------------------------------------- #
# small input adapters -- other lanes' exact object shapes are not final yet
# --------------------------------------------------------------------------- #
def _as_paths(obj: Any) -> np.ndarray:
    """Accept an Ensemble, a list/array of returns, or anything with .paths."""
    if obj is None:
        raise ValueError("paths is None")
    if isinstance(obj, Ensemble):
        arr = np.asarray(obj.paths, dtype=float)
    elif hasattr(obj, "paths") and not isinstance(obj, (list, tuple, np.ndarray)):
        arr = np.asarray(obj.paths, dtype=float)
    else:
        arr = np.asarray(obj, dtype=float).ravel()
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError("ensemble contains no finite paths")
    return arr


def _close_series(prices: Any):
    """Coerce whatever LANE-DATA hands us into a date-indexed close series.

    Accepts a DataFrame with a close-ish column (index datetime, or a
    date/Date/datetime column), or a Series already indexed by date.
    """
    import pandas as pd  # local: keep import-time cost off the API boot path

    if prices is None:
        raise ValueError("prices is None")
    if isinstance(prices, pd.Series):
        s = prices.copy()
    elif isinstance(prices, pd.DataFrame):
        df = prices.copy()
        lower = {str(c).lower(): c for c in df.columns}
        for cand in ("date", "datetime", "timestamp", "index"):
            if cand in lower and not isinstance(df.index, pd.DatetimeIndex):
                df = df.set_index(lower[cand])
                break
        col = None
        for cand in ("adj_close", "adj close", "adjclose", "close", "c", "price"):
            if cand in lower:
                col = lower[cand]
                break
        if col is None:
            num = df.select_dtypes("number")
            if num.shape[1] == 0:
                raise ValueError("no numeric close column found in prices")
            col = num.columns[-1]
        s = df[col]
    else:
        raise TypeError(f"unsupported prices type {type(prices)!r}")

    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    s = s.astype(float).sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s.dropna()


# --------------------------------------------------------------------------- #
# CRPS
# --------------------------------------------------------------------------- #
def _pairwise_abs_sum(x_sorted: np.ndarray) -> float:
    """sum_i sum_j |x_i - x_j| in O(m log m) given ascending-sorted x.

    Identity (1-indexed):  sum_i sum_j |x_i - x_j| = 2 * sum_i (2i - m - 1) x_(i)
    Verified against the naive double sum in test_evaluate.py.
    """
    m = x_sorted.size
    if m < 2:
        return 0.0
    i = np.arange(1, m + 1, dtype=float)
    return float(2.0 * np.dot(2.0 * i - m - 1.0, x_sorted))


def crps(paths: Any, actual: float, fair: bool = True) -> float:
    """Sample-based ensemble CRPS.  Lower is better.  Units = return units.

    ``paths``  : list[float] of simulated cumulative returns, or an Ensemble.
    ``actual`` : the realized cumulative return over the same horizon.
    ``fair``   : True  -> unbiased Ferro estimator, pairwise term / (2 m (m-1))
                 False -> NRG plug-in,             pairwise term / (2 m^2)

    Both terms are computed exactly; the only approximation is Monte Carlo
    sampling of the ensemble itself.
    """
    x = np.sort(_as_paths(paths))
    y = float(actual)
    m = x.size
    term1 = float(np.mean(np.abs(x - y)))
    if m < 2:
        return term1
    s = _pairwise_abs_sum(x)
    denom = 2.0 * m * (m - 1) if fair else 2.0 * m * m
    return term1 - s / denom


def crps_nrg(paths: Any, actual: float) -> float:
    """The biased NRG plug-in, exposed for comparison/tests only."""
    return crps(paths, actual, fair=False)


def crps_gaussian(mu: float, sigma: float, y: float) -> float:
    """Closed-form CRPS of N(mu, sigma^2) against observation y.

        CRPS = sigma * [ z (2 Phi(z) - 1) + 2 phi(z) - 1/sqrt(pi) ],  z=(y-mu)/sigma

    Special case used as the test anchor: mu=0, sigma=1, y=0 gives
        2 phi(0) - 1/sqrt(pi) = 2/sqrt(2 pi) - 1/sqrt(pi) = (sqrt(2) - 1)/sqrt(pi)
        ~= 0.2337
    """
    sigma = float(sigma)
    if sigma <= 0:
        return abs(float(y) - float(mu))
    z = (float(y) - float(mu)) / sigma
    phi = math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    Phi = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return sigma * (z * (2.0 * Phi - 1.0) + 2.0 * phi - 1.0 / math.sqrt(math.pi))


# --------------------------------------------------------------------------- #
# the null model -- FROZEN, may not be removed (CONTRACT.md s7)
# --------------------------------------------------------------------------- #
def null_sigma(
    prices: Any,
    asof: str,
    horizon: int = DEFAULT_HORIZON_DAYS,
    lookback: int = NULL_VOL_LOOKBACK,
) -> float:
    """Horizon-scaled sigma of the frozen null: trailing `lookback` daily simple
    returns, strictly at or before `asof`, scaled by sqrt(horizon).

    Uses ddof=1.  Raises if fewer than 20 usable observations exist, because a
    sigma estimated on <20 points is not a baseline, it is noise.
    """
    import pandas as pd

    s = _close_series(prices)
    cutoff = pd.Timestamp(asof)
    hist = s[s.index <= cutoff]
    if hist.size < 21:
        raise ValueError(
            f"only {hist.size} price observations at or before {asof}; "
            "need >= 21 to estimate the null sigma"
        )
    rets = hist.pct_change().dropna().to_numpy()
    win = rets[-int(lookback):] if rets.size > lookback else rets
    if win.size < 20:
        raise ValueError(f"only {win.size} returns available for the null sigma at {asof}")
    daily = float(np.std(win, ddof=1))
    return daily * math.sqrt(float(horizon))


def null_ensemble(
    prices: Any,
    asof: str,
    horizon: int = DEFAULT_HORIZON_DAYS,
    n_paths: int = DEFAULT_N_PATHS,
    seed: int = 0,
) -> List[float]:
    """FROZEN null model: Gaussian, ZERO drift, trailing NULL_VOL_LOOKBACK daily
    vol scaled to the horizon.  Returns a list of simulated cumulative returns.

    Sampled form, for the UI and for apples-to-apples estimator comparisons.
    Scoring uses :func:`crps_gaussian` on the same sigma instead, to avoid a
    finite-m estimator asymmetry leaking into ``crps_lift``.
    """
    sigma = null_sigma(prices, asof, horizon=horizon)
    rng = np.random.default_rng(int(seed))
    return [float(v) for v in rng.normal(0.0, sigma, int(n_paths))]


# --------------------------------------------------------------------------- #
# PIT and calibration
# --------------------------------------------------------------------------- #
def _pit_seed(*parts: Any) -> int:
    h = hashlib.md5("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def pit(paths: Any, actual: float, seed: Optional[int] = None) -> float:
    """Probability integral transform of ``actual`` under the ensemble, in [0,1].

    seed is None (default)  -> deterministic:  (#{x<y} + 0.5 #{x==y}) / m
                               i.e. the literal "fraction of paths below actual".
    seed is an int          -> randomized PIT: (#{x<y} + U (1 + #{x==y})) / (m+1)
                               with U ~ Uniform(0,1) from that seed.

    Use the randomized form for calibration histograms (walk_forward does).  The
    deterministic form is fine for a single-event display number.
    """
    x = _as_paths(paths)
    y = float(actual)
    m = x.size
    below = int(np.count_nonzero(x < y))
    ties = int(np.count_nonzero(x == y))
    if seed is None:
        return float(min(1.0, max(0.0, (below + 0.5 * ties) / m)))
    u = float(np.random.default_rng(int(seed)).random())
    return float(min(1.0, max(0.0, (below + u * (1.0 + ties)) / (m + 1.0))))


def pit_histogram(pits: Sequence[float], bins: int = PIT_BINS) -> List[int]:
    """Counts of PIT values in ``bins`` equal-width buckets over [0, 1].

    A flat histogram is the win condition (CONTRACT.md s7).  Always returns a
    list of length ``bins``, all zeros when there is nothing to bin.
    """
    bins = int(bins)
    if bins < 1:
        raise ValueError("bins must be >= 1")
    arr = np.asarray([p for p in pits if p is not None], dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return [0] * bins
    arr = np.clip(arr, 0.0, 1.0)
    idx = np.minimum((arr * bins).astype(int), bins - 1)
    return [int(c) for c in np.bincount(idx, minlength=bins)]


def calibration_test(pits: Sequence[float], bins: int = PIT_BINS) -> Dict[str, Any]:
    """Flatness test of the PIT values against Uniform(0,1), with real p-values.

    Returns Kolmogorov-Smirnov (primary), Cramer-von Mises (secondary, more
    sensitive to central mass) and a chi-square on the binned histogram.

    ``calibration_ok`` is True when we FAIL to reject uniformity at alpha=0.05.
    That is a "no evidence of miscalibration" verdict, not proof of calibration:
    ``underpowered`` is True whenever n < MIN_CALIBRATION_N, and at n = 0 the
    verdict is None rather than a flattering True.
    """
    arr = np.asarray([p for p in pits if p is not None], dtype=float)
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    out: Dict[str, Any] = {
        "n": n,
        "test": "kolmogorov-smirnov vs Uniform(0,1)",
        "alpha": 0.05,
        "ks_stat": None,
        "ks_pvalue": None,
        "cvm_stat": None,
        "cvm_pvalue": None,
        "chi2_stat": None,
        "chi2_pvalue": None,
        "histogram": pit_histogram(arr, bins=bins),
        "mean_pit": None,
        "calibration_ok": None,
        "underpowered": True,
        "min_n_for_power": MIN_CALIBRATION_N,
        "power_note": (
            "LOW POWER WARNING: a KS test on ~12 PIT values has only ~30% power "
            "against a 2x-too-narrow ensemble. Treat a per-ticker "
            "calibration_ok as indicative; the pooled universe verdict from "
            "walk_forward_universe() is the statistically meaningful one."
        ),
    }
    if n == 0:
        return out

    arr = np.clip(arr, _EPS, 1.0 - _EPS)
    out["mean_pit"] = float(np.mean(arr))
    out["underpowered"] = n < MIN_CALIBRATION_N

    try:
        from scipy import stats as _st

        ks = _st.kstest(arr, "uniform")
        out["ks_stat"], out["ks_pvalue"] = float(ks.statistic), float(ks.pvalue)
        try:
            cvm = _st.cramervonmises(arr, "uniform")
            out["cvm_stat"], out["cvm_pvalue"] = float(cvm.statistic), float(cvm.pvalue)
        except Exception:  # pragma: no cover - scipy version differences
            pass
        counts = np.asarray(out["histogram"], dtype=float)
        if n >= bins:
            expected = np.full(bins, n / bins, dtype=float)
            chi2 = float(np.sum((counts - expected) ** 2 / expected))
            out["chi2_stat"] = chi2
            out["chi2_pvalue"] = float(_st.chi2.sf(chi2, bins - 1))
    except ImportError:  # pragma: no cover - scipy is in requirements
        d = _ks_stat_uniform(arr)
        out["ks_stat"] = d
        out["ks_pvalue"] = _ks_pvalue_asymptotic(d, n)
        out["test"] += " (asymptotic p-value; scipy unavailable)"

    if out["ks_pvalue"] is not None:
        out["calibration_ok"] = bool(out["ks_pvalue"] >= 0.05)
    return out


def _ks_stat_uniform(arr: np.ndarray) -> float:
    x = np.sort(arr)
    n = x.size
    i = np.arange(1, n + 1, dtype=float)
    return float(max(np.max(i / n - x), np.max(x - (i - 1) / n)))


def _ks_pvalue_asymptotic(d: float, n: int) -> float:
    """Kolmogorov distribution survival function, series form."""
    lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
    if lam <= 0:
        return 1.0
    total = 0.0
    for k in range(1, 101):
        total += ((-1.0) ** (k - 1)) * math.exp(-2.0 * (k**2) * lam * lam)
    return float(min(1.0, max(0.0, 2.0 * total)))


# --------------------------------------------------------------------------- #
# z-score -- the literal "by how many standard deviations" answer
# --------------------------------------------------------------------------- #
def z_score(ensemble: Any, actual: float) -> float:
    """(actual - ensemble mean) / ensemble std.  Accepts an Ensemble or a list.

    Uses the Ensemble's own reported mean/std when present (so the UI and the
    eval cannot silently disagree), otherwise computes them from the paths.
    """
    if isinstance(ensemble, Ensemble) or (
        hasattr(ensemble, "paths") and hasattr(ensemble, "std")
    ):
        mu = getattr(ensemble, "mean", None)
        sd = getattr(ensemble, "std", None)
        if (mu is None or sd is None or not np.isfinite(sd)
                or sd <= _EPS * max(1.0, abs(float(mu or 0.0)))):
            x = _as_paths(ensemble)
            mu, sd = float(np.mean(x)), float(np.std(x, ddof=1))
    else:
        x = _as_paths(ensemble)
        mu, sd = float(np.mean(x)), float(np.std(x, ddof=1))
    # A constant ensemble has sd on the order of float noise, not zero; a
    # relative threshold is what actually catches it.
    if sd is None or not np.isfinite(sd) or sd <= _EPS * max(1.0, abs(float(mu))):
        return float("nan")
    return float((float(actual) - float(mu)) / float(sd))


# --------------------------------------------------------------------------- #
# single-event scoring -> the frozen Score type
# --------------------------------------------------------------------------- #
def score_event(
    model_paths: Any,
    actual: float,
    prices: Any = None,
    asof: Optional[str] = None,
    horizon: int = DEFAULT_HORIZON_DAYS,
    null_sigma_override: Optional[float] = None,
    pit_seed: Optional[int] = None,
) -> Score:
    """Score one ensemble against one realized return.  Returns the frozen Score.

    ``crps_null`` comes from the closed-form Gaussian at the frozen null sigma;
    it is never optional.  Supply either (prices, asof) or null_sigma_override.
    """
    x = _as_paths(model_paths)
    y = float(actual)
    if null_sigma_override is not None:
        sig = float(null_sigma_override)
    else:
        if prices is None or asof is None:
            raise ValueError("score_event needs (prices, asof) or null_sigma_override")
        sig = null_sigma(prices, asof, horizon=horizon)

    c_model = crps(x, y)
    c_null = crps_gaussian(0.0, sig, y)
    lift = (c_null - c_model) / c_null if c_null > _EPS else float("nan")
    return Score(
        crps=float(c_model),
        crps_null=float(c_null),
        crps_lift=float(lift),
        pit=float(pit(x, y, seed=pit_seed)),
        actual_return=y,
        z_score=float(z_score(x, y)),
    )


# --------------------------------------------------------------------------- #
# appendix only -- CONTRACT.md s7 forbids this as a headline
# --------------------------------------------------------------------------- #
def appendix_directional_hit_rate(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """APPENDIX METRIC. NOT A HEADLINE. FROZEN by CONTRACT.md section 7.

    A directional hit-rate makes a coin flip look skilled: on a corpus with any
    drift at all, "always up" scores well above 50% while carrying no
    information.  Reported only so a reader can see we did not hide it, and
    always next to the base rate it must beat.
    """
    hits, n, up = 0, 0, 0
    for r in rows:
        med = r.get("median")
        act = r.get("actual_return")
        if med is None or act is None:
            continue
        n += 1
        up += int(act > 0)
        hits += int((med > 0) == (act > 0))
    if n == 0:
        return {"n": 0, "hit_rate": None, "base_rate_always_up": None,
                "label": "APPENDIX -- not a headline metric (CONTRACT.md s7)"}
    return {
        "n": n,
        "hit_rate": hits / n,
        "base_rate_always_up": up / n,
        "label": "APPENDIX -- not a headline metric (CONTRACT.md s7)",
        "warning": (
            "Compare hit_rate to base_rate_always_up, not to 0.50. A corpus with "
            "drift rewards a constant call."
        ),
    }


# --------------------------------------------------------------------------- #
# walk-forward evaluation
# --------------------------------------------------------------------------- #
def _load_prices(ticker: str, prices: Any = None):
    """Real prices from LANE-DATA when available; otherwise a CLEARLY LABELLED
    synthetic GBM series so the code path stays runnable.  Returns
    (close_series, source_label).
    """
    if prices is not None:
        return _close_series(prices), "injected"
    try:
        from . import data as _data  # LANE-DATA

        close = _close_series(_data.load_prices(ticker))
        # LANE-DATA flags its own synthetic fallback. Consult that flag rather
        # than trusting the loader -- a synthetic series that scores well is the
        # single easiest way for this project to fool itself.
        synth = getattr(_data, "SYNTHETIC_TICKERS", set())
        if str(ticker).upper() in {str(t).upper() for t in synth}:
            warnings.warn(
                f"[LANE-EVAL] data.load_prices({ticker}) returned LANE-DATA's "
                "labelled SYNTHETIC fallback. Every number derived from this run "
                "is NOT REAL.",
                RuntimeWarning,
                stacklevel=2,
            )
            return close, "SYNTHETIC_FALLBACK(data.py)"
        return close, "data.load_prices"
    except Exception as exc:  # noqa: BLE001
        warnings.warn(
            f"[LANE-EVAL] data.load_prices({ticker}) unavailable ({exc!r}); "
            "falling back to SYNTHETIC prices. Any number derived from this is "
            "NOT REAL.",
            RuntimeWarning,
            stacklevel=2,
        )
        return _synthetic_prices(ticker), "SYNTHETIC_FALLBACK"


def _synthetic_prices(ticker: str, start: str = "2005-01-03", n: int = 5200):
    """SYNTHETIC. Labelled everywhere it is used. Fat-tailed, vol-clustering
    GBM-ish series purely so the pipeline is exercisable with no data on disk."""
    import pandas as pd

    rng = np.random.default_rng(_pit_seed("synthetic", ticker))
    idx = pd.bdate_range(start=start, periods=n)
    vol = 0.018 * np.ones(n)
    for t in range(1, n):
        vol[t] = math.sqrt(0.9 * vol[t - 1] ** 2 + 0.1 * (0.018**2)) * float(
            rng.normal(1.0, 0.06)
        )
    shocks = rng.standard_t(4, size=n) / math.sqrt(2.0)
    rets = vol * shocks
    px = 50.0 * np.exp(np.cumsum(rets))
    return pd.Series(px, index=idx, name="close")


def _fallback_detect_events(close, ticker: str) -> List[Event]:
    """FALLBACK ONLY. Used when events.detect_events is not importable.

    Implements the FROZEN definition verbatim (CONTRACT.md s3): a trading day
    whose close-to-close return over a rolling WINDOW_DAYS window clears
    JUMP_THRESHOLD (the SIGNIFICANT floor), labelled with its tier via
    config.tier_for, with overlapping windows deduplicated to the single most
    extreme window.  LANE-EVENTS owns the real implementation; this exists so
    evaluate.py is self-testable and so a missing events.py degrades rather
    than crashes.
    """
    v = close.to_numpy()
    dates = close.index
    cands = []
    for t in range(WINDOW_DAYS, v.size):
        move = v[t] / v[t - WINDOW_DAYS] - 1.0
        if abs(move) >= JUMP_THRESHOLD:
            cands.append((t, float(move)))
    # Dedupe overlapping windows: strongest move wins, suppress its neighbours.
    keep: List[Tuple[int, float]] = []
    taken: List[int] = []
    for t, move in sorted(cands, key=lambda c: -abs(c[1])):
        if any(abs(t - u) < WINDOW_DAYS for u in taken):
            continue
        taken.append(t)
        keep.append((t, move))
    keep.sort(key=lambda c: c[0])
    return [
        Event(
            ticker=ticker,
            date=dates[t].strftime("%Y-%m-%d"),
            move_pct=move,
            direction="up" if move > 0 else "down",
            window_days=WINDOW_DAYS,
            tier=tier_for(move) or "significant",
        )
        for t, move in keep
    ]


def _load_events(ticker: str, close, events: Any = None) -> Tuple[List[Event], str]:
    if events is not None:
        return list(events), "injected"
    try:
        from . import events as _ev  # LANE-EVENTS

        got = _ev.detect_events(close)
        got = [e for e in got if getattr(e, "ticker", ticker) == ticker] or list(got)
        return list(got), "events.detect_events"
    except Exception:  # noqa: BLE001
        return _fallback_detect_events(close, ticker), "evaluate._fallback_detect_events"


def _default_generator() -> Tuple[Optional[Callable[[ForecastRequest], Any]], str]:
    try:
        from . import generator as _gen  # LANE-MODEL

        return _gen.generate_ensemble, "generator.generate_ensemble"
    except Exception:  # noqa: BLE001
        return None, "NULL_FALLBACK"


def _bootstrap_ci(vals: np.ndarray, n_boot: int = 4000, alpha: float = 0.10,
                  seed: int = 7) -> Tuple[Optional[float], Optional[float]]:
    vals = vals[np.isfinite(vals)]
    if vals.size < 3:
        return (None, None)
    rng = np.random.default_rng(seed)
    means = rng.choice(vals, size=(n_boot, vals.size), replace=True).mean(axis=1)
    lo, hi = np.quantile(means, [alpha / 2.0, 1.0 - alpha / 2.0])
    return (float(lo), float(hi))


def _subset(rows: List[Dict[str, Any]], key: str, val: Any) -> Dict[str, Any]:
    sel = [r for r in rows if r.get(key) == val]
    lifts = np.asarray([r["crps_lift"] for r in sel], dtype=float)
    lifts = lifts[np.isfinite(lifts)]
    pits = [r["pit"] for r in sel if r.get("pit") is not None]
    return {
        "n": len(sel),
        "mean_crps_lift": float(np.mean(lifts)) if lifts.size else None,
        "median_crps_lift": float(np.median(lifts)) if lifts.size else None,
        "pit_histogram": pit_histogram(pits),
    }


def walk_forward(
    ticker: str,
    generate: Optional[Callable[[ForecastRequest], Any]] = None,
    prices: Any = None,
    events: Any = None,
    test_start: str = TEST_START,
    test_end: str = TEST_END,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    n_paths: int = DEFAULT_N_PATHS,
    embargo_days: int = EMBARGO_DAYS,
    seed: int = 0,
    event_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Rolling out-of-sample evaluation over TEST_START..TEST_END.

    Returns the GET /api/backtest payload (CONTRACT.md s6) plus the extra fields
    the honesty architecture requires:

      n_tests, mean_crps_lift, pit_histogram, calibration_ok, per_event   [frozen]
      median_crps_lift, crps_lift_ci90                                   [dispersion]
      mean_crps_lift_demeaned                                            [drift guard]
      breakdown_famous / breakdown_obscure                               [s8.2]
      calibration, disclosures, appendix, meta                           [s7, s8.3]

    Leak guard: every test event is at or after TEST_START, and the first
    ``embargo_days`` TRADING days after TRAIN_END are purged (CONTRACT.md s2).

    Drift guard: ``mean_crps_lift_demeaned`` re-centres each model ensemble on
    zero before scoring, against the SAME null.  A generator whose lift is
    really an assumed drift shows a large raw lift and a near-zero or negative
    demeaned lift.  Both are always reported.
    """
    import pandas as pd

    close, price_src = _load_prices(ticker, prices)
    gen_fn, gen_src = (generate, "injected") if generate is not None else _default_generator()

    # ---- embargo: purge the first `embargo_days` TRADING days after TRAIN_END
    idx = close.index
    train_end_ts = pd.Timestamp(TRAIN_END)
    after_train = idx[idx > train_end_ts]
    if len(after_train) > embargo_days:
        embargo_until = after_train[embargo_days - 1] if embargo_days > 0 else train_end_ts
    else:
        embargo_until = train_end_ts
    eff_start = max(pd.Timestamp(test_start), pd.Timestamp(embargo_until))

    all_events, ev_src = _load_events(ticker, close, events)
    test_events = []
    for e in all_events:
        try:
            d = pd.Timestamp(getattr(e, "date"))
        except Exception:  # noqa: BLE001
            continue
        if d > eff_start and d <= pd.Timestamp(test_end):
            test_events.append(e)
    test_events.sort(key=lambda e: str(e.date))

    pos = {ts: i for i, ts in enumerate(idx)}
    vals = close.to_numpy()

    rows: List[Dict[str, Any]] = []
    skipped: List[Dict[str, str]] = []

    for e in test_events:
        d = pd.Timestamp(e.date)
        if d not in pos:
            nxt = idx[idx >= d]
            if len(nxt) == 0:
                skipped.append({"date": str(e.date), "reason": "date after price history"})
                continue
            d = nxt[0]
        i = pos[d]
        if i + horizon_days >= len(vals):
            skipped.append({"date": str(e.date), "reason": "insufficient forward history"})
            continue
        asof = d.strftime("%Y-%m-%d")
        actual = float(vals[i + horizon_days] / vals[i] - 1.0)

        try:
            sig = null_sigma(close, asof, horizon=horizon_days)
        except ValueError as exc:
            skipped.append({"date": asof, "reason": f"null sigma unavailable: {exc}"})
            continue

        ev_seed = _pit_seed(ticker, asof, seed)
        if gen_fn is not None:
            req = ForecastRequest(
                ticker=ticker,
                event_text=event_text or (getattr(e, "headline", "") or
                                          f"{ticker} moved {e.move_pct:+.1%} over "
                                          f"{getattr(e,'window_days',WINDOW_DAYS)} trading days"),
                as_of_date=asof,
                horizon_days=horizon_days,
                n_paths=n_paths,
            )
            try:
                model_paths = _as_paths(gen_fn(req))
                model_src = gen_src
            except Exception as exc:  # noqa: BLE001
                warnings.warn(
                    f"[LANE-EVAL] generator failed on {ticker} {asof} ({exc!r}); "
                    "scoring the NULL as the model for this event (lift == 0 by "
                    "construction, no fabricated skill).",
                    RuntimeWarning,
                    stacklevel=2,
                )
                model_paths = np.asarray(
                    null_ensemble(close, asof, horizon_days, n_paths, seed=ev_seed)
                )
                model_src = "NULL_FALLBACK(generator error)"
        else:
            model_paths = np.asarray(
                null_ensemble(close, asof, horizon_days, n_paths, seed=ev_seed)
            )
            model_src = "NULL_FALLBACK(no generator)"

        c_model = crps(model_paths, actual)
        c_null = crps_gaussian(0.0, sig, actual)
        lift = (c_null - c_model) / c_null if c_null > _EPS else float("nan")

        demeaned = model_paths - float(np.mean(model_paths))
        c_dm = crps(demeaned, actual)
        lift_dm = (c_null - c_dm) / c_null if c_null > _EPS else float("nan")

        p = pit(model_paths, actual, seed=ev_seed)
        mu = float(np.mean(model_paths))
        sd = float(np.std(model_paths, ddof=1))
        rows.append(
            {
                "date": asof,
                "ticker": ticker,
                "event_move_pct": float(getattr(e, "move_pct", float("nan"))),
                "direction": getattr(e, "direction", None),
                "tier": str(getattr(e, "tier", None)
                            or tier_for(getattr(e, "move_pct", 0.0)) or "unknown"),
                "famous": bool(getattr(e, "famous", False)),
                "crps": float(c_model),
                "crps_null": float(c_null),
                "crps_lift": float(lift),
                "crps_demeaned": float(c_dm),
                "crps_lift_demeaned": float(lift_dm),
                "pit": float(p),
                "z_score": float((actual - mu) / sd) if sd > 0 else float("nan"),
                "actual_return": actual,
                "mean": mu,
                "median": float(np.median(model_paths)),
                "std": sd,
                "null_sigma": float(sig),
                "model_source": model_src,
            }
        )

    n = len(rows)
    lifts = np.asarray([r["crps_lift"] for r in rows], dtype=float)
    lifts_dm = np.asarray([r["crps_lift_demeaned"] for r in rows], dtype=float)
    pits = [r["pit"] for r in rows]
    cal = calibration_test(pits)
    lo, hi = _bootstrap_ci(lifts)

    has_salience = any(r["famous"] for r in rows)
    payload: Dict[str, Any] = {
        # ---- frozen /api/backtest shape ----------------------------------- #
        "ticker": ticker,
        "n_tests": n,
        "mean_crps_lift": float(np.nanmean(lifts)) if n else None,
        "pit_histogram": pit_histogram(pits),
        "calibration_ok": cal["calibration_ok"],
        "per_event": rows,
        # ---- dispersion of the headline ----------------------------------- #
        "median_crps_lift": float(np.nanmedian(lifts)) if n else None,
        "crps_lift_ci90": [lo, hi],
        "mean_crps": float(np.mean([r["crps"] for r in rows])) if n else None,
        "mean_crps_null": float(np.mean([r["crps_null"] for r in rows])) if n else None,
        # ---- drift guard --------------------------------------------------- #
        "mean_crps_lift_demeaned": float(np.nanmean(lifts_dm)) if n else None,
        "drift_share_of_lift": (
            float(1.0 - (np.nanmean(lifts_dm) / np.nanmean(lifts)))
            if n and abs(float(np.nanmean(lifts))) > _EPS
            else None
        ),
        # ---- CONTRACT s8.2 famous vs obscure ------------------------------- #
        "breakdown_famous": _subset(rows, "famous", True),
        "breakdown_obscure": _subset(rows, "famous", False),
        "salience_labels_present": has_salience,
        # ---- CONTRACT s3 two tiers, never conflated in a report ------------ #
        "breakdown_major": _subset(rows, "tier", "major"),
        "breakdown_significant": _subset(rows, "tier", "significant"),
        # ---- calibration detail -------------------------------------------- #
        "calibration": cal,
        # ---- appendix (never a headline) ----------------------------------- #
        "appendix": {"directional_hit_rate": appendix_directional_hit_rate(rows)},
        # ---- provenance ----------------------------------------------------- #
        "meta": {
            "price_source": price_src,
            "event_source": ev_src,
            "generator_source": gen_src if gen_fn is not None else "NULL_FALLBACK",
            "synthetic": price_src.startswith("SYNTHETIC_FALLBACK"),
            "train_end": TRAIN_END,
            "test_window": [str(eff_start.date()), str(pd.Timestamp(test_end).date())],
            "embargo_days": embargo_days,
            "embargo_applied_until": str(pd.Timestamp(embargo_until).date()),
            "horizon_days": horizon_days,
            "n_paths": n_paths,
            "crps_estimator": "fair (Ferro 2014), pairwise term / (2 m (m-1))",
            "crps_null_estimator": "closed-form Gaussian",
            "pit_convention": "randomized, seed derived from (ticker, date, seed)",
            "events_considered": len(test_events),
            "events_skipped": skipped,
        },
        "disclosures": _disclosures(n, price_src, gen_fn is not None, has_salience,
                                    cal, rows),
    }
    return payload


def _disclosures(n: int, price_src: str, have_gen: bool, has_salience: bool,
                 cal: Dict[str, Any],
                 rows: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """Plain-English caveats. CONTRACT.md s8.3 requires these to be stated out
    loud in the product, so they ship inside the payload rather than living only
    in a slide."""
    out = [
        "Any LLM in the generator has read the post-2019 world. Cutting input "
        "data at 2019 does not cut the weights. We therefore report lift over a "
        "null model, not raw accuracy.",
        "The null model (Gaussian, trailing 250d sigma, zero drift) is reported "
        "on every event and every aggregate and cannot be removed.",
        "Directional hit-rate is an appendix metric only. It is not a result.",
    ]
    if n == 0:
        out.append(
            "NO TEST EVENTS for this ticker at the frozen 25% / 5-day threshold. "
            "Every aggregate below is null, not zero. Nothing has been measured."
        )
    if n and n < MIN_CALIBRATION_N:
        out.append(
            f"n = {n} test events. A calibration test at this n has low power "
            f"(~30% against a 2x-too-narrow ensemble at n=12). calibration_ok = "
            f"{cal.get('calibration_ok')} means 'no evidence of miscalibration', "
            "not 'calibrated'. Use the pooled universe verdict."
        )
    if price_src.startswith("SYNTHETIC_FALLBACK"):
        out.append(
            "SYNTHETIC PRICES. The price series for this run is a generated "
            f"series ({price_src}), not real market data. These numbers are NOT "
            "REAL and must not be shown as a result."
        )
    if not have_gen:
        out.append(
            "NO GENERATOR AVAILABLE. The null model was scored against itself, "
            "so crps_lift is ~0 by construction. This is a plumbing check, not "
            "a result."
        )
    if not has_salience:
        out.append(
            "No event carried a famous=True salience label, so the famous/obscure "
            "split (CONTRACT s8.2) is not yet informative for this ticker."
        )
    if rows:
        n_major = sum(1 for r in rows if r.get("tier") == "major")
        n_sig = sum(1 for r in rows if r.get("tier") == "significant")
        out.append(
            f"TIERS ARE NOT INTERCHANGEABLE (CONTRACT s3): {n_major} major "
            f"(>={TIER_MAJOR:.0%}) and {n_sig} significant "
            f"(>={TIER_SIGNIFICANT:.0%}) test events. The pooled headline mixes "
            "both; breakdown_major is the black-swan number and the only one "
            "the stage narrative describes."
        )
    return out


def walk_forward_universe(
    tickers: Optional[Sequence[str]] = None,
    prices_map: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Pooled walk-forward across the universe.

    The per-ticker calibration verdict is underpowered by construction (~12
    events).  Pooling ~10 tickers gets n into the range where a KS test can
    actually see a 2x-too-narrow ensemble, so THIS is the calibration number
    worth quoting.  Also surfaces per-ticker concentration, because a pooled
    mean dominated by one ticker is a single-ticker statistic wearing a
    universe's clothes.
    """
    from .config import UNIVERSE

    tickers = list(tickers or UNIVERSE)
    prices_map = prices_map or {}
    per_ticker: Dict[str, Any] = {}
    all_rows: List[Dict[str, Any]] = []
    for t in tickers:
        kw = dict(kwargs)
        if t in prices_map:
            kw["prices"] = prices_map[t]
        res = walk_forward(t, **kw)
        per_ticker[t] = {
            "n_tests": res["n_tests"],
            "mean_crps_lift": res["mean_crps_lift"],
            "mean_crps_lift_demeaned": res["mean_crps_lift_demeaned"],
            "calibration_ok": res["calibration_ok"],
            "synthetic": res["meta"]["synthetic"],
        }
        all_rows.extend(res["per_event"])

    n = len(all_rows)
    lifts = np.asarray([r["crps_lift"] for r in all_rows], dtype=float)
    lifts_dm = np.asarray([r["crps_lift_demeaned"] for r in all_rows], dtype=float)
    pits = [r["pit"] for r in all_rows]
    cal = calibration_test(pits)
    lo, hi = _bootstrap_ci(lifts)

    counts: Dict[str, int] = {}
    for r in all_rows:
        counts[r["ticker"]] = counts.get(r["ticker"], 0) + 1
    top = max(counts.items(), key=lambda kv: kv[1]) if counts else (None, 0)

    disc = [
        "Pooled across the universe because a per-ticker calibration test at "
        "n~12 has ~30% power against a 2x-too-narrow ensemble.",
        "The null model is reported on every event and every aggregate and "
        "cannot be removed (CONTRACT.md s7).",
        "Directional hit-rate is an appendix metric only. It is not a result.",
    ]
    n_synth = sum(1 for v in per_ticker.values() if v["synthetic"])
    if n_synth:
        disc.append(
            f"SYNTHETIC DATA: {n_synth} of {len(tickers)} tickers used a labelled "
            "synthetic price series. Their numbers are NOT REAL."
        )
    zero = [t for t, v in per_ticker.items() if v["n_tests"] == 0]
    if zero:
        disc.append(
            f"NO TEST EVENTS at the frozen 25%/5-day threshold for: "
            f"{', '.join(zero)}. They contribute nothing to the pooled number."
        )
    if n and top[1] / n > 0.4:
        disc.append(
            f"CONCENTRATION: {top[0]} supplies {top[1]}/{n} "
            f"({top[1]/n:.0%}) of all test events. The pooled headline is "
            f"substantially a {top[0]} statistic."
        )
    n_major = sum(1 for r in all_rows if r.get("tier") == "major")
    if n:
        disc.append(
            f"TIER MIX: {n_major} major (>={TIER_MAJOR:.0%}) and {n - n_major} "
            f"significant (>={TIER_SIGNIFICANT:.0%}) test events. Report "
            "breakdown_major separately -- the stage narrative is a major-tier "
            "story and the pooled number is not."
        )
    if n and abs(float(np.nanmean(lifts))) > _EPS:
        share = 1.0 - float(np.nanmean(lifts_dm)) / float(np.nanmean(lifts))
        disc.append(
            f"DRIFT DECOMPOSITION: {share:.0%} of the pooled lift disappears when "
            "the model ensembles are demeaned. Lift that is all drift is a "
            "bull-decade artifact, not skill."
        )

    return {
        "scope": "universe",
        "tickers": tickers,
        "n_tests": n,
        "mean_crps_lift": float(np.nanmean(lifts)) if n else None,
        "median_crps_lift": float(np.nanmedian(lifts)) if n else None,
        "crps_lift_ci90": [lo, hi],
        "mean_crps_lift_demeaned": float(np.nanmean(lifts_dm)) if n else None,
        "pit_histogram": pit_histogram(pits),
        "calibration_ok": cal["calibration_ok"],
        "calibration": cal,
        "per_ticker": per_ticker,
        "events_per_ticker": counts,
        "breakdown_famous": _subset(all_rows, "famous", True),
        "breakdown_obscure": _subset(all_rows, "famous", False),
        "breakdown_major": _subset(all_rows, "tier", "major"),
        "breakdown_significant": _subset(all_rows, "tier", "significant"),
        "appendix": {"directional_hit_rate": appendix_directional_hit_rate(all_rows)},
        "disclosures": disc,
    }


# --------------------------------------------------------------------------- #
# reproducibility entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    # python -m rulial.evaluate            -> pooled walk-forward, real pipeline
    import argparse

    ap = argparse.ArgumentParser(description="rulial-markets walk-forward eval")
    ap.add_argument("--tickers", default="", help="comma-separated; default UNIVERSE")
    ap.add_argument("--n-paths", type=int, default=DEFAULT_N_PATHS)
    args = ap.parse_args()

    from .config import UNIVERSE as _U

    tks = [t.strip().upper() for t in args.tickers.split(",") if t.strip()] or list(_U)
    out = walk_forward_universe(tks, n_paths=args.n_paths)
    print(f"{'TICKER':<8}{'n':>4}{'crps_lift':>12}{'demeaned':>12}{'calib':>8}  src")
    for t in tks:
        v = out["per_ticker"][t]
        fmt = lambda x: "        None" if x is None else f"{x:12.4f}"
        tag = " SYNTHETIC" if v["synthetic"] else ""
        print(f"{t:<8}{v['n_tests']:>4}{fmt(v['mean_crps_lift'])}"
              f"{fmt(v['mean_crps_lift_demeaned'])}{str(v['calibration_ok']):>8}{tag}")
    print("-" * 52)
    print(f"POOLED   n={out['n_tests']}  mean_crps_lift={out['mean_crps_lift']}  "
          f"demeaned={out['mean_crps_lift_demeaned']}")
    print(f"PIT histogram: {out['pit_histogram']}   calibration_ok={out['calibration_ok']}")
    for d in out["disclosures"]:
        print(f"  * {d}")
