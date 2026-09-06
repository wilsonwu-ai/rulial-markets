# BA — event research

**Ticker:** BA (The Boeing Company, NYSE), duopoly commercial aircraft OEM plus a defense and space arm.

**What actually drives the stock.** Boeing is not a normal industrial. Its revenue is a long-dated
backlog of aircraft orders, so the equity trades less on the current quarter than on two things:
(1) the market's belief about *air travel demand five years out*, and (2) whether Boeing can
physically deliver airplanes. That makes it a high-beta proxy for global travel demand and a
single-name credit story, because the company carries the balance sheet of a manufacturer whose
cash conversion depends on handing over finished jets. Layered on top of the cycle are three
company-specific overhangs that recur across this ledger: the 787 Dreamliner development delays
(2007-2011), the 737 MAX grounding (March 2019 to November 2020), and periodic labour and
supplier disruption. The combination means BA can drop 30 percent in a week on a macro shock,
and can also drop 8 percent in a day on a documentation letter from the FAA.

**One structural caveat up front.** Boeing's last stock split was a 2-for-1 in June 1997, well
before the earliest event in this ledger. There is no split artifact anywhere in this window.

## Ledger reproduction check (anchor)

Before researching causes I re-derived every ledger row directly from `data/prices/BA.csv`
using `close[t] / close[t-5] - 1`. All 29 rows reproduce to six decimal places. Examples:

| date | ledger `move_pct` | recomputed | base date (t-5) |
|---|---|---|---|
| 2008-10-10 | -0.223481 | -0.223481 | 2008-10-03 |
| 2008-11-03 | +0.247639 | +0.247639 | 2008-10-27 |
| 2020-03-17 | -0.462621 | -0.462621 | 2020-03-10 |
| 2020-03-26 | +0.847815 | +0.847815 | 2020-03-19 |
| 2020-04-02 | -0.317253 | -0.317253 | 2020-03-26 |
| 2020-06-08 | +0.522558 | +0.522558 | 2020-06-01 |
| 2025-04-04 | -0.211875 | -0.211875 | 2025-03-28 |

The price series has no missing trading days across any event window, and no anomalous single
prints. The detection is arithmetically clean. The question is whether it is *semantically*
clean, which is what the rest of this file is for.

## Every event examined

29 rows, 4 major and 25 significant.

| date | move | tier | category | headline | conf |
|---|---|---|---|---|---|
| 2008-10-10 | -22.3% | significant | macro | Worst week of the global financial crisis | 0.60 |
| 2008-11-03 | +24.8% | significant | crisis | Machinists ratify contract, ending the 8-week strike, into the late-October market bounce | 0.75 |
| 2008-11-11 | -18.0% | significant | macro | Post-election GFC selloff | 0.55 |
| 2009-01-06 | +15.8% | significant | unexplained | New-year rally, no BA-specific catalyst found | 0.30 |
| 2009-03-03 | -17.2% | significant | macro | Slide into the March 2009 bear-market bottom | 0.55 |
| 2009-03-26 | +16.5% | significant | unexplained | March 2009 bottom bounce, no BA-specific catalyst found | 0.35 |
| 2009-06-05 | +17.4% | significant | unexplained | Reflation rally, no BA-specific catalyst confirmed | 0.35 |
| 2009-08-27 | +15.8% | significant | product | Boeing publishes revised 787 schedule, first flight by end of 2009 | 0.80 |
| 2011-08-08 | -16.5% | significant | macro | S&P strips the US of its AAA rating, Black Monday 2011 | 0.75 |
| 2020-02-28 | -16.7% | significant | macro | First COVID-19 crash week, airlines hit hardest | 0.80 |
| 2020-03-09 | -21.5% | significant | macro | Oil price war plus COVID, circuit-breaker Monday | 0.60 |
| 2020-03-17 | **-46.3%** | **major** | crisis | Boeing asks Washington for $60bn, market reads it as distress | 0.90 |
| 2020-03-26 | **+84.8%** | **major** | macro | CARES Act passes the Senate, largest one-day gain in BA history | 0.90 |
| 2020-04-02 | **-31.7%** | **major** | macro | The bailout rally unwinds, S&P cuts Boeing to BBB- | 0.80 |
| 2020-04-09 | +23.2% | significant | macro | Fed's $2.3tn facilities plus the "flattening curve" week | 0.75 |
| 2020-04-24 | -16.2% | significant | crisis | Embraer tie-up collapses, oil goes negative, off a spiked base | 0.55 |
| 2020-06-08 | **+52.3%** | **major** | macro | Reopening melt-up, May payrolls shock, sell-side upgrades | 0.85 |
| 2020-06-15 | -17.2% | significant | macro | June 11 second-wave selloff and the Fed's grim 2020 forecast | 0.80 |
| 2020-11-10 | +22.8% | significant | macro | Pfizer vaccine efficacy readout | 0.90 |
| 2020-11-19 | +16.4% | significant | regulatory | FAA ungrounds the 737 MAX after 20 months | 0.85 |
| 2021-03-12 | +20.6% | significant | macro | Stimulus signing plus the vaccine-era travel-recovery trade | 0.70 |
| 2022-03-07 | -17.6% | significant | geopolitical | Ukraine invasion, oil spike, Russian titanium supply cut | 0.75 |
| 2022-04-29 | -15.9% | significant | earnings | Q1 2022 loss, $1.2bn of defense charges including Air Force One | 0.85 |
| 2022-05-12 | -18.2% | significant | guidance | 777X slips to 2025 with $1.5bn of cost, 787 deliveries still halted | 0.75 |
| 2022-06-02 | +15.1% | significant | unexplained | Late-May rebound, no BA-specific catalyst confirmed | 0.35 |
| 2022-06-13 | -16.8% | significant | macro | May CPI shock and the pre-FOMC crash | 0.65 |
| 2022-06-21 | +18.0% | significant | macro | Rebound off the June 2022 low | 0.55 |
| 2022-11-08 | +18.3% | significant | guidance | First investor day since 2018, free cash flow guidance above consensus | 0.85 |
| 2025-04-04 | -21.2% | significant | geopolitical | "Liberation Day" tariffs and Chinese retaliation | 0.85 |

---

## Major events

### 2020-03-17, -46.3% (window 2020-03-11 to 2020-03-17)

**What happened.** On March 17, 2020 Boeing confirmed it was seeking at least $60bn in US
government support for itself and the aerospace supply chain, framed as "public and private
liquidity, including loan guarantees" covering roughly 17,000 suppliers. Inside the same window
Boeing had already drawn down its full revolving credit facility, and on March 20 it suspended
the dividend and share buybacks and the CEO and chairman gave up their pay for the year.

**Why it moved.** A bailout request is a solvency signal. Until that week the market was pricing
BA as a cyclical with a temporary demand hole on top of the MAX grounding. Asking for federal
liquidity reframed the question from "how bad is 2020 earnings" to "does this company make it
through the year without dilution or state ownership," and the equity repriced accordingly.
Shares closed below $100 for the first time in seven years against a 52-week high of $398.66.
This is the largest single drawdown in the entire BA ledger and it is a *company-specific credit
event embedded inside a macro crash*, which is why it is far larger than the market's own move.

**Sources**
- [Forbes: Boeing Seeks $60 Billion Bailout For U.S. Aerospace](https://www.forbes.com/sites/jeremybogaisky/2020/03/17/boeing-seeks-60-billion-bailout-for-us-aerospace/)
- [Fortune: Boeing stock plunges after coronavirus bailout quest spooks investors](https://fortune.com/2020/03/18/coronavirus-boeing-stock-ba-share-price-bailout-request/)
- [HeraldNet: Boeing tumbles 17% after seeking $60B for aerospace bailout](https://www.heraldnet.com/business/boeing-tumbles-after-seeking-60-billion-government-bailout/)

### 2020-03-26, +84.8% (window 2020-03-20 to 2020-03-26)

**What happened.** The Senate passed the $2 trillion CARES Act 96-0 late on March 25, 2020. The
bill contained a $500bn fund for loans and loan guarantees to large employers, roughly $17bn of
which was widely reported as earmarked for businesses critical to national security, understood
at the time to mean Boeing, plus about $50bn for passenger airlines. BA rose 24.3 percent on
March 24 alone on the expectation of passage, its largest one-day gain on record, then added
roughly 12 percent on March 25 and 14 percent on March 26.

**Why it moved.** This is the exact mirror image of the March 17 event, and that is the point.
The March 17 crash priced a non-trivial probability of insolvency or forced nationalisation. The
CARES Act removed the tail. When a stock is trading on survival probability rather than earnings,
resolving the survival question produces a move whose size has no relationship to the change in
fundamental cash flows. Nothing about 2020 aircraft demand improved during this week.

**Sources**
- [TheStreet: Boeing Extends Historic Gains, But Bailout Questions Persist After Senate Passes $2 Trillion CARES Act](https://www.thestreet.com/investing/boeing-extends-historic-gain-but-bailout-questions-persist)
- [Nasdaq: Why Boeing Stock Barreled 15% Higher on Today's Coronavirus Stimulus](https://www.nasdaq.com/articles/why-boeing-stock-barreled-15-higher-on-todays-coronavirus-stimulus-2020-03-26)
- [Quartz: Boeing, cruise lines lead stock market rally as $2 trillion in stimulus nears](https://qz.com/1825549/boeing-cruise-lines-lead-stock-market-rally-as-stimulus-nears)
- [CNN Politics: Boeing could receive billions from stimulus package](https://www.cnn.com/2020/03/25/politics/boeing-bailout/index.html)

### 2020-04-02, -31.7% (window 2020-03-27 to 2020-04-02)

**What happened.** The base of this window is the March 26 peak, so mechanically this event is
the unwind of the CARES rally. Two things drove it. First, S&P cut Boeing's credit rating to
BBB-, one notch above junk and the lowest rating on Boeing's debt since 1981, citing the
coronavirus hit to aircraft demand and an uncertain recovery path. Second, Boeing launched a
voluntary layoff programme and the market began to price the possibility that grounded aircraft
would be permanently retired rather than replaced. Boeing fell about 12 percent on April 1 alone.
Boeing lost 45.8 percent over March 2020 as a whole.

**Why it moved.** Once the survival question was answered by CARES, the market went back to the
demand question and did not like the answer. The near-junk rating matters more for Boeing than
for a typical industrial because the company funds working capital across a multi-year build
cycle. A downgrade raises the cost of the very liquidity it just secured, and constrains the
investor base that can hold the debt.

**Sources**
- [CNN Business live: S&P downgrades Boeing to near junk bond status](https://edition.cnn.com/business/live-news/stock-market-news-043020/h_7b975e57c8933a9a33a8d563f9384117)
- [Motley Fool: Why Shares of Boeing Lost Nearly Half Their Value in March](https://www.fool.com/investing/2020/04/01/why-shares-of-boeing-lost-nearly-half-their-value.aspx)
- [Nasdaq mirror of the same piece](https://www.nasdaq.com/articles/why-shares-of-boeing-lost-nearly-half-their-value-in-march-2020-04-01)

### 2020-06-08, +52.3% (window 2020-06-02 to 2020-06-08)

**What happened.** The May 2020 US employment report, released June 5, showed payrolls rising
instead of falling, which the market read as evidence the recovery had already begun. Reopening
and travel names ran hard. Boeing gained roughly 40 percent in the week to June 5 and another
12 percent on June 8. Sell-side flow reinforced it: Seaport Global initiated coverage with a buy
rating, noting Boeing historically outperforms other industrials early in a recovery, and Goldman
Sachs reiterated buy and lifted its target from $209 to $238 on analysis that airlines had cut
2020-2021 delivery plans by only about 17 percent, far less than feared.

**Why it moved.** BA at this point was a levered call option on the shape of the travel recovery.
The June 5 payrolls print did not change 2020 aircraft deliveries at all. It changed the
discount the market applied to the *scenario* in which travel normalised quickly, and because BA
had been priced for the slow scenario, that repricing was violent. The Goldman note is the
cleanest statement of the mechanism: the fundamental input that moved was airline delivery
deferrals, and it moved less than consensus had assumed.

**Sources**
- [Motley Fool: Why Shares of Boeing Are Rallying Today (June 8, 2020)](https://www.fool.com/investing/2020/06/08/why-shares-of-boeing-are-rallying-today.aspx)
- [Investing.com: Boeing Stock Rally Gathers Pace As Economy Reopens](https://www.investing.com/analysis/boeing-stock-rally-gathers-pace-as-economy-reopens-200585185)

---

## Selected significant events

### 2008-11-03, +24.8% — the strike ends

The IAM machinists' strike that began September 7, 2008 and idled roughly 27,000 workers was
settled by a tentative agreement in late October and ratified November 1, 2008 by 74 percent of
voters. The strike cost Boeing about $100 million per day in revenue and delivery penalties. The
window also contains the late-October 2008 market rebound, so this is a genuine two-cause event:
a company-specific supply restart landing on top of a violent bear-market bounce. That
combination is what pushes a 2008 industrial past 24 percent in a week.

**Sources**
- [Wikipedia: 2008 Boeing machinists' strike](https://en.wikipedia.org/wiki/2008_Boeing_machinists_strike)
- [Seattle Times: Machinists return to work at an unsettled Boeing after 8-week strike](https://www.seattletimes.com/business/boeing-aerospace/machinists-return-to-work-at-an-unsettled-boeing-after-8-week-strike/)

### 2009-08-27, +15.8% — the 787 gets a date

Boeing published an updated 787 schedule on August 27, 2009 putting first flight by the end of
2009 and first delivery at the end of 2010, after the June 23, 2009 postponement for structural
reasons. BA rose 8.4 percent on August 27 itself, from $47.82 to $51.82, which is the single
largest day in the window and pins the cause to the announcement rather than to the market. This
is the cleanest purely company-specific event in the pre-2019 half of the ledger.

**Sources**
- [Wikipedia: Boeing 787 Dreamliner (program schedule history)](https://en.wikipedia.org/wiki/Boeing_787_Dreamliner)

### 2011-08-08, -16.5% — the US loses its AAA

Standard & Poor's downgraded US sovereign debt from AAA to AA+ on August 5, 2011, and on the
next trading day, August 8, the S&P 500 fell 6.5 percent. BA is a high-beta industrial with heavy
US government defense exposure, so it fell roughly two and a half times the index over the
window. No Boeing-specific news is required to explain this one.

**Sources**
- [Wikipedia: Black Monday (2011)](https://en.wikipedia.org/wiki/Black_Monday_(2011))
- [NPR: S&P Lowers United States Long-Term Rating](https://www.npr.org/sections/thetwo-way/2011/08/06/139038762/s-p-lowers-united-states-long-term-rating)
- [CNN Money: S&P downgrades U.S. credit rating](https://money.cnn.com/2011/08/05/news/economy/downgrade_rumors/index.htm)

### 2020-02-28, -16.7% — the first COVID week

The week of February 24-28, 2020 was the first broad COVID-19 repricing. Airline stocks were hit
hardest of any group, many down more than 25 percent year to date by that Friday, and BA fell
more than 5 percent on February 28 alone. Because Boeing's demand is airline capital
expenditure, airline equity weakness transmits to BA almost mechanically. The 737 MAX grounding
was still live, which removed any valuation cushion.

**Sources**
- [Motley Fool: Why Boeing Shares Are Down Today (February 28, 2020)](https://www.fool.com/investing/2020/02/28/why-boeing-shares-are-down-today.aspx)

### 2020-04-09, +23.2% — the Fed backstop week

Over April 6-9, 2020 the Dow gained 12.67 percent and the S&P 500 12.10 percent, on the
combination of the Fed announcing facilities supporting up to $2.3 trillion of credit (April 9,
including the Main Street Lending Program) and evidence that infection curves were peaking in
Italy and New York. BA rose from $124.52 to $151.84 across the window. Same mechanism as the
CARES event: credit-risk compression, not demand news.

**Sources**
- [Al Jazeera: US markets rise on Fed intervention](https://www.aljazeera.com/economy/2020/4/9/us-markets-rise-on-fed-intervention)
- [Congressional Research Service R46411: The Federal Reserve's Response to COVID-19](https://www.congress.gov/crs-product/R46411)

### 2020-04-24, -16.2% — a partly mechanical event

This window bases off April 17, 2020, when BA jumped 14.7 percent in a day on broad
risk-on flow, and ends April 24. Inside it: WTI crude traded negative on April 20, and Boeing
terminated its $4.2bn Master Transaction Agreement with Embraer, with April 24 as the stated
termination date and the announcement on April 25. Embraer publicly said Boeing had "wrongfully
terminated" the deal. I flag this event as partly a base artifact. Roughly half the move is the
decay of an outsized single-day spike at the start of the window rather than fresh bad news.
Confidence is set at 0.55 for that reason.

**Sources**
- [Boeing: Boeing Terminates Agreement to Establish Joint Ventures with Embraer (April 25, 2020)](https://boeing.mediaroom.com/2020-04-25-Boeing-Terminates-Agreement-to-Establish-Joint-Ventures-with-Embraer)
- [CNBC: Brazil's Embraer says Boeing 'wrongfully terminated' deal](https://www.cnbc.com/2020/04/25/boeing-terminates-joint-venture-agreement-with-brazils-embraer.html)

### 2020-06-15, -17.2% — the second-wave scare

On June 11, 2020 the S&P 500 fell 5.89 percent and the Dow fell more than 1,800 points, the worst
day in three months, on second-wave case growth plus the Fed's June 10 projection that the US
economy would shrink 6.5 percent in 2020. Airlines, cruise lines and retailers led the decline.
BA fell from $203.41 to $170.00 on June 11 alone. This event and the June 8 event are the same
trade being put on and taken off inside eight trading days.

**Sources**
- [Motley Fool: Why Boeing, Triumph Group, and Spirit AeroSystems fell (June 10-11, 2020)](https://www.fool.com/investing/2020/06/10/time-sensitive-why-boeing-triumph-group-and-spirit.aspx)

### 2020-11-10, +22.8% — the Pfizer readout

Pfizer and BioNTech reported interim Phase 3 efficacy above 90 percent on November 9, 2020. BA
rose 13.7 percent that day and another 5.2 percent on November 10. This is the single highest
confidence macro attribution in the ledger, because the catalyst is a dated, unambiguous,
non-financial announcement and the sector response was uniform across every travel name.

**Sources**
- [CNBC: Airlines, Boeing surge on upbeat coronavirus vaccine news](https://www.cnbc.com/2020/11/09/airlines-surge-on-upbeat-vaccine-news-american-jumps-19percent-.html)

### 2020-11-19, +16.4% — the MAX flies again

On November 18, 2020 the FAA rescinded the grounding order on the 737 MAX, 20 months after the
March 2019 grounding that followed two crashes killing 346 people. The window also contains the
November 16 Moderna vaccine readout, so this is again a two-cause event, but the regulatory item
is BA-specific and is the reason BA outperformed the broader travel complex that week.

**Sources**
- [Boeing: Boeing Responds to FAA Approval to Resume 737 MAX Operations (Nov 18, 2020)](https://boeing.mediaroom.com/2020-11-18-Boeing-Responds-to-FAA-Approval-to-Resume-737-MAX-Operations)
- [Washington Post: Boeing 737 Max ungrounded by FAA 20 months after deadly crashes](https://www.washingtonpost.com/local/trafficandcommuting/boeing-737-max-ungrounded/2020/11/18/c4d6c1a8-2902-11eb-8fa2-06e7cbb145c0_story.html)

### 2021-03-12, +20.6% — the reopening trade

The window covers March 8-12, 2021, the peak of the vaccine-era reflation trade. Airline shares
were rallying from March 8 on vaccine rollout, TSA throughput was running above the prior year
for the first time since the pandemic began, and the American Rescue Plan (signed March 11, 2021)
contained another round of airline payroll support. The Southwest order for 100 MAX 7s that is
sometimes attached to this move actually landed on March 29, 2021, outside the window, and is
**not** the cause here. Confidence 0.70 because the attribution is sectoral rather than
company-specific.

**Sources**
- [CNBC: Air travel jumps as vaccinations spur vacation bookings, stocks surge (March 15, 2021)](https://www.cnbc.com/2021/03/15/air-travel-recovers-as-vaccinations-spur-bookings.html)
- [PR Newswire: Southwest Airlines Adds 100 Firm Orders For The Boeing 737 MAX 7 (March 29, 2021, outside the window)](https://www.prnewswire.com/news-releases/southwest-airlines-adds-100-firm-orders-for-the-boeing-737-max-7-301257190.html)

### 2022-03-07, -17.6% — the invasion window

BA fell 6.5 percent on March 7, 2022 and slid every day of the window. Two channels: the general
risk-off and oil spike following Russia's invasion of Ukraine, which raises airline fuel costs
and therefore threatens fleet capex, and a direct supply-chain hit. On March 7, 2022 Boeing
suspended purchases of titanium from VSMPO-Avisma, its largest titanium supplier, four months
after renewing the contract at the Dubai Airshow. Boeing also suspended parts and maintenance
support for Russian airlines and its Moscow operations.

**Sources**
- [CNBC: Boeing suspends buying titanium from Russia, assures of 'sufficient supply'](https://www.cnbc.com/2022/03/07/boeing-suspends-buying-titanium-from-russia-assures-of-sufficient-supply.html)
- [RTE: Boeing suspends buying titanium from Russia](https://www.rte.ie/news/business/2022/0307/1284924-boeing-suspends-titanium-deals-from-russia/)

### 2022-04-29, -15.9% — the only clean earnings event

Boeing reported Q1 2022 on April 27, 2022: a $1.2bn quarterly loss on $14bn of revenue,
including a $660m charge on the VC-25B Air Force One programme and a $367m charge on the T-7A
Red Hawk, both driven by supplier costs, requirement changes and schedule slippage. Cumulative
Air Force One losses reached about $1.1bn and management warned of more to come. BA fell 8.1
percent on the earnings day itself, which is what makes this the one unambiguously
earnings-driven event in the whole BA ledger.

**Sources**
- [CNBC: Boeing lost $1.1 billion on Trump Air Force One contract; CEO regrets deal](https://www.cnbc.com/2022/04/27/boeing-lost-billion-dollars-on-trump-air-force-one-plane-deal.html)
- [UPI: Boeing loses $1.2B in first quarter, including $660M on Air Force One](https://www.upi.com/Top_News/US/2022/04/27/boeing-reports-loss-first-quarter-2022-Air-Force-One/5071651085696/)
- [Breaking Defense: Boeing adds $1B in new charges for Air Force One replacement, T-7 Red Hawk programs](https://breakingdefense.com/2022/04/boeing-adds-1b-in-new-charges-for-air-force-one-replacement-t-7-red-hawk-programs/)

### 2022-05-12, -18.2% — programme slippage compounding

BA fell 11.7 percent across May 2022 while the S&P 500 was roughly flat, so this is genuinely
idiosyncratic. Inside the window: first delivery of the 777X was pushed to 2025 with an
additional $1.5bn of cost, the FAA told Boeing its 787 delivery-approval documentation was
incomplete so 787 deliveries stayed halted, and customers went public with criticism, with
Avolon's CEO saying Boeing had "lost its way" and Ryanair's Michael O'Leary saying management was
"not up to the job." Each item is individually small. The mechanism is that after the MAX
grounding the market had no confidence buffer left, so ordinary programme slippage was priced as
evidence of structural incompetence.

**Sources**
- [Motley Fool: Why Shares in Boeing Slumped in May (June 3, 2022)](https://www.fool.com/investing/2022/06/03/why-shares-in-boeing-slumped-in-may/)

### 2022-11-08, +18.3% — guidance returns

Boeing held its first investor day since 2018 on November 2, 2022 and issued forward free cash
flow guidance for the first time since early 2019: $1.5-2bn for 2022 against consensus of about
$670m, $3-5bn for 2023, and roughly $10bn of normalised free cash flow on $100bn of revenue by
2025-2026. Shares rose 4.7 percent that day and continued higher through the window on a
supportive market tape.

**Why it moved.** Guidance itself was the event. For three and a half years Boeing had refused to
give forward numbers, which forced every model to be built on analyst assumption. Restoring
guidance compressed the dispersion of estimates, and for a stock trading on scenario weights that
is worth more than the guidance level.

**Sources**
- [Seeking Alpha: Boeing advances after providing free cash flow update at investor day](https://seekingalpha.com/news/3899755-boeing-advances-after-providing-free-cash-flow-update-at-investor-day)
- [Benzinga: Boeing forecasts up to $5B free cash flow in 2023, $10B by mid-decade, shares pop](https://www.benzinga.com/news/large-cap/22/11/29528577/boeing-forecasts-upto-5b-free-cash-flow-in-2023-10b-by-mid-decade-shares-pop)
- [Benzinga: Boeing Hosted Its First Investor Day In 4 Years After 737 MAX Debacle](https://www.benzinga.com/analyst-ratings/analyst-color/22/11/29549846/boeing-hosted-its-first-investor-day-in-4-years-and-the-company-made-a-statement-wh)

### 2025-04-04, -21.2% — Liberation Day

President Trump announced a broad package of import duties on April 2, 2025. Markets fell hard on
April 3 and 4 as China announced retaliation. Boeing fell 8.3 percent on Friday April 4 alone,
to $136.59, a two-and-a-half year low. BA is unusually exposed to this specific shock because it
is the largest single US exporter by value and China is one of its largest end markets, so a
tariff war is both a cost shock and a direct order-book threat. The stock subsequently recovered
54 percent by early June 2025 as tariff negotiations progressed.

**Sources**
- [Seeking Alpha: Boeing tanks to two-and-a-half-year low, swept up in Trump's tariff selloff](https://seekingalpha.com/news/4428824-boeing-tanks-to-two-and-a-half-year-low-swept-up-in-trumps-tariff-selloff)
- [Wikipedia: Liberation Day tariffs](https://en.wikipedia.org/wiki/Liberation_Day_tariffs)
- [Forbes: Boeing Stock Surges 54% On Trump Tariff Chaos](https://www.forbes.com/sites/robertdaugherty/2025/06/07/boeing-stock-surges-54-on-trump-tariff-chaos-the-dj-taco-trade/)

### Lower-confidence macro attributions

These four are stated from general market knowledge of the relevant week. I did not retrieve a
source URL for each in this pass, so they should be treated as provisional and verified before
they are used as labelled training examples.

- **2008-10-10, -22.3%.** The week of October 6-10, 2008 was the worst week in Dow history. No
  Boeing-specific catalyst is required, and the strike was still in progress, which compounds it.
- **2008-11-11, -18.0%.** The post-election GFC selloff. The base is November 4, election day,
  which was a local high.
- **2009-03-03, -17.2%.** The final slide into the March 6, 2009 bear-market low.
- **2020-03-09, -21.5%.** The Saudi-Russia oil price war weekend followed by the March 9 limit-down
  open and first circuit breaker, layered on accelerating COVID case growth.
- **2022-06-13, -16.8%.** The May 2022 CPI print on June 10 came in above expectations and the
  market sold off into the June 15 FOMC, which delivered 75bp. BA fell 8.8 percent on June 13.

---

## Regime

**BA lives in a macro-and-credit regime, not an earnings regime.** Of 29 detected events, exactly
one (2022-04-29) is driven by a quarterly results release. Two more (2022-05-12, 2022-11-08) are
guidance events, and one (2020-11-19) is regulatory. Everything else is either a market-wide
shock transmitted through a high-beta industrial, or a company-specific *liquidity/credit* event.
This is unusual and it matters for analog retrieval: an event description phrased as an earnings
surprise has almost no historical support in this ticker.

**Three distinguishable sub-regimes, and analogs do not transfer across them.**

1. **Crisis-beta (2008-10 to 2009-08, 2011-08, 2020-02 to 2020-06, 2025-04).** BA is a leveraged
   proxy on the market. Moves are driven by systemic risk pricing, and the BA-specific component
   is amplification, not causation. Roughly two-thirds of the ledger.
2. **Survival repricing (2020-03-17 through 2020-06-08).** The distinct and much more violent
   sub-regime. When solvency probability is the pricing variable, moves of 30 to 85 percent in a
   week are generated by *news about financing*, not news about airplanes. All four major-tier
   events sit here. This is the tail that makes BA interesting and it is also, critically, a
   regime that only existed for about 12 weeks in 60 years of price history.
3. **Programme execution (2009-08-27, 2020-11-19, 2022-04-29, 2022-05-12, 2022-11-08).**
   Idiosyncratic, 15 to 18 percent, driven by whether Boeing can build and deliver aircraft and
   whether regulators will let it. This is the only sub-regime where a "Boeing announces X"
   event description has real analog support.

**Concentration warning for the seed corpus.** 10 of 29 events (34 percent) fall inside 2020, and
all 4 major-tier events fall inside a 12-week span from 2020-03-17 to 2020-06-08. Under the
contract's `TRAIN_END = 2019-12-31`, the train-period BA ledger is **9 events, of which 8 are
2008-2009 GFC and 1 is the August 2011 US downgrade**. That is one regime wearing nine hats, and
it is the same failure mode the contract already flags for JPM. BA contributes almost nothing
usable to a pre-2020 seed corpus beyond "high-beta industrial in a systemic crisis."

**Directional asymmetry worth noting.** Down-events cluster tighter (14 events, mean -19.4
percent) than up-events (15 events, mean +27.4 percent), and the up-tail is driven entirely by
the 2020 policy-response rebounds. An ensemble generator fitted on BA analogs will inherit a
fat right tail that is really a fat *policy-response* tail, and it will fire that tail
inappropriately unless the conditioning text distinguishes "government intervenes" from "demand
recovers."

---

## Ledger verdict

**The detection survives contact with reality.** 25 of 29 dates map to an event a human market
participant would name without hesitation, and 20 of those have a retrieved source URL. Four
dates I could not attribute and I have listed them honestly below rather than guessing.

Specifically:

- **Arithmetic is clean.** All 29 `move_pct` values reproduce exactly from the price file using
  `close[t]/close[t-5] - 1`. No rounding drift, no off-by-one on the window.
- **No split artifacts.** Boeing's last split was June 1997, before the ledger's first event.
- **No missing-day artifacts.** Every event window is 5 consecutive trading rows with no gaps.
- **No bad prints.** Every extreme close is corroborated by contemporaneous reporting. The
  2020-03-26 close of $180.55 against a 2020-03-19 close of $97.71 is real and is documented as
  the largest one-day gain in the company's history followed by two more double-digit days.
- **The `famous` flag is well calibrated.** Every row flagged famous is genuinely a recognisable
  public event. The one arguable miss is 2025-04-04 (`famous: false`), which is the Liberation
  Day tariff crash and is about as famous as a 2025 market event gets. Similarly 2008-11-03
  (`famous: false`) sits on the end of the machinists' strike, which is famous inside aerospace
  if not to a general audience. This matters because the contract's §8 leakage disclosure relies
  on the famous/obscure split to detect memorisation, and mislabelling a famous event as obscure
  weakens that test. **Recommend LANE-EVENTS review the `famous` heuristic for these two rows.**

**One genuine quality caveat, not a defect.** The 5-day window means an event's magnitude is
sensitive to what the base day did. 2020-04-24 is the clearest case: about half its -16.2 percent
is the decay of a +14.7 percent single-day spike on the base date (2020-04-17) rather than fresh
negative news. 2022-06-21 has the mirror problem, basing off the CPI-crash low. These are not
detection errors under the stated definition, but any downstream lane treating a ledger date as
"the day the news landed" will be wrong for these two. The causal news for a BA event typically
lands 1 to 5 trading days *before* the ledger date, and in the four major events it lands
1 to 2 days before.

**Fitness as a seed ticker: mixed, and worse under the train cutoff than it looks.** Post-2020
BA is a rich and varied corpus. Pre-2020 BA, which is all the contract permits for seeding, is
9 events and effectively one regime. Use BA for its test-period behaviour and for the
survival-repricing tail, but do not expect its train-period events to teach the retriever
anything a JPM or XOM GFC event does not already teach.

---

## Unexplained

Listed honestly. In each case I could not find a Boeing-specific catalyst inside the window, and
the market-wide explanation I could offer would be generic enough that asserting it would be a
guess dressed as a finding. These should carry no headline in the corpus.

- **2009-01-06, +15.8%** (window 2008-12-30 to 2009-01-06). The first days of 2009 saw a broad
  rally off the December lows, but I found no dated Boeing catalyst and no source confirming why
  BA specifically outperformed. The rise was gradual across the window with no single dominant day.
- **2009-03-26, +16.5%** (window 2009-03-19 to 2009-03-26). Sits inside the March 2009 bottom
  bounce. Plausible candidates exist (the March 23 Geithner PPIP announcement, quarter-end flows)
  but I retrieved no source tying any of them to Boeing, and no Boeing announcement in the window.
- **2009-06-05, +17.4%** (window 2009-05-29 to 2009-06-05). The move built steadily over five
  days rather than on one catalyst. The May 2009 payrolls report on June 5 is a candidate, and the
  787 programme was in the run-up to a planned first flight, but I could not confirm either as the
  driver and my web search budget was exhausted before I could verify the 787 timeline for that
  specific week.
- **2022-06-02, +15.1%** (window 2022-05-25 to 2022-06-02). A late-May 2022 broad-market rebound
  off the mid-May low. No Boeing announcement located in the window. Reports of progress on the
  MAX's return to service in China circulated around this period but I did not retrieve a source
  dating any such report inside this window, so I am not asserting it.

**Search-budget disclosure.** This session exhausted its 200-call web search budget. The four
unexplained events above and the five lower-confidence macro attributions in the previous section
are the ones that would benefit most from a second research pass, in that priority order.
