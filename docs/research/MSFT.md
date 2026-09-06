# MSFT — event research

**Ticker:** MSFT (Microsoft Corporation), mega-cap US software.
**Events in ledger:** 7 (1 major, 6 significant).
**Researched:** 7 of 7. **Unexplained:** 0.

## What this ticker is and what moves it

Microsoft is a ~$3-4T mega-cap whose revenue is dominated by recurring commercial
software and cloud infrastructure. That business mix is the single most important
fact for this ledger: recurring revenue does not gap, so MSFT does not produce
idiosyncratic weekly moves of the size that a single-product or single-drug company
does. Over the entire sample the stock cleared the 15% weekly bar only seven times,
and it cleared the 25% bar exactly once.

The consequence, which matters more than any individual event below, is that MSFT's
tail moves come from two and only two sources. Five of the seven are the stock riding
a market-wide crisis with roughly beta-1 exposure and no Microsoft-specific news at
all. The other two are the same trade twice: a cloud growth number that accelerated
past a de-rated expectation. There is no third archetype in this sample.

## Every event examined

| Date | Move | Tier | Category | Headline | Confidence |
|---|---|---|---|---|---|
| 2008-10-10 | -18.3% | significant | macro | Worst week in Dow history as the post-Lehman credit freeze peaked | 0.94 |
| 2008-11-20 | -17.5% | significant | macro | Capitulation to the 11-year S&P low as Citigroup looked like the next failure | 0.90 |
| 2008-11-28 | +15.3% | significant | macro | Bounce off the November low on the Citigroup rescue and the Fed's $800bn facilities | 0.90 |
| 2015-04-28 | +15.3% | significant | earnings | FQ3 2015 beat with commercial cloud up 106%, biggest one-day gain in six years | 0.93 |
| 2020-03-12 | -16.4% | significant | macro | COVID crash: worst day since 1987 the day after the WHO pandemic declaration | 0.95 |
| 2020-03-30 | +17.8% | significant | macro | Rebound off the 23 March bottom on unlimited Fed QE and the $2.2T CARES Act | 0.92 |
| **2026-08-03** | **+25.3%** | **major** | **earnings** | **FQ4 2026 blowout: Azure +43%, biggest one-day market-cap gain in history** | **0.97** |

Every move figure above was independently reproduced from split-adjusted daily
closes as `close[t] / close[t-5] - 1` (see Ledger verdict).

---

## 2026-08-03, +25.3%, major

**What happened.** Microsoft reported fiscal Q4 2026 after the close on Wednesday
29 July 2026. Revenue was $90.0bn, up 18% year over year, with GAAP diluted EPS of
$4.81, up 32%. Azure and other cloud services revenue grew 43%, Microsoft Cloud
revenue was $59.3bn (up 27%), Microsoft 365 Copilot passed 30 million paid seats,
and commercial remaining performance obligation rose 84% to $678bn. Azure crossed
$100bn of revenue for the first full fiscal year.
([Microsoft IR, FY26 Q4](https://www.microsoft.com/en-us/investor/earnings/fy-2026-q4/press-release-webcast))

**Why it moved.** The setup did as much work as the print. Microsoft went into the
quarter down roughly 30% from an October 2025 high of $555, because the market had
stopped believing that the AI capital expenditure would convert into revenue.
Azure at 43% beat the company's own 39-40% guide, and management then guided 45%
for the September quarter against a 41% consensus. An acceleration plus a raise is
the specific combination that forces a multiple re-rating rather than a one-day
earnings pop, because it invalidates the thesis (spending without return) rather
than just beating a number.
([Fortune](https://fortune.com/2026/07/30/microsoft-stock-biggest-one-day-gain-since-2008-480-billion-market-value-cloud-growth/),
[Bloomberg](https://www.bloomberg.com/news/articles/2026-07-29/microsoft-reports-quarterly-cloud-revenue-that-beat-estimates))

**Why the window is 25% and not 15%.** The move was not one gap. Thursday 30 July
closed +15.5% (390.54 to 451.10), the largest one-day market-value gain in stock
market history at roughly $450-480bn added, per
[Bloomberg](https://www.bloomberg.com/news/articles/2026-07-30/microsoft-eyes-history-with-490-billion-pop-in-market-value)
and [Fortune](https://fortune.com/2026/07/30/microsoft-stock-biggest-one-day-gain-since-2008-480-billion-market-value-cloud-growth/).
Friday added +3.0% and Monday 3 August added a further +4.9% to close at 487.65 on
sell-side price target revisions and a broad megacap-tech bid that also lifted META
(+6.2%) and GOOGL (+4.3%) that day
([TradingKey](https://www.tradingkey.com/news/market-movers/262070900-market-movers-msft-20260803)).
So the ledger date of 3 August is the tail of a three-day re-rating, not the day the
news landed. The causal date is 29 July.

**One discrepancy, left open.** Microsoft's own release states Q4 capital
expenditure of $35.8bn and $115.9bn for the fiscal year. Fortune's account cites
$41bn for the quarter, a guide above $50bn for the next, a $190bn 2026 spending
plan, and an accounting change extending data centre useful life from 15 to 25
years. These are probably different definitions (cash PP&E versus PP&E plus finance
leases, and fiscal versus calendar year) but I did not reconcile them, so I am
reporting both and asserting neither.

---

## 2020-03-30, +17.8%

**What happened.** The window runs from the closing low of 23 March 2020 (135.98)
to 30 March (160.23). On the morning of 23 March, before the US open, the Federal
Reserve announced open-ended purchases of Treasuries and agency MBS "in the amounts
needed to support the smooth functioning of markets," together with new corporate
credit and asset-backed facilities
([Federal Reserve](https://www.federalreserve.gov/newsevents/pressreleases/monetary20200323a.htm),
[CNBC](https://www.cnbc.com/2020/03/23/fed-announces-a-slew-of-new-programs-to-help-markets-including-open-ended-asset-purchases.html)).
The $2.2tn CARES Act was signed on 27 March ([CARES Act](https://en.wikipedia.org/wiki/CARES_Act)).

**Why it moved.** This is a liquidity event, not a Microsoft event. The March 2020
selloff was a forced-deleveraging and dash-for-cash episode in which even the
highest-quality balance sheets were sold. Removing the funding constraint removed
the reason to sell Microsoft, and the S&P posted its biggest weekly gain since March
2009 in that stretch. Microsoft had a genuine COVID tailwind (Teams and remote
work), but the timing is dictated by the Fed announcement, not by any company
disclosure, so I categorise this macro rather than product.

## 2020-03-12, -16.4%

**What happened.** The WHO declared COVID-19 a pandemic on 11 March 2020. On 12
March the Dow fell 10%, its worst day since October 1987, and the S&P fell 9.5%,
amid the suspension of most travel from Europe to the US and a cascade of global
shutdowns
([PBS NewsHour / AP](https://www.pbs.org/newshour/economy/worst-day-on-wall-street-since-1987-as-virus-fears-spread)).

**Why it moved.** Repricing of a genuinely unknown distribution. Microsoft fell
16.4% over the window against an S&P drawdown of similar magnitude, which is beta
exposure to a market-wide shock rather than anything about Microsoft's business.
Note the ledger's own evidence for this: MSFT fell here and rebounded 18 days later,
with no company news in between.

## 2008-11-28, +15.3%

**What happened.** The window runs from the 20 November closing low (17.53) to 28
November (20.22). On 23 November the US government announced a rescue of Citigroup
including an FDIC guarantee on more than $300bn of assets, and on 25 November the
government announced an $800bn programme to restart consumer and small-business
lending
([CNNMoney, 24 Nov 2008](https://money.cnn.com/2008/11/24/markets/markets_newyork/index.htm?postversion=2008112415),
[CNNMoney, 26 Nov 2008](https://money.cnn.com/2008/11/26/markets/markets_newyork/)).
The two-session gain of 891 Dow points was the largest two-session point gain on
record at the time and the largest two-session percentage gain since October 1987.

**Why it moved.** Same mechanism as March 2020, twenty years earlier: the marginal
seller in a solvency panic is not selling Microsoft on a view about Microsoft, so a
credible backstop for the banking system produces a violent mechanical bounce in
everything. Note the 28 November session itself was a half day (28.6m shares against
80-150m on surrounding days), so the window closed on a thin tape.

## 2008-11-20, -17.5%

**What happened.** The S&P 500 closed at 752.44 on 20 November 2008, its lowest
close since 1997, down 6.7% on the day, with Citigroup down 26% and the cost of
insuring against corporate default at an all-time high, as an auto-industry rescue
vote was postponed
([TradingEconomics, 20 Nov 2008](https://tradingeconomics.com/articles/11202008132217.htm)).

**Why it moved.** Systemic solvency fear at its maximum. Microsoft was collateral,
not cause.

**Explicit non-driver.** There is real Microsoft-specific news in this window:
Jerry Yang announced his resignation as Yahoo CEO on 18 November, and on 20
November Microsoft said it would not buy Yahoo but might still do a search
partnership
([The Register](https://www.theregister.com/2008/11/18/yang_resigns/),
[IT Pro timeline](https://www.itpro.com/609714/timeline-the-saga-of-microsoft-and-yahoo)).
I do not believe this drove a 17.5% weekly move in a company Microsoft had already
walked away from in May 2008, and the whole market fell in lockstep. Recording it
here so a later reader does not rediscover it and mistake coincidence for cause.

## 2008-10-10, -18.3%

**What happened.** From 6 to 10 October 2008 the Dow closed lower in all five
sessions, falling more than 1,874 points or 18%, the worst weekly decline in its
history on both a point and a percentage basis, with the S&P down more than 20%.
The mechanism was a total lock-up of short-term credit markets after Lehman's
failure ([CNNMoney](https://money.cnn.com/2008/10/31/markets/october_stocks_tough_month/index.htm),
[Benzinga](https://www.benzinga.com/general/education/21/10/23355953/this-day-in-market-history-dow-rebounds-11-following-worst-week-ever-in-2008)).

**Why it moved.** Microsoft's -18.3% is almost exactly the market's move. This is
the cleanest possible beta observation in the ledger and carries essentially no
Microsoft-specific information.

## 2015-04-28, +15.3%

**What happened.** Microsoft reported fiscal Q3 2015 after the close on 23 April
2015: revenue $21.7bn (up 6%), diluted EPS $0.61, and commercial cloud revenue up
106% to a $6.3bn annualised run rate, offset by Windows OEM revenue down 19% (Pro)
and 26% (non-Pro)
([Microsoft IR, FY15 Q3](https://www.microsoft.com/en-us/investor/earnings/fy-2015-q3/press-release-webcast)).
The stock gapped from 43.34 to 47.87 on 24 April, +10.45% on 131m shares against
roughly 46m the prior day, then added a further +0.3% and +2.4% over the next two
sessions to close the window at 49.16.

**Why it moved.** Structurally identical to July 2026. Microsoft was being valued as
a declining Windows franchise, and the print showed the cloud transition compounding
fast enough to more than offset a collapsing OEM business. The market was repricing
the terminal story, which is why one 6%-revenue-growth quarter produced a
double-digit gap. I have the primary earnings document and the price tape; I did not
find a contemporaneous 2015 news article, so the +2.4% on 28 April specifically is
attributed to momentum and follow-through rather than to a named second catalyst.

---

## Regime

**MSFT lives in two regimes, and they are cleanly separable.**

*Regime 1, market beta in a liquidity or solvency crisis (5 of 7 events, 71%).*
October 2008, November 2008 down, November 2008 up, March 2020 down, March 2020 up.
In every one of these the driver is a market-wide event with no Microsoft content,
and Microsoft's move is close to the index move. These events come in
down-then-up pairs separated by days or weeks, because the same mechanism (forced
selling, then a policy backstop) generates both signs.

*Regime 2, a cloud-growth re-rating off a de-rated multiple (2 of 7, 29%).*
April 2015 and July 2026. Both are up. Both follow a period in which the market had
marked Microsoft down on a structural bear thesis (Windows decline in 2015, AI
capex without return in 2026). Both are resolved by a growth rate that accelerated
past the company's own guide. This is a genuine, repeating, ticker-specific
archetype and it is the most useful thing in this file for analog retrieval.

**Three consequences for the generator, in order of importance.**

1. **The trainable corpus is four events, and three of them are the same eight
   weeks of 2008.** With `TRAIN_END = 2019-12-31`, MSFT contributes 2008-10-10,
   2008-11-20, 2008-11-28 and 2015-04-28. That is one crisis cluster plus one
   earnings event. MSFT is a weak seed ticker on its own and should be pooled;
   its 2020 and 2026 events are test-side only.

2. **There is no in-sample precedent for a Microsoft-specific 15% down week.**
   Every down event here is beta. If a user asks the model to condition on
   something like "MSFT announces an Azure revenue miss," the retrieval layer has
   no analog for it in this ticker and will pull crisis-beta analogs, which have
   the wrong shape (fast, market-wide, mean-reverting within weeks) for an
   idiosyncratic fundamental disappointment. This asymmetry should be surfaced in
   the UI, not silently papered over.

3. **The ledger date lags the causal date by one to three sessions on the
   earnings events.** For 2026-08-03 the news was 29 July, and for 2015-04-28 it
   was 23 April. Anything that uses the ledger date as `as_of_date` will be
   conditioning on information the market already had for several days. The
   crisis events do not have this problem, because they are continuous repricings
   rather than a point release.

---

## Ledger verdict

**The ledger survives contact with reality. All seven dates are real, all seven are
arithmetically exact, and none is a data artifact.**

*Arithmetic.* I independently recomputed every move from yfinance split-adjusted
daily closes as `close[t] / close[t-5] - 1` and reproduced all seven to five decimal
places:

| Date | close[t-5] | close[t] | recomputed | ledger |
|---|---|---|---|---|
| 2008-10-10 | 26.32 (10-03) | 21.50 | -0.18313 | -0.183131 |
| 2008-11-20 | 21.25 (11-13) | 17.53 | -0.17506 | -0.175059 |
| 2008-11-28 | 17.53 (11-20) | 20.22 | +0.15345 | +0.153451 |
| 2015-04-28 | 42.64 (04-21) | 49.16 | +0.15291 | +0.152908 |
| 2020-03-12 | 166.27 (03-05) | 139.06 | -0.16365 | -0.163650 |
| 2020-03-30 | 135.98 (03-23) | 160.23 | +0.17834 | +0.178335 |
| 2026-08-03 | 389.10 (07-27) | 487.65 | +0.25327 | +0.253277 |

*No split contamination.* Microsoft's most recent split was February 2003, before
the earliest event here, so none of these dates can be an unadjusted-split artifact.
The 2015 and 2026 gaps are corroborated by volume spikes (131m shares on 2015-04-24
against a ~46m baseline; 110m on 2026-07-30 against a ~28m baseline), which is what
a real news gap looks like and is not what a bad price print looks like.

*Two structural notes for the parent, neither of which is an error.*

**(a) 2008-11-20 and 2008-11-28 are not independent draws.** They are adjacent
non-overlapping windows that share the 20 November close as one window's endpoint
and the next window's start. Non-maximum suppression correctly did not merge them,
but they are the capitulation and the bounce off the same low, driven by the same
episode. Treating them as two observations overstates the effective sample size of
the 2008 cluster. If the corpus is small, consider flagging paired reversal windows.

**(b) The `famous` flag looks miscalibrated and this one does matter.** In the
current ledger, `famous=true` on 2020-03-12 and 2026-08-03, and `famous=false` on
2008-10-10, 2008-11-20, 2008-11-28 and 2020-03-30. The week of 6-10 October 2008 is
the worst week in Dow history and 2020-03-30 is the rebound off the most-discussed
market bottom of the last decade. Both are about as famous as a market event gets.
Since CONTRACT section 8.2 uses the famous/obscure split to separate memorisation
from forecasting, a flag that marks the 2008 crash as obscure will make the model's
"obscure event" performance look better than it is. Recommend the flag be derived
from something auditable (article count in the harvested corpus, say) rather than
assigned.

---

## Unexplained

**None.** All seven events have a named, sourced cause.

Two honest qualifications rather than unexplained entries:

- **2015-04-28, residual +2.4% on the final session.** The 23 April earnings report
  explains the 10.45% gap on 24 April and I have the primary document for it. I did
  not find a contemporaneous source naming a catalyst for the 28 April session
  specifically, and I am attributing it to follow-through. Microsoft's Build
  conference opened 29 April 2015, one day after the window closed, which is a
  plausible but unverified contributor and should not be treated as established.
- **2026-08-03, capex figures conflict between primary and secondary sources.**
  Documented in that section above. The direction of the event is not in doubt; the
  capex number is.

## Source verification note

Links fetched and read in full: the two Microsoft investor relations press release
pages (FY15 Q3, FY26 Q4), the Fortune 30 July 2026 article, and the TradingKey
3 August 2026 market-movers page. The remaining links were returned by web search
with the quoted content in the result snippet, and are cited at that level of
confidence rather than as full reads. The CNBC FY26 Q4 article returned HTTP 403
and could not be read directly. Price data throughout is yfinance daily
split-adjusted closes, retrieved 2026-09-06.
