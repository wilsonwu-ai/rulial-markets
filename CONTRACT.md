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

## 3. Event definition (FROZEN)

An *event* is a trading day where `|close_to_close_return| >= 0.25` over a
rolling `WINDOW_DAYS = 5` window (a 25% move in a week, not a single day —
single-day 25% moves are too rare to build a corpus from).

```python
JUMP_THRESHOLD = 0.25
WINDOW_DAYS    = 5
```

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
