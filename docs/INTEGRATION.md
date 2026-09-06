# INTEGRATION.md

Written by the INTEGRATOR after ten build lanes landed in parallel. Everything
below was executed, not inferred. Where a number appears, the command that
produced it appears next to it.

**Status: the repo runs end to end.** Fresh clone to a scored forecast is four
commands (section 1). 334 tests pass. All six HTTP routes answer. The frontend
builds and talks to the backend.

**The headline result is honest and it is not flattering.** Read section 5
before putting a number on a slide.

---

## 1. Start the demo

```bash
cd rulial-markets
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # ~30s
PYTHONPATH=backend .venv/bin/python -m uvicorn rulial.api:app --port 8000 &
cd frontend && npm install && npm run dev                             # :3000
```

Open <http://localhost:3000>. The frontend proxies `/api/*` to `:8000`.

`make demo` runs both together. `./scripts/bootstrap.sh` does the whole thing
from nothing. Neither needs network at runtime: prices, the event ledger and the
news corpus are all committed under `data/`.

Verify in one line:

```bash
curl -s localhost:8000/api/health
# {"ok":true,"version":"0.1.0","modules":{"data":true,"events":true,"news":true,
#  "generator":true,"evaluate":true},"module_errors":{}}
```

Rebuild the dataset only if you mean to (it is already committed):

```bash
.venv/bin/python scripts/build_ledger.py --dry-run   # prints counts, writes nothing
```

---

## 2. What I fixed

### 2.1 The evaluation harness leaked the answer into the prompt (critical)

`evaluate.walk_forward` built each scored event's conditioning text as:

```python
f"{ticker} moved {e.move_pct:+.1%} over {window} trading days"
```

It interpolated the **realized move** into the text the model is scored on.
This is not cosmetic. `generator._implied_magnitude()` parses the percent back
out and `_severity_anchor()` uses it to decide which analogs to retrieve:

```
_implied_magnitude("NVDA moved -28.4% over 5 trading days") -> 0.284
```

So on every one of the 140 held-out events, the model was handed the size of
the answer before forecasting it. CONTRACT.md section 2 is the leak guard and
this path walked around it.

It did **not** flatter the score. With the leak the universe mean lift is
+1.93%; with a magnitude-free query it is +3.18%. "The leak made us look worse"
is not a defence of a leak, and a judge who reads `walk_forward` finds it in
thirty seconds and then disbelieves every other number in the repo.

**Fix.** `evaluate._backtest_query()` now builds every query, under two rules:
never interpolate `move_pct`/direction/window return; and scrub magnitudes out
of the researched headline too, because that text was written with hindsight and
often states the outcome verbatim. `evaluate.scrub_outcome()` is the scrubber
and it is exported so it can be tested:

```
scrub_outcome("Nov 15 Q3 FY2019: revenue +2.5% to $3.18bn, below guidance.
               Stock -18.8% Nov 16, -12% more Nov 19")
-> "Nov 15 Q3 FY2019: revenue [pct] to [amt], below guidance.
    Stock [pct] Nov 16, [pct] more Nov 19"
_implied_magnitude(that) -> None
```

What survives is the qualitative catalyst description, which is what a
forecaster actually has at `as_of` and what the product claims to condition on.

### 2.2 233 researched event headlines were dead data

`data/event_context.json` holds a researched, sourced description of why each of
233 ledger windows moved (headline, cause, category, source URLs, confidence).
**Nothing read it.** Every one of the 329 ledger rows shipped `headline: ""`, so:

- `/api/events` served a ledger with no story in it and the UI rendered blank rows;
- `generator._event_document` — the TF-IDF document a user's event text is
  matched against — contained only the ticker name and a canned direction
  phrase. The product's whole premise is conditioning on an event description
  and there was nothing on the other side of the join.

**Fix.** `scripts/build_ledger.py::attach_context()` populates
`Event.headline` / `.context` / `.category` from that file (233/329 matched,
0 orphans). `events.py` and `generator.py` carry the fields through
serialization; `api.py` exposes them additively on `EventModel`.
`/api/events?ticker=NVDA` now returns 22 of 39 rows with a real headline.

This is not a leak: every row describes an analog's **own** window, whose
outcome is already in `move_pct` and already in the ledger. The guard that
matters — an analog's forward window must close on or before `as_of_date` —
lives in `generator._forward_window_closes_by` and is untouched.

### 2.3 Feeding that text into retrieval made the model worse, so it ships off

Wiring the researched text into retrieval makes it genuinely semantic: the NVDA
2018 crypto-hangover query stops matching "NVDA + down words" and starts
matching the 2008 defective-GPU warning and the datacenter guidance events. It
reads better and it **scores worse**. Same 140 held-out events, universe
walk-forward, identical in every other respect:

| retrieval document | mean lift | median | CI90 |
|---|---|---|---|
| ticker + direction only **(shipped)** | **+1.934%** | +1.345% | [+0.524%, +3.403%] |
| + researched headline | -1.305% | +0.575% | [-3.108%, +0.422%] |
| + headline + cause + category | -1.642% | -0.448% | [-3.567%, +0.221%] |

(Those three rows are the pre-leak-fix harness, held constant so the arms are
comparable to each other and to the number previously on record.)

The honest reading is that the enrichment is not the defect. The width machinery
downstream of retrieval (`HORIZON_CALIBRATION`, the IQR scale) was calibrated by
LANE-MODEL against the metadata-only analog pool; a sharper, more topically
coherent pool needs its own calibration. **Re-fitting those constants against
these 140 test events is fitting on the test set**, which is the one thing
CONTRACT.md section 2 exists to prevent, so it was not done.

Gated behind `generator.RETRIEVAL_USES_RESEARCH_TEXT = False`, with the table
above in the source. The flag does not gate display — headlines reach the UI
either way. Turning it on is a one-line experiment for whoever re-calibrates
on **train**.

### 2.4 One test was wrong and I changed it

`test_api.py::test_only_the_frozen_routes_exist` asserted a five-route set. It
predated CONTRACT.md section 6b, which freezes `POST /api/scenario`. The
contract is the authority, not the test; I added the route to the expected set
and said so in a comment. **This is the only test I changed.** No test was
weakened or deleted, and no assertion was relaxed to make code pass.

### 2.5 Concurrency note

`backend/rulial/inverse.py` and the `/api/scenario` route landed **during** this
integration pass (file mtimes 14:34-14:35). They are not my work. I verified the
route (section 4) and corrected the route-inventory test to match.

---

## 3. The dataset, as actually built

`scripts/build_ledger.py` reproduces `data/events.jsonl` exactly: **329 events**,
164 train / 141 test in window / 24 beyond `TEST_END`. Real Yahoo prices, no
synthetic markers in any CSV.

| ticker | train | test | | ticker | train | test |
|---|---|---|---|---|---|---|
| NVDA | 39 | 32 | | META | 13 | 14 |
| AAPL | 8 | 3 | | GOOGL | 7 | 2 |
| MSFT | 4 | 2 | | JPM | 23 | 7 |
| AMZN | 18 | 7 | | XOM | 3 | 7 |
| TSLA | 40 | 48 | | BA | 9 | 19 |

Every ticker has train events, so the empty-ledger problem the earlier lanes
worried about is gone. Tiers: 68 major, 261 significant. Famous: 37 train /
37 test, so CONTRACT section 8.2's famous-vs-obscure split is populated and
exercised (it was empty when LANE-EVAL reported).

News corpus: 329 files, 1131 articles, 34 events with zero articles. **1129 of
1131 are SEC EDGAR filings**; the GDELT news tier is proven working but was
rate-limited during the build and is still essentially unpopulated. The
researched `event_context.json` is the better seed text and is what actually
reaches the product.

---

## 4. Every route, verified

Backend on `:8000`. Responses trimmed, not edited.

```
GET /api/health
{"ok":true,"version":"0.1.0","modules":{...all true},"module_errors":{}}

GET /api/tickers                                     # 10 rows, contract order
[{"symbol":"NVDA","name":"NVIDIA Corporation","sector":"Technology",
  "has_data":true,"n_events":39}, ...]

GET /api/events?ticker=NVDA                          # 39 rows, train only
max date = 2019-08-22   (<= TRAIN_END, correct)
{"ticker":"NVDA","date":"2008-01-22","move_pct":-0.181976,"direction":"down",
 "window_days":5,"tier":"significant","famous":false,
 "headline":"January 2008 global equity rout; semis hit by Intel's Q4 miss,
             then the Fed's emergency 75bp cut"}

GET /api/backtest?ticker=NVDA
{"n_tests":32,"mean_crps_lift":0.0144,"calibration_ok":true,
 "pit_histogram":[2,2,1,3,2,5,3,5,5,4]}
GET /api/backtest?ticker=AAPL     -> n_tests=3, note about underpowered PIT
GET /api/backtest?ticker=FAKE     -> unavailable=true, names the frozen universe

POST /api/scenario  {ticker NVDA, direction down, target_prob 0.75, as_of 2018-11-15}
best_error 0.185, search_iterations 19
  achieved 0.565 verified=true | "NVIDIA ... revenue misses by 37%, and warns ..."
note: "Only 2 of 16 admissible analogs are down-side moves that ALSO kept moving
       down over the next 5 days. Post-event mean reversion is the norm ..."
```

That last one is the contract's honesty rule working as designed: the target was
75%, the model computed 56.5%, and the response reports **56.5%** with the miss
in `best_error` and the reason in `note`.

Frontend: `npm run build` compiles clean (Next 16.3.4, TypeScript clean, both
routes prerendered static). `npm run dev` serves 200 on `/` and proxies
`/api/tickers` and `/api/events` through to the backend, headlines included.

---

## 5. The numbers that go on stage

### 5.1 One forecast, end to end

`POST /api/forecast` — NVDA, `as_of_date` 2018-11-15, the day before the
"crypto hangover" guidance cut. The outcome is known and the model does not
see it.

> "NVIDIA guides Q4 revenue far below consensus as crypto-mining GPU demand
> collapses and unsold channel inventory floods the gaming segment"

| | |
|---|---|
| p5 / p25 / p50 / p75 / p95 | **-7.90% / -3.79% / -0.47% / +3.67% / +10.98%** |
| mean / std | +0.375% / 6.04% |
| **actual return** | **-28.36%** |
| CRPS | 0.254141 |
| CRPS null | 0.250394 |
| **crps_lift** | **-1.50%** |
| PIT | 0.000 |
| z-score | **-4.75** |

**We miss this one badly.** The realized -28.4% lands outside the 5th percentile
of all 2000 paths, and we score 1.5% *worse* than the null. On stage the dot
lands outside the fan. Say so before a judge says it for you: a 4.8-sigma
5-day move is what a black swan is, and an ensemble that contained it would be
so wide it would fail calibration everywhere else.

### 5.2 The pooled result, 140 held-out post-2020 events

Leak-free harness, shipped configuration:

```
mean crps_lift    -1.29%   CI90 [-2.84%, +0.28%]   (straddles zero)
median            -1.10%
demeaned          -1.96%
calibration_ok    true
PIT histogram     [16,16,14,9,12,17,12,13,14,17]   (flat; expected 14/bin)
```

Calibration is the win condition CONTRACT section 7 names, and we hit it:

```
|z| < 1   69.3%   (a correct normal gives 68.3%)
|z| < 2   88.6%   (95.4%  -> our tails are genuinely fatter)
|z| > 3    3.6%
we beat the null on 44.3% of events
```

Breakdowns:

| slice | n | mean lift | median |
|---|---|---|---|
| famous | 36 | **-3.93%** | -2.37% |
| obscure | 104 | -0.38% | -0.60% |
| major (>=25%) | 28 | -2.25% | -1.49% |
| significant (15-25%) | 112 | -1.06% | -1.07% |

**The famous/obscure split is the one to lead with.** CONTRACT section 8.2 says
a model that only wins on famous events is remembering rather than forecasting.
We are *worse* on famous events than obscure ones — the opposite of the
memorization signature. That is a real, measured answer to the sharpest
leakage question, and it is only available because the ledger's `famous` flag
got populated.

### 5.3 The finding nobody planned

Conditioning currently costs us. Same harness, same events:

| conditioning | mean lift | CI90 |
|---|---|---|
| neutral query, model told nothing about the event | **+3.18%** | [+1.67%, +4.70%] |
| researched catalyst description (shipped) | -1.29% | [-2.84%, +0.28%] |

**Our conditional model is worse than our own unconditional model.** The width
machinery beats the null on its own; every channel we use to tell it what
happened makes it worse. That is consistent with what recon measured before any
of this was built (a width-only generator caps near +2% against this null) and
with LANE-MODEL's own negative lift.

I did not tune it away, because the only data left to tune against is the test
set. Ship it as the finding.

---

## 6. What does not work, or is not there

1. **No deployment.** Every lane flagged it; it is still unowned. Nothing here
   is deployed and there is no Dockerfile or Procfile. `main.py` binds `0.0.0.0`
   and honours `$PORT`, and the frontend static-exports
   (`NEXT_PUBLIC_API_BASE=... STATIC_EXPORT=1 npm run build` -> `out/`), so both
   halves are deploy-ready and neither is deployed. **Highest-severity open item.**
2. **No scenario UI.** CONTRACT section 6c freezes a 50-95% slider with
   60/75/90 presets. The backend route exists and works; no frontend component
   consumes it. `grep -rn target_prob frontend/src` returns nothing.
3. **No LLM in the default path.** `ANTHROPIC_API_KEY` is unset, so the scenario
   prior is a deterministic keyword heuristic. It is loudly labelled in
   `Ensemble.narrative`, `diagnostics['prior_source']` and a `RuntimeWarning`.
   The CLI path measured 24s, over the 5s demo budget; the SDK path with an API
   key should land in 1-2s.
4. **The news corpus is SEC filings, not news** (1129/1131). The GDELT tier
   works and is unpopulated. `python3 -m rulial.news` from a cooled IP tops it
   up; it is resumable and self-healing.
5. **96 of 329 events have no researched context**, so their headlines are still
   blank in the UI.
6. **`data/events.jsonl` carries 24 events past `TEST_END`** (to 2026-08-05).
   `walk_forward` filters them; nothing else should read them as test data.
7. **`load_fundamentals` is a 2026 point-in-time snapshot.** Safe for
   `/api/tickers` display, and it must never become a model feature for a
   pre-2019 event. Nothing guards this in code.
8. **No frontend tests.** No visual regression guard on the charts.

---

## 7. Reproduce any number here

```bash
.venv/bin/python -m pytest backend/tests -q          # 334 passed, 1 deselected
.venv/bin/python scripts/build_ledger.py --dry-run   # the per-ticker table
PYTHONPATH=backend .venv/bin/python -c \
  "from rulial import evaluate as EV; r=EV.walk_forward_universe(); \
   print(r['n_tests'], r['mean_crps_lift'], r['crps_lift_ci90'])"
```

The one live-network test is deselected by default; run it with
`pytest backend/tests -m network`.
