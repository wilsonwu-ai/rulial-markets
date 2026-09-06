# AAPL — event research

Apple Inc. (NASDAQ: AAPL). Consumer hardware with an attached services annuity: iPhone
is the earnings engine, China is the manufacturing base and a material end market, and
the shareholder base is the widest of any US listed equity. Two consequences matter for
this ledger. First, AAPL is a mega-cap index constituent, so at the 15% weekly threshold
its "events" are usually the market's events transmitted through a high-beta name rather
than anything Apple did. Second, the genuinely idiosyncratic shocks it does produce are
almost entirely **guidance** shocks, not revenue misses: the January quarter guide and
the China supply chain are where Apple surprises people.

**Ledger scope.** 13 events, **all tier `significant`**, **zero tier `major`**. The single
largest window in 45 years of price history is `-22.7%` (April 2025 tariffs), which never
clears the 25% bar. This is exactly the outcome CONTRACT.md §3 predicted for AAPL.

**Verification method.** Every window below was re-derived from `data/prices/AAPL.csv`
before any news was searched. For each ledger date I recomputed the 5-trading-day
close-to-close return and identified the single largest contributing day inside the
window, then searched news for that day rather than for the ledger date. All 13 windows
reproduce the recorded `move_pct` to four decimal places.

---

## Events examined

| Date | Move | Tier | Driver day inside window | Category | Headline | Conf. |
|---|---|---|---|---|---|---|
| 2008-01-28 | -19.4% | significant | 01-23 (-10.7%) | guidance | Apple guides FY08 Q2 far below consensus into a recession scare | 0.92 |
| 2008-09-17 | -15.7% | significant | 09-17 (-8.6%) | macro | Lehman fails, AIG is nationalised, the whole tape gaps down | 0.85 |
| 2008-10-03 | -24.3% | significant | 09-29 (-17.9%) | macro | House rejects TARP, Dow loses 777 points, RBC and Morgan Stanley cut AAPL | 0.93 |
| 2008-10-14 | +16.7% | significant | 10-13 (+13.9%) | macro | Coordinated European bank recapitalisations spark the Dow's biggest point gain ever | 0.90 |
| 2008-11-03 | +16.1% | significant | 10-28 (+8.5%) | macro | Dow's second-biggest point gain on record ahead of the October FOMC cut | 0.85 |
| 2008-11-20 | -16.5% | significant | 11-20 (-6.7%) | macro | S&P 500 closes at 752, the bear market low, on an auto-bailout stall | 0.88 |
| 2008-11-28 | +15.1% | significant | 11-24 (+12.6%) | macro | Citigroup rescue plus Obama's economic team plus Fed MBS buying: best 5 days since 1933 | 0.90 |
| 2009-01-27 | +16.0% | significant | 01-22 (+6.7%) | earnings | Apple's first $10bn quarter beats a market braced for a Jobs-less disaster | 0.88 |
| 2020-03-12 | -15.3% | significant | 03-12 (-9.9%) | macro | COVID: oil price war, WHO pandemic declaration, Europe travel ban, worst day since 1987 | 0.93 |
| 2020-03-20 | -17.5% | significant | 03-16 (-12.9%) | macro | COVID leg two: worst week since October 2008 into a record quad-witching | 0.92 |
| 2020-08-06 | +18.4% | significant | 07-31 (+10.5%) | earnings | Record June quarter plus a surprise 4-for-1 stock split | 0.94 |
| 2025-04-08 | -22.7% | significant | 04-03 (-9.3%) | geopolitical | "Liberation Day" reciprocal tariffs hit the most China-exposed mega-cap | 0.95 |
| 2025-04-15 | +17.2% | significant | 04-09 (+15.3%) | geopolitical | 90-day tariff pause, then a CBP carve-out for smartphones and computers | 0.93 |

No event in this ledger is unexplained.

---

## Event detail

### 2008-01-28, -19.4% (guidance)

Window 2008-01-18 to 2008-01-28. Apple reported FY08 Q1 after the close on 22 January.
Profit rose 57% and still the stock collapsed, because the guide was the story: management
forecast Q2 EPS of $0.94 against a $1.09 consensus and revenue near $6.8bn against $6.99bn
([NBC News](https://www.nbcnews.com/id/wbna22789176)). AAPL fell 10.65% on 23 January and
kept bleeding, another 2.50% and 4.12% on the two following sessions. The mechanism is not
"a miss" but a **regime reclassification**: the guide was read as evidence that even Apple
was not insulated from a US consumer recession, and the multiple, not the estimates, did
the falling. The window also carries a macro leg, with 22 January down 3.54% alongside the
global sell-off that produced the Fed's emergency intermeeting cut.

Sources: [NBC News, "Apple shares plunge despite good earnings"](https://www.nbcnews.com/id/wbna22789176) ·
[Fox News / AP, "Apple profit nearly doubles but forecast well below expectations"](https://www.foxnews.com/story/apple-profit-nearly-doubles-but-forecast-well-below-expectations.print)

### 2008-09-17, -15.7% (macro)

Window 2008-09-10 to 2008-09-17. Nothing Apple did. Lehman Brothers filed the largest
Chapter 11 in US history on 15 September, the Fed took a 79.9% equity stake in AIG for an
$85bn loan on 16 September, and the S&P 500 still fell 4.71% on 17 September as the rescue
failed to stop the run on the remaining broker-dealers
([Benzinga](https://benzinga.com/general/education/21/09/22971375/this-day-in-market-history-85b-aig-bailout)).
AAPL's own worst day was the 17th, at -8.6%, roughly twice the index. This is pure
high-beta transmission: money-market and dealer funding stress forced indiscriminate
de-risking, and Apple was a crowded, liquid, easy thing to sell.

Sources: [Begin To Invest, "September 15th: Lehman Bankrupt, AIG Failing"](https://www.begintoinvest.com/september-15/) ·
[Benzinga, "$85B AIG Bailout"](https://benzinga.com/general/education/21/09/22971375/this-day-in-market-history-85b-aig-bailout) ·
[PBS NewsHour, 17 Sept 2008](https://www.pbs.org/newshour/economy/business-july-dec08-aig_09-17)

### 2008-10-03, -24.3% (macro): the largest down window before 2025

Window 2008-09-26 to 2008-10-03, and it is dominated by a single day: **29 September 2008,
AAPL -17.92%**, the worst single session in the stock's history. Two forces landed together.
RBC and Morgan Stanley both cut Apple to neutral that morning, with RBC's Mike Abramsky
citing a survey in which 40% of consumers said they planned to spend less on electronics
over the next 90 days, the weakest reading the survey had ever produced
([Fortune](https://fortune.com/2008/09/29/apple-bruised-in-downgrades)). Hours later the
House voted down the TARP bailout and the Dow lost 777.68 points, its worst point loss then
on record ([CNN Money](https://money.cnn.com/2008/09/29/markets/markets_newyork/)). The
downgrade supplied the idiosyncratic reason to sell and the failed vote supplied the
liquidity vacuum to sell into.

A footnote that matters for anyone using this window as a training example: on 3 October,
the ledger date itself, a false CNN iReport post claimed Steve Jobs had suffered a heart
attack and AAPL fell 10% in ten minutes before recovering to close down 3%. The SEC opened
an investigation ([CNN Money](https://money.cnn.com/2008/10/03/technology/apple/),
[The Register](https://www.theregister.com/2008/10/24/sec_jobs_heart_attack_probe/)). It is
a real, verifiable event on the exact ledger date, and it is **not** the cause of the window.
Treating it as the cause would be a textbook date-alignment error.

Sources: [Fortune, "Apple bruised in downgrades"](https://fortune.com/2008/09/29/apple-bruised-in-downgrades) ·
[Fortune, "Why Apple shares took a nosedive"](https://fortune.com/2008/09/29/why-apple-shares-took-a-nosedive) ·
[CNN Money market report, 29 Sept 2008](https://money.cnn.com/2008/09/29/markets/markets_newyork/) ·
[CNN Money, "Steve Jobs rumor causes brief fall in Apple stock"](https://money.cnn.com/2008/10/03/technology/apple/) ·
[The Register, SEC probe](https://www.theregister.com/2008/10/24/sec_jobs_heart_attack_probe/)

### 2008-10-14, +16.7% (macro)

Window 2008-10-07 to 2008-10-14, driven by 13 October (AAPL +13.9%). Over that weekend the
UK committed £37bn to recapitalise RBS, HBOS and Lloyds TSB, France pledged up to €360bn of
refinancing guarantees and capital, Germany put up €400bn of guarantees plus €100bn of state
capital, and Paulson signalled the US would use TARP to buy bank equity directly rather than
assets ([Al Jazeera](https://www.aljazeera.com/news/2008/10/13/markets-surge-on-rescue-pledges),
[Forbes](https://www.forbes.com/2008/10/13/europe-bailouts-update-markets-econ-cx_ll_po_1013markets14.html)).
The Dow rose 936.42 points, or 11.08%, still the largest one-day point gain in its history.
Apple happened to hold its "spotlight turns to notebooks" event on 14 October, launching the
unibody MacBook and MacBook Pro ([MacRumors](https://www.macrumors.com/2008/10/14/apple-october-2008-notebook-media-event-coverage/)),
but AAPL fell 5.6% that day. **The product launch is coincident, not causal**, and this is
the second date-alignment trap in the ledger.

Sources: [Al Jazeera, "Markets surge on rescue pledges"](https://www.aljazeera.com/news/2008/10/13/markets-surge-on-rescue-pledges) ·
[Forbes, "It's Raining Bailouts In Europe"](https://www.forbes.com/2008/10/13/europe-bailouts-update-markets-econ-cx_ll_po_1013markets14.html) ·
[MacRumors, Apple October 2008 notebook event](https://www.macrumors.com/2008/10/14/apple-october-2008-notebook-media-event-coverage/)

### 2008-11-03, +16.1% (macro)

Window 2008-10-27 to 2008-11-03, driven by 28 October (AAPL +8.5%). The Dow added 889 points
that day, its second-biggest point gain ever at the time and its sixth-biggest percentage
gain at 10.9%, as Asian markets rebounded overnight and buyers stepped into the cheapest
valuations in two decades ahead of the FOMC's second cut of the month
([CNN Money](https://money.cnn.com/2008/10/28/markets/markets_newyork/index.htm)). Apple's
FY08 Q4 report had come and gone on 21 October, outside this window, so the move is a
short-covering and valuation bounce rather than a company event.

Source: [CNN Money market report, 28 Oct 2008](https://money.cnn.com/2008/10/28/markets/markets_newyork/index.htm)

### 2008-11-20, -16.5% (macro)

Window 2008-11-13 to 2008-11-20. This window ends on the exact closing low of the bear
market: the S&P 500 settled at 752.44, its weakest level since 1997, after weak economic
data, another shift in Treasury's approach to the banks, and a postponed Congressional vote
on the auto rescue. Citigroup fell 26% that session and corporate default insurance costs
hit an all-time high ([Trading Economics](https://tradingeconomics.com/articles/11202008132217.htm),
[Wikipedia, US bear market of 2007-2009](https://en.wikipedia.org/wiki/United_States_bear_market_of_2007%E2%80%932009)).
Apple's decline was steady rather than event-driven, with its worst day only -6.7%, which is
the signature of forced liquidation rather than news.

Sources: [Trading Economics, "S&P at the Lowest Level Since 1997"](https://tradingeconomics.com/articles/11202008132217.htm) ·
[Wikipedia, United States bear market of 2007-2009](https://en.wikipedia.org/wiki/United_States_bear_market_of_2007%E2%80%932009)

### 2008-11-28, +15.1% (macro)

Window 2008-11-20 to 2008-11-28, starting from the exact bear-market low and driven by
24 November (AAPL +12.6%). On 23 November the Treasury, Fed and FDIC announced the Citigroup
package: a $20bn preferred capital injection plus an asset guarantee covering roughly $306bn
of assets ([CNN Money](https://money.cnn.com/2008/11/24/news/companies/citigroup_reaction/)).
Obama named his economic team the same week and the Fed committed to large-scale
mortgage-backed securities purchases on 25 November. The S&P 500 gained 19.1% over the five
sessions, its largest five-day percentage gain since March 1933
([NBC News](https://www.nbcnews.com/id/wbna27996123)). Note that this window and the previous
one **share the 2008-11-20 close as an endpoint**, so the two are mechanically anti-correlated
rather than independent draws.

Sources: [CNN Money, "Sizing up the Citigroup rescue"](https://money.cnn.com/2008/11/24/news/companies/citigroup_reaction/) ·
[NBC News, "Dow ends up, extending gains into fifth day"](https://www.nbcnews.com/id/wbna27996123)

### 2009-01-27, +16.0% (earnings)

Window 2009-01-20 to 2009-01-27, driven by 22 January (AAPL +6.7%), the first session after
the FY09 Q1 print. Apple reported record revenue of $10.17bn and record net profit of $1.61bn,
or $1.78 per diluted share, its first quarter above $10bn
([Apple Newsroom](https://www.apple.com/newsroom/2009/01/21Apple-Reports-First-Quarter-Results/),
[SEC 8-K exhibit](https://www.sec.gov/Archives/edgar/data/0000320193/000119312509009009/dex991.htm)).
Shares rose about 9% after hours ([CNN Money](https://money.cnn.com/2009/01/21/technology/Apple_earns/index.htm)).
The mechanism is expectations, not absolute numbers: Steve Jobs had announced a medical leave
of absence on 14 January and the market had marked Apple down for both a recession and a
leadership vacuum, so an in-line-to-strong quarter delivered by Tim Cook repriced the
governance discount as much as the earnings.

Sources: [Apple Newsroom, "Apple Reports First Quarter Results"](https://www.apple.com/newsroom/2009/01/21Apple-Reports-First-Quarter-Results/) ·
[SEC EDGAR, Apple 8-K exhibit 99.1](https://www.sec.gov/Archives/edgar/data/0000320193/000119312509009009/dex991.htm) ·
[CNN Money, "Apple trounces Wall Street estimates"](https://money.cnn.com/2009/01/21/technology/Apple_earns/index.htm) ·
[MacRumors, record Q1 2009 profit](https://www.macrumors.com/2009/01/21/apple-reports-1-61-billion-profit-for-q1-2009/)

### 2020-03-12, -15.3% (macro)

Window 2020-03-05 to 2020-03-12, with two crash days inside it: 9 March (-7.9%) and
12 March (-9.9%). On 8 March the OPEC-Russia talks collapsed and Saudi Arabia launched a
production war, sending crude to its worst day since 1991 and tripping the S&P 500's
circuit breaker on the 9th ([CNBC](https://www.cnbc.com/2020/03/08/opec-deal-collapse-sparks-price-war-20-oil-in-2020-is-coming.html)).
The WHO declared a pandemic on 11 March and the US suspended most travel from Europe. On
12 March all three US indices fell more than 9%, the worst session since Black Monday 1987,
because the Fed's bond-buying response was judged insufficient against a demand shock it
could not treat ([TIME](https://time.com/5802039/us-stocks-plummet-coronavirus/),
[Washington Post](https://www.washingtonpost.com/us-policy/2020/03/12/markets-stocks-today-coronavirus/)).
Apple carried an extra China-specific leg, having already withdrawn March-quarter guidance
on 17 February over Foxconn shutdowns.

Sources: [CNBC, oil price war](https://www.cnbc.com/2020/03/08/opec-deal-collapse-sparks-price-war-20-oil-in-2020-is-coming.html) ·
[TIME, "US Stocks Plummet in Worst Day Since 1987's Black Monday"](https://time.com/5802039/us-stocks-plummet-coronavirus/) ·
[Washington Post, 12 March 2020](https://www.washingtonpost.com/us-policy/2020/03/12/markets-stocks-today-coronavirus/)

### 2020-03-20, -17.5% (macro)

Window 2020-03-13 to 2020-03-20, driven by 16 March (AAPL -12.9%), the session after the
Fed's emergency Sunday cut to zero and $700bn QE restart, which the market read as
confirmation of how bad things were rather than as support. The week was the worst for all
three indices since October 2008, the S&P 500 fell 15%, VIX broke above its 2008 high, and
the week closed into one of the largest quadruple-witching expirations on record, which
mechanically amplified the move ([CNBC](https://www.cnbc.com/2020/03/20/stock-market-live-today.html),
[Newsquawk](https://www.newsquawk.com/headlines/newsquawk-us-market-wrap-20th-march-2020-largest-weekly-stock-decline-since-08-as-global-economy-falls-off-a-cliff-edge-20-03-2020)).
Note this window **overlaps** 2020-03-12's by one day and shares the same regime; the two
are close to a single 12-session event that non-maximum suppression split in half.

Sources: [CNBC, "Dow down 900, worst week in 11 years"](https://www.cnbc.com/2020/03/20/stock-market-live-today.html) ·
[CNN Business, "Stocks log worst week since 2008"](https://www.cnn.com/business/live-news/stock-market-news-today-032020) ·
[Newsquawk US market wrap, 20 March 2020](https://www.newsquawk.com/headlines/newsquawk-us-market-wrap-20th-march-2020-largest-weekly-stock-decline-since-08-as-global-economy-falls-off-a-cliff-edge-20-03-2020)

### 2020-08-06, +18.4% (earnings): the cleanest company-specific event in the ledger

Window 2020-07-30 to 2020-08-06, driven by 31 July (AAPL +10.5%). On 30 July after the close
Apple reported June-quarter revenue of $59.7bn, up 11%, and diluted EPS of $2.58, up 18%,
against a market that had expected COVID to gut hardware demand, and simultaneously announced
a **4-for-1 stock split** with an 24 August record date and 31 August split-adjusted trading
([Apple 8-K exhibit 99.1, SEC](https://www.sec.gov/Archives/edgar/data/320193/000032019320000060/a8-kexhibit991q3202062.htm),
[CNBC](https://www.cnbc.com/2020/07/30/apple-stock-split-announced.html)). Shares rose $40.28
to $425.04 the next day ([9to5Mac](https://9to5mac.com/2020/07/30/apple-announces-4-to-1-stock-split-as-shares-cross-400-following-record-q3-earnings/)).
The mechanism has two parts: a fundamental repricing of stay-at-home hardware demand, and a
flow effect, since the split made AAPL eligible for a larger Dow weight and accessible to
retail and options buyers at a lower notional. The rally continued for the following week,
which is why the detected window ends on 6 August rather than 31 July.

Sources: [SEC EDGAR, Apple FY20 Q3 press release](https://www.sec.gov/Archives/edgar/data/320193/000032019320000060/a8-kexhibit991q3202062.htm) ·
[CNBC, "Apple announces 4-for-1 stock split"](https://www.cnbc.com/2020/07/30/apple-stock-split-announced.html) ·
[9to5Mac](https://9to5mac.com/2020/07/30/apple-announces-4-to-1-stock-split-as-shares-cross-400-following-record-q3-earnings/) ·
[Forbes](https://www.forbes.com/sites/lcarrel/2020/07/31/apple-announces-4-for-1-stock-split-to-bring-in-new-investors/)

### 2025-04-08, -22.7% (geopolitical): the largest window in AAPL history

Window 2025-04-01 to 2025-04-08, four consecutive down days of -9.25%, -7.29%, -3.67% and
-4.98%. On 2 April, after the close, the administration announced "reciprocal" tariffs
including a 54% rate on China. Apple is the most exposed mega-cap to that policy because
roughly 85% of iPhones are assembled in China and its alternative sites, Vietnam and India,
were themselves tariffed ([Fortune](https://fortune.com/2025/04/08/apple-stock-selloff-trump-tariffs-economy-tech-markets-china-vietnam-india/)).
China announced matching tariffs on 4 April ([MacRumors](https://www.macrumors.com/2025/04/04/apple-shares-plunge-china-unveils-tariffs/)).
Apple lost roughly $638bn of market capitalisation in three sessions and fell below $3trn
([CNBC](https://www.cnbc.com/2025/04/07/apples-3-day-loss-in-market-cap-swells-to-almost-640-billion.html)).
The mechanism is a gross-margin shock with no near-term mitigation: Apple could not reprice
iPhones into a soft consumer, could not re-shore assembly inside a quarter, and had no way to
quantify the hit, so the market repriced the entire margin structure rather than one quarter.

Sources: [Fortune, "Apple's historic selloff has bulls balking from tariff risks"](https://fortune.com/2025/04/08/apple-stock-selloff-trump-tariffs-economy-tech-markets-china-vietnam-india/) ·
[CNBC, "Apple's 3-day loss in market cap swells to almost $640 billion"](https://www.cnbc.com/2025/04/07/apples-3-day-loss-in-market-cap-swells-to-almost-640-billion.html) ·
[MacRumors, China matching tariffs](https://www.macrumors.com/2025/04/04/apple-shares-plunge-china-unveils-tariffs/) ·
[AppleInsider, third consecutive down day](https://appleinsider.com/articles/25/04/07/apple-stock-hammered-for-third-consecutive-market-day-falls-on-news-of-more-tariffs)

### 2025-04-15, +17.2% (geopolitical)

Window 2025-04-08 to 2025-04-15. This is the mirror image of the event above and it is the
sharpest illustration of the ledger's window-end labelling: **the terminal day itself moved
-0.19%**. The window is carried by 9 April, when a 90-day pause on reciprocal tariffs for
countries other than China sent AAPL up 15.33% to close at $198.85, at one point its best day
since 1998 ([CNBC](https://www.cnbc.com/2025/04/09/stock-market-today-live-updates.html)), then
by 11 and 14 April (+4.06%, +2.21%) after US Customs and Border Protection issued guidance on
11 April excluding smartphones, laptops, semiconductors and displays from the reciprocal
tariffs, retroactive to 5 April ([CNBC](https://www.cnbc.com/2025/04/12/trump-exempts-phones-computers-chips-tariffs-apple-dell.html),
[EY tax alert](https://www.ey.com/en_gl/technical/tax-alerts/us-exempts-certain-electronic-products-from-tariffs-under-president-trumps-reciprocal-tariff-policy)).
Apple regained $3trn. The relief was understood as conditional: Commerce opened a Section 232
semiconductor investigation on 14 April covering downstream products including smartphones
([WilmerHale client alert](https://www.wilmerhale.com/en/insights/client-alerts/20250417-president-trump-announces-then-suspends-reciprocal-tariffs-defers-tariffs-on-certain-electronics-and-increases-tariffs-on-china)),
which is why 16 April gave back 3.89%.

Sources: [CNBC, stock market 9 April 2025](https://www.cnbc.com/2025/04/09/stock-market-today-live-updates.html) ·
[CNBC, "Trump exempts phones, computers, chips from new tariffs"](https://www.cnbc.com/2025/04/12/trump-exempts-phones-computers-chips-tariffs-apple-dell.html) ·
[EY, US exempts certain electronic products](https://www.ey.com/en_gl/technical/tax-alerts/us-exempts-certain-electronic-products-from-tariffs-under-president-trumps-reciprocal-tariff-policy) ·
[WilmerHale, tariff sequence client alert](https://www.wilmerhale.com/en/insights/client-alerts/20250417-president-trump-announces-then-suspends-reciprocal-tariffs-defers-tariffs-on-certain-electronics-and-increases-tariffs-on-china) ·
[AppleInsider, tariff war timeline](https://appleinsider.com/articles/25/04/16/trump-vs-china-how-the-tariff-war-has-hit-apple-so-far)

---

## Regime

**AAPL at the 15% threshold is a macro beta instrument, not a company-news instrument.**

By category: macro 8, geopolitical 2, earnings 2, guidance 1. Only **three of thirteen**
windows (2008-01-28, 2009-01-27, 2020-08-06) were caused by something Apple itself said or
did; two of those three are the January guide and the July print, the same two calendar slots.
Every other window is an index-wide risk event transmitted through a high-beta mega-cap, and
in most of them AAPL's move is roughly 1.5x to 2.5x the S&P 500's over the same days.

By period, and this is the material limitation:

| Cluster | Events | Share |
|---|---|---|
| GFC, Jan 2008 to Jan 2009 | 8 | 62% |
| COVID crash, Mar 2020 | 2 | 15% |
| COVID recovery / split, Aug 2020 | 1 | 8% |
| Tariff shock, Apr 2025 | 2 | 15% |

**Three consequences for using AAPL as a seed.**

1. **The training half is a single regime.** With `TRAIN_END = 2019-12-31`, all 8 in-sample
   AAPL events fall inside a 12-month GFC window. Analogs retrieved from AAPL's training
   corpus will encode one mechanism, systemic financial de-leveraging, and will transfer
   badly to the two mechanisms that actually generated the out-of-sample events (a pandemic
   demand shock and a trade-policy margin shock). This is the AAPL-specific instance of the
   concern CONTRACT.md §3 raises about JPM.
2. **The events are not independent draws.** 2008-11-20 and 2008-11-28 share an endpoint and
   are mechanically anti-correlated. 2020-03-12 and 2020-03-20 overlap by a day and are one
   crash split in two. 2025-04-08 and 2025-04-15 are the same policy shock and its reversal.
   Any calibration that treats 13 AAPL events as 13 independent observations is over-counting;
   the effective sample is closer to 8.
3. **Up-moves and down-moves have different mechanisms.** Every up window in this ledger is a
   *policy reversal or rescue* (bank recapitalisation, Citi rescue, tariff pause) or an
   *earnings beat*. No up window is organic. A generator that samples symmetric forward paths
   off a down-event conditioner will misrepresent AAPL's recovery dynamics, which are
   announcement-gapped rather than gradual.

---

## Ledger verdict

**The detection survives contact with reality. All 13 dates correspond to events a market
participant would recognise, and none is a data artifact.** Specifically:

- **Arithmetic reconciles.** All 13 recomputed 5-day returns match the recorded `move_pct`
  to four decimals against `data/prices/AAPL.csv`.
- **Splits are correctly adjusted.** The 2008 window closes print near $3 to $5, which is the
  nominal $90 to $155 divided by 28, the product of the 2014 7-for-1 and 2020 4-for-1 splits.
  Critically, there is **no spurious event on or near 2020-08-31**, the 4-for-1 ex-date, which
  is exactly where an unadjusted series would have manufactured a fake -75% event. The
  2014-06-09 7-for-1 ex-date is likewise clean.
- **No noise, no bad prints.** Every window has an identifiable driver day of 6% or more
  attached to a documented news event.
- **The tier split behaves as CONTRACT.md predicted.** Zero major events. Do not expect AAPL
  to contribute to the 25% stage narrative.

**Three caveats the parent should carry forward, none of which is a detection bug.**

1. **The ledger date is the window END, not the news date.** In 8 of 13 cases the causal news
   is 1 to 6 trading days before the label. Two windows have a driver day that is not even in
   the same month as the label (2008-10-03 driven by 09-29; 2008-11-03 driven by 10-28), and
   two have a terminal day that moved essentially zero (2008-01-28 at 0.00%, 2025-04-15 at
   -0.19%). **Any downstream lane that joins news to the ledger date rather than to the window
   will mis-attribute.** The 2008-10-03 window is the live trap: a genuine, well-documented,
   SEC-investigated Apple headline (the Jobs heart-attack hoax) sits on the exact label date
   and is not the cause.
2. **`famous` is inconsistently set.** 2020-03-12 and 2020-08-06 are flagged `famous: true`,
   but 2025-04-08, the single largest weekly move in AAPL's 45-year history at -22.7%, is
   flagged `false`. Flagging is LANE-EVENTS' territory, not mine; reporting it per the contract.
3. **`headline` and `articles` are empty on all 13 rows**, as expected at this stage. The
   headlines in the table above are supplied for LANE-NEWS to populate against.

---

## Unexplained

**None.** All 13 AAPL events have a documented cause with a retrieved source. The lowest
confidence in the set is 0.85, assigned to the two windows (2008-09-17 and 2008-11-03) where
the explanation is a broad market regime rather than a single datable catalyst, so the mapping
from cause to that specific window boundary is looser than elsewhere.
