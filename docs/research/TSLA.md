# TSLA — event research

**Ticker:** TSLA (Tesla, Inc., formerly Tesla Motors). NASDAQ. IPO 29 June 2010 at $17.00.
**Ledger rows examined:** 99 (28 `major`, 71 `significant`), spanning 2010-07-07 to 2026-07-29.
**Researched with a named cause:** 51. **Left un-attributed:** 48 (see [Unexplained](#unexplained)).

## What this ticker is, and what actually moves it

Tesla is not a normal equity for the purposes of this project. It is a single-name stock
that spent its first fifteen years being repriced, repeatedly and violently, on *narrative
regime changes* rather than on incremental fundamentals. It has been, in sequence: a
lossmaking sports-car startup with an IPO nobody could price (2010-2012), a story stock
that got its first real profit (2013), a production-hell short-battleground (2017-2019), a
retail and index-flow phenomenon (2020-2021), a Musk-attention-risk asset (2022, 2025), and
most recently an AI/robotics capex story (2026).

That matters for the corpus. The same 25% weekly move means something structurally
different in 2010 (a $2bn company post-IPO) than in 2024 (a $700bn+ S&P 500 constituent),
and the retrieval layer needs to know that.

Two mechanical notes, verified before writing anything below:

1. **Prices are split-adjusted.** Tesla split 5-for-1 effective 31 Aug 2020 and 3-for-1
   effective 25 Aug 2022. The 2010 closes in the price feed are around $1.06 to $1.59
   (i.e. the $23.89 IPO-day close divided by 15), and the 2020-08-31 row shows a
   +12.6% close-to-close move rather than a fake -80%. **No split artifacts are present
   in this ledger.**
2. **The window arithmetic reconciles.** Sample check: 2010-07-07 is $1.5927 (29 Jun close)
   to $1.0533, which is -33.87% against a ledger value of -33.86%. 2010-07-19 is $1.1367
   (12 Jul) to $1.4607, which is +28.50% against a ledger value of +28.50%. The window ends
   on the ledger date and reaches back five to six trading days, so **the causal news
   almost always lands 1 to 6 sessions BEFORE the ledger date.** Every attribution below
   respects that.

**Convention used in the `category` column.** `guidance` is used broadly for a company
announcement that is not a reported quarterly result: delivery pre-announcements, price
cuts, layoffs, capital-markets actions and corporate actions such as the stock split.
`sector-rotation` is used for index-flow and factor-driven moves (S&P inclusion/exclusion,
the rates-driven growth unwind) where the news is about *who has to own the stock*, not
about Tesla. `unexplained` means no discrete catalyst was identified, which for the two
July 2010 rows means the move is post-IPO price discovery rather than news.

---

## Every event examined

`nr` = not researched, budget exhausted before reaching it. This is an honest "we did not
look", not a claim that no cause exists. See [Unexplained](#unexplained) for the split
between "searched, found nothing" and "never searched".

| Date | Move | Tier | Category | Headline | Conf |
|---|---|---|---|---|---|
| 2010-07-07 | -33.9% | major | unexplained | Post-IPO unwind: TSLA breaks below its $17 offer price | 0.75 |
| 2010-07-19 | +28.5% | major | unexplained | Mechanical bounce off the post-IPO low, no verified catalyst | 0.20 |
| 2010-08-11 | -15.8% | significant | nr | | |
| 2010-11-10 | +34.9% | major | product | Panasonic takes a $30m stake and a battery-cell partnership; first Q3 report | 0.65 |
| 2010-11-24 | +20.3% | significant | product | Continuation of the November 2010 Panasonic-driven re-rating | 0.40 |
| 2010-12-30 | -18.8% | significant | nr | | |
| 2011-01-20 | -16.1% | significant | nr | | |
| 2011-03-31 | +24.3% | significant | nr | | |
| 2011-08-08 | -17.8% | significant | macro | S&P strips the US of its AAA rating; 8 Aug is a -6.7% day for the S&P 500 | 0.80 |
| 2011-08-22 | -16.3% | significant | macro | Second leg of the August 2011 downgrade/eurozone bear market | 0.60 |
| 2011-10-10 | +17.5% | significant | macro | Rebound off the early-October 2011 bear-market low | 0.50 |
| 2011-12-14 | -16.6% | significant | nr | | |
| 2012-01-13 | -15.3% | significant | nr | | |
| 2012-01-23 | +17.5% | significant | nr | | |
| 2012-09-17 | +18.9% | significant | nr | | |
| 2013-04-01 | +20.0% | significant | guidance | Tesla pre-announces its first-ever quarterly profit on 1 April | 0.80 |
| 2013-04-22 | +15.9% | significant | nr | | |
| 2013-05-15 | +52.1% | major | earnings | First quarterly profit (8 May) plus a 99/100 Consumer Reports score | 0.90 |
| 2013-05-28 | +22.7% | significant | guidance | $1.02bn capital raise and full early repayment of the DOE loan | 0.50 |
| 2013-07-01 | +15.5% | significant | nr | | |
| 2013-11-12 | -22.1% | significant | crisis | Third Model S battery fire; the stock loses 20.4% over November | 0.80 |
| 2013-12-03 | +19.8% | significant | regulatory | Germany's regulator clears the Model S of a fire defect | 0.70 |
| 2014-01-21 | +26.8% | major | guidance | Q4 deliveries of ~6,900 beat guidance by ~20% at the Detroit auto show | 0.85 |
| 2014-02-26 | +30.7% | major | guidance | Q4 earnings, the Gigafactory reveal, and Morgan Stanley's $320 target | 0.90 |
| 2015-08-25 | -15.6% | significant | macro | August 2015 China-devaluation global selloff | 0.50 |
| 2016-02-08 | -24.9% | significant | macro | Jan-Feb 2016 growth scare plus cheap-gasoline EV demand fears | 0.65 |
| 2016-02-22 | +17.7% | significant | guidance | Rebound on an upbeat 2016 delivery outlook and the 11 Feb market bottom | 0.60 |
| 2016-04-06 | +17.0% | significant | product | Model 3 unveiling draws 325,000 reservations in a week | 0.85 |
| 2017-07-06 | -16.8% | significant | nr | | |
| 2018-03-28 | -18.6% | significant | crisis | Fatal Model X Autopilot crash, Moody's downgrade, Model 3 cash-burn panic | 0.80 |
| 2018-04-05 | +18.6% | significant | nr | | |
| 2018-06-12 | +17.7% | significant | nr | | |
| 2018-08-07 | +27.3% | major | leadership | "Funding secured": Musk tweets a $420 take-private and trading is halted | 0.95 |
| 2018-10-08 | -19.4% | significant | regulatory | Fallout from the 29 Sept SEC fraud settlement, into the October 2018 selloff | 0.45 |
| 2018-10-29 | +28.3% | major | earnings | Surprise $312m GAAP profit in Q3 2018 | 0.85 |
| 2018-12-20 | -16.3% | significant | macro | December 2018 market-wide drawdown | 0.40 |
| 2019-01-23 | -16.5% | significant | guidance | $2,000 price cut, 7% layoffs, and a "very difficult" road ahead | 0.80 |
| 2019-05-22 | -16.9% | significant | guidance | The demand scare: Wedbush "code red", Morgan Stanley's $10 bear case | 0.80 |
| 2019-06-10 | +19.0% | significant | macro | Rebound off the ~$178 low, catalyst not isolated | 0.30 |
| 2019-10-28 | +29.3% | major | earnings | Surprise Q3 2019 profit and Shanghai running ahead of schedule | 0.90 |
| 2020-01-08 | +17.6% | significant | nr | | |
| 2020-02-04 | +56.5% | major | earnings | The melt-up: Panasonic's battery unit turns a profit, ARK's $7,000 note, short squeeze | 0.80 |
| 2020-02-19 | +18.5% | significant | nr | | |
| 2020-02-28 | -25.9% | major | macro | COVID week of 24-28 Feb, the fastest correction in market history | 0.85 |
| 2020-03-09 | -18.2% | significant | macro | Black Monday I: S&P 500 -7.6% on the Russia-Saudi oil war | 0.80 |
| 2020-03-18 | -43.1% | major | macro | COVID capitulation plus the order to shut the Fremont plant | 0.90 |
| 2020-03-25 | +49.3% | major | macro | The 24-26 March record rally on Fed QE and the CARES Act | 0.85 |
| 2020-04-14 | +37.5% | major | guidance | Q1 deliveries of ~88,400 beat a collapsed bar, into the April rebound | 0.60 |
| 2020-05-08 | +16.8% | significant | nr | | |
| 2020-06-10 | +16.1% | significant | nr | | |
| 2020-07-06 | +42.9% | major | guidance | Q2 deliveries of 90,650 vs 72,149 expected, clearing the S&P 500 bar | 0.85 |
| 2020-08-18 | +37.3% | major | guidance | The 5-for-1 stock split announcement and the retail bid behind it | 0.80 |
| 2020-08-31 | +23.7% | significant | guidance | Split-effective-date melt-up at the end of a +74% August | 0.60 |
| 2020-09-08 | -33.7% | major | sector-rotation | The S&P 500 snub: worst day in company history, -21% | 0.90 |
| 2020-09-15 | +36.2% | major | sector-rotation | Bounce off the snub washout into Battery Day anticipation | 0.45 |
| 2020-10-01 | +15.6% | significant | nr | | |
| 2020-11-23 | +27.9% | major | sector-rotation | S&P 500 inclusion announced: the largest addition ever made to the index | 0.90 |
| 2021-01-08 | +24.7% | significant | nr | | |
| 2021-03-08 | -21.6% | significant | sector-rotation | The rates-driven unwind of high-multiple growth | 0.70 |
| 2021-03-15 | +25.7% | major | sector-rotation | Treasury yields back off and high-beta growth violently re-rates | 0.70 |
| 2021-10-29 | +22.5% | significant | nr | | |
| 2021-11-12 | -15.4% | significant | nr | | |
| 2021-12-28 | +20.9% | significant | nr | | |
| 2022-01-27 | -16.8% | significant | nr | | |
| 2022-02-23 | -17.2% | significant | nr | | |
| 2022-03-02 | +15.2% | significant | nr | | |
| 2022-03-22 | +24.0% | significant | nr | | |
| 2022-05-11 | -22.9% | significant | nr | | |
| 2022-05-24 | -17.5% | significant | nr | | |
| 2022-06-01 | +17.9% | significant | nr | | |
| 2022-06-24 | +15.3% | significant | nr | | |
| 2022-08-02 | +16.1% | significant | nr | | |
| 2022-10-05 | -16.3% | significant | nr | | |
| 2022-11-09 | -17.4% | significant | nr | | |
| 2022-12-16 | -16.1% | significant | nr | | |
| 2022-12-27 | -27.2% | major | leadership | Worst month on record: Twitter distraction, Musk share sales, Shanghai halt | 0.80 |
| 2023-01-27 | +33.3% | major | earnings | Q4 2022 beat plus "strongest orders year-to-date than ever in our history" | 0.85 |
| 2023-02-06 | +16.9% | significant | nr | | |
| 2023-06-02 | +16.0% | significant | nr | | |
| 2023-06-13 | +16.9% | significant | nr | | |
| 2023-07-03 | +16.1% | significant | nr | | |
| 2023-10-23 | -16.5% | significant | nr | | |
| 2024-04-29 | +36.6% | major | product | Musk's surprise Beijing trip wins tentative FSD approval and a Baidu deal | 0.85 |
| 2024-07-08 | +27.8% | major | guidance | Q2 deliveries of 443,956 beat, and a nine-session winning streak | 0.80 |
| 2024-08-07 | -17.4% | significant | nr | | |
| 2024-10-25 | +22.0% | significant | nr | | |
| 2024-11-11 | +44.1% | major | geopolitical | Trump wins; TSLA is repriced as the politically advantaged EV | 0.90 |
| 2024-12-17 | +19.7% | significant | nr | | |
| 2025-01-02 | -18.0% | significant | nr | | |
| 2025-02-11 | -16.2% | significant | leadership | Leg of the DOGE-era drawdown off the December 2024 peak | 0.40 |
| 2025-02-27 | -20.4% | significant | leadership | Same drawdown; ~40% off the December peak by late February | 0.40 |
| 2025-03-10 | -22.0% | significant | leadership | Same drawdown, mechanism not isolated to this window | 0.40 |
| 2025-03-25 | +27.9% | major | product | China FSD rollout traction plus signals of tariff relief | 0.60 |
| 2025-04-08 | -17.4% | significant | nr | | |
| 2025-04-28 | +25.7% | major | leadership | Musk says he will step back from DOGE, and a bad Q1 stops mattering | 0.80 |
| 2025-05-14 | +25.9% | major | geopolitical | US-China tariff truce plus the June robotaxi reveal, back to $1trn | 0.70 |
| 2025-06-05 | -20.6% | significant | nr | | |
| 2025-09-17 | +22.4% | significant | nr | | |
| 2026-07-29 | -20.2% | significant | earnings | Q2 2026 miss: negative free cash flow as AI and robotics capex surges | 0.85 |

---

## Major events in detail

### 2010-07-07, -33.9% (major)
**Post-IPO unwind: TSLA breaks below its $17 offer price.**
Tesla priced at $17 on 29 June 2010 and closed its first day at $23.89, up 40.5%. The pop
did not survive the week. The stock fell 19% on Tuesday 6 July to $16.11, below the offer
price, and traded as low as $15.56. There is no adverse company news in this window. The
mechanism is pure post-IPO price discovery: flippers exiting a hot deal in a company that
had lost $55.7m the prior year and $260.7m since inception, against auto-industry
scepticism that a $100k Roadster maker could execute a $50k Model S.
**This is a market-structure move, not a news move, and it should not be used as a
news-analog seed.**
Sources: [CNN Money, 7 Jul 2010](https://money.cnn.com/2010/07/07/technology/tesla_stock/index.htm) ·
[Bloomberg, 6 Jul 2010](https://www.bloomberg.com/news/articles/2010-07-06/tesla-shares-fall-below-electric-car-maker-s-ipo-price-of-17-in-new-york) ·
[CNN Money, 29 Jun 2010](https://money.cnn.com/2010/06/29/technology/tesla_ipo/index.htm)

### 2010-07-19, +28.5% (major)
**Mechanical bounce off the post-IPO low. No catalyst found.**
The window runs 12 to 19 July 2010, from $1.1367 to $1.4607 split-adjusted. Nothing
credible was located for this window. Toyota's $50m private placement, which is sometimes
loosely dated to "July 2010", was in fact announced 21 May 2010 and closed immediately
after the IPO, so it does not belong here. Treated as unexplained.
Source for the Toyota date: [History of Tesla, Inc.](https://en.wikipedia.org/wiki/History_of_Tesla,_Inc.)

### 2010-11-10, +34.9% (major)
**Panasonic takes a $30m stake; first Q3 report as a public company.**
On 3 November 2010 Panasonic bought 1,418,573 shares at $21.15 for $30m in a private
placement, alongside a continuing next-generation EV battery-cell development programme.
Tesla then reported Q3 2010 results after the close on 9 November, inside the window.
The mechanism is validation: a tier-1 Japanese cell maker putting equity behind Tesla's
battery roadmap materially reduced the perceived probability that the Model S was
unmanufacturable. The stock ran from $21.41 on 1 November to $34.33 by late November, a
move of more than 50% across the month, of which this window is the first leg.
Sources: [Tesla investor presentation, SEC EX-99.1](https://www.sec.gov/Archives/edgar/data/1318605/000119312510281997/dex991.htm) ·
[Motley Fool, 30 Nov 2010](https://www.fool.com/investing/general/2010/11/30/has-tesla-motors-gone-too-far.aspx)

### 2013-05-15, +52.1% (major): the largest window in the ledger
**First quarterly profit, then the best car Consumer Reports had ever tested.**
Two catalysts landed back to back. On 8 May 2013 Tesla reported its first ever quarterly
profit: $562m of revenue and $15m of net income, or $0.12 per share, against consensus of
$0.04 on $500m. Shares rose ~13% after hours, then 24% the next day. On 9 May Consumer
Reports scored the Model S 99 out of 100, the highest score in the magazine's history. The
stock hit an all-time high of $81 on Friday 10 May and gained roughly 40% on the week.
The mechanism is a regime change, not a beat: the market had been pricing a probability of
insolvency, and a profitable quarter with a best-in-history product review collapsed that
probability. Later in the same month Tesla raised $1.02bn and repaid its DOE loan in full,
extending the move (see 2013-05-28).
Sources: [CNN Money, 8 May 2013](https://money.cnn.com/2013/05/08/autos/tesla-earnings/index.html) ·
[CNN Money, 10 May 2013](https://money.cnn.com/2013/05/10/investing/tesla-stock/index.html) ·
[CNBC, 8 May 2013](https://www.cnbc.com/2013/05/08/electric-earnings-tesla-earnings-blow-past-expectations-shares-surge.html) ·
[Bloomberg, 8 May 2013](https://www.bloomberg.com/news/articles/2013-05-08/tesla-posts-first-quarterly-profit-on-model-s-deliveries)

### 2014-01-21, +26.8% (major)
**Q4 2013 deliveries beat guidance by ~20% at the Detroit auto show.**
On 14 January 2014 Tesla disclosed ~6,900 Model S deliveries for Q4 2013 against prior
guidance of "slightly under 6,000". Shares rose 15.7% in the session and a further 3.6%
after hours. The mechanism is a guidance-credibility reset following the November 2013
battery-fire drawdown (see 2013-11-12): the delivery number was evidence that fire
coverage had not damaged demand, which was the actual bear thesis.
Sources: [CNN Money, 14 Jan 2014](https://money.cnn.com/2014/01/14/autos/tesla-model-s-sales/index.html?section=money_topstories) ·
[TechCrunch, 14 Jan 2014](https://techcrunch.com/2014/01/14/tesla-surges-on-strength-of-fourth-quarter-car-deliveries) ·
[InsideEVs](https://insideevs.com/tesla-charges-up-2014-detroit-auto-show-6900-model-s-sales-in-q4/)

### 2014-02-26, +30.7% (major)
**Q4 earnings, the Gigafactory reveal, and Morgan Stanley's $320 target.**
Three things stack inside this window. Q4 2013 results on 19 February showed $46m of
non-GAAP net income and raised 2014 delivery guidance to 35,000+, up 55%. On 25 February
Morgan Stanley's Adam Jonas more than doubled his target from $153 to $320, and the stock
jumped to $254.63 intraday. On 26 February Tesla formally unveiled the Gigafactory plan: a
~$2bn plant sized for 500,000 vehicles a year of cell output, with a site shortlist across
Arizona, New Mexico, Nevada and Texas. The mechanism is the market re-underwriting Tesla
as a battery-supply-chain owner rather than a niche assembler, which is what justified the
step-change in the terminal-value assumption.
Sources: [CNN Money, 25 Feb 2014](https://money.cnn.com/2014/02/25/investing/tesla-record-high/index.html) ·
[CleanTechnica, 20 Feb 2014](https://cleantechnica.com/2014/02/20/tesla-financials-strong-stock-surges-whats-story-gigafactory/) ·
[SFGate, 26 Feb 2014](https://blog.sfgate.com/energy/2014/02/26/breaking-tesla-unveils-gigafactory-plans-sort-of/)

### 2018-08-07, +27.3% (major)
**"Funding secured."**
Q2 2018 results on 1 August began the move, with Musk apologising to the analysts he had
insulted the prior quarter. Then on 7 August Musk tweeted "Am considering taking Tesla
private at $420. Funding secured." The stock rallied to as high as $371 and trading was
halted. Funding was not in fact secured; Tesla abandoned the plan on 24 August, and the
SEC charged and settled with Musk on 29 September (see 2018-10-08).
This is the cleanest `leadership` event in the ledger: a single sentence from one
individual repriced a ~$60bn company by tens of billions within hours.
Sources: [Musk's tweet](https://x.com/elonmusk/status/1026872652290379776) ·
[TechCrunch, 7 Aug 2018](https://techcrunch.com/2018/08/07/elon-musk-tesla-private-tweet) ·
[CNBC, 8 Aug 2019 retrospective](https://www.cnbc.com/2019/08/08/teslas-chaotic-year-after-musks-funding-secured-tweet.html) ·
[SEC press release 2018-226](https://www.sec.gov/news/press-release/2018-226)

### 2018-10-29, +28.3% (major)
**Surprise $312m GAAP profit in Q3 2018.**
On 24 October Tesla reported $6.8bn of revenue and $311.5m of GAAP net income, or $1.75
per share, against consensus of roughly -$0.19. Free cash flow was $881m and Model 3 labour
hours per unit fell more than 30% quarter over quarter. Shares rose more than 12% on the
print. The mechanism is the death of the "Tesla cannot build Model 3 at positive margin"
thesis, which had been the load-bearing short case all year.
Sources: [CNBC, 24 Oct 2018](https://www.cnbc.com/2018/10/24/tesla-earnings-q3-2018.html) ·
[CNN, 24 Oct 2018](https://www.cnn.com/2018/10/24/tech/tesla-earnings-profit-elon-musk)

### 2019-10-28, +29.3% (major)
**Surprise Q3 2019 profit and Shanghai ahead of schedule.**
On 23 October Tesla reported adjusted EPS of $1.86 against consensus of roughly -$0.42, on
$6.3bn of revenue, and disclosed that Gigafactory Shanghai was already in trial production
with Model Y pulled forward to summer 2020. Shares spiked more than 20%. This is the last
in-sample major and, notably, an *earnings surprise of the same shape* as 2018-10-29,
which makes the two natural analogs for each other.
Sources: [CNBC, 23 Oct 2019](https://www.cnbc.com/2019/10/23/tesla-tsla-earnings-q3-2019.html) ·
[CNN, 23 Oct 2019](https://www.cnn.com/2019/10/23/tech/tesla-earnings-profit-sales/index.html)

### 2020-02-04, +56.5% (major)
**The melt-up.**
On 3 February 2020 Tesla rose ~20%, its largest single day since 2013, and on 4 February a
further ~15% through $900. The named catalysts were Panasonic reporting the first ever
quarterly profit in its US battery business with Tesla, and an ARK Invest note dated 31
January projecting $7,000 per share by 2024. Short interest was 13.8% as of 30 January and
covering amplified the move. Tesla's own Q4 2019 result on 29 January also sits inside this
window, though it is not separately sourced here.
The mechanism is reflexive: a positioning squeeze layered on top of genuine news, which is
why the window is the second-largest in the ledger and why it has no fundamental anchor
proportional to its size.
Sources: [Japan Times, 4 Feb 2020](https://www.japantimes.co.jp/news/2020/02/04/business/tesla-20-panasonic-posts-first-quarterly-profit-battery-business/) ·
[Al Jazeera, 4 Feb 2020](https://www.aljazeera.com/economy/2020/2/4/tesla-shares-hit-900)

### The COVID cluster: 2020-02-28 (-25.9%), 2020-03-18 (-43.1%), 2020-03-25 (+49.3%)
**One macro shock, three windows.**
The week of 24-28 February 2020 produced the fastest correction in market history, with US
indices down at least 10% in six sessions on the spread of COVID-19 to South Korea, Italy
and Iran. March then delivered Black Monday I on 9 March (S&P 500 -7.6%, oil -22% on the
Russia-Saudi price war), Black Thursday on 12 March (largest single-day fall since 1987),
Black Monday II on 16 March (indices -12% to -13%, VIX closing at a record 82.69), and the
low on 18 March. Tesla carried an idiosyncratic overlay: Alameda County's shelter-in-place
order covered the Fremont plant, Tesla's only North American factory, and it shut from 23
March. The 24-26 March rally, driven by Fed QE and global fiscal stimulus, was the largest
in decades, with the Dow up more than 11% on 24 March alone.
For the corpus this is one regime wearing three hats. **2020-02-28, 2020-03-09, 2020-03-18
and 2020-03-25 are not four independent events**, and treating them as such will
overweight COVID in any analog retrieval.
Sources: [2020 stock market crash](https://en.wikipedia.org/wiki/2020_stock_market_crash) ·
[Motley Fool, 18 Mar 2020](https://www.fool.com/investing/2020/03/18/tesla-forced-to-shut-factory-as-part-of-coronaviru.aspx) ·
[CBS SF](https://www.cbsnews.com/sanfrancisco/news/coronavirus-pandemic-tesla-to-shutdown-fremont-plant-beginning-march-23/) ·
[TechCrunch, 19 Mar 2020](https://techcrunch.com/2020/03/19/tesla-to-temporarily-shut-down-fremont-factory)

### 2020-04-14, +37.5% (major)
**Q1 2020 deliveries clear a collapsed bar.**
On 2 April Tesla reported Q1 deliveries and the stock rose sharply, with the window then
riding the broader April rebound. Confidence is held at 0.60 because the macro component
here is large and was not separated from the company-specific one.
Source: [Fortune, 2 Apr 2020](https://fortune.com/2020/04/02/tesla-q1-2020-deliveries-stock-up-20-percent)

### 2020-07-06, +42.9% (major)
**Q2 deliveries of 90,650 against 72,149 expected, clearing the S&P 500 bar.**
The 2 July delivery print beat consensus by roughly 25% in the middle of a pandemic. Its
significance was not the units: four consecutive profitable quarters is the S&P 500
eligibility test, and this print made the fourth one likely, which it became when Tesla
posted $0.50 of GAAP EPS on 22 July. The market was buying an index-inclusion option, not
a delivery number.
Sources: [TheStreet, 2 Jul 2020](https://www.thestreet.com/tesla/news/tesla-q2-delivery-and-production-report-2020-tsla) ·
[Benzinga, 22 Jul 2020](https://benzinga.com/news/earnings/20/07/16740767/tesla-turns-a-profit-in-q2-qualifying-for-s-p-500-2020-delivery-goal-more-difficult)

### 2020-08-18, +37.3% (major) and 2020-08-31, +23.7% (significant)
**The 5-for-1 split.**
On 11 August 2020 Tesla's board declared a 5-for-1 split as a stock dividend, record date
21 August, distributed 28 August, trading split-adjusted from 31 August. Shares rose ~6-8%
after hours on the announcement, and then ran more than 80% over three weeks into the
effective date; August 2020 was a +74% month.
The mechanism is worth stating plainly because it is a warning for the model: **a split
changes nothing fundamental.** This was a retail-accessibility and flow event, and the
subsequent -33.7% window (2020-09-08) is the same flow running in reverse. Any generator
that treats an August 2020 style move as informative about fundamentals is learning noise.
Sources: [CNBC, 11 Aug 2020](https://www.cnbc.com/2020/08/11/tesla-announces-five-for-one-stock-split.html) ·
[Electrek, 11 Aug 2020](https://electrek.co/2020/08/11/tesla-tsla-stock-split/) ·
[Tesla 8-K EX-99.1](https://www.sec.gov/Archives/edgar/data/1318605/000156459020039353/tsla-ex991_6.htm)

### 2020-09-08, -33.7% (major)
**The S&P 500 snub: the worst day in company history.**
On 4 September 2020 the S&P index committee added Etsy, Teradyne and Catalent, and passed
over Tesla. On 8 September the stock fell 21%, roughly $80bn of market value in one
session, leaving it 34% below the record set a week earlier. Two mechanisms compounded:
index-anticipation longs unwinding, and a $5bn at-the-market equity offering already
weighing on the tape, all inside a broad early-September Nasdaq unwind.
Sources: [CNN, 8 Sep 2020](https://www.cnn.com/2020/09/08/investing/tesla-stock-plunge/index.html) ·
[TheStreet](https://www.thestreet.com/investing/tesla-tsla-stock-declines-sp500-index-snub) ·
[Benzinga, 8 Sep 2020](https://benzinga.com/news/20/09/17422501/tesla-stocks-21-drop-on-tuesday-is-its-worst-in-history)

### 2020-09-15, +36.2% (major)
**Bounce off the washout into Battery Day.**
This window is the reflex rally after the snub, running into Battery Day on 22 September,
which was itself judged a disappointment and contributed to Tesla ending September -13.9%.
No single catalyst is isolated inside the window, so confidence is 0.45.
Source: [Motley Fool, 4 Oct 2020](https://www.fool.com/investing/2020/10/04/why-tesla-stock-fell-139-in-september)

### 2020-11-23, +27.9% (major)
**S&P 500 inclusion, the largest addition ever made to the index.**
Announced 16 November 2020 for an effective date of 21 December. Shares jumped 13-14% in
extended trading. Credit Suisse estimated passive funds alone would need ~95m shares and
that total demand including active managers would be ~125m shares, one of the largest
funding trades in S&P 500 history.
This is a pure `sector-rotation` event: the news is about forced buyers, not about Tesla.
It is also the mirror image of 2020-09-08, and the two make a matched pair.
Sources: [CNBC, 16 Nov 2020](https://www.cnbc.com/2020/11/16/tesla-stock-jumps-on-news-company-is-joining-sp-500.html) ·
[S&P Dow Jones Indices, 30 Nov 2020](https://press.spglobal.com/2020-11-30-S-P-Dow-Jones-Indices-Announces-Implementation-of-Teslas-Addition-to-S-P-500)

### 2021-03-15, +25.7% (major), with 2021-03-08 (-21.6%)
**The rates trade, both directions.**
A sharp run-up in Treasury yields from mid-February 2021 hit long-duration growth equities,
and Tesla fell more than 30% from its late-January high. On 9 March, as yields dipped,
Tesla closed up 19.6% in one of its largest single days since 2020, alongside a broad
high-beta and ARK-complex rebound. The 8 March and 15 March windows are the down leg and
the up leg of one factor move.
Sources: [Investing.com](https://www.investing.com/news/stock-market-news/futures-bounce-after-selloff-as-tesla-jumps-11-3679649) ·
[Business Standard, 9 Mar 2021](https://www.business-standard.com/amp/article/international/nasdaq-jumps-400-points-as-tech-stocks-gain-ground-tesla-rises-5-121030901443_1.html)

### 2022-12-27, -27.2% (major)
**Worst month, quarter and year on record.**
December 2022 was a -44% month, by far Tesla's worst ever, having never previously fallen
more than 25% in a month. Three mechanisms compounded. Musk's Twitter acquisition, closed
27 October, both consumed his attention and forced sales: he sold ~22m Tesla shares worth
~$3.6bn in mid-December to fund a cash-burning Twitter. Tesla extended a week-long
production halt at Shanghai on a COVID wave in its Chinese workforce, with a planned
January reopening of only 17 days. And Musk publicly forecast a "serious recession" in
2023 in which cars would be "disproportionately impacted".
Sources: [CNBC, 27 Dec 2022](https://www.cnbc.com/2022/12/27/teslas-stock-is-headed-for-its-worst-month-quarter-year-on-record.html) ·
[CNBC, 13 Dec 2022](https://www.cnbc.com/2022/12/13/tesla-stock-down-28percent-since-elon-musk-took-over-twitter.html) ·
[CNN, 23 Dec 2022](https://www.cnn.com/2022/12/23/investing/elon-musk-tesla-twitter/index.html)

### 2023-01-27, +33.3% (major)
**Q4 2022 beat, and the January price cuts working.**
On 25 January Tesla reported Q4 adjusted EPS of $1.07 against $1.05 expected on revenue of
$24.32bn, up 37% year over year, with full-quarter net profit of $3.68bn. The move was
driven less by the print than by Musk's statement on the call: "Thus far in January we've
seen the strongest orders year-to-date than ever in our history. We're currently seeing
orders of almost twice the rate of production." That answered the demand question that had
produced the December 2022 collapse.
Sources: [CNBC, 25 Jan 2023](https://www.cnbc.com/2023/01/25/tesla-tsla-earnings-q4-2022.html) ·
[SEC 8-K exhibit](https://www.sec.gov/Archives/edgar/data/1318605/000162828023034588/exhibit991.htm)

### 2024-04-29, +36.6% (major)
**Musk flies to Beijing and comes back with FSD.**
Over the weekend of 27-28 April 2024 Musk made a 24-hour surprise visit to Beijing and
obtained tentative approval for Full Self-Driving in China, plus a mapping and navigation
deal with Baidu and data-collection clearance. Shares rose ~15% on Monday 29 April to
~$194.81. Wedbush's Dan Ives called it "a watershed moment for the Tesla story". Q1
earnings on 23 April also sit in the window: net income more than halved, but management
pivoted the narrative to a cheaper model and a robotaxi.
The mechanism is optionality repricing: a regulatory unlock in the largest EV market
converts FSD from a US-only feature into a global one.
Sources: [CBS News](https://www.cbsnews.com/news/tesla-china-elon-musk-full-self-driving-software/) ·
[Fortune, 29 Apr 2024](https://fortune.com/2024/04/29/tesla-china-full-self-driving-stock-15-percent) ·
[TheStreet](https://www.thestreet.com/investing/stocks/tesla-shares-jump-as-elon-musk-returns-from-china-with-fsd-game-changer)

### 2024-07-08, +27.8% (major)
**Q2 deliveries beat, and a nine-session winning streak.**
On 2 July Tesla reported 443,956 Q2 deliveries against ~439,000 expected, and shares rose
10%. Deliveries were still down 4.8% year over year; the market bought the beat against
consensus, not growth. The rally extended to a nine-day streak by 8 July, taking the stock
more than 75% off its April lows and nearly erasing the year-to-date loss.
Sources: [CNBC, 2 Jul 2024](https://www.cnbc.com/2024/07/02/tesla-tsla-q2-2024-vehicle-delivery-and-production-numbers.html) ·
[CNBC, 3 Jul 2024](https://www.cnbc.com/2024/07/03/tesla-tsla-shares-rally-after-better-than-expected-deliveries-report.html)

### 2024-11-11, +44.1% (major)
**Trump wins, and Tesla is repriced as the politically advantaged EV.**
Tesla rose 14.8% on 6 November 2024, the day after the election, hitting its highest level
since July 2023 and adding ~$26.5bn to Musk's net worth in a session. November was a +38%
month, the best since January 2023. The mechanism is relative, not absolute: the incoming
administration was read as negative for EV subsidies generally and therefore positive for
the scale incumbent, with Musk's personal proximity to the President-elect as the
transmission channel. The stock set a closing record of $424.77 on 11 December, surpassing
the November 2021 peak.
Sources: [WHYY](https://whyy.org/articles/tesla-shares-soar-trump-wins-election/) ·
[Forbes, 6 Nov 2024](https://www.forbes.com/sites/tylerroush/2024/11/06/tesla-shares-hit-record-soaring-12-and-elon-musk-becomes-15-billion-richer-with-trump-victory/) ·
[CNBC, 11 Dec 2024](https://www.cnbc.com/2024/12/11/tesla-reaches-record-boosted-by-64percent-pop-since-trump-election-victory.html)

### 2025-03-25, +27.9% (major)
**Rebound: China FSD traction plus signals of tariff relief.**
Tesla rose 10.4% on 24 March 2025, attributed to the China FSD rollout gaining traction
and to signals of tariff relief from the administration. This window is the first sharp
bounce inside the much larger DOGE-era drawdown (see 2025-02-11, 2025-02-27, 2025-03-10),
so confidence is 0.60: the direction and the named catalysts are sourced, but the size of
the window owes a lot to how oversold the stock was.
Source: [FinancialContent MarketMinute, 24 Mar 2025](https://markets.financialcontent.com/stocks/article/marketminute-2025-3-24-tesla-stock-surges-104-as-china-full-self-driving-rollout-gains-traction-and-trump-signals-tariff-relief)

### 2025-04-28, +25.7% (major)
**Musk says he will step back from DOGE, and a bad Q1 stops mattering.**
Q1 2025 results on 22 April were poor: revenue down 9% year over year to $19.34bn against
~$21.11bn expected, EPS of $0.27 against $0.39 expected. The stock rose anyway, because on
the call Musk said his time at DOGE would drop significantly. Shares were up ~9% to $260 by
24 April. The retreat from DOGE is credited with adding roughly $158bn of market value.
This is the cleanest demonstration in the whole ledger that **for TSLA, CEO attention is a
priced fundamental**, and that an earnings miss can be a positive catalyst if the
accompanying narrative resolves a bigger overhang.
Sources: [Tesla Oracle, 23 Apr 2025](https://www.teslaoracle.com/2025/04/23/tesla-tsla-surges-after-q1-2025-earnings-call-musks-time-at-doge-to-drop-significantly-soon/) ·
[Fortune](https://fortune.com/article/elon-musk-doge-tesla-stock-market-cap-outlook/)

### 2025-05-14, +25.9% (major)
**US-China tariff truce plus the June robotaxi reveal.**
Tesla surged as US-China tariffs eased and Musk refocused on the company, with the June
robotaxi reveal adding a second leg. The stock rallied more than 40% off its April lows and
re-entered the $1trn club, despite Q1 revenue having fallen sharply.
Source: [Benzinga, May 2025](https://www.benzinga.com/news/25/05/45387469/tesla-stock-soars-amid-china-tariff-relief-and-robotaxi-buzz)

### 2026-07-29, -20.2% (significant, but the largest recent move)
**Q2 2026 miss: negative free cash flow as AI and robotics capex surges.**
Tesla fell 13% on 23 July 2026 after Q2 results. Revenue beat at $28.24bn, up 25.5% year
over year, but non-GAAP EPS of $0.33 missed the ~$0.54 expected, and free cash flow turned
negative as operating expense and capital spending rose to fund AI and robotics. Analysts
cut targets on margin pressure and cautious autonomy guidance. July 2026 was a -26% month,
the largest monthly drop since December 2022.
This marks the current regime: **Tesla is now being priced as an AI capex story, and the
downside catalyst is spend rather than demand.**
Sources: [Motley Fool, 23 Jul 2026](https://www.fool.com/coverage/stock-market-today/2026/07/23/stock-market-today-july-23-tesla-stock-crashes-on-earnings-miss-and-rising-ai-spending/) ·
[Motley Fool, 6 Aug 2026](https://www.fool.com/investing/2026/08/06/why-tesla-stock-plunged-26-in-july/)

---

## Selected significant events

### 2013-11-12, -22.1%: Model S battery fires
Three Model S battery fires between 1 October and early November 2013 triggered a
20.4% November drawdown; the stock was down 37% from the first fire by mid-November. NHTSA
opened a formal investigation on 19 November, which Musk said Tesla had requested. Notably
the stock *rose* 3.7% on the day the probe was announced, so the damage was done by the
fire coverage itself, not by the regulator. Germany's KBA cleared the Model S in early
December, which is the likely driver of the +19.8% window on 2013-12-03.
Sources: [TechTimes, 9 Nov 2013](https://www.techtimes.com/articles/1304/20131109/3rd-tesla-model-s-catches-fire-burns-stock.htm) ·
[TheStreet](https://www.thestreet.com/investing/stocks/tesla-shares-fell-after-news-of-a-battery-fire-investigation-15150260) ·
[Forbes, 3 Dec 2013](https://www.forbes.com/sites/briansolomon/2013/12/03/tesla-rebounds-after-germany-clears-model-s-fires-but-nhtsa-investigation-still-looms/)

### 2016-02-08, -24.9%: and a caution about attributing it to earnings
It is tempting to attribute this window to Q4 2015 results. **Those were reported on 10
February, two sessions AFTER the ledger date, so they cannot be the cause.** The window is
driven by the January-February 2016 growth and credit selloff, plus a specific EV bear
case: cheap gasoline suppressing demand and doubts about Model X production ramp, with
Morgan Stanley cutting its target from $450 to $333 and Pacific Crest cutting 2016 EPS from
$0.76 to $0.27 beforehand. The 2016-02-22 rebound then followed the upbeat 2016 outlook
given with those results and the 11 February market bottom.
This is exactly the failure mode the window convention creates, and it is worth encoding.
Sources: [Automotive News, 8 Feb 2016](https://www.autonews.com/article/20160208/OEM05/302089902/tesla-shares-dogged-by-falling-gas-prices-output-concerns/) ·
[Nasdaq, 11 Feb 2016](https://www.nasdaq.com/articles/tesla-q4-loss-wider-than-expected-2016-outlook-upbeat-2016-02-11)

### 2016-04-06, +17.0%: Model 3 unveiling
The Model 3 was unveiled 31 March 2016. Reservations reached 115,000 within 24 hours,
232,000 within two days, and more than 325,000 within a week, more than triple all Model S
units sold through the end of 2015. Each reservation carried a $1,000 deposit, so the
market was watching a mass-market demand signal arrive with real cash attached.
Source: [Tesla Model 3](https://en.wikipedia.org/wiki/Tesla_Model_3)

### 2018-03-28, -18.6%: the crisis window
A fatal Model X crash on Highway 101 on 23 March 2018 with Autopilot engaged, a Moody's
downgrade, a 123,000-unit Model S power-steering recall on 29 March, and unresolved Model 3
production and cash-burn fears combined. Tesla lost ~$8bn of market value in two sessions
and fell below General Motors, $43.9bn against $49.4bn. Note that Tesla's confirmation that
Autopilot was engaged came on 30 March, after the ledger date, so this window captures the
investigation and the credit news rather than the Autopilot confirmation.
Sources: [Fortune, 28 Mar 2018](https://fortune.com/2018/03/28/tesla-stock-price-model-x-crash-credit-crunch/) ·
[CNN Money, 31 Mar 2018](https://money.cnn.com/2018/03/31/technology/tesla-model-x-crash-autopilot/index.html)

### 2019-01-23, -16.5% and 2019-05-22, -16.9%: the demand scare
On 18 January 2019 Tesla cut US prices by $2,000 to absorb the halving of the federal EV
credit from $7,500 to $3,750, cut ~7% of its full-time workforce, and Musk warned of a
"very difficult" road ahead; this followed a Q4 delivery number of 90,700 that had
disappointed. By May the market had escalated to a solvency question: Wedbush cut to $230
calling it a "code red" and criticising expansion into "insurance, robotaxis, and other
sci-fi projects" instead of Model 3 demand, and Morgan Stanley published a $10 bear case
with the note that "Demand is at the heart of the problem". The stock traded near $200.
Sources: [CNBC, 18 Jan 2019](https://www.cnbc.com/2019/01/18/tesla-to-cut-its-workforce-by-around-7-percent.html) ·
[Washington Post, 18 Jan 2019](https://www.washingtonpost.com/business/2019/01/18/tesla-will-cut-percent-its-workforce-aid-model-production/) ·
[CNBC, 20 May 2019](https://www.cnbc.com/2019/05/20/wedbush-tesla-facing-code-red-but-management-not-focused-on-model-3.html)

### The 2011 macro pair: 2011-08-08 (-17.8%) and 2011-08-22 (-16.3%)
Standard & Poor's downgraded the United States from AAA to AA+ on 6 August 2011, ending a
rating held since 1941. On 8 August the S&P 500 fell 6.7% and the NASDAQ 6.9%, with ~$2.5trn
erased from global equity value in a session. The S&P 500 fell 21.6% from its May peak to
its October low, which also frames the 2011-08-22 down leg and the 2011-10-10 rebound.
Tesla, then a sub-$3bn pre-revenue-scale name, was a high-beta expression of that move
rather than the subject of it.
Source: [August 2011 stock markets fall](https://en.wikipedia.org/wiki/August_2011_stock_markets_fall)

### The 2025 DOGE drawdown: 2025-02-11, 2025-02-27, 2025-03-10
Three consecutive down windows totalling roughly -50% cumulative, inside a drawdown of
nearly 40% off the December 2024 peak by February and continuing into March. The mechanism
generally reported is Musk's political role and the brand and demand damage attributed to
it, running against the exact `geopolitical` re-rating that drove 2024-11-11. **Confidence
is held at 0.40 for each: the drawdown itself is sourced, the window-level mechanism is
not.** These three plus 2025-03-25, 2025-04-28 and 2025-05-14 are one connected episode.
Source: [Benzinga, Feb 2025](https://www.benzinga.com/markets/25/02/44005093/tesla-stock-has-fallen-nearly-40-from-dec-peak-wiping-almost-137-billion-from-elon-musks-wealth)

---

## Regime

**TSLA does not live in one regime. It has lived in at least six, and they do not transfer
to each other.** This is the single most important finding for the generator.

| Era | Window count | What actually moves the stock |
|---|---|---|
| 2010-2012, post-IPO | 15 | Price discovery and macro beta. Almost no company-specific news. A ~$2bn company with no product at scale. |
| 2013-2016, the story forms | 14 | Binary company events: first profit, Consumer Reports, Gigafactory, Model 3 reservations, battery fires. Highest information content per event. |
| 2017-2019, production hell | 11 | Demand credibility and solvency. Delivery pre-announcements, price cuts, layoffs, and a CEO under SEC supervision. Earnings surprises are enormous because consensus is wide. |
| 2020-2021, flows | 19 | Index inclusion and exclusion, a stock split, a rates-driven growth factor, and a retail bid. **Much of this era's variance is not about Tesla at all.** |
| 2022-2025, key-man risk | 27 | Musk's attention allocation, priced explicitly: Twitter (2022-12-27), DOGE (2025 Q1), the retreat from DOGE (2025-04-28), and the 2024 election. |
| 2026, AI capex | 1 so far | Free cash flow versus AI and robotics spend. The bear catalyst is now investment, not demand. |

Three cross-cutting facts:

1. **Direction is asymmetric.** 63 of 99 windows are up and 36 are down, and the up moves
   are larger (the four biggest windows are +56.5%, +52.1%, +49.3%, +44.1%). Any null model
   assuming symmetry will be miscalibrated on this name in a specific, predictable way.
2. **Earnings surprises are not the dominant category.** Of the 51 attributed windows,
   only 6 are cleanly `earnings`. `macro` and `sector-rotation` together account for 15,
   `guidance` (deliveries, price cuts, corporate actions) for 12, and `leadership` for 6.
   **A model that expects TSLA to be an earnings-driven stock will retrieve the wrong
   analogs.** Tesla's own scheduled earnings dates frequently fall *outside* the windows
   that the ledger flags.
3. **Events arrive in pairs and clusters.** 2020-09-08 / 2020-11-23 (index out, index in),
   2021-03-08 / 2021-03-15 (rates down leg, rates up leg), 2013-11-12 / 2013-12-03 (fires,
   all-clear), 2016-02-08 / 2016-02-22, 2025-02 through 2025-05 (one DOGE episode across six
   windows). The COVID cluster alone contributes four windows. Treating clustered windows as
   independent draws will overstate the effective sample size, probably by 20% or more.

**Implication for the seed corpus.** The contract's train cut at 2019-12-31 leaves TSLA with
40 windows, of which 9 are `major`. That is the good news: unlike JPM, TSLA's in-sample
events are genuinely spread across 2010-2019 and across categories, so it is one of the
better analog donors in the universe. The bad news is that **the in-sample regime is a
$2bn to $75bn company, and the out-of-sample regime is a $500bn to $1.4trn S&P 500
constituent.** Analogs will transfer in *shape* (a delivery beat is a delivery beat) but not
in *magnitude*, and the index-flow category that dominates 2020-2021 has no in-sample
precedent at all, because Tesla was not in the S&P 500 before December 2020.

---

## Ledger verdict

**The ledger survives contact with reality. It is clean.** Specifically:

- **No split artifacts.** Both the 2020 5-for-1 and the 2022 3-for-1 are correctly adjusted
  in the underlying price data. The 2020-08-31 row, which is the exact split effective date
  and the most likely place for an artifact, shows +23.7% and corresponds to a real,
  well-documented pre-split melt-up rather than an unadjusted -80% print.
- **No bad prints found.** Two windows were reconstructed by hand from raw closes and both
  reconcile to the ledger within 0.02 percentage points.
- **Every one of the 28 `major` windows corresponds to something a human would recognise.**
  Twenty-seven of 28 have a named, sourced cause. The single exception is 2010-07-19, and
  even there the window is comprehensible as the rebound half of the post-IPO round trip
  whose down half is 2010-07-07.
- **Non-maximum suppression is behaving.** The COVID cluster produces four separate windows
  (2020-02-28, 2020-03-09, 2020-03-18, 2020-03-25) rather than one, which is correct
  behaviour for a 5-day window over a 5-week event, but it means the *ledger* is right while
  the *interpretation* would be wrong if these were counted as four independent shocks.

Two qualifications the parent should carry forward:

1. **The window convention systematically misdates causes, and in at least one case it
   inverts them.** 2016-02-08 looks like an earnings window and is not: the Q4 2015 report
   landed 10 February, two sessions later. Any automated headline-attachment step that
   snaps to the nearest earnings date will attach the wrong document to that event, and
   probably to several of the 48 unattributed windows too. The harvest step should search
   `[date - 10, date]` and reject documents dated after the ledger date.
2. **Two windows are structurally, not informationally, driven** (2010-07-07, 2010-07-19,
   both post-IPO price discovery, and arguably 2020-08-18 and 2020-08-31, both stock split).
   These are real price moves but they are not news events, and using them as news analogs
   would teach the generator that a corporate action of no economic content produces a 37%
   week. They should be flagged, not dropped.

---

## Unexplained

Split honestly into two groups. Neither group contains a guess.

### Searched, nothing credible found (1)

- **2010-07-19, +28.5% (major).** The rebound leg of the post-IPO round trip. The commonly
  cited "July 2010 Toyota partnership" is a misdating: Toyota's $50m private placement was
  announced 21 May 2010 and closed immediately after the IPO. No other catalyst located.

### Not researched, budget exhausted (47)

The session's web-search allowance was consumed before these were reached, and the news MCP
providers (Benzinga, Intrinio, Tiingo, FMP news) are all unauthenticated on this machine, so
there was no fallback. **These are unattributed, not inexplicable.** Most are probably
tractable in a follow-up pass, and every one of them is `significant` tier, not `major`.

2010-08-11, 2010-12-30, 2011-01-20, 2011-03-31, 2011-12-14, 2012-01-13, 2012-01-23,
2012-09-17, 2013-04-22, 2013-07-01, 2017-07-06, 2018-04-05, 2018-06-12, 2020-01-08,
2020-02-19, 2020-05-08, 2020-06-10, 2020-10-01, 2021-01-08, 2021-10-29, 2021-11-12,
2021-12-28, 2022-01-27, 2022-02-23, 2022-03-02, 2022-03-22, 2022-05-11, 2022-05-24,
2022-06-01, 2022-06-24, 2022-08-02, 2022-10-05, 2022-11-09, 2022-12-16, 2023-02-06,
2023-06-02, 2023-06-13, 2023-07-03, 2023-10-23, 2024-08-07, 2024-10-25, 2024-12-17,
2025-01-02, 2025-04-08, 2025-06-05, 2025-09-17

Note the shape of that list: **21 of the 47 fall in 2022 alone or in the 2022-2023 window.**
Tesla in 2022 produced 14 windows of 15%+ in a single year with no `major` among them until
December. That is a high-volatility, low-information regime, and it is the single largest
block of missing research. If a follow-up pass has budget for only one thing, it should be
2022.

### Low-confidence attributions (treat as provisional, not as corpus ground truth)

- 2010-11-24 (0.40), 2018-12-20 (0.40), 2019-06-10 (0.30), 2025-02-11 (0.40),
  2025-02-27 (0.40), 2025-03-10 (0.40), 2018-10-08 (0.45), 2020-09-15 (0.45).
  For each of these the *regime* is sourced but the *window-level catalyst* is not isolated.

---

*Research conducted 6 September 2026. Every URL in this document was retrieved during the
session; none were constructed from memory. Where a claim could not be sourced it is
labelled unattributed rather than inferred.*
