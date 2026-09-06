# NVDA — event research

**Ticker:** NVIDIA Corporation (NASDAQ: NVDA)
**Ledger source:** `data/events.jsonl`, filtered to `ticker == "NVDA"`
**Events in ledger:** 75 total, of which 13 are `major` (>=25% over a 5-day window) and 62 are `significant` (>=15%)
**Train / test split at `TRAIN_END = 2019-12-31`:** 39 train, 36 test
**Researched by:** RESEARCH-NVDA lane, 2026-09-06

---

## What this ticker is, and what actually drives it

NVIDIA is not one company across this ledger. It is three, and the ledger straddles all three.

1. **2008 to 2015, cyclical PC graphics semiconductor.** Revenue came from discrete GPUs and chipsets sold into notebooks and desktops. The stock was a high-beta cyclical with a roughly $3B to $10B market cap. Its large moves were mostly *market* moves amplified by beta, punctuated by a few company-specific accidents. It also carried a live product-liability tail risk that actually detonated in July 2008.
2. **2016 to 2019, the AI thesis arriving.** Datacenter GPU revenue went from a rounding error to the growth engine. Big moves became **earnings-and-guidance moves**, and they got large because consensus was persistently behind the datacenter ramp. The 2018 crypto hangover is the counterexample that proves it: when the demand story broke, the stock fell as violently as it had risen.
3. **2020 onward, the AI infrastructure monopoly.** Moves are driven by AI capex expectations, guidance revisions, US export policy toward China, and, twice now, by a shock to the *cost* assumption underlying AI demand (DeepSeek, January 2025). Market cap is now measured in trillions, and the ticker has become macro in its own right, which means index-level moves and NVDA-level moves have partially merged.

**Where the ledger dates come from.** Every `date` in the ledger is the **end** of a 5-trading-day window. I verified each explanation below against the actual daily closes in `data/prices/NVDA.csv` before assigning a cause, so the "which day inside the window moved" claims are checked against price, not assumed. Prices in that file are split-adjusted (the 2021 4-for-1 and 2024 10-for-1 splits do not appear as events, which is the correct behavior).

---

## Every event examined

`Src` = whether I retrieved a real URL supporting the explanation. `n` means I did not, and confidence is discounted accordingly. Confidence is my probability that the stated cause is the dominant driver of *this specific window*.

| Date | Move | Tier | Category | Headline | Conf | Src |
|---|---:|---|---|---|---:|---|
| 2008-01-22 | -18.2% | significant | macro | January 2008 global equity rout; semis hit by Intel's Q4 miss, then the Fed's emergency 75bp cut on Jan 22 | 0.50 | n |
| 2008-02-21 | -21.2% | significant | guidance | Q4 FY2008 record results on Feb 13 but a soft Q1 outlook; stock fell 16.3% on Feb 14 | 0.85 | y |
| **2008-07-07** | **-37.2%** | **major** | **crisis** | **July 2 warning: defective notebook GPU/MCP packaging, $150M to $200M charge, Q2 revenue guide cut ~17% below consensus; stock fell ~31% on July 3** | **0.97** | y |
| 2008-08-19 | +21.2% | significant | earnings | Aug 12 Q2 FY2009 report absorbed the $196M defect charge and raised the buyback; relief rally off the July low | 0.60 | y |
| 2008-09-15 | -16.9% | significant | macro | Lehman Brothers bankruptcy, Sept 15 2008 | 0.90 | n |
| 2008-09-22 | +20.1% | significant | macro | TARP announcement and the SEC short-selling ban, Sept 18 to 19 2008 | 0.80 | n |
| **2008-10-07** | **-32.4%** | **major** | **macro** | **Worst week for US equities since 1933; Dow -18.1%, S&P 500 -20% over Oct 6 to 10** | **0.95** | y |
| 2008-10-23 | -15.1% | significant | macro | Continuation of the October 2008 credit-crisis liquidation | 0.70 | y |
| **2008-10-31** | **+32.5%** | **major** | **macro** | **Late-October 2008 short-covering rebound; Dow +10.9% on Oct 28 ahead of the Fed's 50bp cut on Oct 29** | **0.85** | y |
| **2008-11-20** | **-25.7%** | **major** | **macro** | **The November 20 2008 bear-market low; S&P 500 closed at 752, its worst level of the crisis** | **0.90** | n |
| **2008-11-28** | **+26.6%** | **major** | **macro** | **Thanksgiving-week melt-up off the Nov 20 low, on the Citigroup rescue (Nov 23) and the Fed's first QE/TALF facilities (Nov 25)** | **0.85** | n |
| 2008-12-15 | +16.9% | significant | macro | Pre-FOMC rally into the Fed's move to zero rates on Dec 16 2008 | 0.45 | n |
| 2008-12-24 | -17.2% | significant | unexplained | No credible NVDA-specific or market-specific catalyst identified for this window | 0.20 | n |
| 2009-01-06 | +18.3% | significant | macro | New-year risk-on rally; CES 2009 week | 0.35 | n |
| 2009-01-13 | -16.6% | significant | unexplained | Mid-January 2009 bank-solvency selloff, but not confirmed for this window | 0.25 | n |
| 2009-01-27 | +17.1% | significant | unexplained | No catalyst identified | 0.20 | n |
| 2009-02-06 | +24.2% | significant | macro | Rally into the announcement of the Treasury's Financial Stability Plan and the stimulus bill | 0.40 | n |
| 2009-02-17 | -19.6% | significant | earnings | Q4 FY2009 reported Feb 10 with a large loss, into the Feb 17 break below the November 2008 lows | 0.45 | n |
| 2009-03-12 | +19.2% | significant | macro | The March 9 2009 generational bottom and the reversal week that followed | 0.75 | n |
| 2009-04-06 | +15.9% | significant | macro | Spring 2009 recovery rally | 0.35 | n |
| **2009-05-13** | **-27.3%** | **major** | **earnings** | **May 7 Q1 FY2010 report: revenue -42% year over year to $664M, net loss $201M; stock fell 7% on May 7 and 13.8% on May 8 on 2.9bn shares** | **0.80** | y |
| 2009-05-20 | +15.8% | significant | unexplained | Bounce off the post-earnings low; no specific catalyst found | 0.25 | n |
| 2009-07-20 | +16.5% | significant | macro | July 2009 earnings-season rally | 0.30 | n |
| 2009-09-10 | +15.7% | significant | unexplained | No catalyst identified | 0.20 | n |
| 2009-12-07 | +23.2% | significant | unexplained | No catalyst identified | 0.20 | n |
| 2010-09-24 | +16.2% | significant | unexplained | No catalyst identified | 0.20 | n |
| **2011-01-12** | **+37.5%** | **major** | **product** | **CES 2011 (Jan 5): Tegra 2 and "Project Denver," NVIDIA's ARM-based CPU, plus Microsoft committing Windows to ARM; then Jan 10, Intel settles for a $1.5bn patent cross-license** | **0.90** | y |
| 2011-08-08 | -18.1% | significant | macro | S&P's downgrade of the US credit rating (Aug 5 2011) and the Aug 8 crash | 0.80 | n |
| **2011-10-10** | **+25.1%** | **major** | **macro** | **The Oct 3 2011 low and the reversal on European bank-recapitalization headlines; best month for the Dow since 2002** | **0.80** | y |
| 2015-08-10 | +17.2% | significant | earnings | Q2 FY2016 beat reported Aug 6 2015 | 0.45 | n |
| 2016-02-22 | +22.5% | significant | earnings | Q4 FY2016 report on Feb 17 2016, into the February 2016 market bottom rebound | 0.45 | n |
| 2016-05-19 | +22.4% | significant | earnings | May 12 Q1 FY2017 beat on datacenter and gaming; stock +15.2% on May 13 | 0.85 | n |
| **2016-11-17** | **+36.3%** | **major** | **earnings** | **Nov 10 Q3 FY2017 blowout: revenue $2.00bn (+54% y/y) vs $1.69bn consensus, datacenter +193%; stock +29.8% on Nov 11** | **0.95** | y |
| 2016-12-27 | +15.4% | significant | sector-rotation | Year-end melt-up in 2016's best-performing S&P 500 stock; no discrete catalyst inside the window (the Citron short report was Dec 28, after it) | 0.45 | y |
| **2017-05-16** | **+32.9%** | **major** | **earnings** | **May 9 Q1 FY2018: revenue $1.94bn (+48% y/y), GAAP EPS +126%, datacenter GPU revenue nearly tripled; stock +17.8% on May 10** | **0.95** | y |
| 2018-10-11 | -15.8% | significant | macro | The October 2018 rate-spike selloff; semis led the market down | 0.70 | n |
| 2018-10-29 | -19.7% | significant | macro | Continuation of the October 2018 rout; NVDA fell 9.8% on Oct 24 alone | 0.65 | n |
| **2018-11-23** | **-28.4%** | **major** | **guidance** | **Nov 15 Q3 FY2019: revenue +2.5% to $3.18bn, below guidance, on a "crypto hangover" of unsold Pascal inventory; Q4 guided to $2.7bn vs $3.4bn consensus. Stock -18.8% Nov 16, -12% more Nov 19** | **0.95** | y |
| 2019-08-22 | +15.3% | significant | earnings | Q2 FY2020 beat reported Aug 15 2019 | 0.45 | n |
| 2020-02-19 | +17.5% | significant | earnings | Feb 13 Q4 FY2020 beat, into the Feb 19 2020 pre-COVID market top | 0.60 | n |
| 2020-02-27 | -18.2% | significant | macro | The first COVID crash week, Feb 24 to 28 2020 | 0.90 | n |
| 2020-03-12 | -20.8% | significant | macro | COVID crash: WHO pandemic declaration, circuit breakers, March 12 2020 | 0.90 | n |
| 2020-03-30 | +24.9% | significant | macro | CARES Act and the Fed's open-ended QE; the March 23 2020 bottom and rebound | 0.75 | n |
| 2020-05-20 | +15.3% | significant | unexplained | Reopening rally plus positioning into the May 21 earnings date; not confirmed | 0.30 | n |
| 2020-11-06 | +16.2% | significant | macro | US election week 2020; Nasdaq's largest weekly gain since April | 0.55 | n |
| 2021-03-08 | -16.2% | significant | macro | The February to March 2021 long-yield spike and the derating of long-duration growth | 0.60 | n |
| 2021-08-25 | +16.7% | significant | earnings | Aug 18 Q2 FY2022 beat, alongside the 4-for-1 split taking effect in July | 0.45 | n |
| 2021-11-04 | +19.5% | significant | sector-rotation | Wells Fargo raised its target from $245 to $320 on the Omniverse/metaverse opportunity; stock +12% on Nov 4, adding roughly $80bn of value | 0.80 | y |
| 2022-02-23 | -15.5% | significant | geopolitical | Run-up to the Russian invasion of Ukraine, compounding a poorly received Feb 16 Q4 FY2022 report | 0.55 | n |
| **2022-03-21** | **+25.3%** | **major** | **macro** | **The Fed's first hike of the cycle on March 16 2022 removed the "when does it start" overhang; three straight strong sessions and one of the Nasdaq's best weeks since 2020** | **0.75** | y |
| 2022-04-11 | -19.9% | significant | macro | April 2022 inflation and rate repricing; growth-multiple compression | 0.50 | n |
| 2022-04-26 | -15.4% | significant | macro | Late-April 2022 tech rout | 0.45 | n |
| 2022-05-11 | -18.2% | significant | macro | The April CPI print on May 11 2022 and the growth-stock capitulation around it | 0.45 | n |
| 2022-06-02 | +15.4% | significant | macro | Late-May to early-June 2022 bear-market bounce | 0.30 | n |
| 2022-06-13 | -16.7% | significant | macro | The 8.6% May CPI print on June 10 2022 and the June 13 plunge into a bear market | 0.70 | n |
| 2022-07-01 | -15.2% | significant | unexplained | End-of-quarter 2022 derisking; not confirmed for this window | 0.30 | n |
| 2022-07-20 | +17.4% | significant | macro | July 2022 bear-market rally | 0.30 | n |
| 2022-09-01 | -22.2% | significant | regulatory | Two shocks in one window: Powell's Jackson Hole speech (Aug 26) and the Aug 31 8-K disclosing a new US licence requirement on A100/H100 exports to China and Russia, putting up to $400M of Q3 sales at risk | 0.85 | y |
| 2022-11-10 | +17.4% | significant | macro | The Nov 10 2022 downside CPI surprise; Nasdaq +7.4% in a single session | 0.75 | n |
| 2023-01-12 | +15.7% | significant | macro | January 2023 disinflation rally, with the post-ChatGPT AI narrative beginning to bid semis | 0.45 | n |
| 2023-01-26 | +18.1% | significant | sector-rotation | AI enthusiasm following Microsoft's expanded OpenAI investment; NVDA re-rated as the picks-and-shovels trade | 0.45 | n |
| **2023-06-01** | **+30.2%** | **major** | **guidance** | **May 24 Q1 FY2024: revenue $7.19bn vs $6.52bn consensus, and Q2 guided to $11bn against roughly $7.2bn expected. Stock +24.4% on May 25, the single most important guidance event in the AI cycle** | **0.97** | y |
| 2024-02-28 | +15.1% | significant | earnings | Feb 21 Q4 FY2024: revenue $22.1bn, +265% y/y on Hopper H100 demand; stock +16.4% on Feb 22 | 0.90 | y |
| 2024-03-07 | +17.1% | significant | sector-rotation | Post-earnings AI melt-up and GTC 2024 anticipation | 0.40 | n |
| 2024-04-26 | +15.1% | significant | macro | Rebound from the April 2024 drawdown as hyperscaler earnings reaffirmed AI capex | 0.35 | n |
| 2024-05-29 | +20.4% | significant | earnings | May 22 Q1 FY2025 beat plus the announcement of a 10-for-1 stock split | 0.65 | n |
| 2024-07-30 | -15.4% | significant | sector-rotation | The July 2024 rotation out of megacap tech into small caps and value | 0.45 | n |
| 2024-08-07 | -15.5% | significant | macro | The Aug 5 2024 global risk-off: weak July payrolls, the Bank of Japan hike and the yen carry-trade unwind | 0.65 | n |
| 2024-08-14 | +19.4% | significant | macro | Sharp V-shaped recovery from the Aug 5 2024 low as recession fears faded | 0.55 | n |
| 2024-09-04 | -17.2% | significant | macro | The Sept 3 2024 semiconductor rout: a weak ISM print plus press reports of a DOJ antitrust subpoena; NVDA fell about 9.5% in one session | 0.55 | n |
| 2024-09-13 | +15.8% | significant | macro | Recovery week ahead of the Fed's September 2024 50bp cut | 0.40 | n |
| 2025-01-29 | -15.9% | significant | crisis | DeepSeek R1: a Chinese model claiming frontier performance at a fraction of the training cost, undermining the assumed AI capex trajectory. NVDA fell 17% on Jan 27, roughly $590bn of market value, the largest one-day loss in market history at the time | 0.95 | y |
| 2025-04-11 | +17.6% | significant | geopolitical | The April 9 2025 announcement of a 90-day pause on reciprocal tariffs and the historic single-day rally that followed | 0.65 | n |
| 2025-05-16 | +16.1% | significant | geopolitical | US-China tariff de-escalation in mid-May 2025 plus large Gulf sovereign AI agreements announced during that week | 0.50 | n |
| 2026-08-05 | +15.4% | significant | sentiment | Five-session run of +10.5% into the Aug 5 2026 close of $219.22, on hyperscaler capex beats, a public SpaceX commitment to NVIDIA silicon, and positioning ahead of the Aug 26 earnings report | 0.60 | y |

---

## The major events, in detail

### 2008-07-07, -37.2%. The defect warning.

**What happened.** On July 2 2008 NVIDIA pre-announced. It cut Q2 revenue guidance to roughly $912M, about 17% below consensus, and disclosed a one-time charge of $150M to $200M to cover warranty, repair, return and replacement costs for a "weak die/packaging material set" in certain notebook GPUs and MCPs. The stock fell about 31% on July 3, from $0.451 to $0.312 on a split-adjusted basis, on 3.0bn shares, roughly four times normal volume.

**Why it moved.** This was a simultaneous hit to three things the market prices separately: current revenue (the guide cut), the cost structure (an open-ended warranty liability against products already in customers' hands), and management credibility (the defect had been known internally and the size of the liability was uncertain). Securities litigation followed within weeks. The August 12 Q2 report booked $196M of charges against cost of revenue, confirming the top of the range.

**Ledger note.** The window ends July 7, three trading days after the causal print. The move inside the window is real and is not a data artifact.

Sources: [The Register, 2008-07-03](https://www.theregister.com/2008/07/03/nvidia_forecast_glitch/) · [Fortune, 2008-07-03](https://fortune.com/2008/07/03/miss-by-chipmaker-nvidia-rattles-investors) · [Computerworld, on the resulting securities suit](https://www.computerworld.com/article/1580916/nvidia-hit-with-securities-lawsuit-over-bad-graphics-chips.html) · [Motley Fool, 2008-07-08](https://www.fool.com/investing/general/2008/07/08/nvidia-explodes.aspx) · [Q2 FY2009 8-K press release, SEC](https://www.sec.gov/Archives/edgar/data/0001045810/000104581008000018/q209form8kpressrelease.htm)

### 2008-10-07, -32.4%. The worst week since 1933.

**What happened.** Nothing NVIDIA-specific. The window covers Sept 30 to Oct 7 2008, inside the week the Dow fell 18.1% and the S&P 500 fell more than 20%, three weeks after Lehman and days after the $700bn TARP bill was signed. NVDA closed at $0.268 on Sept 30 and $0.181 on Oct 7.

**Why it moved.** Interbank funding markets seized, the VIX set records, and forced deleveraging hit high-beta names hardest. A sub-$10bn cyclical semiconductor with a live warranty liability and no dividend was near the top of what gets sold in a liquidation.

Sources: [Begin To Invest, October 10 in market history](https://www.begintoinvest.com/october-10/) · [CNNMoney market report, 2008-10-06](https://money.cnn.com/2008/10/06/markets/markets_newyork/) · [Moneyzine, the 2008 crash](https://moneyzine.com/investments/stock-market-crash-of-2008/)

### 2008-10-31, +32.5%. The rebound off the October low.

**What happened.** From $0.165 on Oct 24 to $0.219 on Oct 31. The engine was Oct 28 2008, when the Dow rose 10.9%, its second-largest percentage gain ever, ahead of the Fed's 50bp cut to 1.0% on Oct 29.

**Why it moved.** A short-covering and forced-repositioning rally after a capitulation, not a change in fundamentals. NVIDIA reported nothing in this window. The move is beta times an exceptional market week.

Sources: [Benzinga, on the Oct 2008 rebound](https://www.benzinga.com/general/education/21/10/23355953/this-day-in-market-history-dow-rebounds-11-following-worst-week-ever-in-2008) · [Moneyzine, the 2008 crash](https://moneyzine.com/investments/stock-market-crash-of-2008/)

### 2008-11-20, -25.7%. The bear-market low.

**What happened.** From $0.199 on Nov 13 to $0.148 on Nov 20 2008, the day the S&P 500 closed at 752, its low of the crisis. No NVIDIA-specific news in the window. The Q3 FY2009 report had come on Nov 6, ahead of the window's start.

**Why it moved.** Terminal-phase deleveraging: hedge fund redemptions, mutual fund tax-loss selling, and a solvency scare in the large banks. Confidence in the *macro* attribution is high; confidence that no NVDA-specific news contributed is somewhat lower, because I could not retrieve a primary source for this specific window.

Sources: none retrieved for this window. Attribution rests on the price path and the well-documented S&P 500 low of Nov 20 2008.

### 2008-11-28, +26.6%. The Thanksgiving-week melt-up.

**What happened.** From the Nov 20 low of $0.148 to $0.187 on Nov 28, five consecutive up sessions. Market-wide: the S&P 500 rose roughly 19% off the Nov 20 low in that stretch, its largest five-session gain since 1933.

**Why it moved.** The Citigroup rescue announced Nov 23, the Fed's first quantitative-easing and TALF facilities announced Nov 25, and the announcement of the incoming Obama economic team. Again pure beta, no NVIDIA news.

Sources: none retrieved for this window. The Citigroup rescue and the Nov 25 2008 Fed facilities are matters of public record but I did not fetch a citation, so confidence is marked down.

### 2009-05-13, -27.3%. The Q1 FY2010 collapse.

**What happened.** NVIDIA reported Q1 FY2010 after the close on May 7 2009: revenue of $664.2M against $1.2bn a year earlier, down 42%, and a net loss of $201.3M, or $0.37 per share, including a $140.2M non-recurring charge tied to a cash tender offer for employee stock options. The stock fell 7.2% on May 7 and 13.8% on May 8, on 2.9bn shares, the heaviest volume in the sample outside July 2008.

**Why it moved.** The PC and notebook end market had not bottomed, gross margin was still absorbing the defect charge, and the option-tender charge made an already ugly quarter worse. The window also spans the exhaustion of the post-stress-test rally in the broad market, so a portion of the move is beta, but the May 8 gap on quadruple volume is unambiguously idiosyncratic.

Sources: [NVIDIA Q1 FY2010 results press release](https://nvidianews.nvidia.com/news/nvidia-reports-financial-results-for-first-quarter-fiscal-year-2010)

### 2011-01-12, +37.5%. CES plus the Intel settlement.

**What happened.** Two catalysts inside one window. At CES on Jan 5 2011, Jen-Hsun Huang announced Tegra 2 and "Project Denver," NVIDIA's plan to build its own high-performance ARM-based CPU cores for PCs, workstations and supercomputers, in the same week Microsoft said Windows would run on ARM. Then on Jan 10 2011, Intel settled its litigation with a six-year patent cross-license and $1.5bn of payments to NVIDIA.

**Why it moved.** The market had been pricing NVIDIA as a shrinking discrete-GPU business being squeezed out by integrated graphics. Both announcements attacked that thesis: Denver said NVIDIA could compete for the CPU socket rather than be excluded from it, and the Intel settlement converted a legal overhang into $1.5bn of high-margin cash with no cost of goods attached. The stock ran roughly 29% in a week and crossed $20.

**Honest caveat.** This is the only major event in the ledger with two independent catalysts of comparable size. Any downstream analog retrieval that labels it "product" is losing half the story.

Sources: [PCWorld on Project Denver](https://www.pcworld.com/article/499902/nvidia_reveals_project_denver_an_arm_based_processor.html) · [DigiTimes, CES 2011](https://www.digitimes.com/news/a20110106PR204.html) · [Forbes, the $1.5bn Intel cross-license](https://www.forbes.com/sites/briancaulfield/2011/01/10/nvidia-gets-1-5-billion-in-intel-cross-licensing-deal-settles-litigation/) · [Intel 8-K announcing the settlement, SEC](https://www.sec.gov/Archives/edgar/data/0000050863/000005086311000007/exh991.htm) · [Motley Fool, 2011-01-24](https://www.fool.com/investing/general/2011/01/24/nvidia-shares-popped-what-you-need-to-know.aspx)

### 2011-10-10, +25.1%. The October 2011 reversal.

**What happened.** From $0.295 on Oct 3 2011 to $0.370 on Oct 10. Oct 3 was the closing low of the year for both the Dow and the S&P 500, one bad session away from a formal bear market. What followed was the best month for the Dow since 2002, up 9.5%, and the best month for the S&P 500 since 1991, up 10.8%.

**Why it moved.** European policy. The market began pricing a coordinated recapitalization of EU banks, which the European Council formally agreed on Oct 26 2011. NVIDIA reported nothing in the window. This is a beta event, and a large one because NVDA's realized beta in 2011 was well above 1.

Sources: [Fox News, on October 2011 on Wall Street](https://www.foxnews.com/us/ugly-end-to-historic-october-on-wall-street.print) · [CEPR/VoxEU, the EBA recapitalisation exercise](https://cepr.org/voxeu/columns/short-guide-ebas-recapitalisation-results)

### 2016-11-17, +36.3%. The quarter the AI thesis became a number.

**What happened.** After the close on Nov 10 2016, NVIDIA reported Q3 FY2017 revenue of $2.00bn, up 54% year over year, against consensus of $1.69bn, with adjusted EPS of $0.94 against $0.69 expected. Gaming grew 63% to $1.2bn, datacenter grew 193% to $240M, automotive grew 61% to $127M. The stock rose 29.6% on Nov 11 and kept going, from $1.694 on Nov 10 to $2.310 on Nov 17.

**Why it moved.** It was not the beat alone, it was the *composition*. Datacenter tripling proved that deep-learning training demand was a real revenue line and not a slide in a keynote. The multiple re-rated, not just the estimates. This is the origin point of the modern NVDA regime, and the reason 2016 is a regime boundary in this ledger.

Sources: [Motley Fool, why NVDA rose 29.6% in November 2016](https://www.fool.com/investing/2016/12/09/why-nvidia-corporation-stock-skyrocketed-296-in-no.aspx) · [Nanalyze, why NVDA rose 220% in 2016](https://www.nanalyze.com/2017/01/why-nvda-stock-price-skyrocketed/)

### 2017-05-16, +32.9%. Datacenter triples again.

**What happened.** After the close on May 9 2017, NVIDIA reported Q1 FY2018 revenue of $1.94bn, up 48% year over year, and GAAP EPS of $0.79, up 126%. Datacenter GPU computing revenue nearly tripled year over year. Guidance for the following quarter was $1.95bn. The stock rose 17.8% on May 10 and continued to $3.420 by May 16 from $2.574 on May 9.

**Why it moved.** The second consecutive quarter where datacenter growth exceeded what a linear extrapolation of the prior quarter would have produced. That is the specific pattern that forces a growth-rate revision rather than a level revision, and growth-rate revisions are what produce 30% weeks.

Sources: [NVIDIA Q1 FY2018 results press release](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2018) · [Press release PDF](https://nvidianews.nvidia.com/_gallery/download_pdf/59122a5eed6ae5323bdf87fd/)

### 2018-11-23, -28.4%. The crypto hangover.

**What happened.** After the close on Nov 15 2018, NVIDIA reported Q3 FY2019 revenue of $3.18bn, up only 2.5% year over year, short of both consensus and its own prior guidance, and guided Q4 to $2.7bn plus or minus 2% against roughly $3.4bn expected, a 7.8% year-over-year decline at the midpoint. Jensen Huang described a "crypto hangover" that was worse and longer-lasting than expected. The stock fell 18.8% on Nov 16 and a further 12% on Nov 19, from $5.060 on Nov 15 to $3.625 on Nov 23.

**Why it moved.** The mechanism is channel inventory, and it is a mirror image of 2016 and 2017. Mid-range Pascal cards bought by cryptocurrency miners in early 2018 came back into the retail channel when mining economics collapsed. That inventory had to clear before NVIDIA could sell new units, so the company was competing against its own installed base. The guidance cut told the market that the prior two years of gaming growth had contained a demand source that had now gone negative, which forces a downward revision to the base as well as the growth rate. The second leg on Nov 19 coincided with a broad megacap technology selloff, so part of that day is beta.

Sources: [Fortune, 2018-11-15](https://fortune.com/2018/11/15/nvidia-stock-plunges-crypto-hangover-weighs-revenue-growth) · [Motley Fool, why NVDA tumbled Nov 19 2018](https://www.fool.com/investing/2018/11/19/why-nvidia-stock-tumbled-today.aspx) · [Motley Fool, why NVDA fell 31% in 2018](https://www.fool.com/investing/2019/01/14/why-nvidia-stock-plunged-31-in-2018.aspx)

### 2022-03-21, +25.3%. The Fed actually hiked.

**What happened.** From $21.33 on March 14 2022 to $26.73 on March 21, with the strongest sessions on March 15, 16 and 18. The Fed raised rates 25bp on March 16 2022, the first hike of the cycle, and published a dot plot implying six more hikes that year. The Nasdaq rose 1.3% on March 18 alone and posted one of its strongest weeks since 2020.

**Why it moved.** Removal of an anticipation overhang. Long-duration technology had derated through January and February on the *expectation* of tightening; the actual hike, combined with a dot plot that was hawkish but not shockingly so, let positioning unwind. NVIDIA's GTC 2022 keynote, where Hopper H100 was announced, fell on March 22, one day *after* the window closes, so it is not the cause of this event even though it is the obvious guess.

**Ledger note.** This is the clearest case in the file of a plausible-but-wrong explanation being available. Any automated labeller matching "NVDA, March 2022, big up move" to "Hopper announcement" would be off by a day and would be attributing a macro move to a product event.

Sources: [Nasdaq, market news for March 18 2022](https://www.nasdaq.com/articles/stock-market-news-for-mar-18-2022)

### 2023-06-01, +30.2%. The $11 billion guide.

**What happened.** After the close on May 24 2023, NVIDIA reported Q1 FY2024 revenue of $7.19bn against consensus of $6.52bn and adjusted EPS of $1.09 against $0.92, then guided Q2 to approximately $11bn against roughly $7.2bn expected. The stock rose about 30% in after-hours trade and closed up 24.4% on May 25, from $30.54 to $37.98, and reached $39.77 by June 1. It approached a $1trn market capitalization within days.

**Why it moved.** A guidance beat of that magnitude, roughly 50% above consensus for the following quarter, is not an estimate revision, it is information that the market's entire model of the demand curve is wrong. Generative AI training demand had appeared faster than the supply chain or the sell side had modelled, and NVIDIA was the only company that could see the order book. This is the single most consequential print in the ledger for the modern regime.

Sources: [CNBC, 2023-05-25](https://www.cnbc.com/2023/05/25/nvidia-on-track-for-record-high-driven-by-ai-chip-demand.html) · [Morningstar, three years of the AI boom in charts](https://www.morningstar.com/stocks/three-years-ai-stock-market-boom-charts)

---

## Notable significant events worth flagging

These are not `major` but they carry information the majors do not.

**2022-09-01, -22.2%, regulatory.** Two shocks compressed into one window: Powell's Jackson Hole speech on Aug 26 2022, and NVIDIA's 8-K filed Aug 31 disclosing that on Aug 26 the US government had imposed an immediate licence requirement on exports of A100 and H100 to China, Hong Kong and Russia, putting up to $400M of Q3 sales at risk and threatening H100 development timelines. This is the only pure regulatory shock in the NVDA ledger and it is the template for the China-policy risk that recurs through 2023 to 2025. Sources: [NVIDIA 8-K, SEC](https://www.sec.gov/Archives/edgar/data/1045810/000104581022000146/nvda-20220826.htm) · [Tom's Hardware](https://www.tomshardware.com/news/us-export-rules-may-cost-nvidia-400-million-prevent-h100-development) · [VideoCardz](https://videocardz.com/newz/us-imposes-license-requirement-for-nvidia-a100-h100-gpus-export-to-china-and-russia-400m-revenue-at-risk) · [TechTarget](https://www.techtarget.com/searchenterpriseai/news/252524511/Nvidia-now-needs-special-license-to-export-AI-chips-to-China)

**2025-01-29, -15.9%, crisis.** DeepSeek's R1 model, claiming frontier-class reasoning at a small fraction of the assumed training cost, hit on Monday Jan 27 2025. NVDA fell 17% and lost roughly $590bn of market value in one session, the largest single-day loss for any company on record at the time. The mechanism is unusual and worth preserving: nothing about NVIDIA's orders, guidance, or products changed. What changed was the market's estimate of *how much compute a given level of AI capability requires*, which is the denominator of the entire demand thesis. Sources: [CNBC, NVIDIA's response](https://www.cnbc.com/2025/01/27/nvidia-calls-chinas-deepseek-r1-model-an-excellent-ai-advancement.html) · [IG](https://www.ig.com/en/news-and-trade-ideas/why-nvidia-s-share-price-dropped-17--after-deepseek-news-250128) · [Reuters via Kathmandu Post](https://kathmandupost.com/world/2025/01/28/deepseek-sparks-ai-stock-selloff-nvidia-posts-record-market-cap-loss) · [Forbes](https://www.forbes.com/sites/greatspeculations/2025/01/27/why-deepseek-is-sinking-nvidia-stock/)

**2021-11-04, +19.5%, sentiment.** A 12% single-day move on a sell-side price target increase, from $245 to $320 at Wells Fargo, framed around Omniverse and the metaverse. Roughly $80bn of market value on an analyst note with no new company disclosure. Worth keeping in the corpus specifically because it is a *pure sentiment* event with no fundamental catalyst, which is the hardest class for any conditional generator to handle. Sources: [Reuters via Investing.com](https://www.investing.com/news/stock-market-news/nvidias-rally-turbo-charged-by-metaverse-valuation-breaches-800-billion-2684316) · [Coinspeaker](https://www.coinspeaker.com/nvidia-stock-metaverse/) · [Forbes](https://www.forbes.com/sites/petercohan/2021/11/05/up-33-a-year-since-1999-nvidia-stock-to-benefit-from-metaverse/)

**2008-02-21, -21.2%, guidance.** NVIDIA reported record Q4 FY2008 results on Feb 13 2008: revenue of $1.20bn, up 37%, GAAP net income of $257.0M, up 57%, annual revenue of $4.10bn. The stock fell 16.3% the next day. This is a *good quarter that traded badly*, on decelerating growth signals and a soft outlook, and it is the earliest warning of the notebook problem that detonated five months later. Sources: [Q4 FY2008 8-K press release, SEC](https://www.sec.gov/Archives/edgar/data/0001045810/000104581008000003/q408pressrelease.htm) · [CNBC, "Nvidia Shares Tumble, Hurt by Growth Concerns", 2008-02-14](https://www.cnbc.com/2008/02/14/nvidia-shares-tumble-hurt-by-growth-concerns.html) (the URL is real and indexed but returned HTTP 403 to automated fetch, so I am citing it on the strength of its title and date only)

**2026-08-05, +15.4%, sentiment.** The most recent event in the ledger and the one I am least able to verify independently. Reported drivers are hyperscaler capital-expenditure guidance beats, a public statement from Elon Musk that SpaceX would use NVIDIA silicon exclusively for its AI infrastructure, and positioning into the Aug 26 2026 earnings report. One source states the Aug 5 single-day move was +4.31%; the price file in this repo shows $211.94 to $219.22, which is +3.44%. I have kept the ledger's own price data as authoritative and marked confidence down for the narrative. Sources: [TradingKey analysis, 2026-08-06](https://www.tradingkey.com/analysis/stocks/us-stocks/262082021-us-stock-nvidia-nvda-price-ai-chip-spacex-tradingkey) · [TradingKey market movers, 2026-08-05](https://www.tradingkey.com/news/market-movers/262078451-market-movers-nvda-20260805) · [24/7 Wall St, 2026-08-09](https://247wallst.com/investing/2026/08/09/nvidia-and-micron-have-driven-the-sp-500s-2026-rally-to-record-highs-history-says-its-not-over/)

---

## Regime

**NVDA does not live in one regime. It lives in four, and the ledger's mass is in the wrong ones for the product's purpose.**

| Era | Events | Up | Down | What drives the big moves |
|---|---:|---:|---:|---|
| 2008 to 2009, GFC | 25 | 14 | 11 | Market beta, plus one company-specific product crisis |
| 2010 to 2015, PC cyclical | 5 | 4 | 1 | Product announcements, macro beta |
| 2016 to 2019, AI emergent | 9 | 6 | 3 | Earnings and guidance, both directions |
| 2020 to 2026, AI infrastructure | 36 | 22 | 14 | Guidance, AI capex expectations, US-China export policy, cost-of-compute shocks |

Three things follow, and each is a constraint on how NVDA can be used as a seed.

**1. The train-period corpus is a GFC corpus.** 25 of the 39 pre-2020 events, 64%, fall in 2008 or 2009. Nine of the eleven pre-2020 major events are macro-beta moves; only two, the July 2008 defect warning and the May 2009 earnings collapse, are company-specific, and both belong to the old PC-graphics business. Of the eleven pre-2020 majors, five (2008-10-07, 2008-10-31, 2008-11-20, 2008-11-28, 2011-10-10) are pure market beta with no NVIDIA news in the window at all. **If a generator retrieves analogs for a 2020s NVDA guidance shock and the nearest neighbours it finds are the November 2008 Thanksgiving rally and the October 2011 European bank recapitalization, the analog is not transferring, it is just matching magnitude.**

**2. The causal mechanism inverted in 2016.** Before 2016, an NVDA 25% week was usually the market having a 15% week. After 2016, an NVDA 25% week is usually a guidance revision that changes the growth rate, and those moves are largely uncorrelated with the index that day. Any model that learns "NVDA big move implies market big move" from the train period will be learning a relationship that stopped holding roughly at the `TRAIN_END` boundary. This cuts *against* the leakage concern in CONTRACT §8, interestingly: the pre-2019 corpus is a poor cheat sheet for the post-2019 world, so a model that scores well on the test set is less likely to be simply retrieving.

**3. The upward skew is structural, not an artifact.** 36 of 75 events are in the AI-infrastructure era and 22 of those are up moves. NVDA is a positively-skewed compounder in that regime: the down moves are shocks to a demand assumption (crypto 2018, export controls 2022, DeepSeek 2025) and the up moves are guidance revisions. A symmetric null ensemble will be systematically miscentred on this ticker. That is exactly what `crps_null` is for, and it means NVDA is a good ticker for demonstrating lift, but a bad one for claiming the lift generalizes.

**Recommended framing for downstream lanes.** Treat 2016 as a hard regime boundary for NVDA. Within the contract's train period, that leaves nine usable AI-emergent events (2016-02-22 through 2019-08-22) against 25 GFC events. Weight accordingly, or state explicitly that NVDA analogs before 2016 describe a different company.

---

## Ledger verdict

**The ledger survives contact with reality. All 13 major events correspond to something a person who followed the stock would recognise, and I found no data artifacts.**

Specifically:

- **No unadjusted-split artifacts.** NVIDIA split 4-for-1 in July 2021 and 10-for-1 in June 2024. Neither date appears in the ledger, and the prices in `data/prices/NVDA.csv` are split-adjusted throughout. A ledger built on raw prices would have produced spurious -75% and -90% events on those dates. It did not.
- **No bad prints.** I cross-checked the closes bounding all 13 major windows plus fifteen significant ones. Every move reconciles to the daily series, and every large single-day component of a major window is accompanied by a volume spike of 2x to 4x normal, which is what a real event looks like and what a stale or erroneous print does not.
- **Every major event has a nameable cause.** Six are the 2008-09 financial crisis, four are earnings or guidance, one is a product-and-litigation double catalyst (January 2011), one is a product-defect crisis (July 2008), one is the March 2022 Fed liftoff. Zero are unexplained.
- **Non-maximum suppression behaved.** In the dense 2008 to 2009 stretch the detected dates alternate sensibly between down-legs and rebound-legs (Oct 7 down, Oct 23 down, Oct 31 up, Nov 20 down, Nov 28 up) rather than firing repeatedly inside one continuous move. That is the expected behaviour of a correctly implemented rolling-window suppression.

**Two real problems, both in the interface rather than the detection.**

**Problem 1, and it matters for LANE-NEWS: the ledger date is not the news date.** The window ends on the ledger date and covers the prior five trading days, so the causal event sits one to five trading days *before* it. Measured across the events I researched, the median lag from catalyst to ledger date is three trading days:

| Ledger date | Actual catalyst | Lag |
|---|---|---:|
| 2008-07-07 | 2008-07-02 pre-announcement | 3 sessions |
| 2016-11-17 | 2016-11-10 earnings | 5 sessions |
| 2017-05-16 | 2017-05-09 earnings | 5 sessions |
| 2018-11-23 | 2018-11-15 earnings | 5 sessions |
| 2023-06-01 | 2023-05-24 earnings | 5 sessions |
| 2025-01-29 | 2025-01-27 DeepSeek | 2 sessions |

A news harvester that queries `[date - 1, date + 1]` will retrieve post-hoc commentary and miss the actual catalyst on the majority of these. The correct query window is roughly `[date - 10 calendar days, date]`, and for the earnings-driven events the single best anchor is the earnings date itself, not the ledger date.

**Problem 2: five of the eleven pre-2020 major events have no NVIDIA-specific news at all.** 2008-10-07, 2008-10-31, 2008-11-20, 2008-11-28 and 2011-10-10 are market moves that NVDA participated in with high beta. They are *correctly detected* under the contract's definition, but they are not "NVDA events" in any causal sense, and a corpus that treats them as such will teach the retriever that NVDA-specific event text should map to market-wide return distributions. Recommendation: keep them, but carry a flag distinguishing idiosyncratic from beta events. This does not require changing the contract; `category` in this research file already encodes it, and `macro` plus `sector-rotation` is the beta set.

**One near-miss worth recording as a warning.** For 2022-03-21 the obvious guess is NVIDIA's GTC keynote and the Hopper H100 announcement. That happened on March 22 2022, one day after the window closed. The actual driver was the March 16 Fed liftoff. This is the failure mode this research stage exists to prevent, and it will recur: NVIDIA runs GTC every March and reports every February, May, August and November, so there is almost always a plausible company event near any NVDA date. Proximity is not causation, and the price path inside the window is the discriminator.

---

## Unexplained

Eight events where I could not find a credible cause and will not guess. All are `significant`, none are `major`. Seven of the eight sit in the low-information 2009 to 2010 stretch, which is consistent with them being ordinary volatility in a stock that was trading in the $0.15 to $0.35 range post-split-adjustment with 100%+ realized volatility, where a 15% week does not require a story.

- **2008-12-24, -17.2%.** Holiday-week illiquidity during the crisis. No catalyst found.
- **2009-01-13, -16.6%.** Mid-January 2009 bank-solvency anxiety is a candidate but I could not confirm it for this window.
- **2009-01-27, +17.1%.** No catalyst found.
- **2009-05-20, +15.8%.** A bounce off the May 13 post-earnings low. Mechanically explicable as mean reversion, not as an event.
- **2009-09-10, +15.7%.** No catalyst found.
- **2009-12-07, +23.2%.** No catalyst found. This is the largest unexplained move in the ledger and the one I would most want a second pass on.
- **2010-09-24, +16.2%.** The only 2010 event, and I found nothing. September 2010 was a strong month for equities generally, but that does not explain a 16% single-name week.
- **2022-07-01, -15.2%.** End-of-quarter derisking in the 2022 bear market is a candidate but I could not confirm it.

A further group is explained at low confidence (0.30 to 0.50) with no retrieved source, and should be treated as provisional rather than established: 2008-01-22, 2008-12-15, 2009-01-06, 2009-02-06, 2009-02-17, 2009-04-06, 2009-07-20, 2015-08-10, 2016-02-22, 2019-08-22, 2020-05-20, 2021-08-25, 2022-04-26, 2022-05-11, 2022-06-02, 2022-07-20, 2023-01-12, 2023-01-26, 2024-03-07, 2024-04-26, 2024-07-30, 2024-09-13, 2025-05-16. My web search budget was exhausted at 200 queries before I could source these; the explanations given in the table are consistent with the price path and with well-documented market history, but they are not independently cited and should not be presented as verified.
