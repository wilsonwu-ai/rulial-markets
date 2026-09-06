# JPM — event research

**Ticker:** JPM (JPMorgan Chase & Co.), the largest US bank holding company by assets.
**Events in ledger:** 30 (10 `major` at >=25%, 20 `significant` at >=15%), all detected on a
rolling 5-trading-day close-to-close window.

## What drives this name

JPM is not a company whose stock re-rates on product cycles. It is a levered claim on the
US credit cycle and on the market's belief about bank solvency and the policy backstop.
Its idiosyncratic events are real but rare (Bear Stearns, WaMu, the London Whale); the
overwhelming majority of its 15%-plus weekly moves are **systemic repricings of the entire
banking sector**, driven by policy announcements, solvency panics, and liquidity backstops.
Three of the four dated periods in this ledger (2008-09, 2011, 2020) are macro-credit
episodes, not company events.

**One structural caveat before anything else.** 20 of 30 events, and 10 of 10 `major`
events, fall inside a 15-month span from January 2008 to May 2009. That is a single regime.
See the Regime section.

---

## Every event examined

Window ends on the listed date and covers the prior 5 trading days, so the catalyst almost
always falls *before* the date shown.

| Date | Move | Tier | Category | Headline | Conf |
|---|---|---|---|---|---|
| 2008-01-23 | +16.7% | significant | macro | Fed emergency 75bp intermeeting cut, financials snap back from the Jan 22 washout | 0.65 |
| 2008-03-24 | +27.4% | major | crisis | JPM buys Bear Stearns with a Fed backstop, raises the bid from $2 to $10 | 0.90 |
| 2008-07-22 | +31.7% | major | earnings | Q2 earnings beat a very low bar into an SEC-driven short squeeze in financials | 0.85 |
| 2008-10-01 | +22.5% | significant | crisis | JPM takes the WaMu deposit franchise from the FDIC for $1.9bn | 0.85 |
| 2008-10-09 | -26.4% | major | crisis | The worst week in Dow history; credit markets seize post-Lehman | 0.85 |
| 2008-10-27 | -16.4% | significant | crisis | Global forced-selling leg; Dow down 24.7% for October at that close | 0.70 |
| 2008-11-03 | +19.8% | significant | macro | Rebound off the Oct 27 low, led by the Oct 28 Dow +889 and the Oct 29 Fed cut | 0.75 |
| 2008-11-20 | -37.1% | major | crisis | Citigroup solvency run drags the whole sector; S&P 500 to an 11-year low | 0.90 |
| 2008-11-28 | +35.4% | major | regulatory | Government rescues Citigroup with a $306bn asset guarantee and $20bn injection | 0.90 |
| 2008-12-08 | +39.7% | major | macro | Rally off the Dec 1 recession-declaration crash into Obama's public works plan | 0.75 |
| 2008-12-15 | -21.5% | significant | crisis | Give-back from the Dec 8 spike; Madoff arrest hits bank sentiment, Merrill cuts JPM | 0.65 |
| 2009-01-09 | -17.2% | significant | macro | December payrolls fell 524,000, unemployment to 7.2% | 0.55 |
| 2009-01-20 | -27.4% | major | crisis | Inauguration Day bank rout on nationalization fear; worst Inauguration Day in Dow history | 0.90 |
| 2009-01-27 | +38.5% | major | unexplained | Violent rebound off the Jan 20 washout; no single dated catalyst confirmed in-window | 0.40 |
| 2009-02-20 | -24.0% | significant | crisis | Dodd says regulators may have to take over Citi or BofA; nationalization panic peaks | 0.85 |
| 2009-03-06 | -30.3% | major | crisis | Final leg into the March 6 12-year low (S&P intraday 666.79) | 0.80 |
| 2009-03-13 | +49.1% | major | crisis | Pandit memo says Citi is profitable; uptick rule and mark-to-market relief signalled | 0.90 |
| 2009-03-23 | +25.0% | significant | regulatory | Geithner unveils PPIP, up to $1trn to buy toxic assets; Dow +6.8% | 0.90 |
| 2009-04-16 | +21.2% | significant | earnings | Wells Fargo pre-announces a record quarter, JPM adds 19% on Apr 9, then beats on Apr 16 | 0.80 |
| 2009-05-08 | +19.9% | significant | regulatory | SCAP stress tests: JPM among the nine banks told to raise nothing | 0.85 |
| 2011-08-08 | -15.8% | significant | macro | S&P strips the US of AAA; S&P 500 falls 6.5% on the first trading day after | 0.85 |
| 2011-12-06 | +16.4% | significant | macro | Six central banks cut dollar swap-line pricing by 50bp on Nov 30 | 0.75 |
| 2012-05-17 | -16.7% | significant | crisis | The London Whale: $2bn CIO derivatives loss disclosed after the May 10 close | 0.90 |
| 2020-03-09 | -23.1% | significant | macro | COVID Black Monday plus the Saudi-Russia oil price war; yields collapse | 0.90 |
| 2020-03-20 | -19.6% | significant | macro | Second COVID crash leg; Dow's largest weekly decline since 2008 | 0.85 |
| 2020-03-30 | +18.3% | significant | regulatory | Fed goes open-ended on asset purchases March 23; CARES Act signed March 27 | 0.85 |
| 2020-04-09 | +17.4% | significant | regulatory | Fed announces up to $2.3trn in lending facilities on April 9 | 0.85 |
| 2020-06-08 | +15.1% | significant | macro | May payrolls rose 2.5 million against expectations of further losses; reopening rotation | 0.70 |
| 2020-11-09 | +16.6% | significant | macro | Election-week rally, then Pfizer's 90%-efficacy readout; JPM +13.5% on the day | 0.90 |
| 2022-10-18 | +16.6% | significant | earnings | Oct 13 CPI reversal plus a Q3 beat on Oct 14 ($9.7bn, $3.12 EPS, NII +34%) | 0.80 |

---

## Major events in detail

### 2008-03-24, +27.4% — JPM buys Bear Stearns

**What happened.** On March 16, 2008 JPMorgan agreed to acquire Bear Stearns for $2 a share
with a Federal Reserve backstop. On March 24 it raised the offer to $10 a share in stock and
agreed to buy 95 million newly issued Bear shares, 39.5% of the company, at the same price
([CNN Money](https://money.cnn.com/2008/03/24/news/companies/bear/index.htm),
[Forbes](https://www.forbes.com/2008/03/24/bear-morgan-acquisition-markets-cx_cl_0324bear.html)).

**Why it moved.** The window runs from the March 14 close of $36.54, the day Bear's liquidity
crunch became public, to $46.55 on March 24. JPM rose 10.3% on March 17 alone. The market read
the deal as JPM acquiring a franchise at a distressed price with the taxpayer absorbing the
tail risk, and simultaneously as the Fed demonstrating it would not let a dealer fail
disorderly. Both readings are bullish for the acquirer. The March 24 price increase, which is
economically a *worse* deal for JPM, did not reverse it, because by then the story was
systemic relief rather than deal terms.

**Category:** crisis (company-specific inside a systemic event). **Confidence 0.90.**

### 2008-07-22, +31.7% — Q2 earnings beat into a short squeeze

**What happened.** The window base is the July 15 close of $31.02, the low of the summer
financials panic. On July 15 the SEC restricted naked short selling in 19 financial names
including the primary dealers ([SEC comment file on the ban](https://www.sec.gov/comments/s7-08-09/s70809-3779.pdf),
[Harvard Law School Forum summary of the July emergency order](https://corpgov.law.harvard.edu/wp-content/uploads/2008/07/fig_sec-bars-naked-short-sales-of-major-financial-firms.PDF)).
On July 17 JPM reported Q2 net income of $2.0bn, EPS $0.54, down 53% year over year but far
above a market braced for much worse
([JPMorgan Q2 2008 release](https://jpmorganchaseco.gcs-web.com/news-releases/news-release-details/jpmorgan-chase-reports-second-quarter-2008-net-income-20-billion)).

**Why it moved.** JPM rose 15.9% on July 16 and a further 13.5% on July 17 to $40.80. The
mechanism is a positioning unwind, not a fundamental re-rating: earnings fell by half, but
short interest had been built for a capital hole that the print did not show, and the SEC
action raised the cost of maintaining that position. This is the cleanest "good news off a
depressed base" event in the ledger.

**Category:** earnings. **Confidence 0.85.**

### 2008-10-09, -26.4% — the worst week in Dow history

**What happened.** In the week ending October 9, 2008 the Dow fell a record 18% and the S&P 500
had its worst week since 1933. On October 9 alone the Dow fell 679 points, 7.3%, to its lowest
close since May 2003 ([Cantech Letter](https://www.cantechletter.com/2023/12/2008-10-09-what-happened/),
[Benzinga on the following week's rebound](https://www.benzinga.com/general/education/21/10/23355953/this-day-in-market-history-dow-rebounds-11-following-worst-week-ever-in-2008)).

**Why it moved.** Post-Lehman, interbank funding markets had effectively closed. The signature
of the week is that TARP had *already* passed on October 3 and stocks fell anyway, which told
the market that a $700bn asset-purchase authority was not equivalent to a solvency guarantee.
JPM, the strongest balance sheet in the group, still fell 26% because the repricing was of bank
funding risk generally, not of JPM's credit specifically.

**Category:** crisis. **Confidence 0.85.**

### 2008-11-20, -37.1% — the Citigroup solvency run

**What happened.** On November 20 the S&P 500 lost 6.7% and closed at its lowest level since
April 1997. Citigroup fell 26% to a 15-year low, JPMorgan fell nearly 18% to about $23, and
Bank of America fell 14%. The decline came even after Prince Alwaleed bin Talal raised his Citi
stake to 5% ([CNN Money market report](https://money.cnn.com/2008/11/20/markets/markets_newyork/index.htm?postversion=2008112018),
[CNN Money on bank stocks](https://money.cnn.com/2008/11/20/news/companies/bank_stocks/index.htm),
[CNBC](https://www.cnbc.com/2008/11/20/sp-plunges-to-11year-low.html)).

**Why it moved.** This is the largest single event in the JPM ledger and it is a **contagion**
event, not a JPM event. The market was pricing the probability that the government would
resolve Citigroup by wiping out common equity, and applying that hazard rate to every large
bank's equity. Volume tells the story: 160.7 million JPM shares on November 20 and 194.1 million
on November 21, against a normal 2008 tape of 50 to 70 million. That is forced deleveraging,
not opinion changing.

**Category:** crisis. **Confidence 0.90.**

### 2008-11-28, +35.4% — the Citigroup rescue

**What happened.** On November 23, 2008 Treasury, the Federal Reserve and the FDIC announced a
rescue of Citigroup: a guarantee on roughly $306bn of assets plus a fresh $20bn Treasury
investment ([Federal Reserve press release, Nov 23 2008](https://www.federalreserve.gov/newsevents/pressreleases/bcreg20081123a.htm),
[CNN Money](https://money.cnn.com/2008/11/23/news/companies/citigroup/index.htm),
[Yale New Bagehot Project](https://newbagehot.yale.edu/docs/united-states-citigroup-capital-injection-2008/)).
Citi rose 65% in morning trade on November 24 and the Dow gained nearly 4%.

**Why it moved.** This is the mirror image of the November 20 event and the pair should be read
together. The hazard rate that had been marked into every bank's equity on November 20 was
explicitly capped by the sovereign on November 23. JPM's 35% five-day gain is almost entirely
the removal of that contagion premium, off a base ($23.38) that had itself been set by the
panic. Note the asymmetry the ensemble model should care about: the down move (-37%) and the
recovery (+35%) are of similar magnitude and separated by six trading days.

**Category:** regulatory. **Confidence 0.90.**

### 2008-12-08, +39.7% — the Obama public works rally

**What happened.** The window base is the December 1 close of $26.12. December 1 was the day the
NBER dated the recession and the S&P 500 fell 8.93%, with S&P financials down 17%
([Wikipedia, Global financial crisis in December 2008](https://en.wikipedia.org/wiki/Global_financial_crisis_in_December_2008)).
Over the following weekend President-elect Obama outlined the largest public works program since
the interstate highway system, and stocks rallied on December 8
([CNN Money market report, Dec 8 2008](https://money.cnn.com/2008/12/08/markets/markets_newyork/index.htm),
[PBS NewsHour](https://www.pbs.org/newshour/economy/business-july-dec08-markets_12-08)).

**Why it moved.** Roughly half of the +39.7% is base effect from the December 1 crash. The
incremental news is fiscal: a credible commitment to demand support reduces the expected loss
severity on a bank loan book. The cited sources confirm the market-wide rally and the fiscal
catalyst; they do not isolate a JPM-specific driver, which is why confidence is 0.75 rather than
0.9.

**Category:** macro. **Confidence 0.75.**

### 2009-01-20, -27.4% — Inauguration Day bank rout

**What happened.** On January 20, 2009 the Dow fell 4%, its largest Inauguration Day decline in
112 years, and the S&P 500 fell 5.3%. State Street fell 59%, Bank of America 29%, Citigroup 20%,
and Royal Bank of Scotland 69% in New York trading. The driver was open speculation that the
government would have to seize one or more large US banks
([CNN Money market report](https://money.cnn.com/2009/01/20/markets/markets_newyork/index.htm),
[CNN Money on bank stocks](https://money.cnn.com/2009/01/20/news/companies/banks_stocks/index.htm?postversion=2009012016),
[Al Jazeera](https://www.aljazeera.com/news/2009/1/21/record-us-stock-fall-greets-obama)).

**Why it moved.** Nationalization is the one scenario in which a bank's equity goes to zero
while its business keeps operating. Once the market started assigning meaningful probability to
it, correlation across bank equities went to one and the strongest balance sheet offered no
protection. The UK's escalating RBS intervention supplied the template that made the US version
imaginable.

**Category:** crisis. **Confidence 0.90.**

### 2009-01-27, +38.5% — rebound with no confirmed in-window catalyst

**What happened.** The window runs from the depressed January 20 close to January 27. Two
candidate catalysts exist but neither is dated inside the window: Timothy Geithner was sworn in
as Treasury Secretary on January 26 ([WBUR](https://www.wbur.org/news/2009/01/26/geithner-is-sworn-in-as-treasury-secretary)),
and CNN reported bank stocks broadly higher on "bad bank" aggregator speculation on
**January 28**, one day after the ledger date
([CNN Money, Wells Fargo, Jan 28 2009](https://money.cnn.com/2009/01/28/news/companies/wells_fargo/)).

**Why it likely moved.** The arithmetic is dominated by the base: January 20 was a capitulation
close. Anything short of a nationalization announcement produced a violent snapback. I could not
verify a specific dated catalyst on January 21 through January 27, so I am **not** asserting one.

**Category:** unexplained. **Confidence 0.40.** Listed in the Unexplained section.

### 2009-03-06, -30.3% — the last leg to the 12-year low

**What happened.** The S&P 500 reached an intraday low of 666.79 on March 6, 2009, roughly 57%
below its October 2007 high, and the lowest level since 1996
([CNBC 10th-anniversary retrospective](https://www.cnbc.com/2019/03/04/the-10th-anniversary-of-the-climactic-march-2009-market-bottom-arrives-this-week.html),
[Yahoo Finance retrospective](https://finance.yahoo.com/news/stock-market-bottomed-9-years-110500236.html)).
The proximate regime was the nationalization panic that had peaked two weeks earlier, when Senate
Banking Chairman Chris Dodd said on February 20 that regulators might have to take over Citi or
Bank of America
([Washington Times](https://www.washingtontimes.com/news/2009/feb/21/stocks-tank-talk-bank-nationalization/),
[CNBC](https://www.cnbc.com/2009/02/20/bank-nationalization-casts-a-shadow.html)).

**Why it moved.** Same mechanism as January 20 and February 20, now at maximum intensity. My
sources establish the market-level bottom and the nationalization regime; I did not verify a
JPM-specific catalyst inside the February 27 to March 6 window, so confidence is 0.80 rather
than 0.9.

**Category:** crisis. **Confidence 0.80.**

### 2009-03-13, +49.1% — the largest move in the ledger

**What happened.** On March 10, 2009 a memo from Citigroup CEO Vikram Pandit, filed with the SEC,
said Citi had generated $19bn of revenue in January and February excluding disclosed marks and
was operating at a profit. Citi rose 38% and the KBW Bank Index rose 15.6%. The rally accelerated
when Barney Frank said the SEC would restore the uptick rule, and a House hearing on
mark-to-market accounting was scheduled for that Thursday
([CNN Money, Mar 10 2009](https://money.cnn.com/2009/03/10/markets/markets_newyork/index.htm?postversion=2009031011),
[Business Standard on the Pandit memo](https://www.business-standard.com/article/finance/citi-profitable-in-first-two-months-this-year-report-109031000165_1.html),
[NBC News](https://www.nbcnews.com/news/amp/wbna29611953)).

**Why it moved.** Three distinct fears were relieved in four days: that the largest banks were
not generating pre-provision earnings, that accounting rules would force further writedowns into
a fire-sale market, and that short sellers faced no constraint. None of these was a JPM
announcement. JPM gained 49% in five days because it was the highest-beta liquid expression of
"the banking system will not be nationalized," and because the March 6 base was a panic low.

**Category:** crisis. **Confidence 0.90.**

---

## Notable non-major events worth carrying into the corpus

- **2008-10-01, +22.5%, the WaMu acquisition.** On September 25, 2008 JPMorgan acquired the
  deposits, assets and certain liabilities of Washington Mutual's banking operations from the
  FDIC for approximately $1.9bn, in the largest bank failure in US history
  ([JPMorgan press release](https://jpmorganchaseco.gcs-web.com/news-releases/news-release-details/jpmorgan-chase-acquires-deposits-assets-and-certain-liabilities),
  [SEC EX-99.1, Sept 25 2008](https://www.sec.gov/Archives/edgar/data/19617/000119312508201638/dex991.htm),
  [FDIC failed bank list](https://www.fdic.gov/resources/resolutions/bank-failures/failed-bank-list/wamu.html)).
  JPM rose 18.4% on September 26 alone, from $40.55 open to a $48.24 close on 148 million shares.
  This is the **only unambiguously idiosyncratic positive event** in the pre-2019 ledger: a
  franchise acquired at a distressed price with the liability tail left behind at the holding
  company. It is the closest thing JPM has to a company-specific analog.

- **2012-05-17, -16.7%, the London Whale.** JPMorgan disclosed at least $2bn of losses in the
  Chief Investment Office on May 10, 2012, after the close; the total eventually reached about
  $6bn ([Wikipedia](https://en.wikipedia.org/wiki/2012_JPMorgan_Chase_trading_loss)). The window
  base is the May 10 close of $40.74, the last pre-disclosure print, and JPM fell 9.3% on May 11
  on 217 million shares against a typical 30 to 40 million. This is the **only pure
  idiosyncratic negative event** in the ledger. It is also the only event in the ledger where
  the catalyst lands exactly on the first day of the detection window, which makes it the
  cleanest test case the corpus has.

- **2022-10-18, +16.6%.** The window base is the October 11 close. Two catalysts: the October 13
  CPI reversal day (JPM +5.6%) and Q3 2022 results on October 14, net income $9.7bn, diluted EPS
  $3.12, managed revenue $33.5bn, and net interest income of $17.6bn, up 34% year over year
  ([SEC 8-K exhibit 99.1, filed 2022-10-14](https://www.sec.gov/Archives/edgar/data/19617/000001961722000486/a3q22erfexhibit991narrative.htm)).
  The mechanism is the one thing that makes a bank a *beneficiary* of a shock rather than a
  victim: rate rises expand net interest income faster than they raise credit costs, at least
  early in the cycle.

- **2020-11-09, +16.6%.** JPM opened at $113.16 against a $102.96 prior close and finished at
  $116.90 on 47.8 million shares, the day Pfizer and BioNTech reported over 90% efficacy in the
  first Phase 3 interim analysis
  ([Pfizer press release, Nov 9 2020](https://www.pfizer.com/news/press-release/press-release-detail/pfizer-and-biontech-announce-vaccine-candidate-against)).
  Banks were the largest beneficiaries of the vaccine rotation because a reopening path collapses
  the expected credit loss on the 2020 loan-loss reserve build.

- **2020-03-30 and 2020-04-09, the policy backstop.** The March window base is the March 23
  close of $79.03, the exact day the FOMC committed to buying Treasuries and agency MBS "in the
  amounts needed to support smooth market functioning" and launched PMCCF, SMCCF, TALF, MMLF and
  CPFF ([Federal Reserve, Mar 23 2020](https://www.federalreserve.gov/newsevents/pressreleases/monetary20200323b.htm)).
  The CARES Act became law on March 27
  ([US Treasury](https://home.treasury.gov/policy-issues/coronavirus/about-the-cares-act)).
  The April window ends on the day the Fed announced up to $2.3trn of lending, including the
  $600bn Main Street Lending Program and the $500bn Municipal Liquidity Facility
  ([Federal Reserve, Apr 9 2020](https://www.federalreserve.gov/newsevents/pressreleases/monetary20200409a.htm)).
  Both are the same mechanism as November 2008: the sovereign caps the tail, and the bank equity
  that was pricing that tail reprices in days.

- **2011-08-08, -15.8%.** S&P downgraded the US from AAA to AA+ after the close on Friday
  August 5; the S&P 500 fell 6.5% on Monday August 8, the worst day since 2008
  ([Wikipedia, Black Monday 2011](https://en.wikipedia.org/wiki/Black_Monday_(2011)),
  [CNN Money](https://money.cnn.com/2011/08/08/markets/markets_newyork/index.htm),
  [NPR](https://www.npr.org/sections/thetwo-way/2011/08/06/139038762/s-p-lowers-united-states-long-term-rating)).
  Banks led the decline because a sovereign downgrade is simultaneously a collateral-value
  question and a growth question.

- **2011-12-06, +16.4%.** On November 30, 2011 six central banks cut the pricing on existing
  dollar liquidity swap lines by 50 basis points to OIS plus 50 and extended them to
  February 2013
  ([Federal Reserve, Nov 30 2011](https://www.federalreserve.gov/newsevents/pressreleases/monetary20111130a.htm)).
  European bank dollar funding was the binding constraint at the time and US money-centre banks
  were the counterparty exposure.

- **2020-06-08, +15.1%.** May 2020 payrolls rose by 2.5 million and unemployment fell to 13.3%
  from 14.7%, against a consensus expecting further heavy losses
  ([BLS Employment Situation, released June 5 2020](https://www.bls.gov/news.release/archives/empsit_06052020.htm)).
  Banks were the highest-beta expression of the reopening trade.

- **2009-04-16 and 2009-05-08, the all-clear.** Wells Fargo pre-announced a record $3bn quarter
  on April 9, 2009; JPM rose 19% that day
  ([MPR News](https://www.mprnews.org/story/2009/04/09/wells-fargo-projects-record-3-billion-1q-profit),
  [NBC News](https://www.nbcnews.com/news/amp/wbna30151303)). On May 7, 2009 the SCAP stress test
  results named JPMorgan among the nine of nineteen banks not required to raise capital
  ([Federal Reserve SCAP overview](https://www.federalreserve.gov/newsevents/files/bcreg20090507a1.pdf),
  [CNN Money](https://money.cnn.com/2009/05/07/news/companies/stress_test_announcement/index.htm)).
  These two events close the 2008-09 cluster: the sector's earnings power and its capital
  adequacy were both externally validated within a month.

---

## Regime

**JPM lives in a policy-and-solvency regime, not an earnings regime.**

Breaking the 30 events by what actually caused them:

| Driver | Count | Share |
|---|---|---|
| Systemic credit crisis or solvency panic | 9 | 30% |
| Macro data or index-level shock (payrolls, CPI, sovereign downgrade, COVID, vaccine) | 10 | 33% |
| Government or central bank policy action (Citi rescue, PPIP, SCAP, swap lines, Fed 2020) | 5 | 17% |
| Company earnings | 3 | 10% |
| Company idiosyncratic (WaMu, London Whale) | 2 | 7% |
| No confirmed catalyst | 1 | 3% |

Three consequences for the generator:

1. **Analogs transfer within the policy-backstop family, and almost nowhere else.** The
   November 2008 Citi rescue, March 2009 PPIP, March 2020 Fed open-ended QE and April 2020
   $2.3trn are structurally the same event: a sovereign caps a tail risk that bank equity had
   been pricing, and the equity reprices 15% to 35% in under a week. That is a genuinely
   reusable pattern. An NVDA product event is not an analog for any of them.

2. **The ledger is dominated by mean reversion off panic bases, and the pairing is tight.**
   -37.1% (Nov 20) then +35.4% (Nov 28), six trading days apart. -30.3% (Mar 6) then +49.1%
   (Mar 13), five trading days apart. -27.4% (Jan 20) then +38.5% (Jan 27). Any conditional
   ensemble built on this ticker will inherit a very fat two-sided tail and a strong short-horizon
   reversal signature. That is real, but it is a property of *crisis* JPM, not of JPM.

3. **The concentration is the limitation.** 20 of 30 events, and 10 of 10 `major` events, fall
   between 2008-01-23 and 2009-05-08. **JPM's `major` tier is one regime wearing ten hats**, which
   is exactly what CONTRACT.md §3 warned about, and this research confirms it empirically rather
   than by assumption. Concretely: if the model retrieves a JPM `major` analog for a 2020s query,
   it is retrieving a 2008-09 bank-solvency panic no matter what the query says. The `significant`
   tier is what rescues JPM as a seed, because it is the only tier that supplies 2011, 2012, 2020
   and 2022 observations.

**Direction asymmetry worth noting.** 18 of 30 events are up and 12 are down, and the largest
single move in either direction is an up move (+49.1%). For a bank in a crisis, upside gaps come
from policy announcements that arrive overnight and are not tradeable in size, while downside
gaps come from funding stress that compounds over days. The ensemble should not be symmetric.

---

## Ledger verdict

**The ledger survives contact with reality. I found no artifacts.**

Four specific checks, each against real price data rather than against memory:

1. **The arithmetic reproduces exactly.** I recomputed the 5-day close-to-close return from
   yfinance split-adjusted closes for eight events spanning four regimes and matched the ledger
   to five decimal places: 2008-03-24 ($36.54 to $46.55, +0.2739 vs ledger 0.273946);
   2008-11-20 ($37.19 to $23.38, -0.3713 vs -0.371336); 2008-11-28 (+0.3541 vs 0.354149);
   2008-12-08 (+0.3970 vs 0.397014); 2012-05-17 ($40.74 to $33.93, -0.1671 vs -0.167158);
   2020-03-09 (-0.2311 vs -0.231073); 2020-03-30 (+0.1831 vs 0.183095); 2022-10-18
   ($101.96 to $118.84, +0.1656 vs 0.165555). The detector is doing what it says.

2. **No split artifacts.** JPMorgan executed no stock split in 2008-2022, so the classic
   unadjusted-split false positive cannot be present here. Spot checks of the daily series across
   dividend dates (for example the $0.38 dividend on 2008-10-02 and $0.90 on 2020-04-03) show no
   discontinuity being counted as a move.

3. **No bad prints.** Every event date has a corroborating volume signature. The three largest
   moves all coincide with volume 3x to 6x normal: 160.7m shares on 2008-11-20, 217.3m on
   2012-05-11, 47.8m on 2020-11-09 against a 2020 baseline nearer 20m. A bad print does not bring
   volume with it.

4. **Non-maximum suppression is behaving.** Adjacent events are five or more trading days apart
   and the ledger keeps the extreme window rather than both halves of it. The two closest pairs
   (2008-11-20 and 2008-11-28; 2009-03-06 and 2009-03-13) are genuine sign-flipped events, not
   double counts of one move.

**One defect found, and it is in metadata rather than detection.** The `famous` flag is
unreliable and should not be used as the "obscure versus famous" split that CONTRACT.md §8.2
requires. 2008-10-09, the end of the worst week in Dow history, is flagged `famous: false`.
2009-03-13, the week the market bottomed, is flagged `famous: false`. 2008-11-20 and 2009-01-20
are likewise flagged false. Meanwhile 2008-10-01 is flagged `true`. If the eval lane splits
results on this field, the "obscure" bucket will be full of the single most memorized week in
modern market history and the leakage disclosure will be measuring nothing. **Recommendation to
the parent: recompute `famous` from an external salience signal, or hand-label it, before it is
used in scoring.** This is a ledger-consumer issue, not a detection issue.

**Coverage:** 29 of 30 events have a dated, sourced mechanism. One does not.

---

## Unexplained

**2009-01-27, +38.5% (major).** I could not verify a catalyst dated inside the January 21 to
January 27 window. The two nearest candidates both fall outside it: Geithner's swearing-in on
January 26 is in-window but is a personnel event that does not on its own explain a 38% move in
a bank stock, and the "bad bank" aggregator reporting that CNN ties to a broad bank rally is
dated January 28, the day *after* the ledger date. The honest reading is that the move is
dominated by the January 20 capitulation base, with an unidentified policy-expectation catalyst
supplying the rest. **I am recording it as unexplained rather than attaching the January 28
story to a January 27 date.** If this event is used as a seed, its narrative field should say so.

**2009-01-09, -17.2% (significant), weakly explained.** December 2008 payrolls fell 524,000 and
unemployment rose to 7.2%, released the morning of January 9
([BLS Employment Situation, Jan 9 2009](https://www.bls.gov/news.release/archives/empsit_01092009.pdf),
[CNN Money pre-market](https://money.cnn.com/2009/01/09/markets/stockswatch/index.htm)). That is
a real, correctly dated catalyst, but a payrolls print of the expected sign does not obviously
account for a 17% weekly move in a single bank, and I did not find a JPM-specific driver in the
December 31 to January 9 window. Confidence 0.55. Treat the cause as partial.

**Not researched to the same depth:** none. All 30 events were examined.
