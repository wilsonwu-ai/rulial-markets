# CONTRACT.md — FROZEN INTERFACE

> Every build lane codes against this file. **No lane may change it.**
> If a lane believes the contract is wrong, it reports the problem in its
> return value and codes to the contract anyway. The parent reconciles.
>
> This file exists so eight agents can build in parallel without reading
> each other's code.

## 0. The one-paragraph product

`rulial-markets` takes a **conditional event description** ("NVDA announces a 40%
datacenter revenue miss") and emits an **ensemble of possible forward return
paths** — not a point prediction. We score the ensemble's *calibration* against
held-out history, and we report **lift over a null model**. The Wolfram framing:
we are sampling the rulial ensemble of computationally-reachable futures and
asking where the observed one landed.

## 1. Universe (FROZEN — 10 tickers)

```python
UNIVERSE = ["NVDA","AAPL","MSFT","AMZN","TSLA","META","GOOGL","JPM","XOM","BA"]
```

## 2. Time boundary (FROZEN — this is the leak guard)

```python
TRAIN_END   = "2019-12-31"   # seed corpus + calibration may use data <= this
TEST_START  = "2020-01-01"   # evaluation only
EMBARGO_DAYS = 5             # purge gap between train and test windows
```

**No lane may move `TRAIN_END` "for better results." Moving it is the leak.**

## 3. Event definition (FROZEN — two tiers)

An *event* is a trading day where `|close_to_close_return|` clears a tier
threshold over a rolling `WINDOW_DAYS = 5` window (a move in a week, not a
single day — single-day 25% moves are too rare to build a corpus from).

```python
TIER_MAJOR       = 0.25   # the stage narrative: black-swan scale
TIER_SIGNIFICANT = 0.15   # the training corpus: every ticker contributes
JUMP_THRESHOLD   = TIER_SIGNIFICANT   # detection floor
WINDOW_DAYS      = 5
```

**Why two tiers.** At 25% only, four of the ten tickers (AAPL, BA, MSFT, XOM)
produce zero pre-2019 events — mega-caps do not move 25% in a week — and JPM's
ten events are all 2008-09, one regime wearing ten hats. The 15% tier widens
the corpus so analog retrieval has something to retrieve; the 25% tier stays
intact as the demo narrative. Every `Event` carries `tier` so the two never
get conflated in a report.

**Neither threshold may be tuned by a lane.** Moving them silently changes
every number downstream.

Overlapping windows are deduplicated to the single most extreme window.

## 4. Python module boundaries (FROZEN — one owner each)

| Module | Owner lane | Exports |
|---|---|---|
| `backend/rulial/config.py` | parent (already written) | UNIVERSE, TRAIN_END, thresholds |
| `backend/rulial/data.py` | LANE-DATA | `load_prices(ticker) -> pd.DataFrame`, `load_fundamentals(ticker)` |
| `backend/rulial/events.py` | LANE-EVENTS | `detect_events(prices) -> list[Event]`, `build_ledger() -> None` |
| `backend/rulial/news.py` | LANE-NEWS | `harvest(event) -> list[Article]`, `build_corpus() -> None` |
| `backend/rulial/generator.py` | LANE-MODEL | `generate_ensemble(req) -> Ensemble` |
| `backend/rulial/evaluate.py` | LANE-EVAL | `crps(ensemble, actual)`, `null_ensemble(...)`, `pit(...)`, `walk_forward(...)` |
| `backend/rulial/api.py` | LANE-API | FastAPI app, routes below |
| `frontend/**` | LANE-UI | Next.js app |
| `docs/PRD.md` | LANE-PRD | the PRD |
| `docs/diagrams/*.html` | LANE-DIAGRAM | architecture diagrams |

**A lane writes ONLY its own files.** Reading another lane's file is fine
(import the signature from this contract, not from their source).

## 5. Core types (FROZEN)

```python
# backend/rulial/types.py  -- written by parent, imported by all
from dataclasses import dataclass, field

@dataclass
class Article:
    url: str
    title: str
    published: str        # ISO8601 date
    source: str           # "yahoo" | "bloomberg" | "reuters" | ...
    snippet: str = ""

@dataclass
class Event:
    ticker: str
    date: str             # ISO8601, the END of the jump window
    move_pct: float       # e.g. -0.31 or +0.42
    direction: str        # "up" | "down"
    window_days: int
    headline: str = ""
    articles: list = field(default_factory=list)   # list[Article]

@dataclass
class ForecastRequest:
    ticker: str
    event_text: str       # free text from the user
    as_of_date: str       # ISO8601 — the model sees NOTHING after this
    horizon_days: int = 5
    n_paths: int = 2000

@dataclass
class Ensemble:
    ticker: str
    as_of_date: str
    horizon_days: int
    paths: list           # list[float] simulated cumulative returns
    quantiles: dict       # {"p5":..,"p25":..,"p50":..,"p75":..,"p95":..}
    mean: float
    std: float
    analogs: list         # list[Event] historical analogs that shaped it
    narrative: str        # 2-3 sentence plain-English rationale

@dataclass
class Score:
    crps: float           # lower is better
    crps_null: float      # unconditional-volatility baseline
    crps_lift: float      # (crps_null - crps) / crps_null   >0 means we beat null
    pit: float            # probability integral transform of the actual, in [0,1]
    actual_return: float
    z_score: float        # (actual - mean) / std  -- the "how many sigma" answer
```

## 6. HTTP API (FROZEN)

```
GET  /api/tickers
  -> [{ "symbol": "NVDA", "name": "NVIDIA Corp", "sector": "...", "has_data": true,
        "n_events": 7 }]

GET  /api/events?ticker=NVDA
  -> [ Event as JSON, ... ]          # the seed ledger, train period only

POST /api/forecast
  body: ForecastRequest as JSON
  -> { "ensemble": Ensemble as JSON,
       "score": Score as JSON | null }   # score non-null only when as_of_date
                                          # is historical and the actual is known

GET  /api/backtest?ticker=NVDA
  -> { "n_tests": 12,
       "mean_crps_lift": 0.18,
       "pit_histogram": [10 bucket counts],
       "calibration_ok": true,
       "per_event": [ {date, crps, crps_null, crps_lift, z_score}, ... ] }

GET  /api/health -> {"ok": true}
```

Backend runs on **:8000**. Frontend dev on **:3000**, proxying `/api/*` to :8000.

## 6b. Inverse scenario API (FROZEN) — Pavel's inversion

The forward model answers "given this event, what is the distribution?".
This inverts it: "given a target probability, what event would produce it?".

```
POST /api/scenario
  body: { ticker: str,
          direction: "up" | "down",
          target_prob: float,        # 0.50 .. 0.95, P(move in `direction`)
          as_of_date: str,           # ISO, <= TRAIN_END for scored demos
          horizon_days: int = 5,
          n_candidates: int = 3 }

  -> { target_prob: float,
       direction: str,
       ticker: str,
       scenarios: [ { event_text: str,
                      achieved_prob: float,     # COMPUTED, never asserted
                      error: float,             # |achieved - target|
                      quantiles: {p5,p25,p50,p75,p95},
                      analogs_used: [ Event ],
                      narrative: str,
                      verified: true } ],
       best_error: float,
       search_iterations: int,
       note: str }
```

### The rule that makes this feature honest

**`achieved_prob` is ALWAYS computed by running the candidate event text back
through `generator.generate_ensemble` and measuring the fraction of paths that
move in `direction`. An LLM proposes the text. It never states the number.**

If a proposed event is drafted as "57% bearish" and the forward model computes
43%, the response says **43%**. The search may iterate to close the gap, and if
it cannot, `note` says so plainly and `best_error` carries the miss. Reporting an
asserted probability would make this a language model with a percent sign, which
is precisely the thing the rest of this project exists not to be.

### The inverse is not unique

Many different events map to the same probability. The endpoint therefore returns
a **set** of candidate scenarios, never "the" answer, and the UI must say so.
This is a property of the problem, not a limitation of the implementation.

### Pipeline

1. **RETRIEVE** — real events from the ledger whose realized forward windows sit
   near the target probability for this ticker and direction.
2. **PROPOSE** — an LLM drafts candidate event texts grounded in those analogs.
   Falls back to templated recombination of real analog headlines with no LLM.
3. **VERIFY** — every candidate is scored by the existing forward model.
4. **SELECT** — rank by `|achieved - target|`, dedupe near-identical texts.

### Frozen for this endpoint

- `achieved_prob` computed, never asserted. No exceptions.
- No widening of `vol_mult` to hit a target. That games the metric, and
  over-widening was already measured at -52% lift.
- Candidate events must respect `as_of_date`: no analog whose forward window
  closes after it, same guard as the forward path.
- `verified` may only be `true` when the forward model actually ran.

## 6c. Scenario UI contract (FROZEN)

- A **slider**, 50% to 95%, is the primary control for `target_prob`.
- **Preset buttons at 60 / 75 / 90**, in both directions, for one-click stage use.
- Direction is expressed by color: **green for up/buy, red for down/sell**, and
  ALWAYS paired with a text label and an arrow glyph. Color is never the only
  signal (CONTRACT.md accessibility, and 8% of men are red-green colorblind).
- The achieved probability is displayed next to the target whenever they differ,
  so the viewer always sees what the model actually computed.

## 6d. Rulial ensemble (FROZEN) — and why we keep Boltzmann beside it

### The distinction, stated so nobody has to guess

**Boltzmann ensemble** (what we had): one generator, many sampled paths. An ensemble over
*configurations under a fixed rule*. Its spread answers "how uncertain is the outcome, GIVEN
that my model is the right one?"

**Rulial ensemble** (what we add): many generators, each sampled. An ensemble over *possible
rules*. Its spread answers "how uncertain am I, given that I do not know which rule generates
reality?" Wolfram's rulial ensemble is explicitly an ensemble of rules, and he contrasts it
against the gas case, which is Boltzmann.

**We ship both.** Dropping Boltzmann would hide the comparison that justifies the choice.

### FROZEN rule grid — 144 generators

```python
RULE_AXES = {
  "analog_selection": ["tfidf_magnitude", "ticker_only", "tier_only", "text_only"],   # 4
  "conditioning":     ["cross_ticker", "same_ticker", "same_era"],                    # 3
  "drift_prior":      ["scenario", "zero", "unconditional", "sign_only"],             # 4
  "resampling":       ["block", "iid", "stationary"],                                 # 3
}                                                                    # 4*3*4*3 = 144
```

A *rule* is one point in that grid. No lane may add, remove or reweight an axis: the grid is
the ensemble, and quietly dropping the axis that disagrees with you is the exact move this
construction exists to prevent.

### API

```
POST /api/rulial   -> { ticker, event_text, as_of_date, horizon_days, n_paths_per_rule }
  -> { boltzmann: { quantiles, median, p_down, n_paths },
       rulial: { n_generators,
                 per_generator: [ { rule: {...4 axes...}, quantiles, median, p_down } ],
                 consensus: { median_band: [lo,hi], p_down_band: [lo,hi],
                              sign_agreement: float, reducible: bool } },
       invariants:     [ str ],   # properties surviving >=90% of rules
       rule_dependent: [ str ],   # properties that flip across rules
       note: str }
```

### What may be reported

- **Invariant** = holds under at least 90% of the 144 generators. Only invariants may be
  stated as findings.
- **Rule-dependent** = flips sign or changes materially across the grid. These must be
  reported as rule-dependent and MUST NOT be presented as skill.

This is not decoration. The measured `+14.8% lift that becomes -4.5% when demeaned` is a
rule-dependence on the drift axis, and a Boltzmann ensemble cannot see it by construction.
The rulial ensemble surfaces it without anyone remembering to check.

### Wolfram mapping, now literal rather than analogical

| Wolfram | Ours |
|---|---|
| Rulial ensemble | the 144 generators |
| Computationally bounded observer | us, unable to run every possible rule |
| Coarse-graining | what survives across rules |
| Pockets of reducibility | regions of rule-space where the generators agree |

### Frozen for this endpoint

- The grid is 144 and fixed. No pruning to improve a result.
- `reducible` is a measured agreement fraction, never asserted.
- Boltzmann stays in the response so the comparison is always visible.
- A property that flips across rules is never reported as a finding.

## 7. Scoring (FROZEN — this is the whole defensibility argument)

- Primary metric: **CRPS** (continuous ranked probability score) of the ensemble
  vs the realized return.
- Always reported alongside **`crps_null`**, the unconditional-volatility
  baseline (Gaussian with trailing 250d sigma, zero drift).
- Headline number is **`crps_lift`** — improvement over null.
- Calibration: **PIT histogram**. A well-calibrated ensemble gives a *flat*
  PIT histogram. Flat is the win condition, not "we called the crash."

**FROZEN: directional hit-rate may not be reported as a headline result.**
It makes a coin flip look skilled. It may appear in an appendix, labelled.

**FROZEN: the null model may not be removed from the eval**, however good it
makes us look to drop it.

**FROZEN: the stage narrative (Harvey / Iran / layoffs) may never become the
scoring function.** Narrative lives in the demo. CRPS-vs-null lives in the eval.

## 8. Leakage disclosure (FROZEN — must appear in UI and PRD)

Any LLM used in the generator has read the post-2019 world. Cutting *input* data
at 2019 does not cut the *weights*. We therefore:
1. Report lift over null, not raw accuracy — memorization must beat a baseline
   to count for anything.
2. Include obscure/low-salience events in the test set alongside famous ones,
   and report them separately. A model that only wins on famous events is
   remembering, not forecasting.
3. State this limitation on the results screen. Out loud, in the product.

## 9. Rules for every lane

- Write ONLY the files you own. Never `git add`, `git commit`, `git push`,
  `git stash`, or `git reset`. The parent handles all git.
- Never edit `CONTRACT.md`, `backend/rulial/config.py`, or `backend/rulial/types.py`.
- Never `pip install` or `npm install` globally — add to `requirements.txt` /
  `package.json` only if you own that file; otherwise report the dep in your
  return value.
- Every module must import cleanly with no network access at import time.
- If real data is unavailable, ship a working code path with a clearly-labelled
  synthetic fallback. Never fabricate a number and present it as real.
