"""
rulial.generator -- the conditional forward-return ensemble.  (LANE-MODEL)

Public surface (CONTRACT.md s4):
    generate_ensemble(req: ForecastRequest, ...) -> Ensemble

--------------------------------------------------------------------------
WHY THIS IS BUILT THE WAY IT IS
--------------------------------------------------------------------------
Wolfram's rulial ensemble is explicitly an ensemble over RULES, not over
configurations under a fixed rule.  A Monte Carlo that samples 2,000 noise
draws from one generator is Boltzmann's ensemble -- the gas case Wolfram
contrasts the rulial ensemble *against*.  So we do not do that.

We define a small explicit SET OF GENERATOR RULES (`RULE_SET`) that disagree
with each other about the things we are genuinely unsure of:

    * which historical analogs are admissible   (analog_scope)
    * where the distribution should be centred  (drift_mode)
    * how wide it should be                     (vol_anchor)
    * how much serial structure to preserve     (block_len)

Every forecast is a weighted mixture over those rules, and we report how far
the answer moves when you change the rule (`diagnostics["rulial_dispersion"]`).
That cross-rule spread is the honest uncertainty-about-the-model, and it is
the thing the path cloud alone cannot tell you.

This is not vocabulary hygiene.  Our measured failure mode is that ALL of the
apparent skill in a naive analog generator comes from an assumed drift:
resampling 2010-2019 analog outcomes scores +14.8% CRPS lift raw and -4.5%
(significantly WORSE than null) once demeaned, because the train corpus is
30 up-jumps / 3 down-jumps with +5.77% mean forward return.  Drift is exactly
the parameter that differs between rules.  So:

    * drift is NEVER smuggled in.  Analog windows are demeaned by default.
    * the raw-drift rule survives, at 10% weight, LABELLED AS A TRAP, so we
      can measure it rather than pretend it is not tempting.
    * `demeaned_twin(ens)` hands LANE-EVAL a zero-drift copy of any ensemble
      so drift-decomposed lift is a one-liner on their side.

Second measured constraint: the frozen null (Gaussian, trailing 250d sigma,
zero drift) already auto-expands ~1.78x after a 25% weekly move, and an
ORACLE that cheats by using the realized post-jump sigma only scores +2.0%
CRPS lift against it.  Ensemble SHAPE at equal width (bimodal, Student-t)
buys ~0.  Nobody on this project should expect a width-only generator to
produce a headline number.  The value here is calibration and the honest
accounting of where the location came from, not a big lift.

--------------------------------------------------------------------------
THE THREE STAGES
--------------------------------------------------------------------------
1. RETRIEVE   -- TF-IDF + metadata match of `req.event_text` against the seed
                 event corpus, hard-filtered to events whose ENTIRE forward
                 window closes at or before `req.as_of_date`.
2. GENERATE   -- weighted mixture over RULE_SET.  Each rule runs a circular
                 block bootstrap over its admissible analogs' realized forward
                 windows.  An LLM (or a loud deterministic fallback) supplies
                 a small scenario prior: 2-4 named regimes with weights, a
                 horizon drift and a vol multiplier.  The LLM never emits a
                 point prediction and its outputs are hard-clamped.
3. COARSE-GRAIN -- Wolfram's computationally-bounded observer.  Individual
                 paths are unscoreable (forward signed R^2 ~ 0, measured).
                 We reduce to quantiles / mean / std / a per-day fan / a
                 narrative naming the actual analogs used.

--------------------------------------------------------------------------
WHAT WAS MEASURED, AND WHAT IT COST TO GET RIGHT
--------------------------------------------------------------------------
Every number below is from real Yahoo daily closes over the full history of
all ten universe tickers, train period only (<= 2019-12-31), 647 events at
the frozen two-tier definition, LLM off, scored with the fair (unbiased)
CRPS ensemble estimator against the frozen null's closed-form Gaussian CRPS.

Three real defects were found by measuring rather than by reasoning:

  1. Stacking the prior's vol multiplier ON TOP of the analog width
     double-counted. Ensemble ran 2.57x the null's sigma: -52% CRPS lift.
     Fix: the multiplier scales the TRAILING anchor; the analog anchor is a
     competing width estimate, never a factor to multiply by.
  2. Pooling RAW forward returns across analogs mixed a 2001 NVDA window with
     a 2016 JPM window, so pooled sigma tracked whichever name was most
     volatile. Fix: filtered historical simulation -- each analog's window is
     divided by ITS OWN trailing sigma at ITS OWN event date, then rescaled to
     the requested name's current sigma.
  3. Anchoring width on the sample standard deviation of those standardized
     windows over-widened, because they have kurtosis ~4.8 and a handful of
     dot-com windows inflate the sd by ~1.23x. Fix: anchor on the IQR scale.
     Measured IQR/sd on this corpus is 0.812, which lands independently on the
     empirically PIT-optimal width.

Shipped result on train data, versus the frozen null:

     metric                      ours     null      ideal
     PIT chi-square (9 dof)       9.5     33.6      ~9
     PIT tail rate               0.097    0.159     0.10
     sigma / null sigma          1.24     1.00      --
     CRPS lift (raw)            -5.1%      0        --
     CRPS lift (demeaned)       -3.5%      0        --

Read that honestly: we are 3.5x better CALIBRATED than the null -- which
CONTRACT.md s7 names as the win condition -- and we PAY about five points of
CRPS for it. CRPS on a leptokurtic target rewards under-dispersion, so the
width that maximises lift (+2.1%) puts 31% of outcomes in the extreme 10% of
the ensemble. We did not ship that width. The recon work independently
measured the ceiling for ANY width-only generator against this null at +2.0%,
using an oracle that cheats with the realized post-event sigma, so a large
positive lift here would be evidence of a leak, not of skill.

--------------------------------------------------------------------------
LEAKAGE (CONTRACT.md s8)
--------------------------------------------------------------------------
Cutting input data at 2019 does not cut the LLM's weights.  See the module
constant LEAKAGE_DISCLOSURE, which the API and UI should surface verbatim.
`diagnostics["warnings"]` carries the per-request version.

No network access at import time.  numpy + stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import warnings
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .config import (
    CORPUS_DIR,
    DEFAULT_HORIZON_DAYS,
    DEFAULT_N_PATHS,
    EVENTS_PATH,
    JUMP_THRESHOLD,
    TIER_MAJOR,
    TIER_SIGNIFICANT,
    NULL_VOL_LOOKBACK,
    PRICES_DIR,
    TICKER_NAMES,
    TRAIN_END,
    UNIVERSE,
    WINDOW_DAYS,
)
from .types import Article, Ensemble, Event, ForecastRequest

__all__ = [
    "generate_ensemble",
    "demeaned_twin",
    "retrieve_analogs",
    "scenario_prior",
    "load_seed_corpus",
    "GeneratorRule",
    "RULE_SET",
    "ScenarioPrior",
    "LookaheadError",
    "LEAKAGE_DISCLOSURE",
]


# ===========================================================================
# 0.  Constants, disclosure text, small helpers
# ===========================================================================

LEAKAGE_DISCLOSURE = (
    "The language model that proposes this forecast's scenario prior was trained on "
    "text published after 2019. Cutting the input data at 2019 does not cut the weights. "
    "For a famous event the model may be recalling the outcome rather than reasoning about it. "
    "This is why we report lift over a null model rather than raw accuracy, why the test set "
    "contains obscure events alongside famous ones and reports them separately, and why the "
    "LLM's influence in this generator is capped: it may set width and, on 45% of paths, a "
    "clamped drift. It may not emit a point prediction."
)

# Sampling / clamping guards on the LLM prior.  These exist so the model
# cannot turn a distribution into a point forecast.
MAX_PRIOR_DRIFT_5D = 0.35     # |cumulative log drift| over a 5-day horizon
MIN_VOL_MULT = 0.50
MAX_VOL_MULT = 3.00
MAX_SCENARIOS = 4

# How much of the LLM's WIDTH opinion to believe: vol_multiplier ** this.
#
# MEASURED, on 647 real train events. Asked about a 40% datacenter revenue
# miss, claude-haiku-4-5 returned vol_multiplier = 2.0 for every one of its
# three scenarios -- it wants to be twice as wide as normal. The data does not
# support that: realized post-event dispersion runs about 1.24x the null.
# Taking the model at its word puts the ensemble at 1.47x with a PIT
# chi-square of 19.7; compressing by 0.6 puts it at 1.25x with chi-square 15.0
# and improves CRPS lift from -6.1% to -2.2%. Every metric moves the right way,
# and the optimum is broad (0.45-0.60), so this is not a fitted decimal.
#
# The principle: we trust the model's ORDERING of severity -- it reliably says
# a fraud probe is wider than a guidance trim -- and not its MAGNITUDE, which
# is systematically about twice what the tape delivers. Applied to LLM priors
# only; the heuristic fallback is already calibrated at 1.05-1.35.
LLM_WIDTH_TRUST = 0.60

# Retrieval scoring weights.
W_TEXT = 0.55
W_TICKER = 0.22
W_DIRECTION = 0.13
W_MAGNITUDE = 0.10

DEFAULT_N_ANALOGS = 25

# The ONE fitted constant in this module. Everything else is measured directly
# from the data at request time.
#
# Why it exists: a per-path block bootstrap reproduces the serial structure
# INSIDE a real post-event window (those windows trend), and drawing one analog
# per path adds cross-path volatility heterogeneity. Both are real features we
# want, and both make cumulative h-day dispersion wider than sqrt(h) scaling of
# the daily robust scale implies. This scalar corrects that aggregation.
#
# How it was fit: on TRAIN DATA ONLY (647 real events, 10 tickers, all history
# through 2019-12-31), minimising the PIT histogram's chi-square against
# uniform -- which CONTRACT.md s7 names as the win condition -- NOT maximising
# CRPS lift. Fitting on lift instead would push it to ~0.50, which scores
# +1.9% lift while putting 32% of outcomes in the extreme 10% of the ensemble.
# That is the "make ourselves look good" trade the contract exists to prevent.
#
# MEASURED AT THE SHIPPED VALUE, 647 real train events, LLM off:
#     ensemble sigma / null sigma   1.24
#     PIT chi-square (9 dof)        9.5    (the null scores 33.6)
#     PIT tail rate                 0.097  (ideal 0.10; the null is 0.159)
#     CRPS lift vs frozen null      -5.1% raw, -3.5% demeaned
# So: a chi-square of 9.5 on 9 degrees of freedom is as flat as a PIT histogram
# gets, and it is 3.5x flatter than the null's. We pay ~5 points of CRPS for
# that. Both numbers are the honest result and BOTH must be reported -- the
# recon work measured the ceiling for ANY width-only generator against this
# null at +2.0% (using an oracle that cheats with the realized post-event
# sigma), so a large positive lift here would be evidence of a bug or a leak,
# not of skill. Never quietly retune this constant to make the lift positive.
HORIZON_CALIBRATION = 0.80
_TRADING_DAYS_PER_CALENDAR_DAY = 252.0 / 365.25

_TOKEN_RE = re.compile(r"[a-z0-9%\.]+")
_STOP = frozenset(
    """a an the and or of to in on for with at by from as is are was were be been being
    it its this that these those we you they he she i not no but if then than so such
    into over under about after before during up down out off very can will would could
    should may might must do does did done has have had""".split()
)


class LookaheadError(RuntimeError):
    """Raised when anything in the pipeline would consult data after as_of_date."""


def _iso(d: Any) -> str:
    """Coerce a date-ish thing to an ISO yyyy-mm-dd string."""
    if isinstance(d, str):
        return d[:10]
    if isinstance(d, (datetime, date)):
        return d.strftime("%Y-%m-%d")
    return str(d)[:10]


def _to_date(d: Any) -> date:
    return datetime.strptime(_iso(d), "%Y-%m-%d").date()


def _tokens(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _STOP and len(t) > 1]


def _seed_from_request(req: ForecastRequest) -> int:
    """Deterministic per-request seed.

    Reproducible in the sense that matters: the SAME request always produces
    the SAME ensemble, and a caller can pin it explicitly with seed=<int>.
    """
    key = f"{req.ticker}|{req.as_of_date}|{req.horizon_days}|{req.n_paths}|{req.event_text}"
    return int.from_bytes(hashlib.blake2b(key.encode("utf-8"), digest_size=4).digest(), "big")


# ===========================================================================
# 1.  Price loading (LANE-DATA owns data.py; we degrade gracefully)
# ===========================================================================

@dataclass
class _PriceSeries:
    """Minimal price view: aligned ISO dates + close prices + daily log returns."""
    ticker: str
    dates: List[str]
    close: np.ndarray
    source: str                       # "rulial.data" | "csv" | "SYNTHETIC-FALLBACK"

    @property
    def logret(self) -> np.ndarray:
        """Daily log returns, length len(close) - 1, aligned to dates[1:]."""
        if self.close.size < 2:
            return np.zeros(0)
        return np.diff(np.log(self.close))

    def index_of(self, iso_day: str) -> int:
        """Position of the last trading day at or before iso_day; -1 if none."""
        lo, hi = 0, len(self.dates)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.dates[mid] <= iso_day:
                lo = mid + 1
            else:
                hi = mid
        return lo - 1


_PRICE_CACHE: Dict[str, _PriceSeries] = {}


def _synthetic_prices(ticker: str, start: str = "2005-01-03", n: int = 3800) -> _PriceSeries:
    """CLEARLY LABELLED SYNTHETIC FALLBACK.

    Used only when no real price data exists on disk. Never present numbers
    derived from this as real. It exists so the demo and the tests run before
    LANE-DATA lands, and `source` says so everywhere it surfaces.
    """
    rng = np.random.default_rng(abs(hash(ticker)) % (2**31))
    # Deliberately crude: GBM with a slow vol cycle so trailing-250d sigma varies.
    t = np.arange(n)
    vol = 0.016 * (1.0 + 0.45 * np.sin(t / 190.0))
    r = rng.normal(0.0002, 1.0, size=n) * vol
    close = 50.0 * np.exp(np.cumsum(r))
    d0 = _to_date(start)
    dates, cur, i = [], d0, 0
    while len(dates) < n:
        if cur.weekday() < 5:
            dates.append(cur.isoformat())
        cur += timedelta(days=1)
        i += 1
    return _PriceSeries(ticker, dates, close, "SYNTHETIC-FALLBACK")


def _read_price_csv(path: Path, ticker: str) -> Optional[_PriceSeries]:
    """Tolerant CSV reader -- we do not know LANE-DATA's exact column casing."""
    try:
        import csv
        import io

        text = path.read_text()
        synth = "SYNTHETIC" in text[:400].upper().split("\n")[0]
        # LANE-DATA writes a leading "# SYNTHETIC-FALLBACK-DATA" comment line.
        lines = [ln for ln in text.splitlines() if not ln.startswith("#")]
        rows = list(csv.DictReader(io.StringIO("\n".join(lines))))
        if not rows:
            return None
        cols = {c.lower().replace(" ", "_"): c for c in rows[0].keys()}
        dcol = next((cols[c] for c in ("date", "index", "datetime", "timestamp") if c in cols), None)
        ccol = next(
            (cols[c] for c in ("adj_close", "adjclose", "close", "adjusted_close", "px_last")
             if c in cols),
            None,
        )
        if dcol is None or ccol is None:
            return None
        pairs = []
        for r in rows:
            try:
                v = float(r[ccol])
            except (TypeError, ValueError):
                continue
            if v > 0 and not math.isnan(v):
                pairs.append((_iso(r[dcol]), v))
        if len(pairs) < 30:
            return None
        pairs.sort(key=lambda p: p[0])
        return _PriceSeries(ticker, [p[0] for p in pairs],
                            np.asarray([p[1] for p in pairs], dtype=float),
                            "csv:SYNTHETIC-FALLBACK" if synth else "csv")
    except Exception:
        return None


def _load_price_series(ticker: str, prices_dir: Optional[Path] = None) -> _PriceSeries:
    """Prefer LANE-DATA's loader, then CSV on disk, then labelled synthetic."""
    pdir = Path(prices_dir) if prices_dir is not None else PRICES_DIR
    ck = f"{ticker}@{pdir}"
    if ck in _PRICE_CACHE:
        return _PRICE_CACHE[ck]

    series: Optional[_PriceSeries] = None

    # (a) LANE-DATA's loader, if it exists yet.
    if prices_dir is None:
        try:
            from . import data as _data  # type: ignore

            try:
                # Ask for the full cached history: LANE-DATA's default start is
                # HISTORY_START (2010-01-01) and we need the pre-window warm-up
                # bars for a 250-day trailing sigma at early as_of dates.
                df = _data.load_prices(ticker, start="1900-01-01")
            except TypeError:
                df = _data.load_prices(ticker)
            synth = ticker.upper() in getattr(_data, "SYNTHETIC_TICKERS", set())
            if df is not None and len(df) >= 30:
                lower = {str(c).lower(): c for c in df.columns}
                ccol = next(
                    (lower[c] for c in ("adj_close", "adjclose", "close", "adjusted_close")
                     if c in lower),
                    None,
                )
                if ccol is not None:
                    if "date" in lower:
                        dates = [_iso(x) for x in df[lower["date"]].tolist()]
                    else:
                        dates = [_iso(x) for x in df.index.tolist()]
                    close = np.asarray(df[ccol].astype(float).tolist(), dtype=float)
                    ok = np.isfinite(close) & (close > 0)
                    series = _PriceSeries(
                        ticker, [d for d, k in zip(dates, ok) if k], close[ok],
                        "rulial.data:SYNTHETIC-FALLBACK" if synth else "rulial.data",
                    )
        except Exception:
            series = None

    # (b) CSV on disk.
    if series is None:
        for name in (f"{ticker}.csv", f"{ticker.lower()}.csv"):
            p = pdir / name
            if p.exists():
                series = _read_price_csv(p, ticker)
                if series is not None:
                    break

    # (c) Labelled synthetic.
    if series is None:
        series = _synthetic_prices(ticker)

    _PRICE_CACHE[ck] = series
    return series


def _trailing_vol(series: _PriceSeries, as_of: str, lookback: int = NULL_VOL_LOOKBACK) -> Tuple[float, int]:
    """Trailing daily log-return sigma using ONLY bars at or before as_of.

    Returns (sigma_daily, n_obs_used). This is the width of the frozen null.
    """
    i = series.index_of(as_of)
    if i < 2:
        return 0.02, 0
    r = series.logret[: i]              # logret[k] spans dates[k] -> dates[k+1]
    r = r[-lookback:]
    r = r[np.isfinite(r)]
    if r.size < 20:
        return 0.02, int(r.size)
    s = float(np.std(r, ddof=1))
    return (s if s > 1e-8 else 0.02), int(r.size)


# ===========================================================================
# 2.  Seed corpus loading
# ===========================================================================

def _event_from_dict(d: Dict[str, Any]) -> Optional[Event]:
    try:
        arts = []
        for a in (d.get("articles") or []):
            if isinstance(a, dict):
                arts.append(
                    Article(
                        url=str(a.get("url", "")),
                        title=str(a.get("title", "")),
                        published=_iso(a.get("published", "")),
                        source=str(a.get("source", "")),
                        snippet=str(a.get("snippet", "")),
                    )
                )
        mv = float(d["move_pct"])
        return Event(
            ticker=str(d["ticker"]).upper(),
            date=_iso(d["date"]),
            move_pct=mv,
            direction=str(d.get("direction") or ("up" if mv >= 0 else "down")),
            window_days=int(d.get("window_days", WINDOW_DAYS)),
            headline=str(d.get("headline", "")),
            articles=arts,
            tier=str(d.get("tier", "major")),
            famous=bool(d.get("famous", False)),
        )
    except Exception:
        return None


def load_seed_corpus(events_path: Optional[Path] = None,
                     corpus_dir: Optional[Path] = None) -> List[Event]:
    """Read the seed event ledger written by LANE-EVENTS / LANE-NEWS.

    Tolerant of a missing or half-written file -- the demo must not crash on
    an empty corpus, and six of the ten universe tickers legitimately have
    ZERO train events at the frozen 25%/5d threshold.
    """
    path = Path(events_path) if events_path is not None else EVENTS_PATH
    cdir = Path(corpus_dir) if corpus_dir is not None else CORPUS_DIR
    out: List[Event] = []

    if path.exists():
        try:
            raw = path.read_text().strip()
        except Exception:
            raw = ""
        if raw:
            if raw.lstrip().startswith("["):          # someone wrote a JSON array
                try:
                    for d in json.loads(raw):
                        ev = _event_from_dict(d)
                        if ev:
                            out.append(ev)
                except Exception:
                    pass
            else:                                      # jsonl (the contract's shape)
                for line in raw.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = _event_from_dict(json.loads(line))
                    except Exception:
                        ev = None
                    if ev:
                        out.append(ev)

    # Articles may live beside the ledger rather than inside it.
    if cdir.exists():
        for ev in out:
            if ev.articles:
                continue
            for name in (f"{ev.ticker}_{ev.date}.json", f"{ev.ticker}-{ev.date}.json"):
                p = cdir / name
                if not p.exists():
                    continue
                try:
                    blob = json.loads(p.read_text())
                except Exception:
                    continue
                items = blob.get("articles") if isinstance(blob, dict) else blob
                for a in (items or []):
                    if isinstance(a, dict):
                        ev.articles.append(
                            Article(
                                url=str(a.get("url", "")),
                                title=str(a.get("title", "")),
                                published=_iso(a.get("published", "")),
                                source=str(a.get("source", "")),
                                snippet=str(a.get("snippet", "")),
                            )
                        )
                break

    out.sort(key=lambda e: (e.date, e.ticker))
    return out


def _event_document(ev: Event) -> str:
    """The text we match a query against: headline + article titles + snippets."""
    parts = [ev.headline or "", f"{ev.ticker} {TICKER_NAMES.get(ev.ticker, '')}",
             "surged jumped rallied" if ev.direction == "up" else "plunged crashed fell slumped"]
    for a in ev.articles[:8]:
        parts.append(a.title or "")
        parts.append((a.snippet or "")[:400])
    return " ".join(p for p in parts if p)


# ===========================================================================
# 3.  STAGE 1 -- RETRIEVE
# ===========================================================================

_DOWN_WORDS = frozenset(
    """miss misses missed plunge plunges plunged crash crashes crashed fell falls drop drops
    dropped slump slumps sink sinks sank tumble tumbles cut cuts cutting slash slashes lower
    lowered downgrade downgraded warning warns warned fraud probe investigation subpoena
    recall recalls grounded grounding halt halted bankruptcy default delay delays delayed
    layoff layoffs restructuring writedown impairment loss losses weak weakness shortfall
    guidance-cut resign resigns resigned ouster scandal lawsuit fine penalty ban banned
    shortage glut oversupply cancel cancels cancelled cancellation negative decline declines
    bearish selloff sell-off crisis collapse collapses collapsed""".split()
)
_UP_WORDS = frozenset(
    """beat beats blowout surge surges surged soar soars soared jump jumps rally rallies
    record records raise raises raised upgrade upgraded approval approved wins won win
    breakthrough partnership acquisition buyback dividend expansion strong strength
    outperform accelerating accelerate demand backlog guidance-raise bullish rebound
    recovery profit profitable milestone launch launches contract award awarded""".split()
)
_SEVERE_WORDS = frozenset(
    """massive catastrophic unprecedented total complete existential severe historic
    devastating collapse bankruptcy fraud emergency
    grounded halt halted indefinitely withdraws withdrawn writedown crash crashes
    triples tripled doubled soars plunges collapses guts slashes cancels cancelled
    overstated recall investigation regulators blowout""".split()
)


def _severity_anchor(event_text: str) -> float:
    """Target |move| that analog retrieval should aim at, as a fraction.

    Adding the 15% significant tier made ``JUMP_THRESHOLD`` equal to 0.15, and
    `retrieve_analogs` used that as its fallback magnitude anchor. Any event
    text without a literal percent sign therefore retrieved the SMALLEST events
    in the pool and the bootstrap inherited their width.

    The fix retrieves better analogs rather than inflating vol_mult: the
    scenario prior is deliberately timid about width because over-widening was
    measured to score -52% lift. Width should come from WHICH events we
    bootstrap, not from a multiplier.
    """
    toks = _tokens(event_text)
    sev = sum(1 for t in toks if t in _SEVERE_WORDS)
    up = sum(1 for t in toks if t in _UP_WORDS)
    dn = sum(1 for t in toks if t in _DOWN_WORDS)
    anchor = TIER_SIGNIFICANT + 0.035 * sev + 0.015 * abs(up - dn)
    return float(min(0.45, max(TIER_SIGNIFICANT, anchor)))


def _implied_direction(event_text: str) -> Tuple[str, float]:
    """Crude, deterministic, and honestly labelled sign read on the query text.

    Returns (direction, confidence in [0,1]).  Used for retrieval scoring and
    for the no-LLM fallback prior.  It is NOT a forecast.
    """
    toks = _tokens(event_text)
    dn = sum(1 for t in toks if t in _DOWN_WORDS)
    up = sum(1 for t in toks if t in _UP_WORDS)
    if dn == up:
        return "unknown", 0.0
    tot = dn + up
    conf = abs(dn - up) / max(tot, 1)
    return ("down", conf) if dn > up else ("up", conf)


def _implied_magnitude(event_text: str) -> Optional[float]:
    """Largest percentage mentioned in the query, as a fraction. None if absent."""
    best = None
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:%|percent|pct)", (event_text or "").lower()):
        try:
            v = float(m.group(1)) / 100.0
        except ValueError:
            continue
        if 0.0 < v < 5.0 and (best is None or v > best):
            best = v
    return best


def _tfidf_scores(query: str, docs: Sequence[str]) -> np.ndarray:
    """Hand-rolled TF-IDF cosine. No sklearn dependency for a 150-doc corpus."""
    n = len(docs)
    if n == 0:
        return np.zeros(0)
    doc_toks = [_tokens(d) for d in docs]
    q_toks = _tokens(query)
    if not q_toks:
        return np.zeros(n)
    df: Dict[str, int] = {}
    for dt in doc_toks:
        for t in set(dt):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}

    def vec(toks: List[str]) -> Dict[str, float]:
        if not toks:
            return {}
        tf: Dict[str, float] = {}
        for t in toks:
            tf[t] = tf.get(t, 0.0) + 1.0
        v = {t: (1.0 + math.log(c)) * idf.get(t, 1.0) for t, c in tf.items()}
        nrm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / nrm for t, x in v.items()}

    qv = vec(q_toks)
    out = np.zeros(n)
    for i, dt in enumerate(doc_toks):
        dv = vec(dt)
        if len(qv) > len(dv):
            out[i] = sum(dv[t] * qv[t] for t in dv if t in qv)
        else:
            out[i] = sum(qv[t] * dv[t] for t in qv if t in dv)
    return out


def _forward_window_closes_by(ev: Event, as_of: str, horizon_days: int,
                              series: Optional[_PriceSeries]) -> bool:
    """True iff the analog's realized forward window ENDS at or before as_of.

    This is the subtle half of the leak guard.  Filtering on `ev.date <= as_of`
    is not enough: an event dated two days before as_of has a five-day forward
    window that runs PAST as_of, so using its realized outcome is lookahead.
    """
    if ev.date > as_of:
        return False
    if series is not None and "SYNTHETIC-FALLBACK" not in series.source:
        i = series.index_of(ev.date)
        j = series.index_of(as_of)
        return i >= 0 and j >= 0 and (j - i) >= horizon_days
    # No trading calendar available: be conservative in calendar days.
    need = int(math.ceil(horizon_days / _TRADING_DAYS_PER_CALENDAR_DAY)) + 2
    return _to_date(ev.date) + timedelta(days=need) <= _to_date(as_of)


def retrieve_analogs(
    req: ForecastRequest,
    corpus: Optional[Sequence[Event]] = None,
    k: int = DEFAULT_N_ANALOGS,
    *,
    prices_dir: Optional[Path] = None,
    events_path: Optional[Path] = None,
    corpus_dir: Optional[Path] = None,
) -> Tuple[List[Event], np.ndarray]:
    """STAGE 1. Return (analogs, similarity scores) sorted best-first.

    Hard-filtered so that every returned analog's ENTIRE realized forward
    window closes at or before `req.as_of_date`.
    """
    pool = list(corpus) if corpus is not None else load_seed_corpus(events_path, corpus_dir)
    as_of = _iso(req.as_of_date)
    h = DEFAULT_HORIZON_DAYS if req.horizon_days is None else max(int(req.horizon_days), 1)

    series_cache: Dict[str, _PriceSeries] = {}

    def _ser(t: str) -> _PriceSeries:
        if t not in series_cache:
            series_cache[t] = _load_price_series(t, prices_dir)
        return series_cache[t]

    admissible = [ev for ev in pool
                  if _forward_window_closes_by(ev, as_of, h, _ser(ev.ticker))]
    if not admissible:
        return [], np.zeros(0)

    docs = [_event_document(ev) for ev in admissible]
    text = _tfidf_scores(req.event_text or "", docs)
    if text.max(initial=0.0) > 0:
        text = text / text.max()

    q_dir, _ = _implied_direction(req.event_text or "")
    q_mag = _implied_magnitude(req.event_text or "")
    q_anchor = _severity_anchor(req.event_text or "")
    tick = req.ticker.upper()

    score = np.zeros(len(admissible))
    for i, ev in enumerate(admissible):
        s = W_TEXT * float(text[i])
        s += W_TICKER * (1.0 if ev.ticker == tick else 0.0)
        if q_dir != "unknown":
            s += W_DIRECTION * (1.0 if ev.direction == q_dir else 0.0)
        else:
            s += W_DIRECTION * 0.5
        target = q_mag if q_mag is not None else q_anchor
        s += W_MAGNITUDE * math.exp(-abs(abs(ev.move_pct) - target) / 0.20)
        want_major = target >= TIER_MAJOR
        is_major = abs(ev.move_pct) >= TIER_MAJOR
        s += W_MAGNITUDE * 0.35 * (1.0 if want_major == is_major else 0.0)
        score[i] = s

    order = np.argsort(-score)[: max(int(k), 1)]
    return [admissible[i] for i in order], score[order]


def _analog_forward_matrix(
    analogs: Sequence[Event], horizon_days: int, as_of: str,
    prices_dir: Optional[Path] = None,
) -> Tuple[np.ndarray, List[Event], List[str]]:
    """VOL-STANDARDIZED realized forward windows for each analog: (n_usable, h).

    This is filtered historical simulation (Barone-Adesi / Engle / Mancini), and
    it is not cosmetic. Pooling RAW forward returns across analogs mixes a 2001
    NVDA window with a 2016 JPM window, so the pooled sigma is dominated by
    whichever name was most volatile and the ensemble comes out far too wide --
    measured at 1.38x the null and -12.7% CRPS lift on real 2010-2019 events.

    Each analog's forward window is therefore divided by THAT analog's own
    trailing-250d sigma as of its own event date, using only bars at or before
    it. The result is dimensionless "how many of its own sigmas did it move",
    which is comparable across names and eras, and the caller rescales it to
    the requested name's current trailing sigma.

    Returns (standardized matrix, analogs actually usable, warnings).
    """
    rows, kept, warn = [], [], []
    n_synth = 0
    for ev in analogs:
        ser = _load_price_series(ev.ticker, prices_dir)
        if "SYNTHETIC-FALLBACK" in ser.source:
            n_synth += 1
        i = ser.index_of(ev.date)
        j = ser.index_of(as_of)
        if i < 0 or j < 0 or (j - i) < horizon_days:
            continue
        r = ser.logret[i: i + horizon_days]          # bars i+1 .. i+horizon
        if r.size != horizon_days or not np.all(np.isfinite(r)):
            continue
        # Trailing sigma AT THE ANALOG'S OWN EVENT DATE -- no lookahead, and it
        # is the analog's own information set, not ours.
        sig_a, _ = _trailing_vol(ser, ev.date)
        if not (sig_a > 1e-8):
            continue
        rows.append(r / sig_a)                       # standardized
        kept.append(ev)
    if n_synth:
        warn.append(
            f"SYNTHETIC PRICE FALLBACK: {n_synth} analog(s) drew forward windows from "
            "clearly-labelled synthetic prices because no real price data was on disk. "
            "Do not report these numbers as real."
        )
    if not rows:
        return np.zeros((0, horizon_days)), [], warn
    return np.vstack(rows), kept, warn


# ===========================================================================
# 4.  STAGE 2a -- the scenario prior (LLM, or a LOUD deterministic fallback)
# ===========================================================================

@dataclass
class ScenarioPrior:
    """A small regime prior over the horizon. Never a point prediction."""
    names: List[str]
    weights: List[float]
    drift_5d: List[float]        # cumulative LOG drift over a 5-day horizon
    vol_mult: List[float]
    source: str                  # "llm:<model>" | "heuristic-fallback" | "neutral"
    reasoning: str = ""
    raw: str = ""
    to_dict = asdict

    def sample(self, rng: np.random.Generator, n: int) -> Tuple[np.ndarray, np.ndarray]:
        w = np.asarray(self.weights, dtype=float)
        w = w / w.sum() if w.sum() > 0 else np.full(len(w), 1.0 / len(w))
        idx = rng.choice(len(w), size=n, p=w)
        return np.asarray(self.drift_5d)[idx], np.asarray(self.vol_mult)[idx]

    @property
    def expected_drift_5d(self) -> float:
        w = np.asarray(self.weights, float)
        w = w / w.sum() if w.sum() > 0 else np.full(len(w), 1.0 / len(w))
        return float(np.dot(w, np.asarray(self.drift_5d, float)))

    @property
    def expected_vol_mult(self) -> float:
        w = np.asarray(self.weights, float)
        w = w / w.sum() if w.sum() > 0 else np.full(len(w), 1.0 / len(w))
        return float(np.dot(w, np.asarray(self.vol_mult, float)))


_PRIOR_SYSTEM = (
    "You are a component inside a probabilistic forecasting system. You do NOT predict a "
    "price or a return. You describe a small set of REGIMES the next few trading days could "
    "fall into, given an event description, and how wide each regime is. Someone else does "
    "the sampling. Output JSON only."
)

_PRIOR_TEMPLATE = """Event description for {ticker} ({name}), as of {as_of}:
\"\"\"{event_text}\"\"\"

Return 2 to {max_s} scenarios for the NEXT {h} TRADING DAYS. JSON only, this exact schema:

{{"scenarios":[{{"name":"short label","weight":0.0-1.0,
                 "drift_5d":-0.35..0.35,"vol_multiplier":0.5..3.0}}],
  "reasoning":"one sentence, under 30 words"}}

Rules:
- weights must sum to about 1.0.
- drift_5d is the CUMULATIVE LOG return of that scenario's centre over 5 trading days.
  It is a regime centre, not a prediction. Keep it modest; |drift_5d| > 0.20 needs a
  genuinely extreme, already-public catalyst.
- vol_multiplier scales dispersion relative to this name's normal volatility. A large
  surprise widens it. 1.0 means "no wider than usual".
- You must include at least one scenario whose drift_5d has the OPPOSITE sign to your
  most-weighted scenario. Markets frequently fade the first move.
- Reason from the described event only. Do not use knowledge of what actually happened
  after {as_of} to this company.
No prose, no markdown fences, JSON only."""


def _clamp_prior(obj: Dict[str, Any], source: str, raw: str) -> Optional[ScenarioPrior]:
    scen = obj.get("scenarios")
    if not isinstance(scen, list) or not scen:
        return None
    names, ws, ds, vs = [], [], [], []
    for s in scen[:MAX_SCENARIOS]:
        if not isinstance(s, dict):
            continue
        try:
            w = float(s.get("weight", 0.0))
            d = float(s.get("drift_5d", 0.0))
            v = float(s.get("vol_multiplier", 1.0))
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(w) and math.isfinite(d) and math.isfinite(v)) or w <= 0:
            continue
        names.append(str(s.get("name", "scenario"))[:48])
        ws.append(w)
        ds.append(max(-MAX_PRIOR_DRIFT_5D, min(MAX_PRIOR_DRIFT_5D, d)))
        # Clamp, then compress toward 1.0 -- see LLM_WIDTH_TRUST.
        vs.append(max(MIN_VOL_MULT, min(MAX_VOL_MULT, v)) ** LLM_WIDTH_TRUST)
    if not ws:
        return None
    tot = sum(ws)
    ws = [w / tot for w in ws]
    return ScenarioPrior(names, ws, ds, vs, source,
                         str(obj.get("reasoning", ""))[:240], raw[:2000])


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        obj = json.loads(t[i: j + 1])
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _llm_prior_sdk(prompt: str, model: str, timeout_s: float) -> Optional[Tuple[Dict[str, Any], str, str]]:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic  # type: ignore

        client = anthropic.Anthropic(api_key=key, timeout=timeout_s, max_retries=0)
        msg = client.messages.create(
            model=model, max_tokens=600, system=_PRIOR_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        obj = _extract_json(text)
        return (obj, text, f"llm:{model}") if obj else None
    except Exception:
        return None


def _llm_prior_cli(prompt: str, model: str, timeout_s: float) -> Optional[Tuple[Dict[str, Any], str, str]]:
    """Claude Code CLI path. OFF by default: measured ~6s, over the demo budget.

    Enable with RULIAL_ALLOW_CLI_LLM=1 and a generous llm_timeout_s.
    """
    if os.environ.get("RULIAL_ALLOW_CLI_LLM", "") not in ("1", "true", "yes"):
        return None
    try:
        p = subprocess.run(
            ["claude", "-p", "--model", model],
            input=_PRIOR_SYSTEM + "\n\n" + prompt,
            capture_output=True, text=True, timeout=timeout_s,
        )
        obj = _extract_json(p.stdout)
        return (obj, p.stdout, f"llm-cli:{model}") if obj else None
    except Exception:
        return None


def _heuristic_prior(event_text: str, horizon_days: int) -> ScenarioPrior:
    """Deterministic no-LLM fallback. LOUD by design -- `source` says so."""
    toks = _tokens(event_text)
    dn = sum(1 for t in toks if t in _DOWN_WORDS)
    up = sum(1 for t in toks if t in _UP_WORDS)
    sev = sum(1 for t in toks if t in _SEVERE_WORDS)
    mag = _implied_magnitude(event_text)

    net = up - dn
    sign = 0.0 if net == 0 else (1.0 if net > 0 else -1.0)
    intensity = min(1.0, (abs(net) + sev) / 4.0)
    if mag is not None:
        intensity = max(intensity, min(1.0, mag / 0.40))

    # Deliberately timid: the recon result is that drift is where all the
    # spurious skill hides, so a keyword count is not allowed to bet much.
    lead = sign * min(0.12, 0.05 + 0.10 * intensity)
    # Calibrated to the measured post-jump realized/null sigma ratio of ~1.19x,
    # NOT to how dramatic the words are. Keyword counts do not get to triple
    # the width -- that is how an ensemble scores -52% lift.
    wide = 1.05 + 0.30 * intensity

    return ScenarioPrior(
        names=["continuation", "chop / digest", "fade the move"],
        weights=[0.40, 0.35, 0.25],
        drift_5d=[lead, 0.0, -0.55 * lead],
        vol_mult=[wide, max(MIN_VOL_MULT, 0.92 * wide), min(MAX_VOL_MULT, wide * 1.12)],
        source="heuristic-fallback",
        reasoning=(
            "NO LLM REACHED. Scenario prior came from a deterministic keyword count "
            f"({up} bullish / {dn} bearish / {sev} severity tokens"
            + (f", {mag:.0%} magnitude cited" if mag is not None else "")
            + "), not from reasoning about the event."
        ),
    )


def scenario_prior(
    req: ForecastRequest,
    *,
    use_llm: Any = "auto",
    model: str = "claude-haiku-4-5",
    llm_timeout_s: float = 4.0,
) -> ScenarioPrior:
    """STAGE 2a. Get the regime prior. Falls back LOUDLY."""
    if use_llm is False or str(use_llm).lower() in ("false", "off", "none", "0"):
        p = _heuristic_prior(req.event_text or "", req.horizon_days)
        p.source = "heuristic-fallback (LLM disabled by caller)"
        return p

    prompt = _PRIOR_TEMPLATE.format(
        ticker=req.ticker, name=TICKER_NAMES.get(req.ticker.upper(), req.ticker),
        as_of=_iso(req.as_of_date), event_text=(req.event_text or "")[:2000],
        h=req.horizon_days, max_s=MAX_SCENARIOS,
    )
    for fn in (_llm_prior_sdk, _llm_prior_cli):
        got = fn(prompt, model, llm_timeout_s)
        if got:
            obj, raw, src = got
            pri = _clamp_prior(obj, src, raw)
            if pri is not None:
                return pri

    p = _heuristic_prior(req.event_text or "", req.horizon_days)
    warnings.warn(
        "rulial.generator: NO LLM REACHABLE (no ANTHROPIC_API_KEY, and the CLI path is "
        "off unless RULIAL_ALLOW_CLI_LLM=1). Scenario prior fell back to a deterministic "
        "keyword heuristic. This is a degraded path -- see Ensemble.narrative and "
        "diagnostics['warnings'].",
        RuntimeWarning, stacklevel=2,
    )
    return p


# ===========================================================================
# 5.  STAGE 2b -- the RULE SET (this is the rulial part)
# ===========================================================================

@dataclass(frozen=True)
class GeneratorRule:
    """One rule in the rulial ensemble.

    analog_scope : "ticker"    -- only analogs on the requested name
                   "universe"  -- every retrieved analog
                   "direction" -- analogs matching the query's implied sign
                   "none"      -- ignore analogs entirely (the frozen null's shape)
    drift_mode   : "neutral"   -- analog windows demeaned, zero drift
                   "prior"     -- demeaned, then the clamped scenario drift added
                   "analog"    -- keep the analogs' realized drift  (THE TRAP)
    vol_anchor   : "analog" | "trailing" | "blend"
    block_len    : circular-block bootstrap length in trading days
    """
    name: str
    analog_scope: str
    drift_mode: str
    vol_anchor: str
    block_len: int
    weight: float
    note: str = ""


RULE_SET: Tuple[GeneratorRule, ...] = (
    GeneratorRule("neutral/ticker/blend/b1", "ticker", "neutral", "blend", 1, 0.10),
    GeneratorRule("neutral/ticker/analogvol/b5", "ticker", "neutral", "analog", 5, 0.08),
    GeneratorRule("neutral/universe/blend/b1", "universe", "neutral", "blend", 1, 0.10),
    GeneratorRule("neutral/universe/trailing/b2", "universe", "neutral", "trailing", 2, 0.09),
    GeneratorRule("neutral/direction/analogvol/b2", "direction", "neutral", "analog", 2, 0.08),
    GeneratorRule("prior/ticker/blend/b1", "ticker", "prior", "blend", 1, 0.10),
    GeneratorRule("prior/universe/blend/b1", "universe", "prior", "blend", 1, 0.10),
    GeneratorRule("prior/universe/analogvol/b5", "universe", "prior", "analog", 5, 0.09),
    GeneratorRule("prior/direction/blend/b2", "direction", "prior", "blend", 2, 0.08),
    GeneratorRule("prior/null-shape/trailing/b1", "none", "prior", "trailing", 1, 0.08,
                  "the frozen null living inside the ensemble -- keeps us honest"),
    GeneratorRule("TRAP:analog-drift/ticker/b5", "ticker", "analog", "analog", 5, 0.05,
                  "KEEPS the analogs' realized drift. Measured at +14.8% raw CRPS lift and "
                  "-4.5% demeaned on 2010-2019: that lift is bull-decade drift, not skill. "
                  "Held at 5% weight so we can MEASURE the temptation instead of denying it."),
    GeneratorRule("TRAP:analog-drift/universe/b1", "universe", "analog", "analog", 1, 0.05,
                  "see TRAP:analog-drift/ticker/b5"),
)


def _scope_analogs(rule: GeneratorRule, A: np.ndarray, analogs: List[Event],
                   ticker: str, q_dir: str) -> np.ndarray:
    """Rows of A admissible under this rule's scope. Empty array => null shape."""
    if rule.analog_scope == "none" or A.shape[0] == 0:
        return np.zeros((0, A.shape[1] if A.size else 0))
    if rule.analog_scope == "ticker":
        m = np.array([ev.ticker == ticker for ev in analogs])
    elif rule.analog_scope == "direction":
        if q_dir == "unknown":
            m = np.ones(len(analogs), dtype=bool)
        else:
            m = np.array([ev.direction == q_dir for ev in analogs])
    else:
        m = np.ones(len(analogs), dtype=bool)
    sub = A[m] if m.any() else A          # graceful widening, never empty-by-scope
    return sub


def _robust_scale(x: np.ndarray, fallback: float = 1.0) -> float:
    """Interquartile scale, normalised to be a sigma for a Gaussian.

    MEASURED REASON, not taste. Standardized analog forward returns have
    kurtosis ~4.8 (Gaussian is 3), so their sample standard deviation is
    inflated ~1.23x by a handful of dot-com-era windows. Anchoring ensemble
    width on that inflated sd puts the ensemble at 1.62x the null's sigma and
    wrecks the PIT histogram (chi2 52.6 on 647 real train events, against 33.6
    for the null itself). The IQR scale is 0.812x the sd on this corpus, which
    lands the ensemble at 1.27x the null and flattens the PIT to chi2 6.6 --
    near-perfect for 9 degrees of freedom, and better calibrated than the null
    by a factor of five. Flat PIT is the contract's win condition (s7), so we
    anchor on the statistic the PIT histogram is actually testing.
    """
    x = np.asarray(x, dtype=float).ravel()
    x = x[np.isfinite(x)]
    if x.size < 8:
        return fallback
    q1, q3 = np.quantile(x, [0.25, 0.75])
    s = float(q3 - q1) / 1.349
    return s if s > 1e-9 else fallback


def _block_bootstrap(rng: np.random.Generator, A: np.ndarray, n: int,
                     h: int, block_len: int, per_path_analog: bool = True) -> np.ndarray:
    """Circular block bootstrap WITHIN one analog's forward window.

    `per_path_analog=True` draws ONE analog per path and takes every block from
    it. That matters more than it looks: splicing blocks from different analogs
    inside a single path averages their volatility levels together, and the
    resulting ensemble is too smooth in the centre (measured: PIT middle bins
    over-populated at 18/18/20 against 14.5 expected). Holding the analog fixed
    per path makes the ensemble a genuine SCALE MIXTURE -- peaked centre, heavy
    tails, the actual shape of post-event returns -- and it makes each path
    mean something you can say out loud: "this future resembles the aftermath
    of NVDA 2018-11-20".

    Blocks never splice across two different events either way, so within-block
    serial structure is always a real observed sequence.

    Returns (n, h) standardized daily log returns.
    """
    n_a, w = A.shape
    L = max(1, min(int(block_len), w))
    n_blocks = int(math.ceil(h / L))
    if per_path_analog:
        ai = np.repeat(rng.integers(0, n_a, size=(n, 1)), n_blocks, axis=1)
    else:
        ai = rng.integers(0, n_a, size=(n, n_blocks))
    st = rng.integers(0, w, size=(n, n_blocks))
    offs = np.arange(L)
    idx = (st[:, :, None] + offs[None, None, :]) % w
    samp = A[ai[:, :, None], idx].reshape(n, n_blocks * L)[:, :h]
    return samp


def _run_rule(
    rule: GeneratorRule, rng: np.random.Generator, n: int, h: int,
    A_all: np.ndarray, analogs: List[Event], ticker: str, q_dir: str,
    trailing_sigma_d: float, prior: ScenarioPrior,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Generate `n` daily-log-return paths (n, h) under one rule."""
    Z = _scope_analogs(rule, A_all, analogs, ticker, q_dir)
    drift_5, vmult = prior.sample(rng, n)
    drift_h = drift_5 * (h / 5.0)

    # Everything below is in UNITS OF THE NAME'S OWN TRAILING SIGMA, then
    # rescaled once at the end. `vmult` is the prior's width statement relative
    # to normal volatility; `sd_z` is what the analogs say post-event windows
    # actually run at (measured ~1.2 sigma on real data). They are ALTERNATIVE
    # width estimates, never multiplied together -- stacking them double-counts
    # and an early build that did so ran 2.57x too wide for -52% CRPS lift.
    if Z.shape[0] == 0:
        # No admissible analogs -> the frozen null's shape: iid Gaussian. This
        # is also the zero-analog fallback for the whole forecast and it must
        # never crash. Here the prior owns the width outright, because there is
        # nothing else to condition on.
        base = rng.standard_normal((n, h)) * (trailing_sigma_d * vmult)[:, None]
        sigma_used = float(trailing_sigma_d * np.mean(vmult))
        analog_mu_d = 0.0
        n_used = 0
    else:
        raw = _block_bootstrap(rng, Z, n, h, rule.block_len)
        mu_z = float(Z.mean())
        # sd_z is the DIVISOR (it is what `raw` actually has); rb_z is the
        # TARGET. They differ by the kurtosis inflation described in
        # _robust_scale, and that difference is the whole calibration fix.
        sd_z = float(Z.std(ddof=1)) if Z.size > 1 else 1.0
        sd_z = sd_z if sd_z > 1e-8 else 1.0
        rb_z = _robust_scale(Z, fallback=sd_z)
        if rule.vol_anchor == "analog":
            mult = np.full(n, rb_z)                  # pure data; prior ignored
        elif rule.vol_anchor == "trailing":
            mult = vmult                             # prior owns the width
        else:
            mult = np.sqrt(rb_z * np.maximum(vmult, 1e-8))   # geometric blend
        base = (raw - mu_z) * (mult / sd_z)[:, None] * trailing_sigma_d
        # Horizon aggregation correction -- see HORIZON_CALIBRATION. Applied
        # only on the analog path: the zero-analog branch above IS the frozen
        # null and must keep the null's exact width.
        base = base * HORIZON_CALIBRATION
        sigma_used = float(trailing_sigma_d * np.mean(mult) * HORIZON_CALIBRATION)
        analog_mu_d = mu_z * trailing_sigma_d
        n_used = int(Z.shape[0])

    paths = base

    # Location: this is where the discipline lives.
    if rule.drift_mode == "neutral":
        add = np.zeros(n)
    elif rule.drift_mode == "prior":
        add = drift_h
    else:                                   # "analog" -- the labelled trap
        add = np.full(n, analog_mu_d * h)
    paths = paths + (add / h)[:, None]

    meta = {
        "rule": rule.name,
        "analogs_used": n_used,
        "sigma_daily_used": sigma_used,
        "analog_mean_daily": analog_mu_d,
        "mean_drift_added_h": float(np.mean(add)),
        "n_paths": int(n),
        "note": rule.note,
    }
    return paths, meta


# ===========================================================================
# 6.  STAGE 3 -- coarse-grain, and the public entry point
# ===========================================================================

def _quantiles(cum: np.ndarray) -> Dict[str, float]:
    q = np.quantile(cum, [0.05, 0.25, 0.50, 0.75, 0.95])
    return {"p5": float(q[0]), "p25": float(q[1]), "p50": float(q[2]),
            "p75": float(q[3]), "p95": float(q[4])}


def _fmt_pct(x: float) -> str:
    return f"{x * 100:+.1f}%"


def _build_narrative(req: ForecastRequest, analogs: List[Event], sims: np.ndarray,
                     qs: Dict[str, float], prior: ScenarioPrior,
                     rule_stats: List[Dict[str, Any]], zero_analog: bool,
                     price_source: str) -> str:
    n_rules = len(rule_stats)
    meds = [s["p50"] for s in rule_stats if s.get("p50") is not None]
    spread = (max(meds) - min(meds)) if len(meds) > 1 else 0.0

    if zero_analog:
        s1 = (f"No historical analog for this description closes its forward window on or before "
              f"{_iso(req.as_of_date)}, so this ensemble falls back to the unconditional null: "
              f"a zero-drift Gaussian at {req.ticker}'s trailing 250-day volatility, widened "
              f"{prior.expected_vol_mult:.2f}x by the scenario prior.")
        s2 = (f"Over {req.horizon_days} trading days the median is {_fmt_pct(qs['p50'])} with a "
              f"90% interval of [{_fmt_pct(qs['p5'])}, {_fmt_pct(qs['p95'])}].")
        s3 = ("Treat this as a width statement, not a forecast: with no analogs there is no "
              "conditional information in it beyond the event text's implied severity.")
        return " ".join([s1, s2, s3])

    top = analogs[:3]
    named = ", ".join(f"{e.ticker} {e.date} ({_fmt_pct(e.move_pct)})" for e in top)
    s1 = (f"Sampled {sims.size:,} forward paths for {req.ticker} over {req.horizon_days} trading "
          f"days as a weighted mixture of {n_rules} generator rules, seeded by {len(analogs)} "
          f"historical analogs that all closed on or before {_iso(req.as_of_date)} -- closest: {named}.")
    s2 = (f"The coarse-grained result: median {_fmt_pct(qs['p50'])}, 90% interval "
          f"[{_fmt_pct(qs['p5'])}, {_fmt_pct(qs['p95'])}]; the scenario prior ({prior.source}) "
          f"contributed an expected {_fmt_pct(prior.expected_drift_5d)} 5-day drift on the 45% of "
          f"paths that accept drift, and a {prior.expected_vol_mult:.2f}x width multiplier on all of them.")
    s3 = (f"Changing the generator rule moves the median by {spread * 100:.1f} percentage points, "
          f"which is our honest uncertainty about the rule itself rather than about the noise draw"
          + (f"; note prices came from a {price_source} source." if "SYNTHETIC-FALLBACK" in price_source
             else "."))
    return " ".join([s1, s2, s3])


def assert_no_lookahead(analogs: Sequence[Event], as_of_date: str, horizon_days: int,
                        prices_dir: Optional[Path] = None) -> None:
    """HARD LEAK GUARD (CONTRACT.md s2). Raises LookaheadError on any violation.

    Two separate checks, because the obvious one is not sufficient:
      (1) no analog may be dated after as_of_date; and
      (2) no analog's realized FORWARD WINDOW may extend past as_of_date -- an
          event three days before as_of has a five-day outcome we cannot know.
    """
    as_of = _iso(as_of_date)
    for ev in analogs:
        if ev.date > as_of:
            raise LookaheadError(
                f"LOOKAHEAD: analog {ev.ticker} {ev.date} is dated after as_of_date {as_of}."
            )
        ser = _load_price_series(ev.ticker, prices_dir)
        if not _forward_window_closes_by(ev, as_of, horizon_days, ser):
            raise LookaheadError(
                f"LOOKAHEAD: analog {ev.ticker} {ev.date} has a {horizon_days}-day forward "
                f"window that has not closed by as_of_date {as_of}. Its realized outcome is "
                "unknowable at that moment and must not shape the ensemble."
            )
    # Plain asserts too, so the intent is visible at the call site.
    assert all(_iso(e.date) <= as_of for e in analogs), "analog date > as_of_date"


def generate_ensemble(
    req: ForecastRequest,
    *,
    seed: Optional[int] = None,
    corpus: Optional[Sequence[Event]] = None,
    n_analogs: int = DEFAULT_N_ANALOGS,
    use_llm: Any = "auto",
    llm_model: str = "claude-haiku-4-5",
    llm_timeout_s: float = 4.0,
    prices_dir: Optional[Path] = None,
    events_path: Optional[Path] = None,
    corpus_dir: Optional[Path] = None,
    keep_path_matrix: bool = False,
) -> Ensemble:
    """Generate the conditional forward-return ensemble. CONTRACT.md s4/s5.

    Parameters
    ----------
    req              ForecastRequest. `as_of_date` is a hard wall.
    seed             int -> exact reproducibility. None -> deterministically
                     derived from the request, so the same request always
                     yields the same ensemble.
    corpus           Optional pre-loaded list[Event]; otherwise read from disk.
    use_llm          "auto" (default) | False. "auto" tries the Anthropic SDK,
                     then the Claude CLI if RULIAL_ALLOW_CLI_LLM=1, then falls
                     back LOUDLY to a deterministic keyword prior.
    keep_path_matrix Attach the full (n_paths, horizon) daily matrix to
                     diagnostics. Off by default to keep responses small.

    Returns
    -------
    Ensemble, with `paths` = terminal CUMULATIVE SIMPLE returns (contract s5).

    An extra `.diagnostics` dict is attached to the instance. It is NOT a
    dataclass field, so `asdict(ens)` / `ens.to_dict()` stay contract-shaped
    and the API serializes unchanged. LANE-EVAL should read:
        diagnostics["paths_demeaned"]      zero-drift twin, for drift-decomposed lift
        diagnostics["drift_decomposition"] mean with and without drift
        diagnostics["rulial_dispersion"]   per-rule quantiles + cross-rule spread
        diagnostics["warnings"]            loud strings for the UI
    or simply call `demeaned_twin(ens)`.
    """
    t0 = datetime.now()
    h = DEFAULT_HORIZON_DAYS if req.horizon_days is None else int(req.horizon_days)
    n = DEFAULT_N_PATHS if req.n_paths is None else int(req.n_paths)
    if h < 1:
        raise ValueError("horizon_days must be >= 1")
    if n < 2:
        raise ValueError("n_paths must be >= 2")
    as_of = _iso(req.as_of_date)
    ticker = req.ticker.upper()
    rng = np.random.default_rng(_seed_from_request(req) if seed is None else int(seed))

    warns: List[str] = [LEAKAGE_DISCLOSURE]

    # ---- price context (the null's width) ---------------------------------
    series = _load_price_series(ticker, prices_dir)
    if series.dates and series.dates[-1] > as_of:
        # We only ever read up to as_of; assert we never index past it.
        assert series.index_of(as_of) < len(series.dates), "price index past as_of"
    trailing_sigma_d, n_vol_obs = _trailing_vol(series, as_of)
    if "SYNTHETIC-FALLBACK" in series.source:
        warns.append(
            f"SYNTHETIC PRICE FALLBACK for {ticker}: no real price data on disk, so the "
            "trailing-volatility anchor and every analog forward window are synthetic. "
            "CLEARLY LABELLED -- do not report these numbers as real."
        )
    if n_vol_obs < NULL_VOL_LOOKBACK:
        warns.append(
            f"Trailing volatility used only {n_vol_obs} of {NULL_VOL_LOOKBACK} bars before {as_of}."
        )

    # ---- STAGE 1: RETRIEVE -------------------------------------------------
    analogs, sim = retrieve_analogs(
        req, corpus=corpus, k=n_analogs, prices_dir=prices_dir,
        events_path=events_path, corpus_dir=corpus_dir,
    )
    assert_no_lookahead(analogs, as_of, h, prices_dir)          # HARD LEAK GUARD

    A, analogs, mat_warn = _analog_forward_matrix(analogs, h, as_of, prices_dir)
    warns.extend(mat_warn)
    zero_analog = A.shape[0] == 0
    if zero_analog:
        warns.append(
            f"ZERO ANALOGS for this request ({ticker} @ {as_of}). The ensemble degrades to the "
            "unconditional null (zero-drift Gaussian at trailing 250d sigma), widened only by the "
            "scenario prior. Six of the ten universe tickers have no train-period events at the "
            "frozen 25%/5-day threshold, so this path is expected, not a bug."
        )

    # ---- STAGE 2a: scenario prior -----------------------------------------
    prior = scenario_prior(req, use_llm=use_llm, model=llm_model, llm_timeout_s=llm_timeout_s)
    if prior.source.startswith("heuristic-fallback"):
        warns.append(
            "NO LLM IN THIS FORECAST: the scenario prior is a deterministic keyword heuristic, "
            "not model reasoning. " + prior.reasoning
        )

    q_dir, _ = _implied_direction(req.event_text or "")

    # ---- STAGE 2b: mixture over the rulial rule set ------------------------
    w = np.array([r.weight for r in RULE_SET], dtype=float)
    w = w / w.sum()
    counts = np.floor(w * n).astype(int)
    counts[np.argmax(w)] += n - counts.sum()          # exact n_paths
    counts = np.maximum(counts, 0)

    blocks, rule_stats = [], []
    for rule, c in zip(RULE_SET, counts):
        if c <= 0:
            continue
        p, meta = _run_rule(rule, rng, int(c), h, A, analogs, ticker, q_dir,
                            trailing_sigma_d, prior)
        cum_r = np.expm1(p.sum(axis=1))
        meta.update({
            "weight": float(rule.weight),
            "p5": float(np.quantile(cum_r, 0.05)),
            "p50": float(np.quantile(cum_r, 0.50)),
            "p95": float(np.quantile(cum_r, 0.95)),
            "mean": float(cum_r.mean()),
            "std": float(cum_r.std(ddof=1)) if cum_r.size > 1 else 0.0,
            "drift_mode": rule.drift_mode,
            "analog_scope": rule.analog_scope,
            "vol_anchor": rule.vol_anchor,
            "block_len": int(rule.block_len),
        })
        blocks.append(p)
        rule_stats.append(meta)

    daily = np.vstack(blocks)                          # (n, h) daily log returns
    order = rng.permutation(daily.shape[0])            # de-block so slices are unbiased
    daily = daily[order]

    # ---- STAGE 3: COARSE-GRAIN --------------------------------------------
    cum_log = daily.sum(axis=1)
    cum = np.expm1(cum_log)                            # cumulative SIMPLE returns
    qs = _quantiles(cum)
    mean = float(cum.mean())
    std = float(cum.std(ddof=1))

    # drift-decomposed twin for LANE-EVAL (recon: raw analog lift is 100% drift)
    demeaned = np.expm1(cum_log - cum_log.mean())

    fan = []
    running = np.cumsum(daily, axis=1)
    for d in range(h):
        col = np.expm1(running[:, d])
        fan.append({
            "day": d + 1,
            "p5": float(np.quantile(col, 0.05)), "p25": float(np.quantile(col, 0.25)),
            "p50": float(np.quantile(col, 0.50)), "p75": float(np.quantile(col, 0.75)),
            "p95": float(np.quantile(col, 0.95)),
        })

    meds = [s["p50"] for s in rule_stats]
    p95s = [s["p95"] for s in rule_stats]
    narrative = _build_narrative(req, analogs, cum, qs, prior, rule_stats,
                                 zero_analog, series.source)

    ens = Ensemble(
        ticker=ticker,
        as_of_date=as_of,
        horizon_days=h,
        paths=[float(x) for x in cum],
        quantiles=qs,
        mean=mean,
        std=std,
        analogs=list(analogs),
        narrative=narrative,
    )

    null_sigma_h = trailing_sigma_d * math.sqrt(h)
    ens.diagnostics = {                                # type: ignore[attr-defined]
        "seed": int(_seed_from_request(req) if seed is None else seed),
        "elapsed_s": (datetime.now() - t0).total_seconds(),
        "price_source": series.source,
        "trailing_sigma_daily": trailing_sigma_d,
        "trailing_vol_obs": n_vol_obs,
        "null_sigma_horizon": null_sigma_h,
        "ensemble_sigma_over_null": (std / null_sigma_h) if null_sigma_h > 0 else float("nan"),
        "n_analogs_retrieved": len(analogs),
        "analog_similarity_top": [float(x) for x in sim[: len(analogs)]],
        "analog_ids": [f"{e.ticker}:{e.date}" for e in analogs],
        "zero_analog_fallback": bool(zero_analog),
        "implied_direction": q_dir,
        "prior": prior.to_dict(),
        "prior_source": prior.source,
        "rulial_dispersion": {
            "per_rule": rule_stats,
            "median_spread": float(max(meds) - min(meds)) if len(meds) > 1 else 0.0,
            "p95_spread": float(max(p95s) - min(p95s)) if len(p95s) > 1 else 0.0,
            "n_rules": len(rule_stats),
        },
        "drift_decomposition": {
            "mean_with_drift": mean,
            "mean_demeaned": float(demeaned.mean()),
            "drift_contribution_log": float(cum_log.mean()),
            "trap_rule_weight": float(sum(r.weight for r in RULE_SET if r.drift_mode == "analog")),
            "prior_rule_weight": float(sum(r.weight for r in RULE_SET if r.drift_mode == "prior")),
        },
        "paths_demeaned": [float(x) for x in demeaned],
        "fan_by_day": fan,
        "warnings": warns,
        "leakage_disclosure": LEAKAGE_DISCLOSURE,
    }
    if keep_path_matrix:
        ens.diagnostics["path_matrix"] = daily.tolist()   # type: ignore[attr-defined]
    return ens


def demeaned_twin(ens: Ensemble) -> Ensemble:
    """A zero-drift copy of `ens`, for drift-decomposed CRPS lift (LANE-EVAL).

    The measured trap: a naive analog generator scores +14.8% CRPS lift raw and
    -4.5% demeaned on 2010-2019, because the train corpus is 30 up-jumps to 3
    down-jumps. Report both numbers or the lift is not evidence of anything.
    """
    p = np.asarray(ens.paths, dtype=float)
    d = getattr(ens, "diagnostics", None)
    if isinstance(d, dict) and d.get("paths_demeaned"):
        dm = np.asarray(d["paths_demeaned"], dtype=float)
    else:
        lg = np.log1p(p)
        dm = np.expm1(lg - lg.mean())
    out = Ensemble(
        ticker=ens.ticker, as_of_date=ens.as_of_date, horizon_days=ens.horizon_days,
        paths=[float(x) for x in dm], quantiles=_quantiles(dm),
        mean=float(dm.mean()), std=float(dm.std(ddof=1)) if dm.size > 1 else 0.0,
        analogs=list(ens.analogs),
        narrative="DEMEANED TWIN (zero drift) of: " + ens.narrative,
    )
    out.diagnostics = {"demeaned_twin_of": ens.as_of_date, "warnings": [  # type: ignore
        "This ensemble has had its drift removed. Use it to check whether CRPS lift "
        "survives without an assumed drift. On 2010-2019 train data it does not."
    ]}
    return out
