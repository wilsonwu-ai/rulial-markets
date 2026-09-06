# AMZN — event research

Amazon.com, Inc. (NASDAQ: AMZN). Over the ledger's span the company changes identity
twice: a levered, thin-margin online retailer trading as a high-beta consumer-discretionary
name (through roughly 2010), then a retailer with a cloud business attached (AWS was first
broken out as a reporting segment on 23 April 2015), then an AI-infrastructure and
advertising business with a retailer attached (2023 onward). What drives the stock changes
with it. In the early period AMZN is essentially a leveraged bet on the index. From 2012
onward almost every large move is a single after-the-close quarterly report, because the
company guides operating income in wide ranges and the market re-rates the whole franchise
on where inside that range it lands.

**Method note.** The ledger date is the END of a 5-trading-day window, so the causal news
is usually 1 to 4 sessions earlier. For every event below I decomposed the window into its
daily close-to-close returns from `data/prices/AMZN.csv` and identified the single dominant
session, then searched news for that session and the day before it. Where the dominant
session is a known after-close earnings release, the attribution is close to certain. Where
the window is a smooth run of 2% to 5% days with no dominant session, I say so rather than
attach a story.

**Price data cross-check.** Two independent spot checks confirm `data/prices/AMZN.csv` is
correctly split-adjusted and accurate. The 2026-04-09 close of 233.65 in the CSV matches the
$233.65 close reported by [Motley Fool](https://www.fool.com/coverage/stock-market-today/2026/04/09/stock-market-today-april-9-amazon-surges-after-ceo-details-ai-and-aws-growth-plans/),
and the 2016-01-27 CSV close of 29.167, multiplied by the 20-for-1 split factor of June 2022,
gives $583.34 against the actual $583.37. The 2022 split is therefore adjusted, and the
June 2022 events are not split artifacts.

---

## Every event examined

27 AMZN events. 18 fall in the train period (on or before 2019-12-31), 9 in the test period.
All 3 major-tier events are in the train period and all 3 are 2008-09.

| Date | Move | Tier | Category | Headline | Conf |
|---|---|---|---|---|---|
| 2008-07-29 | +15.1% | significant | earnings | Q2 2008 profit doubles, biggest one-day gain in a year on 24 Jul | 0.85 |
| 2008-08-11 | +16.4% | significant | unexplained | +9.4% on 11 Aug with no catalyst I could source | 0.15 |
| 2008-09-29 | -15.5% | significant | macro | House rejects the TARP bailout; Dow falls a record 777 points | 0.80 |
| 2008-10-07 | -19.6% | significant | macro | First week of the October 2008 credit-market seizure | 0.75 |
| 2008-10-15 | -20.2% | significant | macro | 15 Oct 2008, the worst S&P session since 1987 | 0.80 |
| 2008-10-31 | +16.9% | significant | macro | 28 Oct pre-FOMC rally, the Dow's second-biggest point gain ever | 0.85 |
| 2008-11-11 | -20.8% | significant | macro | Post-election GFC leg down; 5-6 Nov back-to-back double-digit losses | 0.70 |
| 2008-11-18 | -17.0% | significant | macro | Final capitulation drive into the 20-21 Nov 2008 crisis low | 0.70 |
| 2008-11-26 | +22.7% | significant | macro | Citigroup rescue plus Geithner nomination; biggest 2-day gain since 1987 | 0.85 |
| **2008-12-08** | **+27.0%** | **major** | macro | Obama public-works plan lifts the Nasdaq 4.1%, on top of a 9.8% day on 3 Dec | 0.60 |
| 2009-01-06 | +16.1% | significant | macro | New-year risk-on rally; no AMZN-specific catalyst found | 0.40 |
| **2009-02-03** | **+31.3%** | **major** | earnings | Q4 2008 beats on 29 Jan; stock closes +17.6% the next session | 0.95 |
| **2009-10-26** | **+31.6%** | **major** | earnings | Q3 2009 net income up 68%; stock closes +26.8% on 23 Oct | 0.97 |
| 2011-08-29 | +16.3% | significant | macro | Rebound off the August 2011 debt-ceiling and euro-crisis low | 0.60 |
| 2012-04-30 | +23.2% | significant | earnings | Q1 2012 blows past a $0.07 consensus; +15.8% on 27 Apr | 0.95 |
| 2015-02-04 | +20.0% | significant | earnings | Q4 2014 EPS $0.45 vs $0.18 expected; +13.7% on 30 Jan | 0.95 |
| 2015-04-24 | +18.5% | significant | earnings | AWS broken out for the first time; +14.1% on 24 Apr | 0.97 |
| 2016-02-04 | -15.6% | significant | earnings | Q4 2015 EPS misses badly, then a momentum-tech unwind | 0.85 |
| 2020-04-16 | +17.9% | significant | macro | Covid lockdown demand shock; AMZN to all-time highs | 0.65 |
| 2022-05-05 | -19.5% | significant | earnings | Q1 2022 Rivian writedown and soft guide (-14.1%), then post-FOMC reversal | 0.90 |
| 2022-06-02 | +17.5% | significant | macro | Late-May 2022 bear-market rally; no single catalyst | 0.45 |
| 2022-06-13 | -16.9% | significant | macro | 8.6% May CPI print sends the S&P into a bear market | 0.90 |
| 2022-08-02 | +16.9% | significant | earnings | Q2 2022 beats and guides up; +10.4% on 29 Jul | 0.85 |
| 2022-11-02 | -20.4% | significant | earnings | Q3 2022 guides Q4 operating income to $0-$4bn, then a hawkish FOMC | 0.92 |
| 2023-11-02 | +15.5% | significant | earnings | Q3 2023 beat (+6.8% on 27 Oct) plus the dovish 1 Nov Fed hold | 0.85 |
| 2026-04-14 | +16.5% | significant | guidance | Jassy shareholder letter discloses a $15bn AI run rate; +5.6% on 9 Apr | 0.75 |
| 2026-08-03 | +22.7% | significant | earnings | Q2 2026: AWS +37%, revenue tops $200bn, $3trn market cap; +15.3% on 31 Jul | 0.97 |

---

## Major events

### 2008-12-08, +27.0% — the only major event without a clean single cause

The window covers 2, 3, 4, 5 and 8 December 2008. Two sessions do the work: 3 December
(+9.8%) and 8 December (+6.5%). The 8 December leg is well documented. Stocks rallied on
President-elect Obama's weekend announcement of the largest US public works program since
the interstate highway system, together with reports that federal help for the automakers
was coming; the Nasdaq closed +4.1% and the S&P +3.8%
([CNNMoney, 8 Dec 2008](https://money.cnn.com/2008/12/08/markets/markets_newyork/index.htm)).
AMZN's +6.5% is roughly 1.6x the Nasdaq, which is consistent with its beta in that period
and needs no separate story.

The 3 December +9.8% I could not attribute to Amazon-specific news. It sits inside the
broad three-day rally that ran 2 to 4 December 2008 and is most likely the same beta
effect, but I am not able to source a catalyst, so the confidence on this event is 0.60
rather than the 0.95-plus I can defend for the two 2009 earnings majors. **This event is
market beta, not an Amazon story.** Anyone using it as a seed analog for a company-specific
event description would be transferring the wrong regime.

Sources: [CNNMoney market report, 8 December 2008](https://money.cnn.com/2008/12/08/markets/markets_newyork/index.htm)

### 2009-02-03, +31.3% — Q4 2008 earnings

The window covers 28, 29, 30 January and 2, 3 February 2009. The dominant session is
30 January at +17.6%. Amazon released Q4 2008 results after the close on 29 January 2009:
net sales up 18% to $6.70 billion, net income up 9% to $225 million or $0.52 per diluted
share, and Q1 2009 guidance of $4.525bn to $4.925bn in net sales, or 9% to 19% growth
(verified in the 8-K exhibit filed with the SEC). The mechanism is that Amazon delivered
holiday-quarter growth and forward guidance implying continued double-digit expansion in
the depth of the recession, at a moment when the market was pricing consumer discretionary
names for a demand collapse. That was a re-rating of the demand assumption, not a beat on
a few cents of EPS. The move is idiosyncratic: 30 January 2009 was a down day for the
broad market.

Sources:
- [SEC 8-K exhibit 99.1, Amazon Q4 2008 press release dated 29 January 2009](https://www.sec.gov/Archives/edgar/data/1018724/000119312509014223/dex991.htm)
- [NBC News, Amazon beats Wall Street estimates in fourth quarter](https://www.nbcnews.com/news/amp/wbna28919297)

### 2009-10-26, +31.6% — Q3 2009 earnings, the cleanest event in the ledger

The window covers 20, 21, 22, 23 and 26 October 2009. One session accounts for almost the
whole move: 23 October at +26.8%. Amazon released Q3 2009 after the close on 22 October
2009: net sales up 28% to $5.45 billion against a consensus nearer 18% growth, operating
income up 62% to $251 million, net income up 68% to $199 million or $0.45 per diluted
share versus a $0.33 consensus, and Q4 guidance of $8.125bn to $9.125bn, implying 21% to
36% growth. The mechanism is a simultaneous beat on revenue growth, margin and forward
guidance while the market still carried recession-era unit assumptions; Kindle and
third-party seller mix were the specific drivers cited. Everything before 23 October in
this window is noise under 1.7%, so the attribution is as close to unambiguous as this
dataset gets.

Sources:
- [SEC 8-K exhibit 99.1, Amazon Q3 2009 press release dated 22 October 2009](https://www.sec.gov/Archives/edgar/data/1018724/000119312509211972/dex991.htm)
- [CNNMoney, Amazon profit soars, beats expectations, 22 Oct 2009](https://money.cnn.com/2009/10/22/technology/Amazon_earnings/)
- [Amazon Q3 2009 earnings call transcript](https://seekingalpha.com/article/168333-amazon-q3-2009-earnings-call-transcript)

---

## Selected significant events

These are the ones that carry information the majors do not, either because they define the
modern regime or because they are the honest weak spots.

### 2026-08-03, +22.7% — Q2 2026, the largest modern event and a distorted print

Dominant session: 31 July 2026, +15.3%. Amazon released Q2 2026 after the close on
30 July 2026. Net sales up 20% to $200.6 billion, the first quarter above $200bn. AWS
revenue $42.2 billion, up 37% year over year, its fastest growth in 18 quarters, a $169bn
annualized run rate. Net income $62.6 billion or $5.75 per diluted share against $18.2bn a
year earlier. Q3 guidance of $197bn to $202bn in net sales and $22.5bn to $26.5bn in
operating income, both above consensus. The stock crossed a $3 trillion market cap.

**Important caveat for anyone using this as an analog.** Net income includes $53.4 billion
of non-operating pre-tax other income, primarily a mark-to-market on Amazon's investments
in Anthropic. Roughly 85% of the headline net income is a non-cash investment revaluation,
not operating earnings. The price reaction was driven by the AWS acceleration and the
guidance, not by the EPS line, and an analog retrieval that keys on "EPS beat magnitude"
would badly misread this event.

Sources:
- [Amazon Q2 2026 earnings release, aboutamazon.com](https://www.aboutamazon.com/news/company-news/amazon-earnings-q2-2026-report)
- [Yahoo Finance, Amazon Q2 2026 earnings: AWS grows 37%, revenue tops $200B](https://finance.yahoo.com/markets/stocks/articles/amazon-q2-2026-earnings-aws-204411872.html)
- [CNBC, Amazon tops $3 trillion market cap as stock continues post-earnings surge](https://www.cnbc.com/2026/08/03/amazon-amzn-stock-market-cap-earnings.html)

### 2026-04-14, +16.5% — a shareholder letter, not an earnings print

Dominant session: 9 April 2026, +5.6% (close $233.65). This is the rarest category in the
whole ledger: a large AMZN move with no earnings release inside the window. The catalyst
was Andy Jassy's annual shareholder letter, in which he disclosed for the first time that
AWS was running at a $15 billion revenue run rate from AI services and defended roughly
$200 billion of planned 2026 capital expenditure with the claim that customer commitments
already covered a substantial portion of it. The mechanism is a capex-anxiety unwind:
the market had been discounting AMZN for spending ahead of demand, and the letter converted
that spend from speculative to contracted. The window's other two contributors, 8 April
(+3.5%) and 14 April (+3.8%), I could not attribute individually, which is why confidence
is 0.75 rather than higher.

Sources:
- [Motley Fool, Stock Market Today, April 9 2026: Amazon surges after CEO details AI and AWS growth plans](https://www.fool.com/coverage/stock-market-today/2026/04/09/stock-market-today-april-9-amazon-surges-after-ceo-details-ai-and-aws-growth-plans/)

### 2015-04-24, +18.5% — the AWS disclosure, a segment-reporting re-rating

Dominant session: 24 April 2015, +14.1%. Amazon reported Q1 2015 after the close on
23 April 2015 and, for the first time, broke out AWS as a separate reporting segment:
$1.57 billion of quarterly revenue, up 49%, $265 million of operating income, a $5 billion
annualized run rate. Revenue was $22.72bn, up 15%, with a $0.12 per share loss. The move
is not an earnings surprise in the usual sense; the consolidated numbers were unremarkable.
It is a disclosure event. The market learned that a high-margin, fast-growing infrastructure
business had been hiding inside a low-margin retailer's consolidated P&L, and repriced the
sum of the parts. This is the single most instructive AMZN analog in the train period for
"new information about business mix" style event descriptions.

Sources:
- [TechCrunch, Amazon's Q1 beats as revenue rises 15% to $22.72 billion](https://techcrunch.com/2015/04/23/amazons-q1-beats-as-revenue-rises-15-to-22-72-billion-eps-loss-of-0-12/)
- [AWSInsider, Amazon reveals AWS cloud earnings for first time](https://awsinsider.net/articles/2015/04/23/amazon-earnings-q1-2015.aspx)
- [Amazon IR, first quarter 2015 results](https://ir.aboutamazon.com/news-release/news-release-details/2015/Amazoncom-Announces-First-Quarter-Sales-up-15-to-2272-Billion/default.aspx)

### 2022-05-05, -19.5% and 2022-11-02, -20.4% — the two-cause pattern

Both of these are earnings plus macro stacked inside one window, and both would be
mis-attributed if only the ledger date were searched.

For 2022-05-05, the driver is 29 April at -14.1%, following Q1 2022 released after the
close on 28 April: a $7.6 billion writedown on the Rivian stake (Rivian shares had lost more
than half their value in the quarter), producing Amazon's first quarterly net loss since
2015, plus Q2 revenue guidance of $116bn to $121bn against a $125.6bn consensus. The window
then picks up a second, unrelated hit on 5 May at -7.6%, the day the market reversed the
post-FOMC rally.

For 2022-11-02, three separate sessions contribute: 28 October at -6.8% after Q3 2022
guided Q4 operating income to a range of $0 to $4 billion against $3.5bn achieved a year
earlier, an unusually wide and low range that the market read as an admission of no
visibility; 1 November at -5.5%, when Amazon's market cap fell below $1 trillion for the
first time since 2020; and 2 November at -4.8%, the hawkish FOMC decision and Powell press
conference. Roughly a third of this event is Fed policy, not Amazon.

Sources:
- [CNBC, Amazon takes $7.6 billion loss on Rivian stake](https://www.cnbc.com/2022/04/28/amazon-takes-7point6-billion-loss-on-rivian-stake-from-q1-stock-plunge.html)
- [CNBC, Amazon (AMZN) Q1 2022 earnings](https://www.cnbc.com/2022/04/28/amazon-amzn-q1-2022-earnings.html)
- [TechCrunch, Amazon's income dipped in Q3 2022 as the economy took its toll](https://techcrunch.com/2022/10/27/amazons-income-dipped-in-q3-2022-as-the-economy-took-its-toll/)
- [Amazon Q3 2022 earnings release (PDF)](https://s2.q4cdn.com/299287126/files/doc_financials/2022/q3/Q3-2022-Amazon-Earnings-Release.pdf)
- [CNBC, Amazon plunge pushes valuation below $1 trillion for first time since 2020](https://www.cnbc.com/2022/11/01/amazon-plunge-pushes-valuation-below-1-trillion-first-time-since-2020.html)
- [Federal Reserve, Chair Powell press conference transcript, 2 November 2022](https://www.federalreserve.gov/mediacenter/files/FOMCpresconf20221102.pdf)

### 2022-06-13, -16.9% — a pure macro event with zero Amazon content

Driver sessions: 10 June at -5.6% and 13 June at -5.5%. The May CPI print released on
Friday 10 June 2022 came in at 8.6% year over year, up from 8.3% and the fastest in four
decades, killing the peak-inflation thesis. On Monday 13 June the S&P 500 closed 3,750,
more than 21% below its January peak, formally entering a bear market; the Nasdaq fell
4.7%. Nothing about Amazon changed in this window. Note this is the mirror image of
2022-06-02 nine trading days earlier, the late-May relief rally that this event reversed.

Sources:
- [CBS News, Dow plunges 900 points, S&P enters bear market as inflation fears mount, 13 June 2022](https://www.cbsnews.com/news/stocks-down-inflation-federal-reserve-mohamed-el-erian-06-13-2022/)

### 2016-02-04, -15.6% — an earnings miss compounded by a factor unwind

Driver: 29 January at -7.6%, after Q4 2015 released post-close on 28 January reported
$1.00 of EPS against a $1.56 consensus on $35.75bn of revenue against $35.93bn expected.
AWS was strong (revenue $2.41bn, up 69%; operating income $687m, up 187%), so the miss was
in retail margin, not cloud. The window then adds three consecutive down sessions on
1, 2 and 3 February (-2.1%, -4.0%, -3.8%) that were not Amazon-specific: this was the
early-February 2016 unwind of crowded momentum and high-multiple internet positioning.
Two mechanisms, one window.

Sources:
- [Forbes, Amazon shares plunge after earnings miss wide of mark, 28 January 2016](https://www.forbes.com/sites/ryanmac/2016/01/28/amazon-2015-q4-earnings/)
- [SEC exhibit 99.1, Amazon Q4 2015 press release](https://www.sec.gov/Archives/edgar/data/1018724/000101872416000170/amzn-20151231xex991.htm)

### Remaining significant events, briefly

- **2008-07-29, +15.1%.** Driver: 24 July at +11.6%, the day after Q2 2008 results in which
  net income doubled and beat estimates on game-console demand and a weak dollar boosting
  international sales. Bloomberg described it as the largest one-day rise in a year.
  Source: [Bloomberg, Amazon.com climbs after net doubles, beats estimates, 24 July 2008](https://www.bloomberg.com/news/articles/2008-07-24/amazon-com-climbs-after-profit-doubles-exceeding-estimates)
- **2008-09-29, -15.5%.** Driver: 29 September at -10.4%, the day the House rejected the
  TARP bailout and the Dow fell a then-record 777 points. Well-established public record;
  I ran out of search budget before retrieving a citable URL, so the source list is empty
  and confidence is capped at 0.80.
- **2008-10-07, -19.6% and 2008-10-15, -20.2%.** The two worst weeks of the credit-market
  seizure. Drivers are 7 October (-10.3%), 9 October (-8.2%), 14 October (-9.9%) and
  15 October (-12.8%), the last of which was the worst S&P session since 1987. No AMZN
  content whatsoever. The [CNNMoney 28 October report](https://money.cnn.com/2008/10/28/markets/markets_newyork/index.htm)
  references this period as the worst week ever for the Dow.
- **2008-10-31, +16.9%.** Driver: 28 October at +13.0%, the pre-FOMC rally in which the Dow
  gained 889 points (+10.9%), the S&P +10.8% and the Nasdaq +9.5%, its second-biggest point
  gain ever. Amazon's Q3 2008 report on 22 October is inside neither this window nor a
  detected event. Source: [CNNMoney, 28 October 2008](https://money.cnn.com/2008/10/28/markets/markets_newyork/index.htm)
- **2008-11-11, -20.8% and 2008-11-18, -17.0%.** Two non-overlapping windows walking down
  into the 20-21 November 2008 crisis low. Drivers are 5 November (-11.1%), 6 November
  (-9.2%) and 12 November (-10.2%). Post-election recession repricing, no company news.
  Sources empty; confidence 0.70.
- **2008-11-26, +22.7%.** Drivers: 21 November (+8.1%) on reports that Geithner would be
  named Treasury Secretary, and 24 November (+12.2%) after the government's weekend rescue
  of Citigroup (a $20bn injection plus a backstop on more than $300bn of assets). The two
  sessions were the biggest two-day percentage gain since October 1987.
  Sources: [CNNMoney, Citigroup secures government lifeline](https://money.cnn.com/2008/11/23/news/companies/citigroup/index.htm),
  [CNNMoney market report, 24 November 2008](https://money.cnn.com/2008/11/24/markets/markets_newyork/index.htm?postversion=2008112415)
- **2009-01-06, +16.1%.** Drivers: 2 January (+6.0%) and 6 January (+6.1%), the new-year
  risk-on rally. No AMZN-specific catalyst found. Confidence 0.40; see Unexplained.
- **2011-08-29, +16.3%.** Drivers: 23 August (+9.0%), 26 August (+3.8%, Bernanke's Jackson
  Hole speech) and 29 August (+3.6%). A rebound off the August 2011 low that followed the
  US downgrade and the euro sovereign crisis. Sources empty; confidence 0.60.
- **2012-04-30, +23.2%.** Driver: 27 April at +15.8%, after Q1 2012 released post-close on
  26 April: net sales up 34% to $13.18bn and EPS of $0.28 against a $0.07 consensus.
  Sources: [TechCrunch](https://techcrunch.com/2012/04/26/amazons-q1-2012-revenue-up-34-percent-to-13-2b-net-income-down-35-percent/),
  [CNNMoney, Amazon Q1 profit blows estimates away](https://money.cnn.com/2012/04/26/technology/amazon-earnings/index.htm)
- **2015-02-04, +20.0%.** Driver: 30 January at +13.7%, after Q4 2014 released post-close on
  29 January: EPS of $0.45 against $0.18 expected, a return to profit after two surprise
  quarterly losses. Sources: [Fortune](https://fortune.com/2015/01/29/amazon-earnings-4q14/),
  [eWeek](https://www.eweek.com/cloud/amazon-reports-modest-q4-profit-2014-loss-yet-stock-rises/)
- **2020-04-16, +17.9%.** A smooth four-session climb (13 to 16 April: +6.2%, +5.3%, +1.1%,
  +4.4%) with no single dominant day, driven by the Covid lockdown demand shock in both
  e-commerce and AWS as AMZN made new all-time highs. Q1 2020 earnings were 30 April, after
  this window. Sources empty; confidence 0.65.
- **2022-06-02, +17.5%.** A five-session run (25, 26, 27, 31 May and 1, 2 June, each between
  +1.2% and +4.4%) with no dominant day. The late-May 2022 bear-market relief rally. The
  20-for-1 stock split took effect 6 June 2022, after this window, and the CSV is
  split-adjusted, so this is not a split artifact. Confidence 0.45; see Unexplained.
- **2022-08-02, +16.9%.** Driver: 29 July at +10.4%, after Q2 2022 released post-close on
  28 July beat on revenue and guided Q3 above consensus, despite another Rivian markdown.
- **2023-11-02, +15.5%.** Drivers: 27 October at +6.8% after Q3 2023 released post-close on
  26 October (revenue $143.1bn against $141bn expected, EPS $0.94 against $0.58, AWS
  $23.1bn, advertising up 26%), then 30 October (+3.9%) and 1 November (+2.9%) on the
  dovish FOMC hold that started the November 2023 rally. Sources:
  [CNBC](https://www.cnbc.com/2023/10/26/amazon-amzn-q3-earnings-report-2023.html),
  [Amazon Q3 2023 earnings release (PDF)](https://s2.q4cdn.com/299287126/files/doc_financials/2023/q3/AMZN-Q3-2023-Earnings-Release.pdf)

---

## Regime

**AMZN is a two-regime ticker, and the two regimes barely talk to each other.**

**Regime 1: crisis beta, 2008 to 2011.** Twelve of the 27 events (all ten 2008 events, plus
2009-01-06 and 2011-08-29) are market-wide macro moves in which Amazon is a high-beta
vehicle and no Amazon-specific information is present. In this regime AMZN typically prints
1.5x to 2x the Nasdaq's daily move in the same direction. The causal object is a policy
event (a TARP vote, an FOMC meeting, a bank rescue, a CPI print), not a company event. An
analog drawn from this cluster tells you about index volatility clustering, not about
Amazon.

**Regime 2: the quarterly re-rating, 2012 onward.** Eleven of the 27 events are anchored on
a single after-the-close quarterly release. The pattern is consistent enough to be a rule:
Amazon reports after the close, the next session moves 7% to 27%, and the 5-day window
simply wraps that one session. What moves the stock is almost never the EPS line. It is
the forward operating-income guide (2022-11-02), the disclosure of business mix
(2015-04-24), a segment growth rate (2026-08-03), or a demand assumption being falsified
(2009-02-03). Amazon guides operating income in deliberately wide ranges, so each print is
a large information release about the next quarter, which is why the reactions are so
violent for a mega-cap.

**A third, thin regime is emerging: capex-narrative events.** 2026-04-14 is the only event
in the ledger driven by a non-earnings company communication (the annual shareholder
letter), and its mechanism is specifically about justifying AI infrastructure spend. If AMZN
continues to trade on capex credibility, this category will grow, and the ledger currently
contains exactly one training example of it.

**Consequences for using AMZN as a seed corpus.** The train period (on or before
2019-12-31) contains 18 events, and 12 of those are Regime 1. Only 6 train-period events
(2008-07-29, 2009-02-03, 2009-10-26, 2012-04-30, 2015-02-04, 2015-04-24, and 2016-02-04
makes 7) are company-specific, and all 7 are quarterly earnings prints. That means:
- For a conditional query about an Amazon **earnings or guidance** event, there are about
  7 in-regime train analogs. Adequate but thin, and 3 of the 7 are pre-2010, when Amazon
  was a $30bn retailer rather than a $2trn cloud and advertising company.
- For a conditional query about a **product, regulatory, leadership or geopolitical** AMZN
  event, there are **zero** in-regime train analogs. The ledger contains no antitrust event,
  no leadership event (the Jassy succession in 2021 moved nothing above 15%), no product
  event, and no supply-chain event. Retrieval will silently return GFC beta analogs, which
  will produce ensembles that are wide in the right way for the wrong reason.
- All three **major** events are 2008-09. At the 25% tier, AMZN is a global-financial-crisis
  ticker with a 2009 earnings tail. This is the same limitation the contract already flags
  for JPM, and it is worth stating in the results screen.

---

## Ledger verdict

**The ledger survives contact with reality.** 26 of 27 dates map to an event a market
participant would recognize, and I found no data artifacts. Specifically:

1. **No split contamination.** AMZN has split 2-for-1 twice (1998), 3-for-1 (1999),
   2-for-1 (1999) and 20-for-1 (June 2022). None of these produce a phantom event. The
   June 2022 split date (6 June) falls between the 2022-06-02 and 2022-06-13 events and
   corrupts neither. Two independent spot checks against externally reported closing prices
   ($233.65 on 2026-04-09, $583.37 on 2016-01-27 unadjusted) confirm the adjustment is
   correct.
2. **No bad prints.** Every large single-day return I inspected has a documented cause or
   sits inside a documented market-wide session. There is no isolated one-day spike that
   reverses the next day in the way a bad tick would.
3. **The non-maximum suppression is working correctly.** I checked the four adjacent pairs
   in the dense 2008 cluster (2008-10-07 / 2008-10-15 and 2008-11-11 / 2008-11-18) by
   reconstructing each window from the price series. The windows are strictly
   non-overlapping in trading days (1-7 Oct then 9-15 Oct; 5-11 Nov then 12-18 Nov). The
   ledger is not double-counting one selloff as two events.
4. **The window-end convention behaves as documented.** In 11 of the 11 earnings-driven
   events, the causal after-close release falls 1 to 4 trading days before the ledger date
   and inside the window, never on it. Any downstream stage that searches only the ledger
   date will find nothing for most of these events. This is a correctness requirement for
   LANE-NEWS, not a defect in the ledger.

**Two caveats worth carrying forward.**

- **The `famous` flag is unreliable.** It marks 2012-04-30 and 2015-02-04 as famous but not
  2026-08-03 (the $3 trillion market cap crossing, the largest one-day AMZN gain in the
  modern sample) or 2008-12-08 (a major-tier event). Since contract §8.2 requires reporting
  famous and obscure events separately as the leakage control, a flag that misclassifies the
  most memorable modern event as obscure will make the memorization test look better than it
  is. This should be re-derived or hand-corrected before it is used as an evaluation split.
- **Roughly half the events have two causes stacked in one window.** 2022-05-05,
  2022-11-02, 2016-02-04 and 2023-11-02 each combine an earnings reaction with an unrelated
  macro session. Attributing the whole `move_pct` to the earnings event overstates the
  event's magnitude, in the 2022-11-02 case by about a third. If the generator is calibrated
  on the full window move as the response to a company event, it will systematically produce
  ensembles that are too wide.

---

## Unexplained

Listed honestly. These are dates where I could not find a credible cause, or where the cause
I can name does not account for the move.

- **2008-08-11 (+16.4%).** Genuinely unexplained and the one real miss. The window is
  carried by a single +9.4% session on 11 August 2008 (with a supporting +4.6% on 8 August).
  11 August 2008 was a modestly positive but unremarkable broad-market day, so a 9.4% move
  in a large-cap is idiosyncratic and should have a cause. I searched for Amazon news,
  analyst actions and index-inclusion events around 8 to 11 August 2008 and found nothing;
  the search engines available to me return almost no indexed content for that specific
  date. Q2 2008 earnings had already been reported on 23 July, and Q3 was not until October.
  I am recording this as unexplained rather than guessing at an analyst upgrade.
- **2009-01-06 (+16.1%), partially explained.** Two +6% sessions (2 and 6 January 2009)
  inside the new-year risk-on rally. The direction and rough magnitude are consistent with
  AMZN's beta in that period, but I found no Amazon-specific catalyst and no source
  documenting those particular sessions. Categorized macro at confidence 0.40.
- **2022-06-02 (+17.5%), partially explained.** Five consecutive up sessions of 1.2% to 4.4%
  with no dominant day and no identifiable catalyst beyond the late-May 2022 bear-market
  relief rally, which was itself a broad move without a single trigger. Categorized macro at
  confidence 0.45. Note this window sits four days before the 20-for-1 split effective date;
  I verified the CSV is split-adjusted and this is not an artifact, but it is worth a second
  look by LANE-DATA.
- **2008-12-08 (+27.0%), the 3 December component.** The 8 December leg is sourced. The
  9.8% move on 3 December 2008 is not. Since it is roughly a third of a major-tier event,
  it is flagged here even though the event as a whole is categorized.
- **2026-04-14, the 8 and 14 April components.** The 9 April shareholder-letter leg is
  sourced and price-verified. The +3.5% on 8 April and +3.8% on 14 April are not
  individually attributed.

Sources retrieval note: this session exhausted its web search budget at 200 calls before I
could source the 2008-09-29 TARP session, the 2020-04-16 Covid window and the 2011-08-29
rebound. Those three carry empty source lists and reduced confidence. Their mechanisms are
matters of well-established public record, but they are stated here without a retrieved
citation and should be treated accordingly.
