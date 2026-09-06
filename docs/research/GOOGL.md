# GOOGL — event research

**Ticker.** Alphabet Inc. Class A (Google Inc. before the October 2015 holding-company
reorganization). Ledger prices are split-adjusted, so pre-2014 quotes in this file appear at
roughly 1/50th of the headline prices reported in contemporaneous press coverage (the 2:1
Class C distribution of April 2014 plus the 20:1 split of July 2022).

**What drives it.** Through the whole ledger window Google is a single-product economics story:
search advertising revenue, and specifically the two variables the company disclosed each
quarter, paid clicks and cost-per-click. Every one of GOOGL's idiosyncratic jumps in this
ledger is a quarterly print resolving a live disagreement about whether ad monetization was
decelerating. There is no product-launch event, no leadership event, and no crisis event in
the entire history. The remaining events are market beta during two macro dislocations
(autumn 2008 and March 2020).

## Every event examined

Move column is the ledger's 5-trading-day close-to-close return, which I re-derived from
split-adjusted yfinance daily bars and matched to six decimal places in all nine cases.

| Date | Move | Tier | Category | Headline | Confidence |
|---|---|---|---|---|---|
| 2008-04-22 | +24.2% | significant | earnings | Q1 2008 beat kills the comScore paid-click scare; stock gaps +20% on 18 Apr | 0.95 |
| 2008-10-08 | -17.9% | significant | macro | The credit-freeze week: coordinated six-central-bank rate cut fails to stop the rout | 0.90 |
| 2008-11-11 | -15.1% | macro + regulatory | macro | Post-election plunge, and Google walks away from the Yahoo ad deal under DOJ threat | 0.70 |
| 2008-11-20 | -16.8% | significant | macro | Capitulation into the 20 Nov S&P close of 752, lowest since 1997 | 0.90 |
| 2009-01-27 | +17.2% | significant | earnings | Q4 2008 beats on an ex-items basis; GAAP profit down 70% but the ad apocalypse did not arrive | 0.85 |
| 2013-10-18 | +16.0% | significant | earnings | Q3 2013 mobile and YouTube beat; GOOG closes above $1,000 for the first time | 0.95 |
| 2015-07-17 | **+25.8%** | **major** | earnings | Ruth Porat's first quarter as CFO; +16% in a day, ~$65bn of market cap, then a record | 0.97 |
| 2020-03-12 | -15.5% | significant | macro | COVID crash; 12 Mar was the worst US session since 1987 | 0.95 |
| 2020-11-04 | +15.6% | significant | earnings | Q3 2020 blowout on 29 Oct, then the divided-government tech melt-up on 4 Nov | 0.90 |

Only one event clears the 25% major tier, and it is to the upside.

## Major event

### 2015-07-17, +25.8% over five days

**What happened.** Google reported Q2 2015 after the close on Thursday 16 July. Adjusted EPS
of $6.99 beat a consensus of roughly $6.70 to $6.75, and ex-TAC revenue of $14.35bn beat
$14.27bn ([TechCrunch, 16 Jul
2015](https://techcrunch.com/2015/07/16/google-q2-2015-earnings/)). It was the first quarter
reported by Ruth Porat, who had joined from Morgan Stanley in May. On Friday 17 July the stock
opened at an adjusted $34.00 against the prior close of $30.09 and finished at $34.98, a
+16.3% single day on 257m shares, roughly six times normal volume. Bloomberg reported the move
added about $65bn of market value in one session ([Bloomberg, 23 Jul
2015](https://www.bloomberg.com/news/articles/2015-07-23/google-cfo-ruth-porat-brings-fiscal-discipline)).

**Why it moved.** Two things resolved at once. The numbers themselves were a modest beat, on
the order of 4% on EPS, which does not explain a 16% repricing on its own. The larger input was
Porat's language on the call about expense discipline and headcount, which the market read as
the end of unbounded "other bets" spending by a founder-controlled company that had never
before signalled cost restraint. The multiple, not the quarter, is what re-rated. Mobile search
monetization and YouTube growth removed the second overhang, that desktop-to-mobile transition
was structurally deflationary for Google's revenue per query.

**Window mechanics.** The ledger date is 17 July and the causal news is 16 July after the
close, exactly the offset the detection window is designed to capture. Note that GOOGL had also
already run +8.3% over 10 to 15 July before the print, so the five-day window flatters the
event slightly. The clean single-day event size is +16.3%, not +25.8%.

Sources:
- https://techcrunch.com/2015/07/16/google-q2-2015-earnings/
- https://www.bloomberg.com/news/articles/2015-07-23/google-cfo-ruth-porat-brings-fiscal-discipline
- https://www.thestreet.com/investing/stocks/google-surges-on-q2-earnings-beat-new-role-for-cfo-ruth-porat

## Significant events

### 2008-04-22, +24.2%

Google reported Q1 2008 after the close on 17 April: revenue $5.19bn, up 42% year over year,
and paid clicks up about 20% year over year ([Google press release, 17 April 2008, filed with
the SEC](https://www.sec.gov/Archives/edgar/data/1288776/000119312508083665/dex991.htm)). The
stock gapped from a split-adjusted $11.25 to $13.50 on 18 April, +20.0% in a day, contemporary
press putting it at $539.26 and calling it the biggest one-day rise in two years
([Fortune, 18 Apr 2008](https://fortune.com/2008/04/18/googles-relief-rally/)).

The mechanism is a short squeeze on a specific bear thesis. Through Q1 2008 comScore had been
publishing monthly paid-click data showing US click growth of roughly 1.8% year over year, and
the market had extrapolated that into an ad-recession call on Google, cutting the stock nearly
in half from its November 2007 high. Google's own disclosure showed 20% growth, driven by
international, where overseas revenue reached 51% of the total. The comScore reconciliation
issue was later addressed publicly by comScore itself ([comScore
blog](https://www.comscore.com/Insights/Blog/Reconciling-comScore-s-and-Google-s-Paid-Click-Data)).
This is a clean idiosyncratic repricing, not market beta.

Confidence 0.95.

### 2008-10-08, -17.9%

Pure macro. The window covers 2 to 8 October 2008, the week after the initial TARP vote failure
and during the Reserve Primary Fund and Icelandic banking collapses. On 8 October the Federal
Reserve, Bank of Canada, Bank of England, ECB, Sveriges Riksbank and Swiss National Bank cut
rates in a coordinated 50bp announcement, and the market sold off anyway ([Federal Reserve
press release, 8 Oct
2008](https://www.federalreserve.gov/newsevents/pressreleases/monetary20081008a.htm);
[CNN Money, 8 Oct 2008](https://money.cnn.com/2008/10/08/news/international/world_crisis/)).

Attribution anchor: over the identical window SPY fell 15.98% (116.06 to 97.51) against GOOGL's
17.88%. Roughly nine tenths of the move is market. There is no Google-specific news in the
window; Q3 2008 earnings did not land until 16 October, outside it.

Confidence 0.90 that this is macro. Confidence that any single named catalyst caused it: low,
and deliberately so. This is a systemic week, not an event.

### 2008-11-11, -15.1%

Mixed, and the weakest attribution in the file. The window covers 5 to 11 November 2008. Two
things sit inside it.

1. Macro. The 5 and 6 November sessions were the worst two-day post-election drop on record as
   the market repriced the recession. SPY fell 10.60% over the same window (100.41 on 4 Nov to
   89.77 on 11 Nov).
2. Company-specific and regulatory. On 5 November Google abandoned its search advertising
   agreement with Yahoo after the DOJ told the parties it would sue to block it ([DOJ press
   release 08-981, 5 Nov 2008](https://www.justice.gov/archive/opa/pr/2008/November/08-at-981.html)).
   GOOGL fell 6.7% that day.

GOOGL underperformed SPY by about 4.5 percentage points over the window. The Yahoo termination
is the only verified Google-specific news item inside it, so it is the leading candidate for
that gap, alongside the general derating of online advertising exposure. I could not find a
specific analyst action dated in this window to corroborate, and I am not going to assert one.
The honest statement is: 70% market, remainder most plausibly the DOJ-forced collapse of the
Yahoo deal.

Confidence 0.70.

### 2008-11-20, -16.8%

Pure macro, and the deepest point of the 2008 bear market. The S&P 500 closed at 752.44 on 20
November, its lowest close since 1997 and down more than 50% from the October 2007 peak
([Benzinga, "This Day In Market History"](https://benzinga.com/z/20077767); [Trading Economics,
20 Nov 2008](https://tradingeconomics.com/articles/11202008132217.htm)).

Attribution anchor: SPY fell 17.24% over the identical window (91.17 to 75.45) against GOOGL's
16.83%. GOOGL marginally outperformed the index. There is no company-specific content here at
all. This is the ledger detecting the market, which the ticker happens to be in.

Confidence 0.90.

### 2009-01-27, +17.2%

Google reported Q4 2008 after the close on 22 January. GAAP net income fell 70% to $382m, hit
by writedowns on the AOL and Clearwire stakes, but ex-items EPS of $5.10 beat the roughly $4.95
consensus and revenue rose 18% to $5.70bn ([CBS News, 22 Jan
2009](https://www.cbsnews.com/news/earnings-google-q4-profits-plummet-70-percent-but-still-beats-estimates/);
[CNN Money, 22 Jan 2009](https://money.cnn.com/2009/01/22/technology/google_earns/)). GOOGL rose
5.9% on 23 January and kept going.

Two caveats keep this at 0.85 rather than higher. First, the window base is 20 January 2009,
inauguration day, which was itself a 5% market decline, so the starting point is depressed.
Second, SPY rose 4.91% over the same window, so about a third of a much smaller market move is
embedded. Net of that, roughly 12 percentage points are idiosyncratic and attributable to the
print. The mechanism is the same one as April 2008: the market had priced an advertising
collapse, and the quarter showed advertising merely decelerating.

Confidence 0.85.

### 2013-10-18, +16.0%

Google reported Q3 2013 after the close on 17 October. Revenue rose 12% to $14.89bn, non-GAAP
EPS was $10.74, paid clicks rose 26% year over year, and YouTube brand video ads grew more than
75%. GOOGL rose 13.8% on 18 October and closed above $1,000 per share for the first time, at
$1,011.41 ([CNN Money, 18 Oct 2013](https://money.cnn.com/2013/10/18/investing/google-stock/index.html);
[CNBC, 18 Oct 2013](https://www.cnbc.com/2013/10/18/google-stock-hits-1000-for-the-first-time.html)).

Mechanism: the bear case at the time was that cost-per-click was falling every quarter as
traffic shifted to mobile, where ads monetized worse, and that Google could not offset it with
volume. Q3 2013 showed click volume accelerating to its fastest growth of the year, which
resolved the argument in Google's favour. Deutsche Bank, Credit Suisse and Jefferies all raised
targets the next morning. The $1,000 handle gave it press amplification but was not the cause.

Confidence 0.95.

### 2020-03-12, -15.5%

Pure macro, and outside the training boundary (TEST period). The window covers 5 to 12 March
2020. The WHO declared COVID-19 a pandemic on 11 March and the US announced suspension of most
travel from Europe that evening; on 12 March the Dow fell 9.99% and the S&P 500 fell 9.5%, the
worst session since the 1987 crash ([TIME, 12 Mar
2020](https://time.com/5802039/us-stocks-plummet-coronavirus/); [PBS NewsHour, 12 Mar
2020](https://www.pbs.org/newshour/economy/worst-day-on-wall-street-since-1987-as-virus-fears-spread)).

Attribution anchor: SPY fell 17.97% over the identical window against GOOGL's 15.46%. GOOGL
outperformed. Nothing company-specific.

Confidence 0.95.

### 2020-11-04, +15.6%

Outside the training boundary (TEST period). Two catalysts, both inside the window.

1. Alphabet reported Q3 2020 after the close on 29 October: revenue $46.17bn against $42.90bn
   expected and EPS $16.40 against $11.29 expected, the recovery quarter after Alphabet's
   first-ever revenue decline in Q2 ([CNBC, 29 Oct
   2020](https://www.cnbc.com/2020/10/29/alphabet-googl-earnings-q3-2020.html)). The stock rose
   about 9% after hours. On 30 October it opened at $83.37 against a $77.84 prior close but
   closed at $80.81, only +3.8%, because the Nasdaq fell that session. Part of the earnings
   reaction was deferred.
2. On 4 November, with the presidential race undecided and Senate control apparently staying
   Republican, the market repriced to a divided government: no corporate tax increase and lower
   odds of aggressive big-tech regulation. The Nasdaq closed +3.8% and GOOGL +6.1% ([CNBC, 4 Nov
   2020](https://www.cnbc.com/2020/11/04/how-the-nasdaq-and-tech-stocks-became-the-winner-on-election-night.html);
   [Axios, 4 Nov 2020](https://www.axios.com/2020/11/04/tech-stocks-surge-market-election-nasdaq)).

The second catalyst has extra force for GOOGL specifically because the DOJ had filed its search
monopolization suit against Google on 20 October 2020, two weeks earlier, so the stock carried a
live regulatory discount that the election result partially released.

Attribution anchor: SPY rose 5.17% over the identical window against GOOGL's 15.56%, so about
10 points are idiosyncratic. I split that between the earnings beat and the election repricing
but cannot cleanly apportion it.

Confidence 0.90 on the combined explanation, lower on any single-catalyst version.

## Regime

**GOOGL lives in two regimes and only two, and they do not mix.**

*Regime 1, earnings-gap repricing of ad monetization (2008-04, 2009-01, 2013-10, 2015-07, and
partly 2020-11).* Five of nine events. The structure is identical every time: a consensus forms
that Google's revenue-per-query is structurally deteriorating (comScore paid clicks in 2008,
ad recession in 2009, mobile CPC dilution in 2013, unbounded opex in 2015, COVID ad pullback in
2020), the quarterly disclosure contradicts it, and the stock gaps 13% to 20% in one session on
five to ten times normal volume. These are single-day overnight gaps, not five-day drifts. The
five-day window is capturing a one-day event plus noise, which systematically inflates the
recorded move size relative to the actual shock.

*Regime 2, market beta during systemic dislocation (2008-10, 2008-11 x2, 2020-03).* Four of
nine events. In every one of these GOOGL's move is within roughly two percentage points of
SPY's over the identical window, and in two of the four GOOGL actually outperformed the index.
There is no Google-specific information content in these dates at all. They are the S&P 500
wearing a GOOGL ticker.

**Consequences for analog retrieval.** Three things matter here.

1. **There is no downside idiosyncratic event in GOOGL's entire pre-2019 history.** Not one.
   Every large down move is market beta; every idiosyncratic move is up. A generator retrieving
   GOOGL analogs for a hypothetical bad-news conditional ("Google loses the Apple default
   search deal", "DOJ wins remedies") has literally nothing in this ticker to retrieve, and
   will silently substitute crisis-beta analogs whose mechanism is completely different. That
   is a mis-transfer, and it will look plausible.
2. **The training-period corpus (pre-2019) is seven events, four of which are one crisis
   cluster of eleven weeks in late 2008.** The effective independent sample size is closer to
   four: April 2008 earnings, the 2008 crisis, January 2009 earnings, October 2013 earnings,
   July 2015 earnings. That is thin.
3. **Window inflation is systematic here.** Because GOOGL's idiosyncratic events are overnight
   gaps, the five-day window consistently records a larger number than the shock. 2015-07-17
   reads 25.8% but the event is 16.3%; 2013-10-18 reads 16.0% but the event is 13.8%. Any
   downstream model calibrated on the ledger's `move_pct` for this ticker is calibrated on
   gap-plus-drift, not gap. This is a property of the frozen contract, not a defect to fix, but
   it needs stating.

## Ledger verdict

**The ledger survives contact with reality cleanly. Nine for nine.**

I re-derived each `move_pct` from split-adjusted daily bars and matched the ledger to six
decimal places in every case. Every date corresponds to something a person who lived through it
would name without hesitation: two of the most famous earnings reactions in the company's
history (the $1,000 close and the Porat quarter), the April 2008 comScore vindication, the
worst week of the credit crisis, the 2008 bear-market low close, the COVID crash, and the 2020
election-night tech melt-up.

**No data artifacts found.** Specifically checked and cleared:
- **Splits.** GOOGL has had two corporate actions in the window (the April 2014 Class C
  distribution and the July 2022 20:1 split). Neither appears as a false event, and neither of
  those dates is in the ledger. The adjustment is correctly applied.
- **Bad prints.** No event depends on a single anomalous bar. The two largest are supported by
  volume of 257m (2015-07-17) and 462m (2013-10-18) shares against typical volume of 40m to 90m.
- **Deduplication.** The autumn 2008 dates (8 Oct, 11 Nov, 20 Nov) are 22 and 7 trading days
  apart, so the 5-day non-maximum suppression is behaving correctly and these are genuinely
  distinct windows rather than one event triple-counted. They are, however, one *regime*
  counted three times, which is the point made in the Regime section above.

**One caveat on the detector's semantics, not its correctness.** The window-end convention
means the ledger date is often the day *after* the causal news, and in the gap cases the ledger
date *is* the reaction day with the news the prior evening. Both are consistent with the
contract's definition. But 2008-04-22 is a case where the reaction day was 18 April and the
ledger date is 22 April, two sessions later, because the trailing window was still cumulating.
Anyone reading a ledger date as "the day it happened" will be off by up to four sessions. That
is a documentation issue for the UI, not a detection bug.

**Verdict: accept the GOOGL ledger as-is. Flag its composition, not its accuracy.** The risk to
the project from this ticker is not wrong dates, it is a seed corpus with zero idiosyncratic
downside and a 2008 cluster doing four ninths of the work.

## Unexplained

None. All nine events have a credible, sourced explanation. Two carry qualified confidence and
should be treated as partially explained rather than solved:

- **2008-11-11 (confidence 0.70).** The macro component is certain and quantified against SPY.
  The residual 4.5 percentage points of underperformance is most plausibly the DOJ-forced
  termination of the Google-Yahoo advertising agreement on 5 November, which is verified and
  in-window, but I could not corroborate a specific sell-side action or second catalyst dated
  inside the window, and I am not asserting one.
- **2020-11-04 (confidence 0.90 combined).** The explanation is confident but joint. Two real
  catalysts sit in the window, the 29 October earnings beat and the 4 November divided-
  government trade, and I cannot cleanly apportion the roughly 10 points of idiosyncratic move
  between them.
