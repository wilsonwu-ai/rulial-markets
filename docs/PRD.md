# rulial-markets

**Product Requirements Document**
Sundai Hack 139, "AI Agents That Adapt and Evolve with Wolfram Research"
Harvard, Sunday 6 September 2026, 10:00 to 22:00

Status: v1.0, written against the frozen `CONTRACT.md`
Owner: LANE-PRD. This file is the only file this lane writes.
Audience: the build team (including Guzel) and anyone judging, testing, or attacking the demo.

---

## 0a. Status board — verified facts, not plans

**Live frontend:** https://rulial-markets.wilson-af8.workers.dev (Cloudflare Workers, static export)
**Repo:** https://github.com/wilsonwu-ai/rulial-markets

### Team and lanes

| Person | GitHub | Lane | Categories |
|---|---|---|---|
| Wilson | [@wilsonwu-ai](https://github.com/wilsonwu-ai) | Product, eval methodology, demo | C, F |
| Guzel | [@guzalkhonkh-stack](https://github.com/guzalkhonkh-stack) | Generator and ensemble math | B |
| Pavel | [@Pavel-Tk](https://github.com/Pavel-Tk) | Data pipeline and corpus | A |
| Harsh | [@harshk02](https://github.com/harshk02) | API and integration | D |
| Luke | [@lrast](https://github.com/lrast) | Frontend | E |

### The event ledger, built from real prices

Two tiers over a 5 day window: **major** at 25 percent and above is the stage narrative,
**significant** at 15 percent and above builds the training corpus. At 25 percent alone, four of
ten tickers (AAPL, BA, MSFT, XOM) produced zero pre-2019 events, because mega caps do not move 25
percent in a week, and JPM's ten were all 2008-09, one regime wearing ten hats.

| Split | Events | Major | Significant |
|---|---|---|---|
| Train, to 2019-12-31 | **164** | 36 | 128 |
| Test, 2020 onward | **165** | 32 | 133 |
| **Total** | **329** | 68 | 261 |

Ten tickers, all contributing. 77 carry the `famous` salience flag. Counts were produced twice by
independent implementations and agree exactly, so this is an anchor rather than one implementation
agreeing with itself. Overlapping windows are collapsed by greedy non-maximum suppression, so one
crash yields one event and the survivor is the most extreme window in its neighbourhood.

### One verified end-to-end run

NVDA, as of 2018-11-15, event text: *"NVIDIA warns datacenter revenue will miss badly on crypto
collapse."* Real prices, real analogs, real scoring.

```
quantiles   p5 -16.1%   p50 -0.9%   p95 +14.1%     2000 paths, 25 analogs
CRPS        0.2260   vs null 0.2504   ->  LIFT +9.7%
actual      -28.4%      z-score -3.08      PIT 0.0005
```

**Read both numbers together, because that is the honest result.** The ensemble beat the
unconditional baseline by 9.7 percent, and the realized return still landed 3.1 sigma below our
mean with a PIT of 0.0005, meaning only 0.05 percent of sampled paths were worse. Our distribution
was better than the null and still too narrow to contain the tail. That is what a black swan is,
and it is exactly why the scorecard reports calibration instead of accuracy. Do not hide this on
stage; lead with it.

### Known limitations, current

- The deployed frontend runs in **mock mode**. The FastAPI backend is not hosted; run it locally
  with `make api`, or expose it with a tunnel and set `NEXT_PUBLIC_API_BASE`.
- The news corpus is thin. Only a handful of events have harvested articles so far.
- Six price files were briefly synthetic because `yfinance` was missing from the environment.
  Refetched and verified; IPO dates confirm authenticity (META 2012-05-18, TSLA 2010-06-29).

---

## 0. The two layers (read this before anything else)

This product has two layers. They are held separately on purpose, and merging them is the single failure mode that would sink the project.

**Layer 1, the NARRATIVE layer.** Hurricane Harvey hits the Gulf Coast refineries. Conflict in the Strait of Hormuz. A brutal layoffs report drops at 08:30. A stock moves 25 percent in a week. This is what a person types into the box, what the fan chart on screen is about, and what anyone remembers ten minutes after the demo. Narrative is the interface and the reason the product is legible to a human being.

**Layer 2, the METHOD layer.** CRPS against a null volatility model, PIT calibration histograms, walk-forward validation with a 5 day embargo, lift reported with a confidence interval and decomposed into drift and shape. This is what we are actually scored on, and it is the only part that survives a judge who knows what they are looking at.

**The rule, frozen in `CONTRACT.md` section 7: the narrative may never become the scoring function.**

Why, stated plainly so nobody has to take it on faith. If we scored ourselves on the narrative layer, the natural metric would be directional hit rate: did the stock go the way we said. That metric makes a coin flip look skilled. On a 30 event test set, a pure coin flip produces 60 percent or better roughly 18 percent of the time by chance alone, and the resulting slide would say "60 percent directional accuracy" in large type. Worse, our own measurements say direction is the one thing that genuinely is not predictable here: regressing forward 5 day signed return on trailing move and trailing volatility gives out of sample R squared between -0.0008 and +0.0007 across three split points on roughly 9,000 held out observations. Forward absolute return, the dispersion, gives out of sample R squared of about 0.10 on the same data. Direction is noise. Dispersion is signal. A scoring function built on the narrative would optimise the noise.

So: narrative on stage, method in the eval, and the product itself shows both without letting either contaminate the other. Every screen in section 4 is labelled with which layer it belongs to.

---

## 1. Problem, and the honest reframe

### 1.1 The problem as people state it

Every operator, allocator and risk desk asks a version of the same question: *what happens to my position if X happens?* Hurricane in the Gulf. Sanctions on a shipping lane. A datacenter revenue miss. A regulatory action. The question is real, it is asked constantly, and the tooling for it is poor.

What exists commercially is portfolio level factor shock analysis. Bloomberg PORT lets a user build custom scenarios through the Scen function to stress test a portfolio (Bloomberg Professional, "How to build custom scenarios to stress test your portfolio"). MSCI's predictive stress testing framework applies shocks across multi asset portfolios. Both require the user to arrive already knowing the numeric shock. Neither takes a sentence of English about an event and returns a scored, calibration tested distribution of outcomes for a single name. That gap is real and it is the product opportunity.

### 1.2 The reframe, and why we are not softening it

The tempting pitch is "we predict black swans." We are not going to say that, because it is not testable, and a claim that cannot fail is not a claim.

Three reasons it is not testable:

1. **Sample size.** Under our frozen event definition the entire out of sample test set is 30 events across a 5 year window (measured, see section 6). You cannot establish predictive skill on rare directional events at n = 30. Any headline built on it is noise dressed as a result.
2. **The metric collapses.** "Predicted the black swan" reduces in practice to directional hit rate on rare events, which is exactly the metric that flatters a coin flip. See section 0.
3. **Direction is measurably unpredictable in our data.** Out of sample signed R squared is approximately zero across three split points. This is not an assumption we are importing, it is a measurement we ran on the train period before building anything.

**What we test instead.** We do not forecast the trajectory. We forecast the *distribution*, and we ask two falsifiable questions about it:

- **Sharpness relative to a baseline.** Does our conditional ensemble score a better CRPS than a null model that knows nothing except trailing volatility? This is `crps_lift`, and it can come out negative. It is designed to be able to come out negative.
- **Calibration.** When we say the 90 percent interval, does the realised outcome land inside it about 90 percent of the time, and is the full PIT histogram flat rather than merely the tails being approximately right? Flat is the win condition. "We called the crash" is not a win condition, it is an anecdote.

This reframe is our strongest intellectual move and it should be the first thing said on stage, not a caveat delivered at the end. It converts an unfalsifiable pitch into a falsifiable one, and it is the reason the eval can be shown to a stranger without embarrassment.

### 1.3 What success actually looks like

A well calibrated ensemble with `crps_lift` near zero is a *legitimate result we will report*. It says: conditioning on the event text did not beat trailing volatility at this horizon and this sample size, and here is the number. A miscalibrated ensemble with a large positive lift is a *failure we would have to disclose*, because it means the width is wrong and the lift is probably drift. The PRD says this in advance so that the result cannot be retrofitted at 18:00.

---

## 2. Users and use cases

### 2.1 Primary persona: the allocator with a live position

Wilson is the archetype and the reason this exists. A capital allocator or operator with concentrated exposure, who reads a headline and needs a distribution rather than a take.

- **Job to be done:** "A thing just happened in the world. Give me the range of outcomes for this name over the next week, and tell me how much to trust the range."
- **Current behaviour:** reads sell side notes, forms a gut view, sizes by feel. No calibrated interval anywhere in the loop.
- **What they need from us:** a fan chart, a p5 to p95 band, and a visible track record of whether our bands have historically held.
- **What kills it for them:** an unfalsifiable claim. This persona has run models. A tool that cannot lose is a tool they will not use.

### 2.2 Secondary persona: the quantitatively literate skeptic (the judge)

Someone who will click the third screen before the first, and whose opening question is "what is your baseline."

- **Job to be done:** "Show me you know the difference between skill and volatility clustering."
- **What they need:** the null model visible and non removable, the confidence interval on the lift, the leakage statement in the product rather than in a footnote, and an honest statement of what we did not earn.
- **What kills it:** a headline number with no interval, or a directional accuracy figure anywhere near the top of the page.

### 2.3 Tertiary persona: the curious stranger at the 20:00 launch

Sundai's evening block is explicitly live user testing rather than pitch presentations (Sundai, intro for newcomers). Somebody who has never heard of CRPS will sit down and click.

- **Job to be done:** "Type something dramatic, see something interesting, understand what I am looking at."
- **What they need:** a working public URL, a pre filled example so the empty state is never empty, a fan chart that reads without a stats background, and one sentence under it in plain English.
- **What kills it:** localhost, a spinner, an empty ticker with no events, or a 500 on a ticker we did not test.

### 2.4 Use cases in scope for the hack

| # | Use case | Screen | Layer |
|---|---|---|---|
| U1 | Browse the historical jump ledger for a ticker, with the contemporaneous news that surrounded each jump | Ledger | Narrative |
| U2 | Type a counterfactual event ("NVDA announces a 40 percent datacenter revenue miss"), get an ensemble of forward paths with quantiles and a plain English rationale | Forecast | Narrative surface, Method engine |
| U3 | Re run a real historical event as of its own date and see the realised outcome scored against our ensemble | Forecast, with score panel | Both |
| U4 | Inspect the whole walk forward backtest: lift over null with an interval, PIT histogram, per event table, famous versus obscure split | Scoreboard | Method |

### 2.5 Explicitly out of scope for the hack

- Portfolio level or multi name joint distributions. Single ticker only. Copula and vine copula machinery is the standard approach here (He 2024, *Journal of Forecasting*, doi 10.1002/for.3112) and we are not attempting it.
- Any trading signal, position sizing, or execution. This is a distribution viewer, not a strategy.
- Options implied distributions as either input or benchmark, which would be the honest institutional comparison and is post hack work.
- Intraday horizons. The frozen horizon is 5 trading days.
- Live streaming or real time data. Everything is served from a cached corpus on disk.

---

## 3. The Wolfram theoretical framing

The hack is sponsored by Wolfram Research and themed on adaptation and evolution. The relevant source is Wolfram's November 2025 essay, "What's Special About Life? Bulk Orchestration and the Rulial Ensemble in Biology and Beyond" (https://writings.stephenwolfram.com/2025/11/whats-special-about-life-bulk-orchestration-and-the-rulial-ensemble-in-biology-and-beyond/).

We read it in full and graded every primitive we considered borrowing. The grading is in the product, not just in this document, because cargo culting the vocabulary is exactly what a judge who has read the essay will screen for.

### 3.1 RIGOROUS: the pocket of computational reducibility

Wolfram: "it's an inevitable feature of computational irreducibility that within it there must be pockets of computational reducibility where simpler behavior occurs."

This maps onto our problem as a measured fact rather than an analogy. On the train period only (2010 to 2019, 10 tickers, 21,879 observations), regressing forward 5 day signed return on trailing 5 day move and trailing 250 day volatility gives out of sample R squared of -0.00075, +0.00071 and -0.00019 at 50, 60 and 70 percent split points. The same regressors on forward *absolute* return give +0.0999, +0.1047 and +0.0978. Dispersion is roughly one hundred times more predictable than direction, stable across split points, on holdouts of 6,560 to 10,930 observations.

That is the claim we sell. The framing earned a testable location: it told us where in an unpredictable system a bounded observer can get traction, and the prediction landed on the right variable.

**The obvious objection, which we raise ourselves:** is this just volatility clustering, GARCH, 1986? Yes, the effect is not new and we do not claim to have discovered it. The claim is narrower and still worth something: Wolfram's scheme correctly predicted *which* variable would be tractable before we measured it. That is a framing that earned a location, not a new fact.

### 3.2 RIGOROUS: the computationally bounded observer

Wolfram: "the most critical feature of observers like us is that we're computationally bounded," and it is "the characteristics of observers like us that ultimately lead to the perceived validity of the Second Law."

This is the strongest honest use of the essay in our eval section. Individual paths are unscoreable in our data because signed R squared is approximately zero. So we score coarse grained functionals instead: CRPS, PIT, quantiles. Calibration is defined relative to a chosen coarse graining. That is Wolfram's actual point rather than a borrowed word, and it is the theoretical justification for the entire scoring design in section 7.

### 3.3 CATEGORY ERROR, and we say so first: "rulial ensemble"

`CONTRACT.md` section 0 calls our Monte Carlo path cloud a rulial ensemble. That is wrong as written, and we correct it here rather than waiting to be caught.

Wolfram, verbatim: "In the statistical mechanics of gases we imagine that the underlying laws of mechanics are fixed, but there's a whole ensemble of possible initial configurations for the molecules... But in biology, for example, we can think of different genomes as defining different rules... And so now what we want is a new kind of ensemble, that we can call a rulial ensemble: an ensemble of possible rules."

A Monte Carlo over paths from one fixed generator holds the rule fixed and samples initial conditions and noise draws. That is precisely the gas case Wolfram contrasts *against*. Our path cloud is Boltzmann's ensemble, not Wolfram's.

**Why we care, and it is not vocabulary hygiene.** Our measured failure mode is that apparent skill came from an assumed drift: the naive analog resampling generator scores +14.8 percent CRPS lift, and the same model with analog returns demeaned scores -4.5 percent, significantly worse than null (see section 9.2). Drift is precisely the parameter that would differ between generators. A genuine rulial ensemble, ensembling over generator *configurations* (analog selection rule, conditioning set, drift prior, horizon map) and reporting only properties that survive across nearly all of them, is the fix for our actual bug rather than a rebrand of our demo. It is listed in section 10 as pending work, category R.

### 3.4 UNEARNED, presented as hypothesis only: multiway branching

The multicomputation and multiway branching primitive is intuitively attractive (an event opens several branches: the miss is temporary, the miss is structural, the miss is a guide down). Empirically it buys nothing at our horizon and sample size.

Holding width identical at sigma = 0.0857 and forcing zero drift, leave one out CRPS on the train events gives: Gaussian +0.008 lift, bimodal two branch +0.007, Student t with 4 degrees of freedom +0.014. A bimodal "multiway branch" distribution is statistically indistinguishable from a Gaussian of the same width under CRPS here. An earlier +8.3 percent mixture result was drift leaking in through the branch means, not shape.

We may use branching as a *presentation* device in the narrative layer, clearly labelled as such. We may not present it as a result.

### 3.5 DO NOT USE: bulk orchestration, mechanoidal behavior

These are the essay's title concepts and they have no honest mapping onto our product. Wolfram defines bulk orchestration as what happens when "patches of computational irreducibility have to be fitted together to achieve that purpose," arising specifically from adaptive evolution toward a fitness function: "in rules that have been adaptively evolved for a purpose mechanoidal behavior is the norm." Our forecaster does not adaptively evolve rules against a fitness function. Using these terms would be the cargo culting the audience is screening for. Note also that the essay contains no discussion of markets or economics, and a judge who knows the essay knows this.

### 3.6 Matching Wolfram's epistemic register

Wolfram hedges his own framework heavily: "What I've done here is very much just a beginning, a first exploration, both computational and conceptual, of the rulial ensemble and its consequences." He also concedes "We don't have a general way to characterize what defines biological fitness." A presentation that matches his register will read as more credible than one that treats a first exploration as settled theory.

### 3.7 On the hack theme (adaptation and evolution)

The stated challenge is "an agent, or a population of them, that keeps adapting through contact with an environment, such as feedback, selection pressure, or other agents adapting alongside it" (https://www.sundai.club/events/boston/wolfram-hack). A one shot conditional forecaster does not obviously satisfy that.

The honest framing available to us without changing any frozen file: the 2,000 sampled paths are the **population**, CRPS against the null is the **selection pressure**, and the analog weights updating as each walk forward event is scored is **inheritance**. This is genuine only if the reweighting hook actually exists. It is listed as pending work item M4 in section 10, sized and flagged. If M4 does not ship, we describe the system as a forecaster and do not claim adaptation. We do not get to have the word for free.

---

## 4. Product surface: three screens

Design principle: a stranger with no statistics background must be able to move left to right and end up understanding what the third screen means. Layer labels below are load bearing and should be visible in the UI copy.

### Screen 1: The Ledger (NARRATIVE layer)

**Purpose:** establish that the events are real and that we did not choose them after the fact.

- Ticker selector across the frozen 10 name universe, each row showing `has_data` and `n_events` from `GET /api/tickers`.
- For the selected ticker, the train period event ledger from `GET /api/events?ticker=NVDA`: date, move percent, direction, headline, and the harvested contemporaneous articles with source and publication date.
- A visible statement of the detection rule: 25 percent move over a rolling 5 trading day window, applied mechanically, no hand picking.
- **Empty state is mandatory and will fire.** Six of ten tickers have zero train events under the frozen configuration (section 6). The empty state reads, roughly: "No qualifying jump events for this ticker in the train window. The threshold is mechanical and we did not tune it to produce events." Not an error, not a spinner, not a blank pane.

### Screen 2: The Forecast (NARRATIVE surface, METHOD engine)

**Purpose:** the demo. This is the screen people remember.

- A free text box for `event_text`, pre filled with a working example so the screen is never empty on load.
- Ticker, `as_of_date`, `horizon_days` (default 5), `n_paths` (default 2000).
- `POST /api/forecast` returns an `Ensemble` and, when `as_of_date` is historical and the actual is known, a `Score`.
- Display: a fan chart over the horizon with p5, p25, p50, p75, p95 bands; the mean and standard deviation; the 2 to 3 sentence `narrative` rationale; and the historical `analogs` that shaped the ensemble, each clickable through to its Ledger entry.
- When a `Score` is present: the realised path overlaid on the fan, plus `z_score`, `pit`, `crps`, `crps_null` and `crps_lift`, with a one line reading of the z score in English ("the realised outcome landed 1.4 standard deviations below our ensemble mean").
- **Required copy under the chart:** "This is a distribution, not a prediction. The line you would draw through it is not something we claim to know."

### Screen 3: The Scoreboard (METHOD layer)

**Purpose:** the screen that survives the skeptic. It should be reachable in one click from anywhere, and the demo goes here on purpose rather than being dragged here.

From `GET /api/backtest?ticker=NVDA` and the pooled equivalent:

- `n_tests`, stated prominently. Small n is disclosed, not hidden.
- `mean_crps_lift` with a bootstrap confidence interval, never as a bare point estimate.
- **Drift decomposed lift: raw and demeaned, side by side.** This is mandatory and non negotiable, for the reason in section 9.2.
- PIT histogram, 10 buckets, with the uniform reference line drawn on it. Flat is the win.
- `calibration_ok`, computed on the **pooled** universe rather than per ticker (justification in section 7.4).
- Per event table: date, crps, crps_null, crps_lift, z_score, famous flag.
- Famous versus obscure split, reported separately, per `CONTRACT.md` section 8.2.
- **The leakage disclosure, on this screen, in the product, in normal type.** Required by `CONTRACT.md` section 8.3. Draft copy in section 9.1.
- Directional hit rate appears here and only here, below the fold, labelled "not a result."

### User journey

1. Land on Forecast with a pre filled example. Something is already on screen.
2. Type your own event. Watch the fan redraw. This is the hook.
3. Click an analog. Land on the Ledger. See that the historical events and their news are real.
4. Click "how good is this, actually." Land on the Scoreboard. See the null, the interval, the PIT histogram and the leakage statement.
5. Leave understanding that the interesting claim is the width of the band, not the direction of the line.

---

## 5. Technical architecture

Module boundaries are frozen by `CONTRACT.md` section 4. Each module has exactly one owner lane, and a lane writes only its own files. Imports go through the signatures in the contract, never through reading another lane's source.

```
                    ┌──────────────────────────────┐
                    │  frontend/**   (LANE-UI)     │
                    │  Next.js, 3 screens          │
                    └──────────────┬───────────────┘
                                   │  /api/* proxy :3000 -> :8000
                    ┌──────────────▼───────────────┐
                    │  backend/rulial/api.py       │
                    │  (LANE-API)  FastAPI :8000   │
                    │  tickers / events / forecast │
                    │  / backtest / health         │
                    └──┬────────┬─────────┬────────┘
                       │        │         │
        ┌──────────────▼──┐  ┌──▼──────┐  ┌▼──────────────────┐
        │ generator.py    │  │events.py│  │ evaluate.py       │
        │ (LANE-MODEL)    │  │(LANE-   │  │ (LANE-EVAL)       │
        │ generate_       │  │ EVENTS) │  │ crps, null_       │
        │  ensemble(req)  │  │ detect_ │  │ ensemble, pit,    │
        │  -> Ensemble    │  │ events, │  │ walk_forward      │
        └──────┬──────────┘  │ build_  │  └────────┬──────────┘
               │             │ ledger  │           │
               │             └────┬────┘           │
        ┌──────▼─────────┐        │                │
        │ news.py        │        │                │
        │ (LANE-NEWS)    │        │                │
        │ harvest(event) │        │                │
        │ build_corpus   │        │                │
        └──────┬─────────┘        │                │
               │                  │                │
        ┌──────▼──────────────────▼────────────────▼──────────┐
        │ data.py  (LANE-DATA)                                │
        │ load_prices(ticker) -> pd.DataFrame                 │
        │ load_fundamentals(ticker)                           │
        └──────────────────────┬──────────────────────────────┘
                               │
        ┌──────────────────────▼──────────────────────────────┐
        │ config.py  +  types.py    (parent, FROZEN)          │
        │ UNIVERSE, TRAIN_END, TEST_START, EMBARGO_DAYS,      │
        │ JUMP_THRESHOLD, WINDOW_DAYS, HISTORY_START,         │
        │ Article, Event, ForecastRequest, Ensemble, Score    │
        └─────────────────────────────────────────────────────┘
```

Architecture diagrams in `docs/diagrams/*.html` are owned by LANE-DIAGRAM.

**Constraints that bind every module,** from `CONTRACT.md` section 9:

- Every module imports cleanly with no network access at import time. Data loads are lazy and cached to disk under `data/`.
- No global `pip install` or `npm install`. Declare dependencies in `requirements.txt` or `package.json` only if you own that file, otherwise report the dependency upward.
- If real data is unavailable, ship a working code path with a clearly labelled synthetic fallback. Never fabricate a number and present it as real.
- No lane runs any git command.

**Dependency status, updated during the build:** `requirements.txt` has since landed and pins the stack (numpy, pandas <3, scipy, yfinance, requests, fastapi, uvicorn, pydantic, anthropic, pytest). The remaining hygiene step is that `yfinance` is not installed in the bare environment interpreter (`/opt/anaconda3/bin/python3`), so the documented install path is a virtualenv: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`. PyPI is reachable and `pandas` 2.2.2 is already present system wide. Pending item I1 is therefore closed and replaced by I1b, the fresh clone install verification.

---

## 6. Data

### 6.1 Universe and time boundary (frozen)

Universe: NVDA, AAPL, MSFT, AMZN, TSLA, META, GOOGL, JPM, XOM, BA.

```
HISTORY_START = 2010-01-01
TRAIN_END     = 2019-12-31    seed corpus and calibration may use data <= this
TEST_START    = 2020-01-01    evaluation only
TEST_END      = 2024-12-31
EMBARGO_DAYS  = 5             purge gap between train and test windows
```

No lane moves `TRAIN_END` for better results. Moving it is the leak.

### 6.2 Event definition (frozen)

An event is a trading day where the close to close return over a rolling 5 trading day window is at least 25 percent in absolute value. The event date is the **end** of the jump window. `JUMP_THRESHOLD = 0.25`, `WINDOW_DAYS = 5`. Windows are non overlapping: once an event fires, the next candidate window starts after it, so a single sustained move counts once rather than five times.

### 6.3 THE REAL EVENT COUNT

This is measured, not estimated. Run against real Yahoo daily adjusted closes for all 10 tickers, non overlapping windows, at the frozen threshold. Verification script (session scratchpad, outside the repo because this lane owns only `docs/PRD.md`): `/private/tmp/claude-501/-Users-wilsonwu-Desktop/676333f1-02b3-404d-ae65-d4a5831f92e8/scratchpad/count_events.py`. It needs no dependencies beyond the standard library and re runs in about 20 seconds. The full history column reproduces LANE-DATA's independently computed 145 exactly, which is our cross check that two independent detectors agree.

**One convention caveat, and `events.py` is canonical over this table.** Our verification detector resolves overlapping qualifying windows by scanning forward and taking the first window that fires, then suppressing the next 5 bars. LANE-EVENTS' shipped `events.py` resolves them by repeatedly taking the globally most extreme window and suppressing everything that overlaps it. Both produce pairwise non overlapping events and both avoid triple counting a single crash, but on a chain of overlapping windows they can select different representatives, so per ticker counts may differ by a small number and a given event's date and `move_pct` may differ. Treat the table below as the order of magnitude and the shape of the problem, which is what drives every decision in this section, and treat the ledger emitted by `events.py` as the number of record. Reconciling the two is pending item D2.

| Ticker | First bar | Train events, HISTORY_START = 2010 | Train events, full history | Test events, 2020 to 2024 |
|---|---|---|---|---|
| NVDA | 1999-01-22 | 5 | 47 | 2 |
| AAPL | 1980-12-12 | 0 | 16 | 0 |
| MSFT | 1986-03-13 | 0 | 4 | 0 |
| AMZN | 1997-05-15 | 0 | 47 | 0 |
| TSLA | 2010-06-29 | 10 | 10 | 17 |
| META | 2012-05-18 | 2 | 2 | 5 |
| GOOGL | 2004-08-19 | 1 | 2 | 0 |
| JPM | 1980-03-17 | 0 | 13 | 0 |
| XOM | 1970-01-02 | 0 | 1 | 1 |
| BA | 1970-01-02 | 0 | 3 | 5 |
| **Total** | | **18** | **145** | **30** |

Read this table honestly, because it drives several decisions:

1. **Under `HISTORY_START = 2010` as currently written in `config.py`, the train corpus is 18 events across 4 tickers.** That is not a corpus. Six of ten tickers have zero train events: AAPL, MSFT, AMZN, JPM, XOM, BA. `GET /api/events` returns an empty list for all six and `GET /api/tickers` must report `n_events` of 0 for them.
2. **Extending the price load back to each ticker's inception raises the train corpus to 145 events.** This is a `data.py` load window decision, not a change to any frozen constant: `HISTORY_START` is not in the frozen list in `CONTRACT.md` sections 1 through 3. It is nonetheless a parent decision, listed as pending item D1, and it is the single highest leverage open item in the build. Caveat: only 130 of the 145 fall in the web era (1997 onward) where contemporaneous news is harvestable at all. XOM's sole qualifying event is Black Monday, 19 October 1987. MSFT has one web era event.
3. **The test set is 30 events and TSLA supplies 17 of them, 57 percent.** Five tickers have zero test events: AAPL, MSFT, AMZN, GOOGL, JPM. `GET /api/backtest` returns `n_tests = 0` for those five and must not crash. Any pooled `mean_crps_lift` we report is substantially a TSLA statistic and the Scoreboard must say so next to the number.
4. **A third source, LANE-WOLFRAM, reported 33 train events for the 2010 to 2019 window** against our 18. The difference is the overlap convention; that lane appears to have counted overlapping windows. Our count agrees with LANE-DATA on the full history figure to the event, so we treat the non overlapping convention as canonical and flag the discrepancy so it is reconciled rather than averaged. Pending item D2.

TSLA concentration persists at every threshold we checked (0.20 gives 63 test events with TSLA at 35, 0.15 gives 172 with TSLA at 65), so it is a universe composition property, not a threshold artifact. We are not moving the threshold.

### 6.4 Price data

Solved problem, verified. Daily OHLCV is available for all 10 tickers back to inception or the Yahoo floor, with no credential and no rate limiting observed across roughly 34 calls. Two working paths: the `dubbs-research` MCP `equity_price_historical` route (provider yfinance), and a direct unauthenticated GET to the Yahoo chart endpoint with a browser user agent, which needs no library at all.

**One trap, verified:** multi symbol price requests silently drop tickers whose history starts after the requested start date, returning a `UserWarning` rather than raising. Requesting `AAPL,MSFT` from 1980-01-01 returns AAPL rows only. `data.py` must fetch per ticker, or assert that every requested symbol appears in the result, or the panel will be quietly incomplete.

### 6.5 News corpus construction

**The historical news API is dead and this is settled, not suspected.** Of five providers on `news_company`: benzinga, tiingo and intrinio return HTTP 400 for a missing credential; fmp returns HTTP 402, restricted endpoint. yfinance is the only provider that returns rows, and it **silently ignores `start_date` and `end_date`**. A request for NVDA news over November 2018 returned articles dated 6 September 2026, with `warnings: null` and the requested dates echoed back faithfully in the response metadata. It also ignores `limit`.

That silent failure is an active leakage hazard rather than a mere gap. A lane that trusts request level date filtering to enforce `TRAIN_END` would stamp 2026 articles into the pre 2019 corpus and never see an error. **All date filtering must be done on the returned row's own `date` field.** Earnings transcripts are unavailable at any date (fmp HTTP 402), so no design may depend on them.

**Chosen corpus path: agentic retrieval via WebSearch plus WebFetch, harvested once into a cached JSON corpus on disk under `data/corpus/`, never live per request.** This was tested end to end on four events and it works, with measured caveats:

- Contemporaneous pre 2019 articles with resolvable publisher URLs are retrievable. The NVDA 16 November 2018 crash returned correctly dated CNBC, Fortune and Motley Fool pieces with the right substance.
- Roughly half of major publishers block WebFetch. Motley Fool returned a full body with a parsed publication date; CNN returned HTTP 451. Harvest must try several URLs per event rather than one.
- **Coverage degrades to zero on events with no named catalyst.** AMZN 23 June 2000 (down 27.1 percent, the Ravi Suria convertible bond note) returned rich correct material. AMZN 16 August 2000 (up 25.1 percent, no named catalyst) returned nothing contemporaneous across two search rounds. Coverage is a function of narrative salience, not of date. This is precisely the famous versus obscure split that `CONTRACT.md` section 8.2 already requires us to report separately, so the weakness is measurable rather than hidden.

**Two mandatory harvest filters:**

1. **Blocklist price history aggregator domains** (macrotrends.net, stockanalysis.com, statmuse.com, finance.yahoo.com quote and history pages). They rank highly on catalyst free queries and their pages render prices through 2026. Fetching one into an `Article` for a 2000 dated event injects future prices into the train corpus.
2. **Reject retrospectives on publication date.** Search surfaces "Why NVIDIA Stock Plunged 31 percent in 2018," published 14 January 2019, alongside the genuine 2018 articles. Accept only articles published within roughly `[window_start - 2 days, window_end + 2 days]`, and log the discard count so the rejection rate is visible rather than silent. Articles whose publication date cannot be parsed are rejected and counted.

Estimated harvest cost at 145 events and 3 to 6 calls each is 400 to 800 web calls. It runs once, offline, into `data/corpus/`.

---

## 7. Validation methodology

This section answers Wilson's two direct questions head on.

### 7.1 "How often do you validate?"

**Every test event is an independent out of sample validation point. There is no single train test split that we report and then stop.**

The protocol:

1. **Walk forward with a rolling origin.** For each event in the test window, we form the forecast using only information available strictly before `as_of_date`. The generator, the analog pool, and any fitted parameters are constructed from data at or before the origin. Nothing from after the origin enters the forecast, including events later in the test set itself.
2. **A 5 trading day embargo (`EMBARGO_DAYS = 5`).** A purge gap between the training window and each test point. This exists because our label is a 5 day forward return, so a train observation ending inside the test point's forward window would share overlapping price data with the thing we are trying to predict. Without the embargo the split leaks by construction. This is the standard purge and embargo discipline for overlapping label horizons in financial cross validation.
3. **No refitting on test outcomes, ever.** Test results are read once and reported. If we tune anything after seeing them, the number stops being out of sample and we say so on the Scoreboard.
4. **Reported at three granularities:** per event (the full table, every point visible, nothing aggregated away), per ticker (`GET /api/backtest?ticker=...`), and pooled across the universe.

**How many validation points, concretely.** 30 test events over 2020 to 2024 under the frozen definition, of which TSLA is 17. Per ticker: TSLA 17, META 5, BA 5, NVDA 2, XOM 1, and zero for the other five. We report `n_tests` on the screen next to every number derived from it. At n = 30 with one name at 57 percent weight, the honest framing is: this is a calibration check with a wide interval, not a performance claim.

**Additionally, a train period leave one out pass.** Because 30 test points is thin, the generator is also scored leave one out on the train corpus during development. That is a development instrument for catching a broken generator early, and it is reported as train diagnostics, clearly separated. It is not evidence of out of sample skill and does not appear in the headline.

### 7.2 "By what standard deviation?"

`Score.z_score = (actual_return - ensemble.mean) / ensemble.std` is computed and reported for every scored event, per `CONTRACT.md` section 5. It is the direct answer to "how many sigma was that," it goes on the Forecast screen, and it goes in the per event table on the Scoreboard.

**And it is not our metric, for a specific and important reason.**

The z score is not a proper scoring rule. It can be gamed in one direction, trivially: widen the ensemble and every `|z|` shrinks. A model that outputs a standard deviation of 500 percent is never surprised by anything and would post beautiful z scores forever while being useless. Any metric a forecaster can improve by becoming vaguer is disqualified as a headline.

The z score also uses only the second moment. Our distributions are deliberately non Gaussian (heavy tailed, sometimes asymmetric), and a z score cannot tell you whether the 5th percentile was right. It compresses the entire predictive distribution into one number that assumes the shape we are specifically trying not to assume.

**So the real metrics are CRPS and PIT.**

- **CRPS** (continuous ranked probability score) is *strictly proper*: it is minimised in expectation only by reporting your true predictive distribution. You cannot improve it by widening, and you cannot improve it by narrowing. It uses the whole distribution rather than two moments. It reduces to absolute error for a point forecast, so it is directly comparable across a deterministic and a probabilistic forecaster. This is the standard, established in Gneiting and Raftery (2007) and in Gneiting, Balabdaoui and Raftery, "Probabilistic Forecasts, Calibration and Sharpness," *JRSS-B* 69(2):243 to 268 (2007).
- **PIT** (probability integral transform) is the predictive CDF evaluated at the realised observation. If the ensemble is correctly calibrated, PIT values are uniform on [0,1] and the histogram is flat. A hump in the middle means the ensemble is too wide. U shaped means too narrow. Skewed means biased. It tests every quantile, not just the variance, which is exactly what a z score cannot do.

The paradigm, stated in the same paper, is **maximise sharpness subject to calibration**. Calibration first, and only among calibrated forecasters do we prefer the sharper one. That is the discipline the entire eval is organised around.

**Reported alongside, so the z score is not left dangling:** the empirical coverage of our stated intervals. Of the events where we said 90 percent, how many landed inside. That is the plain English version of PIT and it is what the allocator persona actually wants.

### 7.3 Estimator choices, verified numerically

Three implementation decisions were checked in code rather than assumed, and LANE-EVAL should implement them as specified.

1. **Use the fair (unbiased) CRPS ensemble estimator,** dividing the pairwise term by `2m(m-1)`, not the common plug in form dividing by `2m^2`. Against the analytic Gaussian CRPS for N(0,1) at y = 0.5 (0.331404), mean estimator error over 4,000 replicates: at m = 5 the plug in is off by +0.110 while the fair estimator is off by -0.002; at m = 50, +0.0109 versus -0.0004. Unbiasedness is Ferro (2014), summarised in Zamo and Naveau, *Mathematical Geosciences* (2018), doi 10.1007/s11004-017-9709-7.
2. **Use the O(m log m) sorted identity** for the pairwise term rather than the naive double sum. At `n_paths = 2000` the double sum is a 4,000,000 element matrix per event. The identity `sum_i sum_j |x_i - x_j| = 2 * sum_i (2i - m - 1) * x_(i)` over sorted x was verified to agree to 7.3e-12 on m = 200.
3. **Compute `crps_null` in closed form**, not by sampling it. `CRPS(N(mu,sigma), y) = sigma * [z(2*Phi(z) - 1) + 2*phi(z) - 1/sqrt(pi)]` with `z = (y - mu)/sigma`. Sampling both sides at equal m introduces an estimator asymmetry worth 2 to 3 lift points at m = 50 when our ensemble is sharper than the null. At m = 2000 the distortion falls into Monte Carlo noise, but the closed form removes the question entirely and costs nothing.
4. **Use the randomised PIT**, `(#{x < y} + U)/(m+1)` with U seeded deterministically from ticker and date, rather than the mid rank convention. At m = 50 the mid rank convention produces a spurious single bin spike, 21.8 percent maximum deviation from uniform on a correctly specified ensemble, purely because the discrete PIT grid does not align with 10 equal bins. The randomised PIT gave 2.0 percent, which is Monte Carlo noise. At m = 2000 the artifact shrinks to 3.1 percent versus 2.2 percent, tolerable but fragile if anyone lowers `n_paths`.

### 7.4 `calibration_ok` must be pooled, not per ticker

Per ticker calibration testing at our sample sizes is close to meaningless and we should not ship a boolean that is really a coin flip.

Measured power, 600 replicates, alpha 0.05, KS and Cramer von Mises against uniform, randomised PIT: against an ensemble that is **2x too narrow**, n = 12 events rejects 30 percent of the time (KS) and 28 percent (CvM); n = 60 rejects 92 and 96 percent; n = 120 rejects 99 and 100 percent. Against a milder 1.43x too narrow, n = 12 rejects 14 percent and n = 120 rejects 64 percent. Both tests held size correctly at 0.04 to 0.06 under the null.

So a per ticker `calibration_ok = true` at n = 12 fails to detect a 2x too narrow ensemble 70 percent of the time. The contract's response schema is per ticker, so the compatible resolution is: keep the per ticker field for schema compliance, compute the **pooled** universe verdict as the one the Scoreboard displays as the headline, and label the per ticker value as underpowered wherever it appears. Pending item E3.

### 7.5 A second, harder baseline

`CONTRACT.md` section 7 freezes `crps_null` **in**; it does not forbid additional baselines. We should add one, because the frozen null is soft in exactly the regime we operate in.

The frozen null is Gaussian with trailing 250 day sigma and zero drift. Immediately after a 25 percent weekly move, a 250 day trailing sigma is at its most stale, and volatility clusters. Measured on the train period: trailing 250 day vol post jump is 0.03216 versus 0.01803 otherwise, a factor of 1.78. So the null's width already auto expands after an event, and beating it partly for free is possible without the event text contributing anything.

Recommended second baseline: **filtered historical simulation**, that is EWMA or GARCH devolatised returns, bootstrapped standardised residuals, revolatised by a conditional forecast. This is the standard non ML practice (Barone-Adesi, Engle and Mancini, SSRN 603382) and it exists precisely because trailing unconditional sigma is a poor conditional forecast. Reporting lift against both the frozen null and an FHS baseline is the difference between "we beat a strawman" and "we beat the thing a practitioner would actually use." Pending item E2.

---

## 8. The reward signal

What gets rewarded, what does not, and what is structurally prevented. All of the following are frozen by `CONTRACT.md` section 7.

### 8.1 Rewarded

| Signal | Metric | Direction |
|---|---|---|
| Sharpness relative to a baseline that knows nothing but volatility | `crps_lift = (crps_null - crps)/crps_null` | Higher, and reported with a bootstrap interval |
| Calibration across all quantiles | PIT histogram flatness, KS and CvM against uniform, pooled | Flat |
| Interval coverage matching its label | Empirical coverage of stated p5 to p95 band | Close to 90 percent |
| Skill that survives demeaning | Demeaned `crps_lift` | Positive, or honestly reported as negative |
| Skill on low salience events | Obscure event subset lift, reported separately | Comparable to the famous subset |

### 8.2 Not rewarded, and structurally prevented

- **Directional hit rate may not be reported as a headline result.** Frozen. It makes a coin flip look skilled. It may appear in an appendix, labelled as not a result.
- **The null model may not be removed from the eval**, however good removing it would make us look. Frozen.
- **The stage narrative may never become the scoring function.** Frozen. Harvey, Iran and the layoffs report live in the demo. CRPS against null lives in the eval.
- **Widening the ensemble to flatter the z score** earns nothing, because CRPS is strictly proper and cannot be improved that way. The metric choice itself is the enforcement mechanism.
- **Lift that vanishes on demeaning** is drift, not skill, and is reported as such rather than as a headline. See section 9.2.

### 8.3 The known ceiling, stated in advance

Nobody on this team should be surprised at 18:00 by a small lift number, so here is the measured ceiling.

An **oracle** that cheats by using the realised post jump sigma scores CRPS 0.05504 against the null's 0.05615. That is a lift of **+2.0 percent**, and it is cheating. A naive leave one out conditional Gaussian gets +1.5 percent with a 90 percent interval of [-0.005, +0.033], straddling zero. Realised post jump forward sigma divided by null implied sigma is 1.19, meaning the frozen null is already nearly calibrated on width.

**Therefore: any generator that only rescales a Gaussian width caps at roughly +2 percent lift.** Ensemble shape at equal width buys approximately nothing (section 3.4). The room to move is in conditional **location** and in conditional **shape given a specific event type**, and both are exactly where drift contamination lives. A +2 percent honestly measured lift with flat PIT is a good outcome for this project. A +15 percent lift should be treated as a bug report until demeaned.

---

## 9. Leakage and limitations: the strongest case against us

Stated by us, first, in the product and not only in this document. This is required by `CONTRACT.md` section 8.

### 9.1 LLM lookahead: cutting the input at 2019 does not cut the weights

Any LLM in the generator has read the post 2019 world. It knows how COVID went. It knows Boeing's 737 MAX outcome. Restricting *input* data to on or before `TRAIN_END` does nothing about the *weights*.

This is not a caveat we invented, it is a formal result and we cite it rather than rediscovering it. Lopez-Lira, Tang and Zhu, "The Memorization Problem: Can We Trust LLMs' Economic Forecasts?" (arXiv:2504.14765), Proposition 1: when a model has memorised outcomes, forecasting ability is theoretically **unidentifiable**, because any constrained output is consistent with both genuine skill and disguised recall. Corollary 1: the identified set is the entire possible label set, so constrained outputs carry zero information about forecasting capability. Their measurements: GPT-4o recalls pre cutoff S&P 500 daily levels at 0.61 percent MAPE versus 16.87 percent post cutoff; directional accuracy 80.6 percent pre cutoff versus 45.7 percent post; headline year dating 98.5 percent versus 28.8 percent. Critically, **prompt based mitigation fails**: instructed to ignore post 2010 data, the model still hit 98 percent accuracy after the fake cutoff.

**What we do about it, all three from the frozen contract:**

1. **Report lift over null, never raw accuracy.** Memorisation has to beat a baseline to count for anything.
2. **Include obscure, low salience events in the test set alongside famous ones, and report them separately.** A model that only wins on famous events is remembering, not forecasting. This is a cheap discrete cousin of the Lookahead Propensity metric in Gao, Jiang and Yan, "Detecting Lookahead Bias in LLM Forecasts" (arXiv:2512.23847), and we position it as such rather than as an invention.
3. **State it on the results screen, out loud, in the product.**

Draft product copy for the Scoreboard: "The language model in this system was trained on data that includes the period we are testing on. Cutting our input data at 2019 does not cut its weights. That is why the number above is lift over a baseline rather than raw accuracy, and why we report famous and obscure events separately. If we only win on the famous ones, we are remembering, not forecasting."

**The one place we are genuinely differentiated** is counterfactual conditioning: for an event that never happened, memorisation has nothing to recall. That is a different query type from retrieved real documents or real headlines. But it cuts both ways, and the PRD names the tension rather than hiding it: **the counterfactual mode is our best story and the least scoreable part of the system**, because there is no realised outcome to score against. The majority of the eval set is real historical jumps, where the actual is known and therefore recallable. The demo's best moment and the eval's scoreable population are not the same events.

### 9.2 The drift trap, which is our own measured bug

The intuitive generator, resample historical analog outcomes, scores **+14.8 percent CRPS lift**, 90 percent interval [+0.015, +0.249], on leave one out over the train events. The same model with the analog returns **demeaned** scores **-4.5 percent**, 90 percent interval [-0.084, -0.014], significantly *worse* than null.

The cause: the train corpus is roughly 30 up jumps to 3 down jumps with a mean forward return of +5.77 percent, because 2010 to 2019 was a bull decade for NVDA and TSLA. The lift is 100 percent bull decade drift. The test window opens with COVID, where that drift sign inverts.

**Mitigation, mandatory:** drift decomposed lift, raw and demeaned, is a standard field in the `/api/backtest` response and a standard column on the Scoreboard. This cannot be reported as skill by accident. Pending item E1.

### 9.3 The baseline is soft in exactly our regime

Volatility clusters. A 250 day trailing sigma is at its most stale right after a 25 percent weekly move. Positive `crps_lift` could come entirely from volatility clustering with the event text contributing nothing at all. This is the attack a quantitatively literate judge runs first, ahead of leakage. Our answer is section 7.5's second baseline, and if that does not ship in time, our answer is to say this sentence out loud before we are asked.

### 9.4 Sample size and concentration

30 test events. TSLA is 17 of them, 57 percent. Five tickers have zero test events. Any pooled `mean_crps_lift` is substantially a TSLA statistic. Bootstrap intervals on 30 points are wide and we display them. We do not report a per ticker `calibration_ok` as though it means something at n = 12 (section 7.4).

### 9.5 Corpus coverage is a function of salience

WebSearch harvest returns rich material for events with a named catalyst and nothing at all for catalyst free events. That biases our corpus toward exactly the famous events where LLM memorisation is strongest. The obscure subset is therefore both the most important test and the thinnest slice of the corpus. We report the article count per event so the reader can see which events are thin.

### 9.6 We are not first, and the PRD says so

Almost nothing in our stack is novel as a technique, and pretending otherwise would fail on contact with anyone who reads arXiv.

- Synthetic return path generation is mature: QuantGAN (Wiese et al., arXiv:1907.06673, 2019), diffusion models for the same task (arXiv:2410.18897, 2024), TimeGAN (Yoon et al., NeurIPS 2019), and the non ML standards of filtered historical simulation and the stationary block bootstrap (Politis and Romano, 1994).
- CRPS plus PIT calibration has been the weather forecasting standard since Gneiting, Balabdaoui and Raftery (2007).
- LLMs reading news to predict returns is Lopez-Lira and Tang (arXiv:2304.07619, *Journal of Financial Economics* 2026), reporting roughly 90 percent portfolio hit rates on post cutoff headlines.
- **The closest prior art, and we name it before a judge does: ScenarioDiff (arXiv:2608.17164, 17 August 2026)** is text conditioned probabilistic time series forecasting, conditioned on a qualitative scenario description of the forecast horizon, scored with CRPS, and strongest on event driven domains. That is structurally our system, published a month before this build.
- Time series foundation models already emit calibrated quantiles, and their measured gains on financial returns over a random walk are "small and sparse" (arXiv:2606.27100). That is a realistic prior for our own lift.

**What is actually defensible,** stated narrowly: (a) counterfactual event text as the conditioning input, where memorisation has nothing to recall, which is a different query type from ScenarioDiff's retrieved real documents; (b) the honesty architecture frozen into `CONTRACT.md` sections 7 and 8 as a product and engineering contribution rather than a research one, where the null cannot be removed, the flattering metric cannot be a headline, and the leakage disclosure is a UI requirement; (c) a working, deployed, clickable version of any of this, which none of the papers above have.

The rulial framing is presentation, not method, and this document says so in section 3.3.

---

## 10. PENDING WORK

This is the backlog the team works from today. Every row is claimable. **Demo blocking** means the 20:00 launch fails or embarrasses us without it. Sizes: XS under 15 minutes, S about 30 minutes, M about 1 hour, L 2 hours or more.

Candidate owners: the eight build lanes, plus two roles Sundai requires and `CONTRACT.md` does not assign: a **Launch Lead** and a **Deploy Owner**. Guzel is the natural claimant for anything in categories P, F or X given the electrical engineering and systems background, and the Deploy Owner slot in category X is the highest leverage unclaimed item on this list.

### Category X: SHIP AND LAUNCH (unowned in the contract, highest risk)

| ID | Task | Owner slot | Size | Depends on | Blocking? |
|---|---|---|---|---|---|
| X1 | **Assign a Deploy Owner and pick a hosting target.** Nothing in `CONTRACT.md` section 4 owns deployment, and the contract specifies localhost only. Sundai's first non negotiable launch requirement is a working deployed application at a public URL, due between 18:00 and 19:00. | UNASSIGNED, claim now | XS to decide | Nothing | **YES** |
| X2 | Deploy the backend. FastAPI on :8000 to Railway, Render or Fly, or a single container serving both. Corpus files must ship with the image since there is no live data fetch. | Deploy Owner | M | X1, A1, D3 | **YES** |
| X3 | Deploy the frontend to a public URL with `/api/*` pointed at the deployed backend rather than localhost. | Deploy Owner, LANE-UI | M | X1, X2 | **YES** |
| X4 | Public GitHub repository, open source, with a README that states the frozen contract, the honest limitations, and the team attribution. | Launch Lead | S | Nothing | **YES** |
| X5 | Project page on sundai.club/projects with description, live URL, GitHub link and team attribution. Form fields are behind login and not yet enumerated. | Launch Lead | S | X3, X4 | **YES** |
| X6 | **30 second video, filmed at lunchtime, not at 19:00.** The afternoon block explicitly asks for it. Film against the Forecast screen even if the Scoreboard is not final. | Launch Lead, Guzel | S | Screen 2 rendering anything | **YES** |
| X7 | Pre launch checklist pass between 19:00 and 20:00: click every ticker including the six with zero events, every screen, on a phone, on someone else's laptop, in a private window. | Whole team | M | X3 | **YES** |
| X8 | **Feature freeze at 17:30, not 19:30.** Deploy starts at 18:00. Put it on the wall. | Launch Lead | XS | Nothing | **YES** |
| X9 | Lessons learned write up for the evening share: what an eight lane parallel agent build actually cost and produced. Optional per Sundai, and it is the single most on theme thing we can say. | Wilson | S | Nothing | No |

### Category D: DATA AND CORPUS

| ID | Task | Owner slot | Size | Depends on | Blocking? |
|---|---|---|---|---|---|
| D1 | **Decide the price history load window.** `HISTORY_START = 2010` yields roughly 18 train events across 4 tickers. Loading from inception yields roughly 145. `HISTORY_START` is not in the frozen list in `CONTRACT.md` sections 1 to 3. The shipped `data.py` already caches from a 2 year warm up before `HISTORY_START` and accepts `load_prices(ticker, start=...)` to widen, so this is a one parameter decision, not a refactor. Highest leverage open decision in the build. | Parent | XS to decide, S to apply | Nothing | **YES** |
| D2 | Reconcile three event counts that disagree: this lane's first wins scan (18 train at 2010), LANE-WOLFRAM's overlapping count (33), and LANE-EVENTS' shipped greedy most extreme dedup in `events.py`. Publish the ledger's own totals as canonical, state the convention in one sentence on the Ledger screen, and update section 6.3 of this PRD to the shipped numbers once `data/events.jsonl` exists. | LANE-EVENTS, LANE-PRD | S | D1 | **YES** |
| D3 | Harvest the news corpus once into `data/corpus/`, with the aggregator domain blocklist and the publication date filter from section 6.5. Log the discard count. | LANE-NEWS | L | D1 | **YES** |
| D4 | Per ticker price fetch with an assertion that every requested symbol is present, defending against the silent multi symbol drop. | LANE-DATA | S | Nothing | **YES** |
| D5 | Hand curate a small seed set for pre web events and catalyst free events, labelled `source = "curated"` so it can be filtered out of any headline metric. | LANE-NEWS | M | D3 | No |
| D6 | Label every test event famous or obscure, populating `Event.famous`, using an explicit written rule rather than intuition. | LANE-EVENTS | M | D1 | **YES** |
| D7 | Probe SEC EDGAR 8-K filings through the `regulators_sec_*` routes as a primary source fallback for pre 2005 events where publisher coverage is thin. Untested. | LANE-NEWS | M | D3 | No |

### Category M: MODEL AND GENERATOR

| ID | Task | Owner slot | Size | Depends on | Blocking? |
|---|---|---|---|---|---|
| M1 | `generate_ensemble(req) -> Ensemble` producing all frozen fields, with a clearly labelled synthetic fallback so the API never 500s when the corpus is thin. | LANE-MODEL | L | D1 | **YES** |
| M2 | **Do not build a width only generator.** The oracle ceiling against the frozen null is +2.0 percent (section 8.3). Aim at conditional location and conditional shape by event type. | LANE-MODEL | Design constraint | Section 8.3 | **YES** |
| M3 | Populate `Ensemble.narrative` with 2 to 3 sentences of plain English rationale, and `Ensemble.analogs` with the actual historical events that shaped the draw. Both are demo critical. | LANE-MODEL | M | M1, D3 | **YES** |
| M4 | **The adaptation hook**, which is what makes the theme claim honest: analog weights update as each walk forward event is scored. Population equals paths, selection pressure equals CRPS, inheritance equals the updated weights. If this does not ship, we do not use the word adaptation. | LANE-MODEL, LANE-EVAL | L | M1, E1 | No, but it is the theme |
| M5 | Handle the empty analog pool. Six tickers have zero train events under D1's current setting. The generator must return something sane and labelled rather than raising. | LANE-MODEL | S | M1 | **YES** |

### Category E: EVALUATION

| ID | Task | Owner slot | Size | Depends on | Blocking? |
|---|---|---|---|---|---|
| E1 | **Drift decomposed lift, raw and demeaned, as a standard field in `/api/backtest` and a standard column on the Scoreboard.** Non negotiable, per section 9.2. | LANE-EVAL | M | Nothing | **YES** |
| E2 | A second, harder baseline alongside the frozen null: EWMA or GARCH filtered historical simulation. The contract permits additional baselines. | LANE-EVAL | L | Nothing | No, but it is the first judge question |
| E3 | Pooled `calibration_ok` as the displayed headline, per ticker retained for schema compliance and labelled underpowered. | LANE-EVAL, LANE-API | S | Nothing | **YES** |
| E4 | Implement the four verified estimator choices from section 7.3: fair CRPS, sorted O(m log m) pairwise term, closed form Gaussian `crps_null`, randomised PIT seeded from ticker and date. | LANE-EVAL | M | Nothing | **YES** |
| E5 | Bootstrap confidence interval on `mean_crps_lift`, displayed with the point estimate everywhere it appears. | LANE-EVAL | S | E1 | **YES** |
| E6 | Famous versus obscure split reported separately in the backtest response. | LANE-EVAL | S | D6 | **YES** |
| E7 | Empirical interval coverage, the plain English version of PIT, for the allocator persona. | LANE-EVAL | S | E4 | No |
| E8 | Handle `n_tests = 0` for the five tickers with no test events, without crashing and without emitting a misleading zero. | LANE-EVAL, LANE-API | S | Nothing | **YES** |

### Category A: API

| ID | Task | Owner slot | Size | Depends on | Blocking? |
|---|---|---|---|---|---|
| A1 | All five frozen routes returning contract shaped JSON. | LANE-API | L | M1, E1 | **YES** |
| A2 | `GET /api/tickers` must report `n_events = 0` honestly for the six empty tickers, with `has_data = true`, since price data exists even where events do not. | LANE-API | XS | D1 | **YES** |
| A3 | Never 500 on a thin or empty ticker. Every route returns a well formed empty response with a reason string. | LANE-API | S | A1 | **YES** |
| A4 | CORS and the production API base URL for the deployed frontend. | LANE-API, Deploy Owner | XS | X2 | **YES** |
| A5 | Response caching or precomputation for the backtest route so the demo does not run a 30 event walk forward while a stranger waits. | LANE-API | M | A1 | **YES** |

### Category F: FRONTEND

| ID | Task | Owner slot | Size | Depends on | Blocking? |
|---|---|---|---|---|---|
| F1 | Three screens per section 4, with layer labels visible in the copy. | LANE-UI, Guzel | L | A1 | **YES** |
| F2 | **Empty ledger state** for the six tickers with zero train events. This will fire in front of a stranger. | LANE-UI | S | A2 | **YES** |
| F3 | Fan chart with p5 to p95 bands, and the realised path overlaid when a score exists. | LANE-UI | L | A1 | **YES** |
| F4 | PIT histogram with the uniform reference line drawn on it. | LANE-UI | M | A1, E4 | **YES** |
| F5 | **Leakage disclosure copy on the results screen, in normal type.** Frozen requirement. Draft text is in section 9.1. | LANE-UI | XS | Nothing | **YES** |
| F6 | Pre filled example event so the Forecast screen is never empty on load. | LANE-UI | XS | F1 | **YES** |
| F7 | Loading and error states everywhere. A stranger's first click must never land on a blank pane. | LANE-UI | M | F1 | **YES** |
| F8 | Mobile viewport pass. Demos get opened on phones. | LANE-UI, Guzel | M | F1 | No |

### Category R: RESEARCH AND FRAMING

| ID | Task | Owner slot | Size | Depends on | Blocking? |
|---|---|---|---|---|---|
| R1 | **Parent decision: attempt a genuine generator ensemble (true rulial), or ship the path ensemble and state the category error honestly?** LANE-WOLFRAM recommends the latter, and so does this PRD: the honest statement is cheap, credible, and directly answers the sharpest question, whereas a half built generator ensemble at this sample size produces a number nobody should trust. | Parent | XS to decide | Nothing | No |
| R2 | Confirm whether the 10:30 Wolfram Research topic intro introduces a sponsor requirement, a sponsor prize, or free Wolfram Cloud credentials. Nothing is on the written page. This is the one fact that could invalidate "Wolfram tooling is not mandatory." | Whoever is in the room | XS | Attend | **YES if it changes** |
| R3 | Optional WolframAlpha sponsor relevance insurance: free tier at 2,000 non commercial calls per month, single GET to `/v1/result`, roughly 15 to 30 minutes to wire in as a clearly attributed "Wolfram Alpha says" sidebar. Must not be presented as our model's own computation. | Any lane with slack | S | R2 | No |
| R4 | Does the dispersion predictability (R squared about 0.10) survive into the 2020+ test window, or does the COVID regime break it? Train data only was touched deliberately. If it does not survive, the one rigorous theoretical claim weakens and the deck softens. | LANE-EVAL | M | E1 | No |
| R5 | Upgrade the famous versus obscure binary to an LLM based Lookahead Propensity score (arXiv:2512.23847), roughly one extra call per test event. Out of scope for v1, named here as the obvious v2. | Post hack | L | D6 | No |

### Category I: INFRASTRUCTURE AND HYGIENE

| ID | Task | Owner slot | Size | Depends on | Blocking? |
|---|---|---|---|---|---|
| I1 | ~~Create `requirements.txt`.~~ **LANDED during the build.** Pins numpy, pandas <3, scipy, yfinance, requests, fastapi, uvicorn, pydantic, anthropic, pytest. | Parent | Done | Nothing | Closed |
| I1b | Verify the documented install on a clean machine: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then import every module with no network at import time. `yfinance` is absent from the bare system interpreter, so anyone running without the venv will hit it. | Deploy Owner | S | I1 | **YES** |
| I2 | End to end smoke test: fresh clone, install, run backend, run frontend, click all three screens, all ten tickers. | Whole team | M | X3 | **YES** |
| I3 | Architecture diagrams in `docs/diagrams/*.html`. | LANE-DIAGRAM | M | Section 5 | No |
| I4 | Discord installed on phone and desktop by everyone. The event page calls this essential. | Whole team | XS | Nothing | No |

**Demo blocking count: 38 of 51 items.** If time compresses, the survival ordering is X1, X2, X3, I1, A1, M1, F1, F3, E1, F5, X6, X4, X5, X7. That set produces a deployed, clickable, honestly labelled product with a scored fan chart and the leakage disclosure. Everything else is upside.

---

## 11. Success criteria and the demo script

### 11.1 What "we shipped" means

Sundai's own framing: "We measure success not in demos or presentations, but in shipped applications, user engagement." The evening block is live user testing, not pitch presentations. There is no published rubric and no published prizes. So the de facto criteria are: does it work live in a stranger's browser, is it on theme, and what did you learn.

**Must have, or we did not ship:**

1. A public URL that a stranger can open on their own phone and use without us touching it.
2. All three screens render, and no ticker in the frozen universe produces a crash, a blank pane or a spinner that never resolves. Including the six with zero train events.
3. A real event, entered live by a stranger, returns a fan chart in under about 5 seconds.
4. The Scoreboard shows `n_tests`, `mean_crps_lift` with an interval, raw and demeaned lift, a PIT histogram, and the leakage disclosure in readable type.
5. Public GitHub repo, project page, 30 second video, team attribution.

**Should have:**

6. The second, harder baseline (E2), so the first judge question has a number attached rather than an acknowledgement.
7. The adaptation hook (M4), so the theme claim is earned rather than asserted.
8. Famous versus obscure split visible on screen.

**Explicitly not a success criterion:** a large positive `crps_lift`. A small honestly measured lift with a flat PIT histogram is the expected and acceptable result, for the reasons in section 8.3. We decided this before running the test set, and this document is the record that we did.

### 11.2 The demo script, beat by beat, 3 minutes

Format is live user testing rather than a stage pitch, so this doubles as the script for one person at the laptop. Timings are targets.

**Beat 1, 0:00 to 0:20. The hook, on the Forecast screen, already loaded.**

> "Pick something that happened in the world. Hurricane Harvey hitting the Gulf refineries. A conflict closing a shipping lane. A bad layoffs report. Type it here and pick a ticker."

Let them type. Do not type it for them. The screen is pre filled so it is never blank, but their sentence is the moment.

**Beat 2, 0:20 to 0:50. The fan chart appears.**

> "That is not a prediction. It is 2,000 possible forward paths and the band they fall in. The p5 to p95 spread is the answer we actually think is defensible. The single line you would want to draw through the middle is the thing we specifically do not claim to know."

Point at the analogs list.

> "These are the real historical events that shaped this draw. Click one."

**Beat 3, 0:50 to 1:20. The Ledger.**

> "This is the ledger. Every 25 percent move in a week across ten names, found mechanically by a rule we froze before we looked at any results. Here is the contemporaneous news from the week it happened, filtered so nothing published after the event can get in. We did not pick these events. The threshold picked them."

If they clicked a ticker with an empty ledger, that is a feature, so use it:

> "Six of our ten names have zero qualifying events in the training window. We show that instead of hiding it, because a threshold that always finds events is a threshold someone tuned."

**Beat 4, 1:20 to 2:20. The Scoreboard. This is the beat that wins the room.**

> "Now the part that matters. Every one of these is a walk forward test: forecast made using only information before the date, with a 5 day embargo so the label windows cannot overlap the training data. Thirty test events. Tesla is seventeen of them, which we print on the screen because the pooled number is substantially a Tesla statistic."

> "The headline is not accuracy. It is lift over a null model that knows nothing except trailing volatility, and the null cannot be removed from this page. Here is the lift, with a bootstrap interval. And here is the same number with the drift removed, because when we first built the obvious version it scored plus fifteen percent and every point of it was the fact that 2010 to 2019 was a bull decade. Demeaned, that version was worse than doing nothing. So we print both columns, always."

> "This histogram is the real win condition. If our ensemble is honest, the realised outcomes should land uniformly across our own quantiles and this should be flat. Not 'we called the crash.' Flat."

**Beat 5, 2:20 to 2:45. Say the weakness before they ask.**

> "Two things we will say before you do. First, the language model in here has read the post 2019 world. Cutting our input at 2019 does not cut its weights, and that is a proven identification problem, not a hunch. That is why this page reports lift over a baseline instead of accuracy, and why we split famous events from obscure ones. If we only win on the famous ones, we are remembering, not forecasting."

> "Second, the Wolfram word we are entitled to is not the one on our contract. A Monte Carlo over paths from one fixed generator is an ensemble over configurations under a fixed rule, which is Boltzmann's ensemble, the gas case Wolfram explicitly contrasts the rulial ensemble against. The rulial version would ensemble over generators. We flagged that in our own PRD before anybody asked, and it matters because drift, our actual measured bug, is exactly the parameter that differs between generators."

**Beat 6, 2:45 to 3:00. Land it.**

> "The honest claim is narrow. Direction is unpredictable here, and we measured that: out of sample R squared of essentially zero. Dispersion is predictable, R squared about 0.10 on nine thousand held out observations. That gap is the pocket of reducibility inside the irreducibility, and it is the only thing we are willing to sell you. Everything else on this screen is us trying to break it."

### 11.3 Prepared answers to the three questions we expect

**"Isn't your null model trivially easy to beat right after a 25 percent move?"**
Correct, and it is the first thing we would ask too. Trailing 250 day vol post jump is 1.78x its normal level, so the null auto expands and part of any lift is volatility clustering rather than event comprehension. Two responses: an oracle using the realised post jump sigma caps at +2.0 percent lift, so there is very little free money in width, and we are adding a filtered historical simulation baseline (item E2) so the comparison is against what a practitioner would actually use.

**"You keep saying rulial ensemble, but that is Boltzmann's ensemble. Where are the rules?"**
Concede immediately and completely, then section 3.3. Our path cloud is statistical mechanics, not rulial. The rulial version is ensembling over generators and asking which properties survive across nearly all of them. We care because our measured failure mode is assumed drift, and drift is exactly what differs between generators. A genuine rulial ensemble is the fix for our actual bug, not a rebrand of our demo.

**"Isn't 'pockets of reducibility inside irreducibility' just volatility clustering with a new name?"**
Yes, and it is in the PRD. We are not claiming to have discovered the effect. We are claiming Wolfram's scheme correctly predicted where in an unpredictable system a bounded observer could get traction, and we verified the prediction landed on the right variable, dispersion at R squared 0.10, rather than the wrong one, direction at R squared 0. The framing earned a testable location, not a new fact.

---

## Appendix A: Sources

**Theoretical framing**
- Wolfram, S. (2025). "What's Special About Life? Bulk Orchestration and the Rulial Ensemble in Biology and Beyond." https://writings.stephenwolfram.com/2025/11/whats-special-about-life-bulk-orchestration-and-the-rulial-ensemble-in-biology-and-beyond/

**Scoring and calibration**
- Gneiting, T., Balabdaoui, F., Raftery, A. (2007). "Probabilistic Forecasts, Calibration and Sharpness." *JRSS-B* 69(2):243-268.
- Gneiting, T., Raftery, A. (2007). "Strictly Proper Scoring Rules, Prediction, and Estimation." *JASA*.
- Zamo, M., Naveau, P. (2018). "Estimation of the Continuous Ranked Probability Score with Limited Information." *Mathematical Geosciences*. doi 10.1007/s11004-017-9709-7.

**LLM lookahead and memorisation**
- Lopez-Lira, A., Tang, Y., Zhu, M. "The Memorization Problem: Can We Trust LLMs' Economic Forecasts?" arXiv:2504.14765.
- Lopez-Lira, A., Tang, Y. "Can ChatGPT Forecast Stock Price Movements?" arXiv:2304.07619, *Journal of Financial Economics* 2026.
- Gao, Jiang, Yan. "Detecting Lookahead Bias in LLM Forecasts." arXiv:2512.23847.
- Eliseev, Seleznev. "Fake Date Tests." arXiv:2601.07992.

**Prior art in generation and text conditioned forecasting**
- Tran et al. "ScenarioDiff." arXiv:2608.17164, 17 August 2026.
- Wiese, Knobloch, Korn, Kretschmer. "Quant GANs: Deep Generation of Financial Time Series." arXiv:1907.06673.
- Barone-Adesi, Engle, Mancini. "GARCH Options in Incomplete Markets" (filtered historical simulation). SSRN 603382.
- Politis, Romano (1994). The stationary bootstrap.
- "Pretrained Time-Series Foundation Models for Financial Return Forecasting." arXiv:2606.27100.
- He (2024). *Journal of Forecasting*. doi 10.1002/for.3112 (GARCH plus vine copula).

**Commercial comparables**
- Bloomberg Professional, "How to build custom scenarios to stress test your portfolio."
- MSCI predictive stress testing framework.

**Event and process constraints**
- Sundai Hack 139 event page. https://www.sundai.club/events/boston/wolfram-hack
- Sundai, intro for newcomers. https://github.com/sergeicu/sundai-global/blob/main/intro-for-newcomers.md
- WolframAlpha API free tier. https://products.wolframalpha.com/api/

**Measurements in this document** come from the phase 1 recon lanes (LANE-WOLFRAM, LANE-CONSTRAINTS, LANE-DATA-FEASIBILITY, LANE-PRIOR-ART) and, for the section 6.3 event table, from the verification script named in section 6.3, run by this lane against real Yahoo daily closes on 6 September 2026.
