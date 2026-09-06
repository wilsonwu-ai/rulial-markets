# rulial-markets — PRD

**Sundai Hack 139** · 6 September 2026 · Harvard iLabs
**Theme:** AI Agents That Adapt and Evolve, with Wolfram Research
**Repo:** https://github.com/wilsonwu-ai/rulial-markets
**Status:** in progress. Spec frozen in [`CONTRACT.md`](../CONTRACT.md); build in flight.

---

## 1. One sentence

Describe a market event in plain English, and an agent generates the ensemble of futures that
event could produce, scored against what actually happened.

## 2. The problem, and the reframe that makes it testable

Everyone wants a model that predicts black swans. That is not a well posed request, and a judge
will say so in thirty seconds. Black swans are unpredictable by construction: if a model trained
only on pre-2019 data "predicts" COVID, it either got lucky or it leaked.

So we test the thing next door, which is both tractable and more useful:

> Given an event description and a date, produce a **calibrated distribution** of forward
> returns, and beat an unconditional volatility baseline.

This is a real, measurable claim. It has a null hypothesis, a scoring rule, and a way to lose.

**Two layers, held separately and never merged.**

| Layer | What it is | Where it lives |
|---|---|---|
| **Narrative** | Hurricane Harvey. The Iran conflict. A bad layoffs report. A 25% jump. | The demo, the stage, the hero screen |
| **Method** | CRPS lift over a null volatility model, PIT calibration, walk forward with embargo | The eval, the scorecard, the defence |

**The narrative may never become the scoring function.** A team that pitches black swans starts
grading itself on "did it call the crash," which is directional hit rate, which makes a coin flip
look skilled. This rule is frozen in `CONTRACT.md` section 7 and no module may tune it.

## 3. User and job

**User:** an analyst or PM who has a view about an event and wants a distribution, not a headline.
**Job:** *"I think X is about to happen to this company. Show me the range of outcomes that has
historically followed events like X, and tell me honestly how much you trust it."*

The deliverable is a distribution with an error bar on its own reliability. That second part is
the product.

## 4. Why Wolfram is load bearing

Wolfram's rulial ensemble is the ensemble of all computationally reachable states, and an observer
is a computationally bounded thing that coarse grains that ensemble into something it can hold.

That is not decoration here, it is literally the architecture:

| Wolfram concept | Our implementation | Rigorous or analogical |
|---|---|---|
| Rulial ensemble | The 2000 sampled forward paths | **Rigorous.** An ensemble of reachable futures is what we compute. |
| Observer coarse graining | Reducing paths to p5/p25/p50/p75/p95 | **Rigorous.** We are the bounded observer collapsing the ensemble. |
| Computational irreducibility | Why we simulate rather than solve for a closed form | **Rigorous.** No shortcut exists; you run it. |
| Bulk orchestration | Many weak analog paths producing coherent aggregate structure | **Analogical.** Suggestive, not derived. |
| Pockets of reducibility | Regimes where analogs cluster tightly and the ensemble narrows | **Analogical.** We observe it; we have not proven it. |

We label the analogical mappings as analogical **in the product and in the diagrams**. At a Wolfram
hack, being caught cargo culting Wolfram is the fastest way to lose. Marking our own stretch
mappings is a stronger position than hoping nobody checks.

## 5. Product surface

Three screens. See [`docs/diagrams/01-what.html`](diagrams/01-what.html) for the flow.

1. **Control.** Pick one of ten tickers, pick an as-of date, type an event. Four preset events so
   the stage demo cannot fumble typing: bearish black swan, bullish surprise, geopolitical shock,
   company-specific bad news.
2. **Ensemble.** The money shot. Fan chart of simulated paths with quantile bands, terminal return
   histogram, and when the as-of date is historical, the **actual realized return overlaid as a
   vertical line.** Watching the actual land inside the fan is the demo.
3. **Scorecard.** CRPS, CRPS-null, and lift as the headline. Z-score, which is the literal answer
   to "by how many standard deviations." PIT calibration histogram with a plain English read:
   flat means well calibrated.

A fourth panel, the **leakage disclosure**, is always visible. Not fine print. See section 9.

## 6. Architecture

Module ownership is frozen in [`CONTRACT.md`](../CONTRACT.md) section 4 so that many people can
build at once without collisions. See [`docs/diagrams/02-how.html`](diagrams/02-how.html).

```
data.py     prices, fundamentals, trailing vol
   |
events.py   rolling 5d window, |return| >= 25%, dedup overlaps  -->  data/events.jsonl
   |
news.py     articles STRICTLY BEFORE the event date            -->  data/corpus/*.json
   |
generator.py   retrieve analogs -> generate ensemble -> coarse grain
   |
evaluate.py    CRPS, null model, PIT, walk forward with embargo
   |
api.py      FastAPI :8000  -->  frontend/  Next.js :3000
```

**Three-stage generator (the rulial core):**

1. **Retrieve.** Find historical analog events similar to the event text, restricted to on or
   before the as-of date.
2. **Generate.** Block bootstrap over the analogs' realized forward windows, weighted by an
   LLM-proposed scenario prior. The LLM outputs **scenario weights and drift/vol adjustments,
   never a point prediction.** Falls back to pure bootstrap when no LLM is reachable, loudly.
3. **Coarse grain.** Reduce to quantiles plus a short narrative naming the actual analogs used.

## 7. Data

- **Universe:** NVDA, AAPL, MSFT, AMZN, TSLA, META, GOOGL, JPM, XOM, BA. Ten heavily tracked
  names with real pre-2019 history and genuine large moves.
- **Source:** OpenBB via the `dubbs-research` MCP, yfinance fallback. **Verified working:** a live
  pull returned NVDA 2018-11-15 close $5.06 to 2018-11-19 close $3.62, a **28.5% drawdown in
  three sessions.** Real rows, not a promise.
- **Train boundary:** 2019-12-31. **Test:** 2020-01-01 to 2024-12-31. **Embargo:** 5 days.
- **Event definition:** rolling 5 day window with absolute return at or above 25%, overlapping
  windows deduplicated to the single most extreme.
- **Corpus:** articles published strictly before the event date, 30 day lookback.

## 8. Validation methodology

Answering the two questions directly.

**"How often do you validate?"**
Walk forward with an embargo, not a single train/test split. Train on data through 2019, then
roll through 2020 to 2024 in windows, purging a 5 day gap at each boundary so a window cannot
peek at its own neighbour. Every event in the test period is scored independently.

**"By what standard deviation?"**
We report the z-score, because it is the intuitive answer and it belongs on screen. But z-score
alone is a bad metric: it rewards a model for having a wide ensemble. The real metrics are:

| Metric | What it measures | Win condition |
|---|---|---|
| **CRPS** | Distance between the predicted distribution and the realized outcome | Lower |
| **CRPS-null** | Same, for an unconditional Gaussian at trailing 250d vol | The baseline |
| **CRPS lift** | `(null - ours) / null` | **Above zero. This is the headline.** |
| **PIT histogram** | Where the actual falls in our predicted CDF, across all tests | **Flat** |
| Z-score | Sigma distance from ensemble mean | Reported, not optimized |

A flat PIT histogram means the ensemble is honestly calibrated. That is the win, not calling
the crash.

## 9. Leakage, stated by us before it is stated at us

**The strongest argument against this project:** any LLM in the generator has already read the
post-2019 world. Cutting the input data at 2019 does not cut the weights. A model that "predicts"
the COVID crash may simply remember it.

We do not have a way to fully eliminate this in a one day build. We have three honest mitigations,
and we say so out loud:

1. **Lift over null, never raw accuracy.** Memorization has to beat a real baseline to count.
2. **Famous versus obscure, reported separately.** Every event carries a salience flag. A model
   that only wins on famous events is remembering, not forecasting, and our own scorecard will
   show that.
3. **Disclosed in the product.** The limitation panel is on the results screen, not in a footnote.

See [`docs/diagrams/03-why.html`](diagrams/03-why.html), which renders the leak guards as
structure: the 2019 boundary, the embargo gap, the strictly-before news filter, and the null model
sitting beside every score.

## 10. Pending work, by category

Claimable. Each item names its owner slot, its file, and whether it blocks the demo.

### A. Data pipeline
| # | Task | File | Size | Blocks demo | Status |
|---|---|---|---|---|---|
| A1 | Price loader + CSV cache for 10 tickers | `backend/rulial/data.py` | M | **Yes** | in flight |
| A2 | Trailing vol helper (daily sigma convention) | `backend/rulial/data.py` | S | **Yes** | in flight |
| A3 | Event detection with overlap dedup | `backend/rulial/events.py` | M | **Yes** | in flight |
| A4 | Ledger build + train/test split with embargo | `backend/rulial/events.py` | S | **Yes** | in flight |
| A5 | News harvest with strictly-before filter | `backend/rulial/news.py` | L | **Yes** | in flight |
| A6 | Famous vs obscure salience flag | `backend/rulial/events.py` | S | No | open |

### B. Model
| # | Task | File | Size | Blocks demo | Status |
|---|---|---|---|---|---|
| B1 | Analog retrieval over the seed corpus | `generator.py` | L | **Yes** | in flight |
| B2 | Block bootstrap over analog forward windows | `generator.py` | M | **Yes** | in flight |
| B3 | LLM scenario prior (weights, not predictions) | `generator.py` | L | No | open |
| B4 | Coarse graining + narrative generation | `generator.py` | M | **Yes** | in flight |
| B5 | Reproducibility: seeded RNG throughout | `generator.py` | S | No | open |
| B6 | As-of-date assertion (cannot see the future) | `generator.py` | S | **Yes** | in flight |

### C. Evaluation
| # | Task | File | Size | Blocks demo | Status |
|---|---|---|---|---|---|
| C1 | CRPS sample estimator, numerically verified | `evaluate.py` | M | **Yes** | in flight |
| C2 | Null ensemble (trailing vol Gaussian) | `evaluate.py` | S | **Yes** | in flight |
| C3 | PIT + histogram + flatness test | `evaluate.py` | M | **Yes** | in flight |
| C4 | Walk forward harness with embargo | `evaluate.py` | L | No | open |
| C5 | Famous vs obscure breakdown in the report | `evaluate.py` | S | No | open |

### D. API and integration
| # | Task | File | Size | Blocks demo | Status |
|---|---|---|---|---|---|
| D1 | Five routes per CONTRACT section 6 | `api.py` | M | **Yes** | in flight |
| D2 | Graceful degradation (never 500 on stage) | `api.py` | S | **Yes** | in flight |
| D3 | End to end smoke: clone to forecast | `scripts/` | M | **Yes** | open |

### E. Frontend
| # | Task | File | Size | Blocks demo | Status |
|---|---|---|---|---|---|
| E1 | Control panel with 4 preset events | `frontend/` | M | **Yes** | in flight |
| E2 | Fan chart with quantile bands | `frontend/` | L | **Yes** | in flight |
| E3 | Terminal distribution histogram + actual overlay | `frontend/` | M | **Yes** | in flight |
| E4 | Calibration scorecard | `frontend/` | M | **Yes** | in flight |
| E5 | Leakage disclosure panel | `frontend/` | S | **Yes** | open |
| E6 | Mock mode so the UI demos with the API down | `frontend/` | S | **Yes** | open |
| E7 | Design pass: Data-Dense Dashboard, Fira Code/Sans, dark | `frontend/` | M | No | queued |
| E8 | Deploy to Cloudflare Pages | `deploy/` | S | No | queued |

### F. Docs and demo
| # | Task | File | Size | Blocks demo | Status |
|---|---|---|---|---|---|
| F1 | This PRD | `docs/PRD.md` | M | No | **done** |
| F2 | Four diagrams: what / how / why / rulial | `docs/diagrams/` | L | No | in flight |
| F3 | README quickstart that actually works | `README.md` | S | No | in flight |
| F4 | 3 minute demo script, rehearsed | `docs/` | S | **Yes** | open |

## 11. Proposed lane assignment

Proposed, not decided. Grab what you want and edit this table.

| Person | Lane | Categories |
|---|---|---|
| **Wilson** | Product, eval methodology, demo | C, F |
| **Guzel** | Generator and ensemble math | B |
| **Pavel** | Data pipeline and corpus | A |
| **Harsh** | API and integration | D |
| **Luke** | Frontend | E |

**Claim a lane:** open an issue titled `claim: <category>` or just say so in the group chat, then
work only inside the files listed for that category. `CONTRACT.md` exists so that five people can
build simultaneously without reading each other's code. Do not edit `CONTRACT.md`,
`backend/rulial/config.py`, or `backend/rulial/types.py`; they are frozen. If the contract is
wrong, raise it rather than editing around it.

## 12. Success criteria

**Must have for the demo:**
- A user types an event, gets an ensemble, and sees a real distribution. End to end, no mocks.
- At least one historical case where the actual return is overlaid on the fan chart.
- CRPS lift over null computed from a real run, positive or negative, honestly reported.
- The leakage disclosure visible on screen.

**Would be good:**
- Walk forward across all ten tickers with the famous versus obscure split.
- Deployed and shareable by URL.

**We fail if:** we report a number we did not compute, or we let the narrative become the metric.

## 13. Relationship to Whetstone

[`whetstone`](https://github.com/wilsonwu-ai/whetstone) is the team's other Hack 139 project: an
adversarial test generator where every question is verified by Wolfram, so evolution has a fitness
signal that cannot argue back.

The architectures rhyme, and the connection is worth stating: **Whetstone's oracle is Wolfram.
Ours is the realized market return.** You cannot argue with what a stock actually did. If the two
projects merge, rulial-markets becomes the second domain that shows the architecture is not math
specific, which is the sharpest question a judge can ask of Whetstone.

---

*Pre-work disclosure: the repository scaffold, frozen contract, and this PRD were drafted at the
start of the event. All model, evaluation, and interface code is being written during the hack.*
