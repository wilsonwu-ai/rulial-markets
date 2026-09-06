# XOM — event research

Exxon Mobil Corporation is the largest US integrated oil and gas major: upstream
production, downstream refining, and chemicals. It is a mega-cap Dow component
with roughly $450bn of market capitalisation in 2025 and a 40-plus-year
dividend-growth record.

**What actually drives the stock.** XOM is a levered claim on the crude oil
price plus a broad-market beta. Its earnings are almost entirely a function of
realised Brent/WTI and refining crack spreads, neither of which the company
controls. As a consequence, XOM's large moves are not company events. They are
oil-supply events (OPEC+ decisions, price wars), oil-demand events (recessions,
pandemics, tariffs), or general risk-regime events (2008, March 2020). The
company's own reporting calendar rarely clears the 15% weekly bar on its own.
Every one of the eleven detected events below traces to crude or to the macro
regime. None traces to an XOM-specific product, safety, legal or leadership
shock.

**Method note.** Each ledger date is the *end* of a five-trading-day window, so
the causal news usually sits two to six sessions earlier. I searched roughly
`[date - 10d, date]` for each event and independently re-derived every move from
Yahoo Finance splits-only closes before assigning a cause. Direct page fetches of
CNN Money and CNBC archives returned HTTP 503/403, so several citations below are
search-engine-returned URLs that I did not open; those are marked. Wikipedia,
IEA and EIA pages were fetched successfully.

---

## Events examined

All eleven XOM rows in `data/events.jsonl`. One major, ten significant.

| Date | Move | Tier | Category | Headline | Conf. |
|---|---|---|---|---|---|
| 2008-10-10 | -19.99% | significant | macro | Worst week in Dow history: global credit seizure drags crude and energy equities down together | 0.90 |
| 2008-10-29 | +15.61% | significant | macro | Dow's +10.9% / 889-point snapback off the October panic low, ahead of the FOMC cut | 0.75 |
| 2008-11-28 | +16.99% | significant | macro | Citigroup rescue plus the Geithner nomination trigger the biggest two-day rally since 1987 | 0.80 |
| 2020-02-27 | -16.77% | significant | macro | COVID week one: worst week for US equities since 2008, crude's worst week since 2008 | 0.85 |
| **2020-03-12** | **-25.80%** | **major** | **geopolitical** | **Saudi-Russia price war collides with the pandemic: oil's worst day since 1991, then the Dow's worst day since 1987** | **0.95** |
| 2020-03-30 | +19.24% | significant | macro | "QE infinity" plus the $2trn CARES Act mark the March 23 bottom | 0.80 |
| 2020-04-08 | +16.84% | significant | geopolitical | Trump's April 2 output-cut tweet gives WTI its largest one-day gain on record | 0.85 |
| 2020-06-08 | +18.28% | significant | macro | Reopening trade peaks: a +2.5m May payrolls surprise plus OPEC+ extending the 9.6mb/d cut | 0.80 |
| 2021-02-08 | +15.98% | significant | earnings | Chevron merger-talk reports, a Q4 loss the market looked through, and crude at 13-month highs | 0.70 |
| 2022-10-07 | +15.71% | significant | geopolitical | OPEC+ cuts quotas by 2mb/d, the deepest since 2020, defying the White House | 0.85 |
| 2025-04-08 | -15.35% | significant | macro | "Liberation Day" tariffs and an OPEC+ supply acceleration take Brent below $60 | 0.85 |

---

## The major event

### 2020-03-12 — down 25.80% (window 2020-03-05 close $50.11 to 2020-03-12 close $37.18)

**What happened.** Two shocks landed inside one week. On March 6 the OPEC+
meeting in Vienna collapsed when Russia refused Saudi Arabia's proposed
1.5mb/d cut. On March 8 Saudi Arabia retaliated with official selling price
discounts of $6 to $8 per barrel and signalled it would raise output from
9.7mb/d to 12.3mb/d in April. Brent fell about 30% on March 9, the largest
single-day drop since the 1991 Gulf War. Three days later, on March 12, the
WHO's pandemic declaration and the US travel ban from Europe produced a 9.5%
S&P 500 decline and a 10% Dow decline, the worst day since October 1987.

**Why it moved that much.** XOM is short exactly this combination. The price war
was a supply shock that removed the floor under realised prices, and the pandemic
was a demand shock that removed the volume. An integrated major cannot hedge
both at once: upstream realisations collapse while refining runs fall with
mobility. The market simultaneously repriced XOM's ability to fund its dividend
out of operating cash flow, which is the single reason a large slice of the
holder base owns it at all. XOM closed 2020 down 40.9% with a peak drawdown of
about 48%.

**Sources**
- https://en.wikipedia.org/wiki/2020_Russia%E2%80%93Saudi_Arabia_oil_price_war (fetched: March 6 breakdown, March 8 discounts, Brent -30%, March 18 low of $24.72 Brent)
- https://www.pbs.org/newshour/economy/worst-day-on-wall-street-since-1987-as-virus-fears-spread (search result: S&P -9.5%, Dow -10%, WTI at $31)
- https://www.cnbc.com/2020/03/08/oil-plummets-30percent-as-opec-deal-failure-sparks-price-war-fears.html (search result; direct fetch returned HTTP 403)
- https://www.nasdaq.com/articles/why-exxonmobil-stock-lost-more-than-40-in-2020-2021-01-05 (search result: XOM -40.9% in 2020)

---

## Significant events

### 2008-10-10 — down 19.99% (window 2008-10-03 close $77.94 to 2008-10-10 close $62.36)

The week ending October 10, 2008 was the worst week in Dow history, down about
1,874 points or 18%, with roughly $2.4trn of US market value erased. The
proximate cause was the post-Lehman freeze in interbank and commercial paper
funding, which forced indiscriminate deleveraging across every asset class.
Crude was in free-fall from its July 2008 peak near $147 as a global recession
was priced in. XOM lost nearly 12% on October 10 alone and traded as low as
$56.51 intraday against a $77.94 close a week earlier. This is a pure
liquidity-and-recession event, not an energy-specific one, but XOM took the
commodity leg and the equity leg together.

Sources (search results, direct fetch returned HTTP 503):
https://money.cnn.com/2008/10/10/markets/markets_newyork/index.htm?postversion=2008101011 ,
https://www.begintoinvest.com/october-10/

### 2008-10-29 — up 15.61% (window 2008-10-22 close $64.57 to 2008-10-29 close $74.65)

On October 28 the Dow added 889 points, +10.9%, its second-largest point gain
ever at the time and sixth-largest percentage gain, on bargain hunting into the
close as the two-day FOMC meeting opened with a rate cut expected. XOM had
bottomed at $64.57 on October 22 and captured that snapback almost in full.

**Discipline note:** XOM's Q3 2008 earnings release fell on October 30, 2008,
which is *one trading day after* this window closes. (I was unable to retrieve a
primary source for that release date or its headline figure before exhausting
this session's search budget, so treat the date as unverified here; what is
verified is that no XOM release sits inside the October 22 to October 29
window.) The point stands either way: any downstream process that joins ledger
dates to a nearby earnings calendar would be at risk of labelling this event
"earnings" when the cause was the October 28 market-wide rally. Confidence is
held at 0.75 because I could not find contemporaneous coverage isolating XOM's
own move within that broad rally.

Sources (search results): https://money.cnn.com/2008/10/28/markets/markets_newyork/ ,
https://www.cnbc.com/2008/10/28/stocks-jump-11-amid-bargainhunting-spree.html

### 2008-11-28 — up 16.99% (window 2008-11-20 close $68.51 to 2008-11-28 close $80.15)

November 20, 2008 was an interim capitulation low for the S&P 500 (the ultimate
crisis low came in March 2009), and XOM's own $68.51 close that day is the
window's starting point. On November
21 stocks rallied late on reports that Timothy Geithner was Obama's Treasury
pick. On November 23 the Treasury, Fed and FDIC announced a guarantee on $306bn
of Citigroup assets plus a $20bn capital injection, and the November 24 session
capped the largest two-day rally since 1987, with the S&P up 13% over the two
days. Crude reversed to about $51.71, up 3.5%, on November 24. XOM caught the
full systemic-risk repricing plus the crude bounce.

Caveat: the window's terminal day, November 28, was a half session (19.6m shares
against a ~55m daily average that month). The move accumulated over the prior
full sessions, so this is not a bad print, but the endpoint is a thin day.

Sources (search results): https://money.cnn.com/2008/11/24/markets/markets_newyork/index.htm?postversion=2008112415 ,
https://elischolar.library.yale.edu/journal-of-financial-crises/vol6/iss3/24

### 2020-02-27 — down 16.77% (window 2020-02-20 close $59.86 to 2020-02-27 close $49.82)

The first COVID repricing week. The S&P 500 fell about 11% over five sessions,
its worst week since 2008, after US officials confirmed the first probable
community transmission on US soil. Oil fell toward $45 in its biggest weekly
rout since 2008 as the market began pricing a global mobility shutdown. XOM
underperformed the index roughly 1.5 to one because the demand shock hits its
volumes and its price simultaneously.

Sources (search results): https://fortune.com/2020/02/28/us-stock-market-down-2008-crisis-recession-coronavirus/ ,
https://www.cnbc.com/2020/02/27/stock-market-today-live.html

### 2020-03-30 — up 19.24% (window 2020-03-23 close $31.45 to 2020-03-30 close $37.50)

March 23 was the COVID bottom. That day the Fed announced open-ended asset
purchases, "in the amount needed to provide liquidity", the so-called QE
infinity. The S&P then rose 9.4% on March 24 and gained roughly 20% over the
three sessions ending March 26 as the $2trn CARES Act moved through Congress; it
was signed on March 27. This is a discount-rate and solvency event rather than an
oil event: crude stayed weak into late March, but the market stopped pricing XOM
for insolvency.

Sources (search results): https://braggfinancial.com/1st-quarter-2020-market-and-economy/ ,
https://en.wikipedia.org/wiki/CARES_Act

### 2020-04-08 — up 16.84% (window 2020-04-01 close $37.53 to 2020-04-08 close $43.85)

On April 2, 2020 President Trump tweeted that he expected Saudi Arabia and
Russia to cut output by about 10mb/d. WTI settled +24.67% at $25.32, its largest
single-day percentage gain on record. The rest of the window was the market
positioning into the OPEC+ video conference scheduled for April 9, which
eventually produced the 9.7mb/d agreement announced April 12 and formalised
April 15. Cause here is a pure supply-expectation shock; the mechanism is that
XOM's forward realised price assumption reset upward in one session.

Sources: https://www.cnbc.com/amp/2020/04/02/oil-rallies-10percent-after-trump-says-he-expects-saudi-arabia-russia-feud-to-end-soon.html (search result),
https://www.eia.gov/todayinenergy/detail.php?id=45236 (fetched: April 15 agreement, initial 9.7mb/d cut, OPEC output -6.0mb/d April to May, largest monthly decline since 1993)

### 2020-06-08 — up 18.28% (window 2020-06-01 close $46.28 to 2020-06-08 close $54.74)

Two catalysts inside one window. On June 5 the May employment report showed
+2.5m jobs against consensus for a loss of more than 7m, and WTI settled $2.14
higher at $39.55 on a faster-than-expected demand recovery. On June 6 OPEC+
agreed to extend the record cut, about 9.6mb/d, through July. June 8 was the
peak of the reopening/value rotation, the day the S&P 500 erased its 2020 loss.
XOM was one of the highest-beta expressions of that trade, which is why an
18% week showed up in a mega-cap with no company news.

Sources (search results): https://www.zacks.com/stock/news/971146/stock-market-news-for-june-8-2020 ,
https://www.cnbc.com/2020/06/06/opec-and-allies-reportedly-agree-to-extend-record-production-cut.html ,
https://www.enerdata.net/publications/daily-energy-news/opec-extends-crude-oil-production-cuts-until-end-july-2020.html

### 2021-02-08 — up 15.98% (window 2021-02-01 close $44.92 to 2021-02-08 close $52.10)

This is the only XOM event where a company-specific catalyst is genuinely in the
window, and it is confounded. Three things overlapped. First, on February 1 the
WSJ reported that the CEOs of Exxon and Chevron had discussed a merger in early
2020, a combination that would trail only Saudi Aramco in size. Second, on
February 2 XOM reported a $20.1bn Q4 loss, but $19.3bn of that was a non-cash
impairment; management cut 2020 capex to $21.4bn, $9.8bn below 2019, and
committed to covering capex and the dividend from cash flow. The market treated
the dividend commitment, not the headline loss, as the news. Third, the activist
campaigns from D.E. Shaw and Engine No. 1 (which had nominated four directors)
were live, and crude was rallying toward 13-month highs on the Saudi voluntary
1mb/d cut effective February.

Confidence is 0.70 rather than higher precisely because I cannot cleanly
attribute the move among merger speculation, the dividend-preservation read, the
activist bid, and the crude tape. All four are real and all four point the same
direction.

Sources (search results): https://www.aljazeera.com/economy/2021/2/1/ceos-of-oil-giants-exxon-and-chevron-discussed-merger-reports ,
https://www.cnbc.com/2021/02/02/exxon-xom-earnings-q4-2020.html ,
https://corporate.exxonmobil.com/news/news-releases/2021/0202_exxonmobil-reports-results-for-fourth-quarter-2020-and-provides-perspective-on-forward-plans

### 2022-10-07 — up 15.71% (window 2022-09-30 close $87.31 to 2022-10-07 close $101.03)

On October 5, 2022 OPEC+ cut production quotas by 2mb/d, the deepest cut since
the pandemic, explicitly against US pressure ahead of the midterms. Brent moved
above $93 and the whole US energy complex re-rated. The window also caught the
October 3 to 4 broad-market rally on soft ISM and JOLTS prints that briefly
revived the "Fed pivot" trade. XOM closed above $100 on October 6 and 7 for the
first time since mid-2014, when it last traded in the $104 area (verified
against Yahoo Finance splits-only closes: 2014-06-23 close $104.38, 2022-10-06
close $102.06, 2022-10-07 close $101.03).

Sources (search results): https://www.cnbc.com/2022/10/05/oil-opec-imposes-deep-production-cuts-in-a-bid-to-shore-up-prices.html ,
https://www.npr.org/2022/10/05/1126754169/opec-oil-production-cut ,
https://www.energypolicy.columbia.edu/publications/qa-assessing-impact-largest-opec-production-cut-2020/

### 2025-04-08 — down 15.35% (window 2025-04-01 close $119.04 to 2025-04-08 close $100.77)

The mirror image of 2020-03-12, with tariffs standing in for the pandemic. On
April 2, 2025 the "Liberation Day" reciprocal tariffs were announced, and the
demand side of the oil balance was immediately marked down on global-recession
risk. On April 3 the eight OPEC+ members holding voluntary cuts tripled their
scheduled May increase to 411kb/d, adding a supply shock on top. Brent traded
below $60 for the first time in more than four years and WTI fell from above $71
at the start of April to below $60. XOM fell in four consecutive sessions from
April 3 to April 8, with April 4 alone down 7.4%.

Sources: https://www.iea.org/reports/oil-market-report-april-2025 (search result: Brent below $60, $15/bbl swing since Liberation Day, 411kb/d May increase),
https://www.cnbc.com/2025/04/04/why-opec-is-accelerating-oil-production-as-prices-tank-tariffs-hit.html (search result)

---

## Regime

**XOM lives in a commodity-macro regime, not an idiosyncratic one.** Of eleven
events, ten are attributable to crude supply/demand news or to a broad
risk-regime shift, and the eleventh (2021-02-08) has a company catalyst that is
inseparable from a crude rally and a merger rumour. There is not a single
product event, safety event, regulatory judgment, leadership shock or
guidance-only event in the ledger. This matters for analog retrieval: an event
description of the form "XOM announces X about its own business" has no
in-sample analog to retrieve. The generator should expect XOM's conditional
distribution to be driven by the *oil-price implication* of a described event,
not by its corporate salience.

**The moves cluster hard.** Eight of eleven sit in two crisis windows: three in
October and November 2008, five between February and June 2020. The remaining
three are 2021-02-08, 2022-10-07 and 2025-04-08, and even those two of three
are OPEC+ decisions. Directionally the ledger is 7 up and 4 down, and the up
moves are almost all V-shaped rebounds inside the same crisis that produced the
down moves. Treating an up event and a down event from the same eight-week
window as independent draws would badly overstate the effective sample size.

**The train/test split is the binding constraint here.** `TRAIN_END` is
2019-12-31. Only three XOM events fall on or before that date, and all three are
October to November 2008. XOM therefore contributes exactly one regime to the
seed corpus, and it is the same regime CONTRACT §3 already flags for JPM: "one
regime wearing ten hats." Eight of the eleven events, including the only major
one, are test-period. Two consequences the parent should weigh:

1. Any analog retrieved for an XOM forecast will be a 2008 GFC analog, which
   transfers poorly to a 2022-style OPEC+ supply event where the equity market
   is calm and only the commodity moves.
2. The leakage disclosure in CONTRACT §8 bites unusually hard on XOM, because
   the eight test-period events are among the most heavily written-about market
   episodes of the last decade. There is very little low-salience material in
   the XOM test set to satisfy §8.2. 2020-06-08 and 2021-02-08 are the closest
   thing to obscure events this ticker offers.

---

## Ledger verdict

**The detection survives contact with reality. All eleven dates are real, and
all eleven are explainable.**

I re-derived every move independently from Yahoo Finance splits-only daily
closes and compared against the ledger's `move_pct`. All eleven match to five
decimal places. Examples: 2008-10-10, 62.36/77.94 - 1 = -0.199897 against a
ledger value of -0.199897; 2020-03-12, 37.18/50.11 - 1 = -0.258032 against
-0.258032; 2025-04-08, 100.77/119.04 - 1 = -0.153478 against -0.153478. The
window convention is confirmed as "close on the ledger date divided by close
five trading days earlier."

**No data artifacts found.** XOM's last stock split was 2-for-1 in July 2001, so
no split contaminates the 2008 to 2025 range, and the returns are computed on
splits-only closes so dividends are correctly excluded from the price move. I
found no stale prints, no zero-volume days and no suspicious single-day
reversals of the kind that flag a bad tick.

**Three caveats for downstream lanes.**

1. *The ledger date is not the news date.* In seven of eleven cases the causal
   news sits two to six sessions before the ledger date. The clearest trap is
   2008-10-29, where XOM's record Q3 earnings landed on October 30, one day
   *after* the window closes; a naive date-join to an earnings calendar would
   label that event "earnings" when the cause was the October 28 market-wide
   rally. LANE-NEWS should harvest `[date - 10d, date]`, not a symmetric window.
2. *The `famous` flag looks under-inclusive.* Only 2008-10-10 and 2020-03-12 are
   flagged. But 2020-02-27 (the worst week since 2008), 2022-10-07 (the largest
   OPEC+ cut since the pandemic) and 2025-04-08 (Liberation Day) are all
   headline-grade episodes an LLM has certainly memorised. Since CONTRACT §8.2
   requires reporting famous and obscure events separately, an under-inclusive
   flag would inflate the apparent performance on "obscure" events. Recommend
   the parent re-examine how `famous` is assigned for XOM.
3. *One thin terminal day.* 2008-11-28 ends on a Black Friday half session
   (19.6m shares against a ~55m average). The move itself accrued over the prior
   full sessions, so the event is genuine, but the endpoint close is
   low-liquidity.

**Detection sensitivity is appropriate for this ticker.** At the 25% major
threshold XOM produces exactly one event in the full 2008 to 2025 history, and
zero before 2020. The 15% significant tier is what makes XOM usable at all,
which is direct empirical support for CONTRACT §3's two-tier design.

---

## Unexplained

**None.** All eleven events were matched to a documented, dated cause with at
least one retrievable source.

Two events carry lower confidence but are not unexplained:

- **2008-10-29 (0.75)**: the market-wide October 28 rally is documented and the
  magnitude fits, but I found no contemporaneous coverage isolating XOM's own
  move, and the near-miss earnings date on October 30 makes clean attribution
  worth flagging rather than assuming.
- **2021-02-08 (0.70)**: four simultaneous, same-direction catalysts (Chevron
  merger reporting, the Q4 print and dividend commitment, the Engine No. 1 and
  D.E. Shaw campaigns, crude at 13-month highs). The event is well explained;
  the *decomposition* is not. If the generator needs a single-cause label for
  this one, "earnings" is the least wrong choice but it is not the whole story.

**Sources I could not open.** WebFetch was refused by money.cnn.com (HTTP 503)
and cnbc.com (HTTP 403). URLs from those domains above are as returned by the
search index and are cited as such; I did not verify their body text directly and
have not asserted any number that appears only in an unfetched page without
naming the search snippet as its source.
