# Event ledger research — cross-ticker synthesis

**Lane:** LANE-RESEARCH-SYNTH. **Inputs:** ten independent per-ticker investigations
(`docs/research/<TICKER>.md`), each of which re-derived every `move_pct` from the raw price
series *before* searching for a cause. **Outputs:** this file and `data/event_context.json`.

**Read this first if you only read one thing.** The detector is clean. The corpus is not.
329 events were detected, 233 have a cause we will defend, and **32 of them are the kind of
event this product actually needs** — a company-specific move, outside the 2008-09 financial
crisis, inside the training period. Four of the ten tickers contribute **zero** such events.
That is the finding. Everything below is the evidence.

> ### ⚠ Ledger version this analysis is pinned to
>
> `data/events.jsonl`, **329 events, 2008-01-22 to 2026-08-05**, md5
> `51288b3dfefb76dc5326e7fdad7e7652`. Every number in this file was recomputed against that
> exact file, and the 329 research dates match its keys **exactly, in both directions**.
>
> **This matters because the ledger moved under us mid-run.** At 14:12 a 799-event version
> appeared, extending detection back to 1962; at 14:14 it was reverted to the 329-event
> version. We analysed the 799-event build before it was withdrawn, and the parent should
> know what happens if it comes back: **469 of the 799 events (58.7%) predate 2008 and have
> never been researched by anyone**, 105 of 173 `major` events would be unverified, and
> attribution coverage would fall from 71% to 29%. The concentration story also inverts —
> 2000-2002 alone would be 174 events (27% of the training period) and pre-2003 history would
> be 65% of it, describing Amazon as a book retailer and Apple before the iPod. Two specific
> checks would need redoing: several lanes cleared their ticker of split artifacts with
> reasoning of the form *"MSFT's last split was February 2003, before the earliest event
> here"* — **true for the 329-event ledger, false for the 799-event one**, which has MSFT
> events back to 1986 across nine splits. If history is re-extended, this synthesis and every
> `<TICKER>.md` must be re-run before either is cited.

---

## 1. Does the ledger survive contact with reality?

**Yes, on detection. The arithmetic and the dates are sound.**

All ten lanes independently recomputed `close[t]/close[t-5] - 1` from the price series and
compared it to the stored `move_pct`. **All ten reconciled to at least four decimal places,
most to six.** This lane re-ran the check across all 329 rows against `data/prices/*.csv` as
a final gate: **zero mismatches at 5bp tolerance.** The window convention is confirmed as
*close on the ledger date over close five trading days earlier*.

### Attribution coverage — the real fraction

| Bucket | Count | Share of 329 |
|---|---:|---:|
| A cause is named at some confidence | 264 | 80.2% |
| **Cause held at confidence ≥ 0.5 (what ships in `event_context.json`)** | **233** | **70.8%** |
| …of which at least one retrieved URL backs it | 153 | 46.5% |
| …of which confidence ≥ 0.8 | 161 | 48.9% |
| Category explicitly `unexplained` (searched, nothing found) | 19 | 5.8% |
| Never researched (TSLA only; search budget exhausted) | 46 | 14.0% |

Read those rows in the right order. **80% of the ledger maps to something a market
participant would recognise. Only 47% is backed by a URL a judge could click.** The gap is
not fabrication — it is unsourced-but-plausible attribution, mostly on macro windows where
the lane could name the crisis but not isolate that specific five-day window. We report the
low number, not the high one.

Coverage is very uneven by ticker, and the unevenness is itself the story:

| Ticker | Events | Attributed ≥0.5 | With URL | Notes |
|---|---:|---:|---:|---|
| AAPL | 13 | 13 | 13 | complete |
| MSFT | 7 | 7 | 7 | complete |
| GOOGL | 9 | 9 | 9 | complete |
| XOM | 11 | 11 | 11 | complete |
| JPM | 30 | 29 | 17 | 1 unexplained (2009-01-27) |
| BA | 29 | 25 | 19 | 4 unexplained |
| META | 29 | 26 | 14 | 3 low-confidence 2012 IPO rows |
| AMZN | 27 | 24 | 16 | 1 genuine miss (2008-08-11) |
| NVDA | 75 | 45 | 16 | 30 dropped, mostly unsourced macro |
| **TSLA** | **99** | **44** | **31** | **46 never researched** |

**TSLA and NVDA account for 85 of the 96 dropped rows.** They are also the two highest-event
tickers. Any statement of the form "the ledger is 80% explained" is really "the ledger is
~95% explained for eight tickers and ~50% explained for the two that dominate it by count."

### What we could NOT explain

Nineteen events carry the category `unexplained` — searched, no credible catalyst found.
Named honestly rather than papered over:

- **AMZN 2008-08-11, +16.4%** — a single +9.4% session on an unremarkable broad-market day.
  A 9% move in a large cap should have a cause. None found. The one genuine miss in AMZN.
- **JPM 2009-01-27, +38.5% (major)** — the two candidate catalysts fall outside the window
  (Geithner sworn in 26 Jan; the "bad bank" reporting is dated 28 Jan, *one day after* the
  ledger date). The lane refused to attach the 28 Jan story to a 27 Jan event. Correct call.
- **NVDA 2009-12-07 (+23.2%)** plus six other 2008-10 NVDA windows — no catalyst identified.
- **TSLA 2010-07-19, +28.5% (major)** — the rebound half of the post-IPO round trip. The
  commonly cited "July 2010 Toyota partnership" is a *misdating*; Toyota's $50m placement was
  announced 21 May 2010. The lane caught the error rather than repeating it.
- **BA 2009-01-06** and three others — new-year rallies with no BA-specific catalyst.

---

## 2. Data artifacts: none found, and one new test that corroborates the confidence scores

**Zero data artifacts across all ten tickers.** This was checked hard, not assumed:

- **Splits.** Every ticker with a split in range was checked at the ex-date. NVDA's 2021
  4-for-1 and 2024 10-for-1, AMZN's 2022 20-for-1, AAPL's 2014 7-for-1 and 2020 4-for-1,
  GOOGL's 2014 Class C distribution and 2022 20-for-1, TSLA's 2020 5-for-1 and 2022 3-for-1
  all produce **no phantom event**. The AAPL check is the sharpest: 2020-08-31 is precisely
  where an unadjusted series would have manufactured a fake -75% event, and the ledger is
  clean there. MSFT, JPM, XOM and BA have no split inside the 2008-2026 range at all.
- **Bad prints.** Every large single-day component of a major window is accompanied by a
  2x-6x volume spike (JPM 160.7m shares on 2008-11-20 vs a 50-70m baseline; MSFT 131m on
  2015-04-24 vs ~46m; GOOGL 257m on 2015-07-17 vs 40-90m). *A bad print does not bring
  volume with it.* No isolated spike-and-reverse anywhere.
- **Non-maximum suppression.** Checked on the dense 2008 clusters by reconstructing windows
  from the price series. Adjacent windows are strictly non-overlapping in trading days
  (AMZN: 1-7 Oct then 9-15 Oct; 5-11 Nov then 12-18 Nov). Sign-flipped pairs like JPM
  2008-11-20 / 2008-11-28 are genuine capitulation-and-bounce, not one move counted twice.
- **Cross-checks against external prices.** AMZN's 2026-04-09 CSV close of 233.65 matches
  the reported $233.65; the 2016-01-27 close of 29.167 × 20 = $583.34 against an actual
  $583.37.

### New: a volume anchor test across all 329 events

The individual lanes used volume qualitatively on the events they examined closely. We ran it
systematically over the whole ledger: for every event, max daily volume inside the window
divided by the median daily volume of the preceding 60 sessions. Volume is a good anchor here
because it is in the price file itself, it cannot argue back, and it is independent of every
news search that produced the confidence scores.

| Confidence band | n | Median volume ratio | Share with **no** elevation (<1.2x) |
|---|---:|---:|---:|
| ≥ 0.80 | 158 | **3.14x** | 4% |
| 0.50 – 0.79 | 71 | 1.85x | 14% |
| < 0.50 | 48 | **1.53x** | 17% |
| never researched | 45 | 1.91x | 7% |

**The relationship is monotone and it was not engineered.** Events the lanes attributed
confidently sit on windows with three times normal volume — the signature of a real
information release. Events they could not source sit on windows with half that. This is
independent corroboration that the `confidence` field means something, and it is the
strongest argument available that the low-confidence tail is genuinely low-information rather
than merely under-researched.

**27 of 329 events (8.2%) have no volume elevation at all.** Four are `major` tier. The list
overlaps heavily with the unexplained set — BA 2009-01-06, NVDA 2008-12-24, NVDA 2009-09-10,
AMZN 2009-01-06, JPM 2009-01-09 — which is what you would expect if those windows are drift
rather than news. Two of the four low-volume majors sit on holiday weeks (NVDA 2008-11-28 is
Thanksgiving; the XOM lane separately flagged the same 2008-11-28 endpoint as a Black Friday
half session, 19.6m shares against a ~55m monthly average), so a thin tape rather than a
missing event explains those. **Recommendation: carry the volume ratio as a field and let the
UI show it. It is the cheapest honesty signal in the product.**

### Nine detected events are real price moves with no informational content

These are not detector bugs — they clear the threshold legitimately. They are events whose
generating process is supply and mechanics, not information, and training a text-conditioned
retriever on them teaches it to map news text onto flow.

| Event | What it actually is |
|---|---|
| TSLA 2010-07-07, 2010-07-19 | post-IPO price discovery, no news either way |
| TSLA 2020-08-18, 2020-08-31 | the 5-for-1 stock split melt-up — a corporate action of zero economic content that produced a +37% week |
| META 2012-05-25, 2012-06-04, 2012-06-19 | IPO microstructure: an administered opening price, a broken Nasdaq open, then discovery |
| META 2012-11-16, 2012-11-30 | lockup-expiry mechanics (the 804m-share unlock the stock *rose* into) |

---

## 3. Two interface defects that will silently corrupt downstream lanes

Neither is a detection error. Both were found independently by multiple lanes, which is why
we are confident they are real.

### 3.1 The ledger date is the window END, not the news date — 9 of 10 lanes flagged this

The catalyst sits **1 to 6 trading days before** the label, systematically. NVDA's median lag
across verified events is 3 trading days and **exactly 5 for every earnings-driven major**
(2016-11-17 → earnings 2016-11-10; 2017-05-16 → 2017-05-09; 2018-11-23 → 2018-11-15;
2023-06-01 → 2023-05-24). AMZN is even more mechanical: in **11 of 11** earnings events the
causal after-close release falls inside the window and never on the label date.

**A harvester querying `[date-1, date+1]` retrieves post-hoc commentary and misses the
catalyst on most of these.** Worse, three documented traps put a real, well-indexed,
plausible-looking headline on or near the exact ledger date that is *not* the cause:

- **AAPL 2008-10-03** — the false CNN iReport claim that Steve Jobs had a heart attack lands
  on the exact ledger date and triggered an SEC investigation. The actual cause is 29 Sept:
  AAPL -17.9% on the RBC/Morgan Stanley downgrades plus the failed TARP vote.
- **AAPL 2008-10-14** — the unibody MacBook launch is *on* the ledger date. AAPL fell 5.6%
  that day. The cause is the 13 Oct European bank recapitalisations.
- **NVDA 2022-03-21** — the obvious guess is GTC and the Hopper H100 keynote, which happened
  2022-03-22, **one day after the window closed**. The driver was the 2022-03-16 Fed liftoff.

And two where a naive earnings-calendar join produces the wrong *category*:

- **XOM 2008-10-29** — Q3 2008 earnings landed 30 Oct, one session *after* the window. Join
  to a calendar and you label a market-wide rally "earnings."
- **TSLA 2016-02-08** — Q4 2015 results landed 10 Feb, two sessions *after* the ledger date.

> **Required contract for LANE-NEWS:** harvest `[date − 10 calendar days, date]` and
> **reject any document published after the ledger date.** Do not snap to the nearest
> earnings date. NVIDIA runs GTC every March and reports four times a year; a plausible
> company event sits near almost any NVDA date. Proximity is not causation — the price path
> inside the window is the discriminator.

### 3.2 The `famous` flag is not usable as the leakage control — 6 of 10 lanes flagged this

CONTRACT.md §8.2 requires reporting obscure and famous events separately, as the memorisation
control. **The flag as currently set would make that test measure nothing.** Verified against
`data/events.jsonl`:

| Event | `famous` | What it is |
|---|---|---|
| JPM 2008-10-09 | `false` | end of the worst week in Dow history |
| JPM 2009-03-13 | `false` | the week the market bottomed (+49.1%, the largest move in the ledger) |
| JPM 2008-11-20 | `false` | S&P 500 to an 11-year low |
| JPM 2009-01-20 | `false` | worst Inauguration Day in Dow history |
| AAPL 2025-04-08 | `false` | largest weekly move in AAPL's 45-year history |
| AMZN 2026-08-03 | `false` | the $3trn market-cap crossing |
| MSFT 2008-10-10 | `false` | worst week in Dow history |
| BA 2025-04-04 | `false` | Liberation Day tariff crash |
| XOM 2020-02-27 / 2022-10-07 | `false` | worst week since 2008 / largest OPEC+ cut since the pandemic |
| JPM 2008-10-01 | `true` | (flagged famous, while the four above are not) |

77 of 329 rows are `famous: true`. If LANE-EVAL splits on this field, the "obscure" bucket
contains the single most memorised week in modern market history, and obscure-event
performance will look far better than it is — which is exactly the failure the contract's
leakage disclosure exists to prevent.

> **Recommendation to parent:** recompute `famous` from an auditable external salience signal
> — harvested article count per event is the natural one, available for free once LANE-NEWS
> runs — or hand-label it. **Do not ship §8.2 on the current flag.** This is LANE-EVENTS'
> file; we are reporting, not editing, per the contract.

---

## 4. Category distribution, and what it means for analog retrieval

Over the 233 attributed events:

| Category | All | Share | Train (≤2019-12-31) | Share |
|---|---:|---:|---:|---:|
| macro | 99 | 42.5% | 52 | 43.3% |
| earnings | 51 | 21.9% | 29 | 24.2% |
| guidance | 22 | 9.4% | 11 | 9.2% |
| crisis | 21 | 9.0% | 18 | 15.0% |
| geopolitical | 12 | 5.2% | 0 | 0% |
| sector-rotation | 8 | 3.4% | 0 | 0% |
| regulatory | 8 | 3.4% | 4 | 3.3% |
| product | 7 | 3.0% | 4 | 3.3% |
| leadership | 3 | 1.3% | 1 | 0.8% |
| sentiment / unexplained | 2 | 0.9% | 1 | 0.8% |

**The corpus is not an earnings corpus. It is a macro corpus.** Grouping
macro + crisis + geopolitical + sector-rotation + regulatory as "the market happened to this
ticker": **63.5% of all events, 61.7% of the training period.** Company-specific causes
(earnings + guidance + product + leadership) are 35.6% overall and 37.5% in training.
Note also that **`geopolitical` and `sector-rotation` have zero training-period instances** —
every event in those two categories is on the test side of the boundary.

Analogs only transfer within a regime, and that is the problem. Concretely, from the ten
lane reports:

- **GOOGL has no idiosyncratic downside event in its entire history.** Every large down move
  is market beta; every idiosyncratic move is up. Ask the generator for a bad-news conditional
  on GOOGL (lost Apple default deal, DOJ remedies) and retrieval will silently substitute
  crisis-beta analogs with a completely different mechanism. It will look plausible and be
  wrong.
- **MSFT has no in-sample precedent for a Microsoft-specific 15% down week.** Same failure
  mode: an "Azure revenue miss" query pulls crisis-beta analogs, which are fast, market-wide
  and mean-reverting — the wrong shape for an idiosyncratic fundamental disappointment.
- **XOM has no product, safety, regulatory-judgment, leadership or guidance-only event at
  all.** "XOM announces X about its own business" has no in-sample analog. The generator
  should condition on the *oil-price implication* of a described event, not its corporate
  salience.
- **AMZN has zero train-period analogs for product, regulatory, leadership, geopolitical or
  supply-chain events.** Retrieval returns GFC beta analogs — wide in the right way for the
  wrong reason.
- **The mechanism inverts mid-corpus for NVDA.** Before 2016, an NVDA 25% week was usually
  the market having a 15% week. After 2016 it is a guidance revision largely uncorrelated
  with the index that day. A model learning "NVDA big move ⇒ market big move" from the train
  period learns a relationship that stopped holding at roughly `TRAIN_END`.
- **TSLA's index-flow category (S&P inclusion/exclusion, 2020-21) has no in-sample precedent
  whatsoever**, because Tesla was not in the S&P 500 before December 2020.

There is one genuinely reusable, cross-ticker analog family, and it is worth naming because
it is the strongest thing in the corpus: **"the sovereign caps a tail risk that equity was
pricing."** Nov 2008 Citi rescue, Mar 2009 PPIP, May 2009 SCAP, Nov 2011 swap lines,
Mar 2020 open-ended QE, Apr 2020 $2.3trn, plus the BA CARES Act window and the MSFT/AMZN/XOM
March-2020 rebounds. These are structurally the same event and each produced +15% to +49% in
under a week, across four different tickers and three decades. That pattern transfers.

**Direction is asymmetric and a symmetric null will be miscentred.** 195 of 329 events are
up, 134 down. The asymmetry is mechanistic, not statistical noise: up-moves are announcement
gaps (a policy rescue, a guidance raise, a tariff pause) while down-moves compound over days
(funding stress, demand falsification). BA's entire fat right tail is the 2020 policy
response. This is what `crps_null` is for; it must not be dropped.

---

## 5. The 2008-09 concentration problem — worse than CONTRACT.md §3 assumed

CONTRACT.md §3 flagged that JPM's ten majors are all 2008-09, "one regime wearing ten hats."
That is confirmed empirically (20 of 30 JPM events and **10 of 10 JPM majors** fall in a
15-month span from 2008-01-23 to 2009-05-08). **The problem is not confined to JPM.**

| Slice | 2008-09 events | Share |
|---|---:|---:|
| Whole ledger (329) | 85 | 25.8% |
| **Training period (164)** | **85** | **51.8%** |
| Training period excluding TSLA (124) | 85 | 68.5% |
| **Training period excluding TSLA and META (111)** | **85** | **76.6%** |
| Training-period `major` events (36) | 19 | 52.8% |

The last two rows are the ones that matter. TSLA and META did not exist as public companies
in 2008 — TSLA listed in 2010, META in 2012. **Strip out the two tickers that could not have
had a financial crisis, and more than three quarters of the training corpus is one
eleven-month window in 2008-09.**

Per-ticker, the training corpus outside 2008-09 is almost empty:

| Ticker | Train events | 2008-09 | Non-GFC train dates |
|---|---:|---:|---|
| AAPL | 8 | 8 (100%) | **none** |
| XOM | 3 | 3 (100%) | **none** |
| BA | 9 | 8 (89%) | 2011-08-08 only |
| JPM | 23 | 20 (87%) | 2011-08-08, 2011-12-06, 2012-05-17 |
| MSFT | 4 | 3 (75%) | 2015-04-28 only |
| AMZN | 18 | 13 (72%) | 5 |
| GOOGL | 7 | 5 (71%) | 2013-10-18, 2015-07-17 |
| NVDA | 39 | 25 (64%) | 14 |
| META | 13 | 0 | 13 (but 8 are the 2012 IPO regime) |
| TSLA | 40 | 0 | 40 |

The test side has the mirror-image problem: **102 of the 165 test events (61.8%) fall in 2020
or 2022** — the COVID crash and the rates unwind. The evaluation set is two regimes as much
as the training set is one.

### The number the PRD must state

Count the training-period events that are (a) attributed at confidence ≥ 0.5,
(b) company-specific (earnings / guidance / product / leadership), and (c) outside 2008-09 —
i.e. the events that can actually teach a model what a *company event* looks like without the
whole market moving underneath it:

> **32 events. 9.7% of the 329-event ledger.**
> NVDA 5 · MSFT 1 · AMZN 4 · TSLA 13 · META 7 · GOOGL 2 · **JPM 0 · BA 0 · AAPL 0 · XOM 0.**

Four of the ten tickers in the frozen universe contribute nothing to the corpus this product
is built to retrieve from. That belongs on the results screen next to the leakage disclosure,
not buried in an appendix.

### One consolation, and it cuts the other way

The concentration is bad for retrieval but **good for the leakage argument in CONTRACT.md
§8.** The pre-2019 corpus is a poor cheat sheet for the post-2019 world precisely because it
is a different regime and, for NVDA, a different company. Test-set skill is therefore less
likely to be pure memorised retrieval than the contract feared. Say both things; do not use
the second to excuse the first.

### The effective sample is smaller than the row count

Three independent lanes found the same thing: events arrive in mechanically anti-correlated
pairs sharing an endpoint. JPM -37.1% (20 Nov 2008) then +35.4% (28 Nov), six trading days
apart; -30.3% (6 Mar 2009) then +49.1% (13 Mar), five days apart. AAPL 2020-03-12 and
2020-03-20 overlap by a day and are one crash split in two. TSLA's COVID cluster produces
four windows that are one shock. The lanes' own estimates: AAPL effective n ≈ 8 not 13,
GOOGL ≈ 4 not 9, TSLA's clustering overstates independence by ~20%.

> **Recommendation to LANE-EVAL:** report an effective sample size alongside `n_tests`, and
> do not treat clustered windows as independent draws in the PIT histogram.

---

## 6. Which tickers are good seeds and which are not

Ranked by usefulness as a *training-period analog donor*, which is the only thing that
matters for seeding.

**Tier 1 — real donors**

- **TSLA** (99 events, 40 train, 9 train majors, 13 idiosyncratic non-GFC). The best seed in
  the universe and the only one with a well-spread train period across six distinguishable
  regimes and nine categories. Caveat that matters: the in-sample regime is a $2bn-$75bn
  company and the out-of-sample regime is a $500bn-$1.4trn S&P constituent, so analogs
  transfer in *shape* (a delivery beat is a delivery beat) but not in *magnitude*. Also the
  worst-researched: 46 of 99 rows have no attribution at all, 21 of them in 2022. If there
  is budget for one follow-up pass, spend it on TSLA 2022.
- **NVDA** (75 events, 39 train, 11 train majors). High volume and the only ticker with a
  clean regulatory-shock archetype (Aug 2022 export controls) and a product-defect crisis
  (July 2008 notebook GPU packaging). But 64% of its train events are GFC and only two
  pre-2020 majors are company-specific — both from the old PC-graphics business. **Treat
  2016 as a hard regime boundary**; pre-2016 NVDA analogs describe a different company.

**Tier 2 — usable with a stated caveat**

- **META** (29 events, 13 train, 7 idiosyncratic non-GFC). Four cleanly separable regimes,
  which is unusually good for retrieval. But 8 of 13 train events are the 2012 IPO
  microstructure regime, only 2 of 7 majors are in-sample, and every plausible user query
  about Meta today is a capital-allocation/AI-capex question — a regime that lies entirely on
  the test side. Honest lift on META must come from transferring the 2012-13 platform-
  transition analogs. Defensible, non-obvious, and it should be said out loud on the results
  screen.
- **AMZN** (27 events, 18 train). The 2012-onward quarterly re-rating is a *rule*, not a
  tendency, which makes it a good archetype. But 12 of 18 train events are crisis beta, all
  three majors are 2008-09, and roughly half the events stack two causes in one window
  (2022-11-02 is about a third Fed policy). Attributing the full `move_pct` to the company
  event will produce ensembles that are systematically too wide.
- **JPM** (30 events, 23 train, 10 train majors). Carries the single most transferable analog
  family in the corpus (the policy-backstop pattern) and the two cleanest idiosyncratic test
  cases anywhere: **WaMu 2008-10-01** (the only unambiguously idiosyncratic positive event in
  the pre-2019 ledger) and the **London Whale 2012-05-17** (the only pure idiosyncratic
  negative, and the only event where the catalyst lands exactly on day 1 of the window).
  Everything else is 2008-09. Use the `significant` tier; the `major` tier is unusable as
  anything but a crisis analog.

**Tier 3 — weak seeds, keep for coverage not for retrieval**

- **GOOGL** (9 events, 7 train, effective independent sample ≈ 4). Two clean regimes and
  zero idiosyncratic downside in the entire history. Also has the worst window inflation:
  because its idiosyncratic events are overnight gaps, `move_pct` is systematically larger
  than the shock (2015-07-17 reads 25.8% but the event is 16.3%; 2013-10-18 reads 16.0% but
  the event is 13.8%). Anything calibrated on GOOGL is calibrated on gap-plus-drift.
- **BA** (29 events, 9 train, **0 train majors**). All four majors sit in one 12-week span in
  2020 (2020-03-17, 03-26, 04-02, 06-08) — a survival-repricing regime with no other instance
  in 60 years of price history. The train ledger is 8 GFC events plus the Aug 2011 US
  downgrade. Contributes almost nothing beyond "high-beta industrial in a systemic crisis."
- **AAPL** (13 events, 8 train, **0 majors at any point in the 2008-2026 range**). All 8
  train events fall inside a single 12-month GFC window. Will not contribute to the 25% stage
  narrative at all — exactly as CONTRACT.md §3 predicted.
- **XOM** (11 events, 3 train, all Oct-Nov 2008, **0 train majors**). Produces exactly one
  major event in 2008-2026 and zero before 2020. Empirically vindicates the two-tier design:
  without the 15% tier, XOM is not in the corpus at all.
- **MSFT** (7 events, 4 train, 3 of them the same eight weeks of 2008, **0 train majors**).
  The weakest seed in the universe. Recurring revenue does not gap; MSFT cleared 15% seven
  times and 25% once in the entire sample. **Must be pooled, never used standalone.** Its one
  genuine ticker-specific archetype — a cloud growth rate accelerating past a de-rated
  multiple, April 2015 and July 2026 — has exactly one in-sample instance.

---

## 7. Recommendation on universe composition

**For this build: do not swap any ticker.** The universe is frozen by CONTRACT.md §1, every
downstream number is computed against it, and swapping mid-build to improve the corpus would
be the same class of move as sliding `TRAIN_END`. Ship the ten and state the limitation.

**Five things to do instead, all inside the contract:**

1. **Carry an idiosyncratic-vs-beta flag on every event** and restrict analog retrieval by it.
   The `category` field already encodes it: `macro + crisis + sector-rotation + geopolitical`
   is the beta set, `earnings + guidance + product + leadership` is the idiosyncratic set.
   Without this, a query about an NVDA guidance shock retrieves the November 2008
   Thanksgiving rally and the October 2011 European bank recapitalisation — matching
   magnitude, not mechanism.
2. **Flag the nine structural (non-news) events** from §2 and exclude them from *news* analog
   retrieval. They remain valid price events for the volatility null.
3. **Recompute `famous`** from harvested article count before §8.2 scoring. See §3.2.
4. **Report `crps_lift` split by regime family** (beta vs idiosyncratic), not just pooled. A
   pooled lift number on this corpus is dominated by 2008-09 macro windows.
5. **Report effective sample size** alongside `n_tests`, accounting for the paired-window
   clustering in §5.

**For a v2 universe, the shape of the fix is specific.** The hole is not "more tickers" — it
is *company-specific, non-crisis, 15%-week events between 2010 and 2019*. The five tickers
that contribute nothing there (AAPL, XOM, MSFT, BA, and JPM outside the crisis) are all
mega-caps whose recurring revenue or index membership prevents idiosyncratic weekly gaps.
Replacing one or two of them with names that gap on their own news in the 2010s — a
subscriber-driven consumer-internet name, a binary-catalyst biotech, a mid-cap semiconductor
— is the direct fix. **We are not naming replacement tickers here on the strength of
recollection.** The correct procedure is to run `detect_events` over candidates and swap only
on measured train-period counts of `category ∈ {earnings, guidance, product}` outside 2008-09.
That is a one-hour job for LANE-EVENTS and it is the only honest way to pick.

**The cheaper v2 alternative is more history, not more tickers** — and the withdrawn
799-event build shows it works: extending detection back to 1962 adds 469 events, including
174 in the 2000-2002 dot-com bust, which is a *second* crisis regime and a large set of
genuinely idiosyncratic 1990s internet-era moves. It also adds 105 unverified `major` events
and re-opens the split-artifact question on decades of pre-2003 corporate actions. **That is a
real option with a real cost; it is a decision for the parent, not a lane, and nothing in
this synthesis or in any `<TICKER>.md` covers a single pre-2008 event.**

One thing v2 should keep either way: **the two-tier threshold is empirically vindicated.** At
25% alone, AAPL, BA, MSFT and XOM contribute zero train-period events and XOM contributes one
event in eighteen years. The 15% tier is what makes six of the ten tickers usable at all.

---

## 8. `data/event_context.json`

Machine-readable output for LANE-NEWS and LANE-MODEL. Keyed `"TICKER|YYYY-MM-DD"`. Every key
exists in `data/events.jsonl`; the 329 researched dates match the ledger's keys exactly in
both directions, so nothing is orphaned and nothing was invented.

```json
"JPM|2008-03-24": {
  "headline": "JPM buys Bear Stearns with a Fed backstop, raises the bid from $2 to $10",
  "cause": "On March 16, 2008 JPMorgan agreed to acquire Bear Stearns for $2 a share with a Federal Reserve backstop. On March 24 it raised the offer to $10 a share in stock...",
  "category": "crisis",
  "sources": ["https://money.cnn.com/2008/03/24/news/companies/bear/index.htm", "..."],
  "confidence": 0.9
}
```

**233 entries written. 96 dropped**, logged as required:

| Reason | Count | Breakdown |
|---|---:|---|
| Confidence below 0.5 | 50 | NVDA 30, TSLA 9, BA 4, AMZN 3, META 3, JPM 1 |
| Never researched (no attribution to keep) | 46 | TSLA 46 |

Of the 233 kept: **153 carry at least one source URL** (352 unique URLs), median confidence
0.85, 161 at ≥0.8. Coverage by tier: 65 of 68 `major` events and 168 of 261 `significant`.

**Provenance guarantee.** Every URL in the file was verified to appear verbatim in one of the
ten `docs/research/<TICKER>.md` files. **Zero URLs were constructed, inferred, or written from
memory** — this was checked programmatically, not by inspection. `cause` text is extracted
from the lane reports rather than composed here, so it inherits their sourcing and their
caveats.

**Known limitation of the field, stated plainly.** 80 of the 233 entries have a named cause
and no URL. These are overwhelmingly macro windows where the lane could name the crisis with
high confidence but could not isolate a citation for that specific five-day window; several
lanes hit HTTP 403/503 on `money.cnn.com` and `cnbc.com` archives, and two exhausted their
search budget. `confidence` is the field that carries this — treat anything below 0.8 without
a URL as provisional, and do not present it in the UI as verified. The volume-anchor table in
§2 is independent evidence that `confidence` is doing real work as that filter.
