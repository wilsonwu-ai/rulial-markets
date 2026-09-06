"""
rulial.inverse -- the inverse scenario solver.  (CONTRACT.md s6b, "Pavel's inversion")

The forward model answers "given this event, what is the distribution?".
This module inverts it: "given a target probability, what event would produce
it?".

--------------------------------------------------------------------------
THE ONE RULE THAT MAKES THIS FEATURE HONEST
--------------------------------------------------------------------------
`achieved_prob` is ALWAYS computed by running the candidate event text back
through `generator.generate_ensemble` and measuring the fraction of simulated
paths that end in the requested direction.  An LLM may PROPOSE the text.  It
may NEVER state the number.  If a proposed event is drafted as "57% bearish"
and the forward model computes 43%, this module reports 43%.

Every guard that follows exists to keep that true:

  * `_verify()` is the only function in this file that produces a probability,
    and it produces it from `np.mean(paths < 0)` -- nothing else.
  * `_looks_like_probability_claim()` REJECTS any LLM-drafted candidate that
    tries to assert a probability, an odds statement or a "% chance".
  * Nothing here touches `vol_mult`.  Over-widening the ensemble to hit a
    target was already measured at -52% CRPS lift in LANE-MODEL's recon; it
    games the metric and it is frozen out of this search by construction --
    the ONLY thing the search varies is the candidate event TEXT.
  * `as_of_date` is a hard wall, enforced twice: once in this module's own
    analog retrieval, and again inside `generate_ensemble`, which runs
    `assert_no_lookahead` on everything it retrieves.

--------------------------------------------------------------------------
THE MEASURED CEILING -- READ THIS BEFORE CALLING A MISS A BUG
--------------------------------------------------------------------------
The forward model deliberately holds ~45% of its rule-set weight at ZERO
drift (`RULE_SET` entries with `drift_mode="neutral"`), because LANE-MODEL
measured that all of the apparent skill in a naive analog generator came from
an assumed drift.  Those paths are a coin flip in every direction, by design.

That discipline puts a hard ceiling on P(direction).  With the deterministic
keyword prior (the no-LLM path), the reachable band on real tickers is
roughly 0.50 to 0.56.  It is not a wider band because the keyword prior's
drift saturates at |0.12| log over 5 days while its width keeps growing with
severity -- so past a certain point, MORE dramatic language makes the
probability go DOWN, not up.  That non-monotonicity is real and this search
handles it (it scans a dial, it does not just crank severity to maximum).

The consequence: a `target_prob` of 0.75 or 0.90 is OUTSIDE the reachable
band and WILL be missed.  This module measures the band explicitly with a
5-point calibration probe, reports it in `note`, and returns the closest
achievable scenario with the true `error`.  An honest miss with the ceiling
stated is the correct output.  The two ways to "fix" the miss -- widening the
ensemble, or letting the LLM assert the number -- are both frozen.

--------------------------------------------------------------------------
PIPELINE (CONTRACT.md s6b)
--------------------------------------------------------------------------
1. RETRIEVE  real ledger events for this ticker whose realized forward window
             closes on or before `as_of_date`; compute each one's realized
             forward move; rank them by how well they support the target.
             Widen to cross-ticker analogs when the name's own history is thin
             (META before 2013 is the motivating case) and SAY SO in `note`.
2. PROPOSE   candidate event texts grounded in `docs/research/<TICKER>.md`
             (which explains what actually caused each historical event, with
             sources) and in the real article titles in `data/corpus/`.
             LLM if reachable; LOUD templated recombination if not.
3. VERIFY    run every candidate through `generate_ensemble` and MEASURE.
4. SELECT    rank by |achieved - target|, dedupe near-identical texts,
             iterate a bounded 1-D search on the severity dial.

Public surface:
    solve_inverse(req: ScenarioRequest, ...) -> InverseResult
"""
from __future__ import annotations

import math
import os
import re
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .config import (
    REPO_ROOT,
    TICKER_NAMES,
    UNIVERSE,
    DEFAULT_HORIZON_DAYS,
    DEFAULT_N_PATHS,
)
from .types import Event, ForecastRequest
from . import generator as gen


# ===========================================================================
# 0.  Budgets and constants
# ===========================================================================

#: Hard cap on forward-model evaluations per request (CONTRACT.md s6b / brief).
MAX_FORWARD_EVALS = 40

#: Wall-clock budget. Round 1 always completes; later rounds stop early and
#: `note` says the budget cut the search, so a truncated search is never
#: silently reported as an exhausted one.
DEFAULT_TIME_BUDGET_S = 18.0

#: `target_prob` is clamped to this band (CONTRACT.md s6b request schema).
MIN_TARGET_PROB = 0.50
MAX_TARGET_PROB = 0.95

#: Below this many same-ticker admissible analogs we widen to the universe.
THIN_HISTORY_ANALOGS = 5

#: Candidate texts closer than this Jaccard similarity are treated as dupes.
DUPE_JACCARD = 0.82

#: Paths per verification run. Same default as the forward endpoint so a text
#: pasted into /api/forecast reproduces the same number.
VERIFY_N_PATHS = DEFAULT_N_PATHS

#: Coarse dial grid evaluated first. This IS the calibration probe: it maps
#: out the reachable probability band before the search tries to hit a target.
PROBE_DIALS = (0.0, 0.25, 0.50, 0.75, 1.00)

#: Cited-magnitude range the severity dial sweeps, as a fraction. The forward
#: model reads the largest percentage in the text (`_implied_magnitude`) and
#: uses it as its severity anchor, so this is the search's primary knob.
DIAL_MAG_LOW = 0.03
DIAL_MAG_HIGH = 0.45

_LOUD_NO_LLM = (
    "NO LLM REACHED FOR CANDIDATE DRAFTING. Every candidate event text below was "
    "assembled by DETERMINISTIC TEMPLATED RECOMBINATION of real analog headlines "
    "from docs/research/<TICKER>.md and real article titles from data/corpus/. "
    "It is string assembly, not model reasoning about the event. "
    "(achieved_prob is unaffected by this: it is computed by the forward model either way.)"
)

_NON_UNIQUE = (
    "The inverse is NOT unique: many different events map to the same probability, so "
    "this is a SET of candidates, never 'the' answer."
)


# ===========================================================================
# 1.  Public types
# ===========================================================================

@dataclass
class ScenarioRequest:
    """Request body for CONTRACT.md s6b POST /api/scenario."""
    ticker: str
    direction: str                      # "up" | "down"
    target_prob: float                  # 0.50 .. 0.95
    as_of_date: str                     # ISO
    horizon_days: int = DEFAULT_HORIZON_DAYS
    n_candidates: int = 3
    to_dict = asdict


@dataclass
class Scenario:
    """One verified candidate. `achieved_prob` is measured, never asserted."""
    event_text: str
    achieved_prob: float
    error: float
    quantiles: Dict[str, float]
    analogs_used: List[Event] = field(default_factory=list)
    narrative: str = ""
    verified: bool = False              # True ONLY when generate_ensemble ran
    to_dict = asdict


@dataclass
class InverseResult:
    target_prob: float
    direction: str
    ticker: str
    scenarios: List[Scenario] = field(default_factory=list)
    #: `None` (not 0.0, not 1.0) when NOTHING was verified. Emitting a numeric
    #: placeholder there would be fabricating a measurement, which this project
    #: is not allowed to do. CONTRACT.md s6b types it `float`; the deviation is
    #: deliberate and is reported to the parent.
    best_error: Optional[float] = None
    search_iterations: int = 0
    note: str = ""
    to_dict = asdict


# ===========================================================================
# 2.  Small helpers
# ===========================================================================

def _iso(d: Any) -> str:
    return gen._iso(d)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _tokset(text: str) -> frozenset:
    return frozenset(gen._tokens(text or ""))


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokset(a), _tokset(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / float(len(ta | tb))


_PROB_CLAIM_RE = re.compile(
    r"(probabilit|\bodds\b|\bchance\b|\blikelihood\b|\bconfidence\s+level\b"
    r"|\d+\s*%\s*(chance|probability|likely|odds|confident)"
    r"|(chance|probability|odds)\s+of\s+\d+)",
    re.IGNORECASE,
)


def _looks_like_probability_claim(text: str) -> bool:
    """Reject any drafted candidate that tries to state a probability.

    FROZEN (CONTRACT.md s6b): the LLM writes PROSE ONLY. A candidate that says
    "70% chance of a decline" is asserting the very number this endpoint is
    required to compute, so it never enters the pool. Magnitudes ("a 20%
    revenue miss") are fine and are the search's actual knob -- only
    probability-shaped language is rejected.
    """
    return bool(_PROB_CLAIM_RE.search(text or ""))


# ===========================================================================
# 3.  STAGE 1 -- RETRIEVE (real events, realized forward moves, as_of respected)
# ===========================================================================

@dataclass
class _Analog:
    """A real ledger event plus its realized forward move, as of `as_of_date`."""
    event: Event
    forward_return: float           # realized cumulative SIMPLE return over horizon
    same_ticker: bool
    cause: str = ""                 # from docs/research/<TICKER>.md, if found
    category: str = ""              # "earnings" | "guidance" | "macro" | ...
    headlines: List[str] = field(default_factory=list)   # real article titles
    #: True when the event's OWN move ran in the requested direction as well as
    #: its realized forward window. Prose grounding prefers these.
    aligned: bool = False


_RESEARCH_ROW_RE = re.compile(
    r"^\|\s*\*{0,2}(\d{4}-\d{2}-\d{2})\*{0,2}\s*\|(.*)$"
)

#: Clauses in the research headlines that describe the REALIZED PRICE MOVE
#: rather than the cause. They must be stripped before a headline is recycled
#: into a hypothetical event text -- otherwise the candidate text leaks the
#: outcome into the input, which is the whole thing this repo exists to avoid.
#
# Deliberately blunt: ANY clause led by "stock" / "shares" / "share price" is
# removed, not just ones with a recognised move verb. A whitelist of verbs kept
# missing new phrasings ("the stock loses 20.4% over November"), and a
# description of what CAUSED an event has no legitimate reason to mention the
# share price at all. Over-deleting costs a clause; under-deleting leaks the
# outcome into the model's input, which is the failure this repo exists to
# avoid. `\.(?=\d)` lets the match run through decimals like "18.8%".
_OUTCOME_CLAUSE_RE = re.compile(
    r"(?:^|[;.,]\s*)(?:the\s+|its\s+)?(?:stock|shares|share\s+price)\b"
    r"(?:[^;.]|\.(?=\d))*",
    re.IGNORECASE,
)
_LEADING_DATE_RE = re.compile(
    r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+"
    r"\d{1,2}(?!\d)(?:\s*,\s*\d{4})?\s*[:,]?\s*",
    re.IGNORECASE,
)


def _clean_cause(raw: str) -> str:
    """Turn a research-doc headline into a forward-looking CAUSE clause.

    Strips (a) the realized price move, which is outcome leakage, and (b) the
    leading calendar date, which anchors the text to a past day it should not
    claim to be.
    """
    s = (raw or "").strip().strip("*").strip()
    s = _OUTCOME_CLAUSE_RE.sub("", s)
    s = _LEADING_DATE_RE.sub("", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" ;,.")
    return s


#: SEC filing titles ("NVDA 8-K: Results of Operations and Financial Condition")
#: are real and correctly harvested, but they are boilerplate cover pages, not
#: descriptions of what happened. They stay in `analogs_used` as evidence and
#: are kept out of the prose grounding pool.
_SEC_TITLE_RE = re.compile(r"^[A-Z]{1,6}\s+(?:8-K|10-Q|10-K|S-1|S-4|6-K|20-F|DEF\s*14A)\b",
                           re.IGNORECASE)

#: Keyed by (ticker, research directory) -- NOT by ticker alone. Keying on the
#: ticker only meant a caller passing a different `research_dir` silently got
#: the first directory's parse back, which would make an isolated test or an
#: alternate corpus quietly read the repo's real files.
_RESEARCH_CACHE: Dict[Tuple[str, str], Dict[str, Tuple[str, str]]] = {}


def load_research_causes(ticker: str,
                         research_dir: Optional[Path] = None) -> Dict[str, Tuple[str, str]]:
    """Parse `docs/research/<TICKER>.md` -> {event_date: (category, cause)}.

    The research fleet wrote one file per ticker explaining what actually
    caused each ledger event, with sources. That is the best grounding
    available for drafting candidate texts that read like real market news.
    Missing or malformed file -> empty dict, never an exception.
    """
    t = (ticker or "").upper()
    base = Path(research_dir) if research_dir is not None else (REPO_ROOT / "docs" / "research")
    key = (t, str(base))
    if key in _RESEARCH_CACHE:
        return _RESEARCH_CACHE[key]
    out: Dict[str, Tuple[str, str]] = {}
    path = base / f"{t}.md"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        _RESEARCH_CACHE[key] = out
        return out

    # HEADER-DRIVEN, not fixed-index. The research files do not share one table
    # shape: AAPL.md carries an extra "Driver day inside window" column, and
    # BA.md / MSFT.md contain ledger-reproduction tables
    # ("| date | ledger move_pct | recomputed | base date |") whose rows are
    # also date-led. Reading column 3 blindly turned those into causes like
    # "2008-10-03" and "-0.223481". So: find a header row that names a Headline
    # column, take the indices from it, and ignore every date row that is not
    # under such a header.
    i_cat: Optional[int] = None
    i_head: Optional[int] = None
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            i_cat = i_head = None          # table ended
            continue
        cells = [c.strip().strip("*").strip() for c in s.strip("|").split("|")]
        low = [c.lower() for c in cells]
        if "headline" in low:              # this is a header row
            i_head = low.index("headline")
            i_cat = low.index("category") if "category" in low else None
            continue
        m = _RESEARCH_ROW_RE.match(s)
        if not m or i_head is None or len(cells) <= i_head:
            continue
        category = cells[i_cat].lower() if (i_cat is not None and i_cat < len(cells)) else ""
        cause = _clean_cause(cells[i_head])
        if cause:
            out[m.group(1)] = (category, cause)
    _RESEARCH_CACHE[key] = out
    return out


def _realized_forward(ev: Event, horizon_days: int, as_of: str,
                      prices_dir: Optional[Path] = None) -> Optional[float]:
    """The analog's REALIZED cumulative simple return over `horizon_days`.

    Returns None if the window does not close by `as_of` (the leak guard) or
    the price series cannot supply it.
    """
    ser = gen._load_price_series(ev.ticker, prices_dir)
    if not gen._forward_window_closes_by(ev, as_of, horizon_days, ser):
        return None
    i = ser.index_of(ev.date)
    j = ser.index_of(as_of)
    if i < 0 or j < 0 or (j - i) < horizon_days:
        return None
    r = ser.logret[i: i + horizon_days]
    if r.size != horizon_days or not np.all(np.isfinite(r)):
        return None
    return float(np.expm1(float(np.sum(r))))


def retrieve_analogs_for_target(
    ticker: str,
    direction: str,
    as_of_date: str,
    horizon_days: int,
    *,
    corpus: Optional[Sequence[Event]] = None,
    prices_dir: Optional[Path] = None,
    events_path: Optional[Path] = None,
    corpus_dir: Optional[Path] = None,
    research_dir: Optional[Path] = None,
) -> Tuple[List[_Analog], List[str]]:
    """STAGE 1. Real analogs supporting `direction`, ordered mild -> severe.

    Hard filter: an analog is admissible only if its ENTIRE realized forward
    window closes at or before `as_of_date`. Same guard as the forward path
    (`generator._forward_window_closes_by`), for the same reason: an event
    three days before `as_of` has a five-day outcome we could not have known.

    Cross-ticker widening kicks in below `THIN_HISTORY_ANALOGS` same-ticker
    analogs and is reported in the returned notes.
    """
    notes: List[str] = []
    tick = (ticker or "").upper()
    as_of = _iso(as_of_date)
    h = max(int(horizon_days or DEFAULT_HORIZON_DAYS), 1)
    want_down = direction == "down"

    pool = list(corpus) if corpus is not None else gen.load_seed_corpus(events_path, corpus_dir)

    own: List[_Analog] = []
    other: List[_Analog] = []
    causes_cache: Dict[str, Dict[str, Tuple[str, str]]] = {}

    for ev in pool:
        fwd = _realized_forward(ev, h, as_of, prices_dir)
        if fwd is None:
            continue
        if ev.ticker not in causes_cache:
            causes_cache[ev.ticker] = load_research_causes(ev.ticker, research_dir)
        cat, cause = causes_cache[ev.ticker].get(ev.date, ("", ""))
        a = _Analog(
            event=ev,
            forward_return=fwd,
            same_ticker=(ev.ticker == tick),
            cause=cause,
            category=cat,
            headlines=[t for t in (getattr(x, "title", "") for x in (ev.articles or []))
                       if t and not _SEC_TITLE_RE.match(t)][:4],
        )
        (own if a.same_ticker else other).append(a)

    n_own = len(own)
    pool_analogs = list(own)
    if n_own < THIN_HISTORY_ANALOGS:
        pool_analogs.extend(other)
        notes.append(
            f"CROSS-TICKER ANALOGS USED: {tick} has only {n_own} event(s) in the ledger whose "
            f"{h}-day forward window closes by {as_of}, which is below the {THIN_HISTORY_ANALOGS} "
            "needed to ground candidates on its own history. Candidates are additionally grounded "
            f"in {len(other)} cross-ticker analog(s) from the frozen universe."
        )

    if not pool_analogs:
        notes.append(
            f"ZERO ADMISSIBLE ANALOGS for {tick} as of {as_of}: no ledger event anywhere in the "
            f"universe has a {h}-day forward window closing by that date. Candidate texts fall "
            "back to generic, clearly-labelled templates and the forward model degrades to its "
            "unconditional null."
        )
        return [], notes

    # Keep only analogs that SUPPORT the requested direction -- a 90% down
    # target wants severe bearish analogs, a 55% target wants ambiguous ones,
    # and both live on the same axis: |forward_return| among direction-matching
    # events.
    #
    # "Supports" is checked on BOTH legs, and the second leg is not cosmetic.
    #   * forward_return sign  -- what the ensemble is actually bootstrapped from.
    #   * event.direction      -- what the candidate TEXT will be written from.
    # Requiring only the first produced candidates like "XOM revenue misses by
    # 24% ... the setup echoes TSLA 2013-04-01: Tesla pre-announces its first
    # ever quarterly profit", i.e. a bearish draft grounded in a bullish event.
    # The prose has to be coherent with the analog or the grounding claim is
    # decoration.
    fwd_ok = [a for a in pool_analogs
              if (a.forward_return < 0) == want_down and abs(a.forward_return) > 1e-9]
    if fwd_ok:
        supporting = fwd_ok
    else:
        supporting = pool_analogs
        notes.append(
            f"NO ANALOG with a {direction}-side realized {h}-day forward move is admissible for "
            f"{tick} as of {as_of}; grounding falls back to the full admissible pool "
            "regardless of sign."
        )

    for a in supporting:
        a.aligned = (a.event.direction == direction)

    n_aligned = sum(1 for a in supporting if a.aligned)
    if n_aligned == 0:
        notes.append(
            f"NO DIRECTION-COHERENT ANALOG: not one admissible event was itself a {direction}-side "
            f"move that then kept moving {direction}. Every candidate's 'echoes' clause therefore "
            "cites an event whose own move ran the other way, and says so by printing that "
            "event's signed move."
        )
    elif n_aligned < 4:
        notes.append(
            f"Only {n_aligned} of {len(supporting)} admissible analog(s) are {direction}-side moves "
            f"that ALSO kept moving {direction} over the next {h} days. Post-event mean reversion "
            "is the norm in this ledger, so direction-coherent analogs are genuinely scarce; "
            "candidates prefer them but will fall back to a severity-matched event of the "
            "opposite sign, with its signed move printed in the text."
        )

    if not any(a.same_ticker for a in supporting):
        notes.append(
            f"ZERO SAME-TICKER GROUNDING: none of {tick}'s own admissible events had a "
            f"{direction}-side realized {h}-day forward move, so every candidate below is "
            "grounded in another name's event. The borrowed ticker and date are printed inside "
            "each candidate's text."
        )

    # Mild -> severe. The severity dial indexes straight into this ordering.
    supporting.sort(key=lambda a: abs(a.forward_return))
    return supporting, notes


# ===========================================================================
# 4.  STAGE 2 -- PROPOSE
# ===========================================================================

#: Severity ladders, mild -> severe. Every phrase is built from vocabulary the
#: forward model's deterministic prior actually recognises
#: (`generator._DOWN_WORDS` / `_UP_WORDS` / `_SEVERE_WORDS`), so the dial moves
#: the model rather than only the prose.
_DOWN_LADDER = (
    "management flags a modest shortfall",
    "guidance is lowered and two analysts downgrade the stock",
    "the company warns on demand and cuts full-year guidance; analysts downgrade",
    "the company warns of a severe demand collapse, cuts guidance and takes a writedown; "
    "analysts downgrade",
    "the company warns of a catastrophic demand collapse, slashes guidance, discloses a "
    "writedown and confirms a regulatory investigation; analysts downgrade",
)
_UP_LADDER = (
    "results come in modestly ahead of consensus",
    "the company beats consensus and raises guidance; analysts upgrade the stock",
    "the company posts a strong beat, raises guidance on accelerating demand and wins new "
    "backlog; analysts upgrade",
    "the company posts a blowout beat, sharply raises guidance on record demand and announces "
    "a major partnership; analysts upgrade",
    "the company posts a blowout beat, triples its outlook on record datacenter-scale demand, "
    "announces a breakthrough design win and a buyback; analysts upgrade",
)

_METRIC_BY_CATEGORY = {
    "earnings": "quarterly revenue",
    "guidance": "next-quarter revenue guidance",
    "product": "unit shipments",
    "crisis": "quarterly revenue",
    "macro": "quarterly revenue",
    "regulatory": "quarterly revenue",
    "legal": "quarterly revenue",
    "geopolitical": "quarterly revenue",
    "commodity": "realized upstream revenue",
    "sector-rotation": "quarterly revenue",
}


def _dial_magnitude(dial: float) -> float:
    return DIAL_MAG_LOW + _clamp(dial, 0.0, 1.0) * (DIAL_MAG_HIGH - DIAL_MAG_LOW)


def _anchor_for_dial(analogs: Sequence[_Analog], dial: float,
                     variant: int = 0) -> Optional[_Analog]:
    """Pick the grounding analog at the dial's severity percentile.

    `analogs` is sorted mild -> severe, so the dial is literally a percentile
    into real history: dial 0 grounds the text in the most ambiguous real
    event, dial 1 in the most violent one.

    Preference order inside that percentile, strongest first:
      1. DIRECTION-COHERENT -- the analog's own move ran the requested way too.
         Without this, a bearish draft gets grounded in "Tesla pre-announces
         its first ever quarterly profit", and the grounding claim is
         decoration rather than evidence.
      2. SAME TICKER -- cross-ticker widening on a thin name otherwise buries
         XOM's three real events under a hundred borrowed ones, and "XOM,
         echoing NVDA" is a much weaker claim than "XOM, echoing XOM".
      3. Nearest in severity.

    Preference, not filter: the severity axis is what actually drives the
    ensemble, so we never drop events from it -- we only choose where in the
    neighbourhood to take the prose from.
    """
    n = len(analogs)
    if n == 0:
        return None
    i = int(round(_clamp(dial, 0.0, 1.0) * (n - 1)))
    span = max(1, int(round(0.12 * n)))
    lo, hi = max(0, i - span), min(n - 1, i + span)
    order = list(range(n))
    order.sort(key=lambda j: (
        not analogs[j].aligned,
        not (analogs[j].cause or analogs[j].headlines),   # prefer a sourced explanation
        not analogs[j].same_ticker,
        abs(j - i),
    ))
    # `lo`/`hi` are kept only to document the intended severity neighbourhood;
    # ordering runs over the whole list so that variant 2 walks to the next
    # direction-coherent analog rather than dropping to an incoherent one that
    # merely happens to sit closer in severity.
    del lo, hi
    return analogs[order[variant % len(order)]]


def _template_candidate(ticker: str, direction: str, dial: float,
                        anchor: Optional[_Analog], variant: int = 0) -> str:
    """Deterministic templated recombination of a REAL analog headline.

    This is the no-LLM fallback path and it is labelled as such in `note`.
    Grounding, in priority order:
      1. the cause line from docs/research/<TICKER>.md for the anchor event,
      2. a real article title from data/corpus/ for that event,
      3. a generic category template.
    """
    name = TICKER_NAMES.get(ticker.upper(), ticker.upper())
    ladder = _DOWN_LADDER if direction == "down" else _UP_LADDER
    li = int(round(_clamp(dial, 0.0, 1.0) * (len(ladder) - 1)))
    sev = ladder[li]
    mag = _dial_magnitude(dial)
    metric = _METRIC_BY_CATEGORY.get((anchor.category if anchor else ""), "quarterly revenue")

    ground = ""
    if anchor is not None:
        opts = [o for o in ([anchor.cause] + list(anchor.headlines)) if o]
        if opts:
            ground = _clean_cause(opts[variant % len(opts)])

    # Rotate the framing with `variant` so a diverse candidate set differs in
    # WHAT went wrong, not only in which analog it cites.
    framings = (
        f"{name} ({ticker.upper()}) {metric} "
        f"{'misses by' if direction == 'down' else 'beats by'} {mag * 100:.0f}%",
        f"{name} ({ticker.upper()}) guides {metric} "
        f"{mag * 100:.0f}% {'below' if direction == 'down' else 'above'} consensus",
        f"{name} ({ticker.upper()}) reports {metric} "
        f"{mag * 100:.0f}% {'short of' if direction == 'down' else 'ahead of'} plan",
    )
    head = framings[variant % len(framings)]

    if anchor is None:
        return f"{head}, and {sev}."

    # The provenance clause is part of the text on purpose: a judge can trace
    # any candidate back to a real, dated, sourced event. The anchor's SIGNED
    # move is printed so a direction-incoherent grounding cannot hide -- if the
    # only severity-matched analog available ran the other way, the text says
    # so rather than implying an agreement that is not there.
    ev = anchor.event
    rel = "echoes" if anchor.aligned else "is scaled against"
    tail = f"The setup {rel} {ev.ticker} {ev.date} ({ev.move_pct:+.0%} over " \
           f"{ev.window_days} days)"
    return f"{head}, and {sev}. {tail}: {ground}." if ground else f"{head}, and {sev}. {tail}."


_LLM_SYSTEM = (
    "You are a component inside a probabilistic forecasting system. You draft SHORT, "
    "plausible market-news event descriptions. You do NOT estimate probabilities, odds, "
    "chances or likelihoods -- another component measures those by simulation, and any "
    "probability you write would be discarded and your draft rejected. Output JSON only."
)

_LLM_TEMPLATE = """Draft {k} DISTINCT hypothetical news events for {name} ({ticker}), \
written as if they broke on {as_of}.

Ground them in these REAL historical events for this name (cause explanations come from \
sourced research):
{grounding}

Constraints, all mandatory:
- Each event must be {direction}-side news (bad news for "down", good news for "up").
- Each must cite the figure "{mag_pct:.0f}%" as the size of the business impact \
(a revenue/guidance/shipment miss or beat) -- keep that number exactly.
- 1 to 2 sentences. Concrete and specific: name the business line, the metric, the driver.
- Describe the CAUSE only. Never mention the share price, the stock reaction, or what \
happens next.
- NEVER state a probability, chance, odds or likelihood of anything.
- Do not use knowledge of what actually happened after {as_of}.

JSON only, exactly: {{"events":["...","..."]}}"""


def _llm_propose(ticker: str, direction: str, as_of: str, mag: float, k: int,
                 anchors: Sequence[_Analog], *, model: str, timeout_s: float,
                 steer: str = "") -> Tuple[List[str], Optional[str], Optional[str]]:
    """Ask an LLM for candidate PROSE. Returns (texts, source, error).

    The LLM never emits a probability -- the prompt forbids it and
    `_looks_like_probability_claim` enforces it on the way back in.
    """
    name = TICKER_NAMES.get(ticker.upper(), ticker.upper())
    lines = []
    for a in anchors[:5]:
        bits = [f"- {a.event.ticker} {a.event.date} ({a.event.move_pct:+.1%} over "
                f"{a.event.window_days} days, tier {a.event.tier})"]
        if a.cause:
            bits.append(f"cause: {a.cause}")
        elif a.headlines:
            bits.append(f"headline: {a.headlines[0]}")
        lines.append(": ".join(bits))
    prompt = _LLM_TEMPLATE.format(
        k=max(1, int(k)), name=name, ticker=ticker.upper(), as_of=as_of,
        grounding="\n".join(lines) or "- (no admissible analogs)",
        direction=direction, mag_pct=mag * 100.0,
    )
    if steer:
        prompt += "\n\nAdditional steer from the previous round: " + steer

    obj: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    err: Optional[str] = None

    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        try:
            import anthropic  # type: ignore

            client = anthropic.Anthropic(api_key=key, timeout=timeout_s, max_retries=0)
            msg = client.messages.create(
                model=model, max_tokens=900, system=_LLM_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
            obj = gen._extract_json(text)
            source = f"llm:{model}"
            if obj is None:
                err = "LLM replied but no JSON object could be parsed from it"
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
    else:
        err = "ANTHROPIC_API_KEY is not set"

    if obj is None and os.environ.get("RULIAL_ALLOW_CLI_LLM", "") in ("1", "true", "yes"):
        # Claude CLI path. OFF by default: measured at 80s+ on this machine,
        # four times the entire endpoint budget.
        try:
            p = subprocess.run(
                ["claude", "-p", "--model", model],
                input=_LLM_SYSTEM + "\n\n" + prompt,
                capture_output=True, text=True, timeout=timeout_s,
            )
            obj = gen._extract_json(p.stdout)
            source = f"llm-cli:{model}"
            if obj is None:
                err = "claude CLI replied but no JSON object could be parsed"
        except Exception as exc:  # noqa: BLE001
            err = f"claude CLI: {type(exc).__name__}: {exc}"

    if obj is None:
        return [], None, err

    raw = obj.get("events")
    if not isinstance(raw, list):
        return [], source, "LLM JSON had no 'events' list"

    out, rejected = [], 0
    for x in raw:
        if not isinstance(x, str):
            continue
        s = " ".join(x.split())[:600]
        if len(s) < 25:
            continue
        if _looks_like_probability_claim(s):
            rejected += 1
            continue
        out.append(s)
    if rejected:
        err = (f"{rejected} LLM candidate(s) REJECTED for asserting a probability -- "
               "CONTRACT.md s6b forbids the LLM stating the number.")
    return out, source, err


# ===========================================================================
# 5.  STAGE 3 -- VERIFY  (the only place a probability is produced)
# ===========================================================================

class _Verifier:
    """Runs `generate_ensemble` and MEASURES the directional probability.

    Memoized on the exact request tuple so an eval budget is spent on distinct
    texts, never on re-running one we already measured.
    """

    def __init__(self, ticker: str, as_of: str, horizon_days: int, direction: str,
                 *, seed: Optional[int], corpus: Optional[Sequence[Event]],
                 use_llm: Any, llm_model: str, llm_timeout_s: float,
                 prices_dir: Optional[Path], events_path: Optional[Path],
                 corpus_dir: Optional[Path], n_paths: int = VERIFY_N_PATHS,
                 max_evals: int = MAX_FORWARD_EVALS):
        self.ticker = ticker
        self.as_of = as_of
        self.h = horizon_days
        self.direction = direction
        self.seed = seed
        self.corpus = corpus
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.llm_timeout_s = llm_timeout_s
        self.prices_dir = prices_dir
        self.events_path = events_path
        self.corpus_dir = corpus_dir
        self.n_paths = int(n_paths)
        self.max_evals = int(max_evals)
        self.evals = 0
        self.errors: List[str] = []
        self._cache: Dict[str, Tuple[float, Any]] = {}

    @property
    def exhausted(self) -> bool:
        return self.evals >= self.max_evals

    def run(self, text: str) -> Optional[Tuple[float, Any]]:
        """-> (achieved_prob, Ensemble) or None. NEVER returns an asserted number."""
        if text in self._cache:
            return self._cache[text]
        if self.exhausted:
            return None
        self.evals += 1
        req = ForecastRequest(
            ticker=self.ticker, event_text=text, as_of_date=self.as_of,
            horizon_days=self.h, n_paths=self.n_paths,
        )
        try:
            ens = gen.generate_ensemble(
                req, seed=self.seed, corpus=self.corpus, use_llm=self.use_llm,
                llm_model=self.llm_model, llm_timeout_s=self.llm_timeout_s,
                prices_dir=self.prices_dir, events_path=self.events_path,
                corpus_dir=self.corpus_dir,
            )
        except Exception as exc:  # noqa: BLE001 -- a demo must degrade, not 500
            self.errors.append(f"generate_ensemble failed: {type(exc).__name__}: {exc}")
            return None
        p = np.asarray(ens.paths, dtype=float)
        p = p[np.isfinite(p)]
        if p.size == 0:
            self.errors.append("generate_ensemble returned no finite paths")
            return None
        # ---- THE ONLY PROBABILITY IN THIS MODULE -------------------------
        achieved = float((p < 0.0).mean()) if self.direction == "down" else float((p > 0.0).mean())
        # ------------------------------------------------------------------
        out = (achieved, ens)
        self._cache[text] = out
        return out


# ===========================================================================
# 6.  STAGE 4 -- SELECT + ITERATE, and the public entry point
# ===========================================================================

def _dedupe(cands: List[Tuple[str, float, Any]]) -> List[Tuple[str, float, Any]]:
    """Drop near-identical texts, keeping the better-scoring one."""
    kept: List[Tuple[str, float, Any]] = []
    for c in cands:
        if any(_jaccard(c[0], k[0]) >= DUPE_JACCARD for k in kept):
            continue
        kept.append(c)
    return kept


def _analogs_for_report(anchor: Optional[_Analog], ens: Any, limit: int = 5) -> List[Event]:
    """Which real events to attach to a scenario.

    Truthful answer: the grounding anchor (what the TEXT was written from),
    then the analogs the forward model actually retrieved (what the NUMBER was
    computed from). Deduped, capped, articles trimmed for payload size.
    """
    out: List[Event] = []
    seen = set()

    def _add(ev: Event) -> None:
        key = (ev.ticker, ev.date)
        if key in seen or len(out) >= limit:
            return
        seen.add(key)
        out.append(Event(
            ticker=ev.ticker, date=ev.date, move_pct=ev.move_pct, direction=ev.direction,
            window_days=ev.window_days, headline=ev.headline,
            articles=list(ev.articles or [])[:3], tier=ev.tier, famous=ev.famous,
        ))

    if anchor is not None:
        _add(anchor.event)
    for ev in (getattr(ens, "analogs", None) or []):
        _add(ev)
    return out


def solve_inverse(
    req: ScenarioRequest,
    *,
    seed: Optional[int] = None,
    corpus: Optional[Sequence[Event]] = None,
    use_llm: Any = "auto",
    llm_model: str = "claude-haiku-4-5",
    llm_timeout_s: float = 4.0,
    verify_use_llm: Any = False,
    max_evals: int = MAX_FORWARD_EVALS,
    time_budget_s: float = DEFAULT_TIME_BUDGET_S,
    n_paths: int = VERIFY_N_PATHS,
    prices_dir: Optional[Path] = None,
    events_path: Optional[Path] = None,
    corpus_dir: Optional[Path] = None,
    research_dir: Optional[Path] = None,
) -> InverseResult:
    """Solve CONTRACT.md s6b: target probability -> candidate events that produce it.

    Parameters
    ----------
    seed            Threaded straight through to `generate_ensemble`, so the
                    same request returns byte-identical probabilities.
    use_llm         Controls CANDIDATE DRAFTING only ("auto" | False).
    verify_use_llm  Controls the FORWARD MODEL's scenario prior during
                    verification. Defaults to False so `achieved_prob` is
                    exactly reproducible for a given seed; `note` records
                    which prior produced the numbers.
    max_evals       Hard cap on forward-model runs (default 40).
    time_budget_s   Wall-clock budget. Round 1 always completes; later rounds
                    stop early and say so in `note`.

    Never raises. A broken model, an empty ledger or an out-of-universe ticker
    all return a well-formed `InverseResult` whose `note` explains what
    happened, and whose `scenarios` list is empty rather than fabricated.
    """
    t0 = time.time()
    notes: List[str] = []

    # ---- normalise the request -------------------------------------------
    ticker = (req.ticker or "").strip().upper()
    direction = (req.direction or "down").strip().lower()
    if direction not in ("up", "down"):
        notes.append(f"direction '{req.direction}' is not 'up' or 'down'; defaulted to 'down'.")
        direction = "down"
    try:
        target_raw = float(req.target_prob)
    except (TypeError, ValueError):
        target_raw = 0.75
        notes.append("target_prob was not a number; defaulted to 0.75.")
    target = _clamp(target_raw, MIN_TARGET_PROB, MAX_TARGET_PROB)
    if abs(target - target_raw) > 1e-9:
        notes.append(f"target_prob {target_raw:.4g} clamped to the frozen "
                     f"[{MIN_TARGET_PROB:.2f}, {MAX_TARGET_PROB:.2f}] band -> {target:.2f}.")
    as_of = _iso(req.as_of_date)
    h = max(1, min(int(req.horizon_days or DEFAULT_HORIZON_DAYS), 60))
    k = max(1, min(int(req.n_candidates or 3), 8))

    def _finish(scenarios: List[Scenario], iters: int) -> InverseResult:
        best = min((s.error for s in scenarios), default=None)
        notes.append(_NON_UNIQUE)
        if scenarios:
            # A Monte Carlo estimate needs its own error bar or the ranking
            # implies a precision the simulation does not have.
            p0 = scenarios[0].achieved_prob
            se = math.sqrt(max(p0 * (1.0 - p0), 1e-12) / max(n_paths, 1))
            notes.append(
                f"MONTE CARLO ERROR: achieved_prob is a sample proportion over {n_paths} paths, "
                f"so its standard error is about {se:.3f} ({se * 100:.1f} percentage points). "
                "Differences between candidates smaller than that are noise, not ranking. "
                + ("All candidates in this request shared one explicit seed (common random "
                   "numbers), which makes their DIFFERENCES more stable than independent draws "
                   "would be but does not shrink the error on any single number."
                   if seed is not None else
                   "No explicit seed was given, so each candidate drew the seed the forward model "
                   "derives from its own request -- the same number you get by pasting that exact "
                   "event text into /api/forecast, and stable across repeat calls.")
            )
        notes.append(
            f"Search used {iters} forward-model evaluation(s) of a {max_evals} cap in "
            f"{time.time() - t0:.1f}s. seed={seed!r}, n_paths={n_paths}."
        )
        return InverseResult(
            target_prob=target, direction=direction, ticker=ticker,
            scenarios=scenarios, best_error=best, search_iterations=iters,
            note=" ".join(notes),
        )

    if ticker not in UNIVERSE:
        notes.insert(0, f"'{ticker}' is not in the frozen universe {UNIVERSE}. "
                        "No scenarios were generated.")
        return _finish([], 0)

    # ---- STAGE 1: RETRIEVE ------------------------------------------------
    try:
        analogs, rnotes = retrieve_analogs_for_target(
            ticker, direction, as_of, h, corpus=corpus, prices_dir=prices_dir,
            events_path=events_path, corpus_dir=corpus_dir, research_dir=research_dir,
        )
    except Exception as exc:  # noqa: BLE001
        analogs, rnotes = [], [f"analog retrieval failed ({type(exc).__name__}: {exc}); "
                               "candidates fall back to generic templates."]
    notes.extend(rnotes)

    n_sourced = sum(1 for a in analogs if a.cause)
    notes.append(
        f"RETRIEVE: {len(analogs)} real ledger event(s) admissible for {ticker} {direction} "
        f"as of {as_of} (every one's {h}-day forward window closes on or before that date); "
        f"{n_sourced} carry a sourced cause explanation from docs/research/. Realized forward "
        "moves span "
        + (f"{min(a.forward_return for a in analogs):+.1%} to "
           f"{max(a.forward_return for a in analogs):+.1%}." if analogs else "n/a.")
    )

    verifier = _Verifier(
        ticker, as_of, h, direction, seed=seed, corpus=corpus, use_llm=verify_use_llm,
        llm_model=llm_model, llm_timeout_s=llm_timeout_s, prices_dir=prices_dir,
        events_path=events_path, corpus_dir=corpus_dir, n_paths=n_paths,
        max_evals=max_evals,
    )
    notes.append(
        "VERIFY: achieved_prob is the fraction of forward-model paths ending "
        + ("below" if direction == "down" else "above")
        + f" zero over {h} trading days. It is COMPUTED by generator.generate_ensemble on each "
        "candidate text, never asserted by a language model (CONTRACT.md s6b). The forward "
        "model's scenario prior ran "
        + ("with its LLM path enabled." if verify_use_llm else
           "on its DETERMINISTIC keyword prior (verify_use_llm=False) so these numbers are "
           "exactly reproducible for this seed.")
    )

    # ---- STAGE 2 + 3: probe the reachable band ----------------------------
    # This doubles as the calibration probe. It runs BEFORE any attempt to hit
    # the target, so a miss can be attributed to the model's structure rather
    # than to a search that gave up.
    scored: List[Tuple[str, float, Any, Optional[_Analog], float]] = []  # text, p, ens, anchor, dial

    def _try_dial(dial: float, variant: int = 0) -> Optional[Tuple[str, float, Any, Optional[_Analog]]]:
        anchor = _anchor_for_dial(analogs, dial, variant=variant)
        text = _template_candidate(ticker, direction, dial, anchor, variant=variant)
        got = verifier.run(text)
        if got is None:
            return None
        scored.append((text, got[0], got[1], anchor, dial))
        return (text, got[0], got[1], anchor)

    for d in PROBE_DIALS:
        _try_dial(d)

    if not scored:
        notes.insert(0, "FORWARD MODEL UNAVAILABLE: no candidate could be verified, so no "
                        "scenario is returned. `verified` is never true without a real run, and "
                        "no probability is reported without one. "
                        + (" ".join(verifier.errors[:3]) if verifier.errors else ""))
        return _finish([], verifier.evals)

    probe_lo = min(s[1] for s in scored)
    probe_hi = max(s[1] for s in scored)

    # ---- STAGE 4: bounded 1-D search on the severity dial ------------------
    # The map dial -> achieved is monotone-ish but NOT monotone: past a certain
    # severity the keyword prior's drift saturates while its width keeps
    # growing, so the probability turns back down. Bisection alone would walk
    # off that peak, so we bisect only inside a bracket the probe established,
    # and otherwise refine around the best probe point.
    def _budget_left() -> bool:
        return (not verifier.exhausted) and (time.time() - t0) < time_budget_s

    probe = sorted(((s[4], s[1]) for s in scored), key=lambda x: x[0])
    bracket: Optional[Tuple[float, float]] = None
    for (d1, p1), (d2, p2) in zip(probe, probe[1:]):
        if (p1 - target) * (p2 - target) <= 0:
            bracket = (d1, d2)
            break

    if bracket is not None:
        a_d, b_d = bracket
        for _ in range(10):
            if not _budget_left():
                break
            m = 0.5 * (a_d + b_d)
            got = _try_dial(m)
            if got is None:
                break
            _, p_m, _, _ = got
            # keep the half that still brackets the target
            p_a = min(scored, key=lambda s: abs(s[4] - a_d))[1]
            if (p_a - target) * (p_m - target) <= 0:
                b_d = m
            else:
                a_d = m
            if abs(p_m - target) < 0.0015 or abs(b_d - a_d) < 0.004:
                break
    else:
        best_d = min(scored, key=lambda s: abs(s[1] - target))[4]
        for delta in (0.06, 0.12, 0.18):
            for d in (best_d - delta, best_d + delta):
                if not _budget_left():
                    break
                if 0.0 <= d <= 1.0:
                    _try_dial(d)

    # ---- second-round proposals, steered by what round 1 achieved ---------
    best_dial = min(scored, key=lambda s: abs(s[1] - target))[4]
    best_now = min(scored, key=lambda s: abs(s[1] - target))[1]
    llm_texts: List[str] = []
    llm_source: Optional[str] = None
    llm_err: Optional[str] = None
    if use_llm is not False and _budget_left():
        steer = (
            f"A previous templated draft at this severity measured {best_now:.2f} against a "
            f"{target:.2f} target, so aim for events that are "
            + ("MORE" if target > best_now else "MILDER and more ambiguous than")
            + " that draft, without changing the cited figure."
        )
        llm_texts, llm_source, llm_err = _llm_propose(
            ticker, direction, as_of, _dial_magnitude(best_dial), k + 1,
            [a for a in reversed(analogs)][:5],
            model=llm_model, timeout_s=llm_timeout_s, steer=steer,
        )
    if llm_texts:
        notes.append(f"PROPOSE: {len(llm_texts)} candidate text(s) drafted by {llm_source}. "
                     "The model wrote prose only; every probability below was computed here.")
        if llm_err:
            notes.append(llm_err)
        anchor_for_llm = _anchor_for_dial(analogs, best_dial)
        for t in llm_texts:
            if not _budget_left():
                notes.append("Search stopped early on the time budget before every LLM "
                             "candidate was verified.")
                break
            got = verifier.run(t)
            if got is not None:
                scored.append((t, got[0], got[1], anchor_for_llm, best_dial))
    else:
        notes.append(_LOUD_NO_LLM + (f" (drafting attempt: {llm_err})" if llm_err else ""))

    # ---- diversify: distinct groundings at the winning severity ------------
    # Diversify: same severity, DIFFERENT real grounding. The inverse is not
    # unique, so returning three restatements of one analog would misrepresent
    # the answer set as narrower than it is.
    for v in range(1, 5):
        if not _budget_left():
            break
        _try_dial(best_dial, variant=v)
        if _budget_left():
            _try_dial(_clamp(best_dial + 0.03 * (1 if v % 2 else -1), 0.0, 1.0), variant=v)

    # ---- the reachable band, measured across EVERY evaluation --------------
    # Reported after the search, not after the probe, so the band a reader sees
    # is never narrower than a probability the search actually reached.
    lo_p = min(s[1] for s in scored)
    hi_p = max(s[1] for s in scored)
    notes.append(
        f"REACHABLE BAND (measured over all {verifier.evals} forward-model evaluations; the "
        f"first {len(PROBE_DIALS)} were a fixed severity-dial probe run BEFORE any attempt to hit "
        f"the target): P({direction}) spans {lo_p:.3f} to {hi_p:.3f} for {ticker} as of {as_of} "
        f"(probe alone: {probe_lo:.3f} to {probe_hi:.3f}). The forward model holds ~45% of its "
        "rule-set weight at ZERO drift by design (generator.RULE_SET, drift_mode='neutral'), "
        "which caps how far any event text can move the directional probability, and past a "
        "certain severity the keyword prior's drift saturates while its width keeps growing, so "
        "MORE dramatic language starts moving the probability back DOWN. Widening the ensemble "
        "would push past this ceiling and is FROZEN OUT (CONTRACT.md s6b: over-widening measured "
        "at -52% CRPS lift)."
    )
    if target > hi_p + 0.005 or target < lo_p - 0.005:
        notes.append(
            f"TARGET OUT OF REACH: {target:.2f} lies outside the measured band "
            f"[{lo_p:.3f}, {hi_p:.3f}]. The scenarios below are the CLOSEST ACHIEVABLE and "
            "best_error carries the true miss. This is a stated property of the forward model, "
            "not a search failure -- reporting the target as if it had been achieved would be "
            "the fabrication this endpoint exists to prevent."
        )

    # ---- SELECT ------------------------------------------------------------
    ranked = sorted(scored, key=lambda s: abs(s[1] - target))
    deduped = _dedupe([(t, p, e) for (t, p, e, _a, _d) in ranked])
    anchor_by_text = {s[0]: s[3] for s in scored}

    # Prefer a DISTINCT grounding analog per returned candidate. Three
    # restatements of one analog would present the answer set as narrower than
    # it is, and CONTRACT.md s6b is explicit that the inverse is a set. Error
    # ordering still wins: a second candidate on a used anchor is only demoted,
    # never dropped, so we never trade accuracy for variety.
    def _select_diverse(items: List[Tuple[str, float, Any]], want: int) -> List[Tuple[str, float, Any]]:
        picked: List[Tuple[str, float, Any]] = []
        used: set = set()
        for pas in (True, False):           # pass 1: unused anchors only
            for it in items:
                if len(picked) >= want:
                    break
                if it in picked:
                    continue
                a = anchor_by_text.get(it[0])
                key = (a.event.ticker, a.event.date) if a is not None else None
                if pas and key is not None and key in used:
                    continue
                picked.append(it)
                if key is not None:
                    used.add(key)
        return picked

    out: List[Scenario] = []
    for text, achieved, ens in _select_diverse(deduped, k):
        err = abs(achieved - target)
        anchor = anchor_by_text.get(text)
        base_narr = (getattr(ens, "narrative", "") or "").strip()
        narrative = (
            f"Forward model computed P({direction} over {h} trading days) = {achieved:.1%} for "
            f"this event text against a {target:.0%} target (error {err:.1%}). "
            + (f"Grounded in {anchor.event.ticker} {anchor.event.date}, a real "
               f"{anchor.event.move_pct:+.1%} {anchor.event.window_days}-day move whose realized "
               f"{h}-day forward return was {anchor.forward_return:+.1%}"
               + (f" ({anchor.cause[:180]})." if anchor.cause else ".")
               if anchor is not None else "")
            + " " + base_narr
        ).strip()
        out.append(Scenario(
            event_text=text,
            achieved_prob=achieved,
            error=err,
            quantiles=dict(getattr(ens, "quantiles", {}) or {}),
            analogs_used=_analogs_for_report(anchor, ens),
            narrative=narrative,
            verified=True,          # only reachable when generate_ensemble ran
        ))

    if verifier.errors:
        notes.append("Forward-model errors during search: " + "; ".join(verifier.errors[:3]))
    if verifier.exhausted:
        notes.append(f"Evaluation cap of {max_evals} forward-model runs was reached.")

    return _finish(out, verifier.evals)
