# META — event research

**Ticker:** META (Meta Platforms, Inc.; traded as FB until the June 2022 ticker change). Listed 2012-05-18.
**Ledger rows examined:** 29 (7 major, 22 significant), all from `data/events.jsonl`.
**Research window rule applied:** each ledger date is the END of a 5-trading-day window, so the causal news is searched over roughly `[date - 10 calendar days, date]`.
**Verification method:** every ledger row was re-derived from daily OHLC pulled independently through the OpenBB / yfinance route, so the arithmetic below is checked rather than assumed. Narrative causes were then sourced separately.

## What drives this ticker

Meta is a single-product-line advertising business wearing a technology valuation. Roughly 98 percent of revenue is advertising, sold through an auction whose price is set by the marginal advertiser's expected return. That structure produces a very specific volatility signature: the stock does almost nothing for months, then re-rates violently on one number, the forward revenue and expense guide given on the quarterly call. Three secondary drivers show up repeatedly in the ledger:

1. **Platform dependency risk.** Apple's App Tracking Transparency (2021 to 2022) and, earlier, the desktop-to-mobile transition (2012 to 2013) are both cases where a change outside Meta's control repriced the whole earnings stream.
2. **Capital allocation shocks.** Reality Labs (2021 to 2023) and AI capex (2025 onward) are the same trade in different clothes: the market pays for the ad business and refuses to pay for the option, so every step-up in spend guidance is treated as a dividend cut.
3. **High beta to the macro growth factor.** In 2020 and 2022 Meta traded as a long-duration growth asset. CPI prints and Fed days moved it 5 to 10 percent with no company news at all.

Note for downstream lanes: only 13 of the 29 rows fall inside the `TRAIN_END = 2019-12-31` boundary, and only 2 of the 7 majors do (2012-08-01 and 2013-07-30). See "Ledger verdict".

## Every event examined

| Date | Move | Tier | Category | Headline | Conf |
|---|---|---|---|---|---|
| 2012-05-25 | -16.5% | significant | crisis | IPO breaks issue price; the first week after the botched Nasdaq open | 0.90 |
| 2012-06-04 | -15.7% | significant | crisis | Post-IPO slide continues into lawsuits over selective analyst guidance | 0.80 |
| 2012-06-19 | +16.5% | significant | unexplained | Bounce off the post-IPO low; no single catalyst verified | 0.30 |
| 2012-08-01 | **-28.8%** | **major** | earnings | First quarterly report as a public company; no mobile revenue model | 0.90 |
| 2012-09-14 | +15.9% | significant | leadership | Zuckerberg's first post-IPO public appearance, plus the Fed's QE3 | 0.45 |
| 2012-10-25 | +18.9% | significant | earnings | Q3 2012: mobile advertising revenue disclosed for the first time | 0.80 |
| 2012-11-16 | +22.6% | significant | crisis | The 804 million share lockup expires and the stock goes up | 0.90 |
| 2012-11-30 | +16.7% | significant | unexplained | Post-lockup momentum into a broad late-November tape; no company catalyst found | 0.30 |
| 2013-07-30 | **+44.0%** | **major** | earnings | Q2 2013: mobile hits 41% of ad revenue, the re-rating quarter | 0.95 |
| 2014-02-05 | +16.2% | significant | earnings | Q4 2013: mobile crosses half of ad revenue | 0.85 |
| 2016-02-03 | +19.3% | significant | earnings | Q4 2015: revenue up 52%, the peak-execution quarter | 0.85 |
| 2018-08-01 | -21.1% | significant | guidance | Q2 2018: margin and growth-deceleration guide, then the largest one-day cap loss to that date | 0.90 |
| 2019-02-05 | +18.7% | significant | earnings | Q4 2018: growth intact despite the Cambridge Analytica year | 0.85 |
| 2020-03-12 | -16.6% | significant | macro | COVID crash: WHO pandemic declaration and the Europe travel ban | 0.95 |
| 2020-08-26 | +15.7% | significant | sector-rotation | August 2020 mega-cap melt-up; UBS e-commerce upgrade | 0.85 |
| 2022-02-08 | **-31.0%** | **major** | guidance | First-ever DAU decline plus a $10bn ATT headwind; biggest one-day cap loss in US history | 0.95 |
| 2022-03-18 | +15.4% | significant | macro | Post-FOMC relief rally and the China ADR reversal | 0.60 |
| 2022-04-26 | -16.7% | significant | sector-rotation | Netflix subscriber shock repriced the whole ad and streaming complex | 0.60 |
| 2022-05-04 | **+27.7%** | **major** | earnings | Q1 2022 beat on DAU, then the one-day Fed relief rally of 4 May | 0.90 |
| 2022-05-11 | -15.5% | significant | macro | The May 2022 growth unwind; the Fed rally reversed in 48 hours | 0.70 |
| 2022-06-14 | -16.3% | significant | macro | 8.6% CPI print forces a 75bp Fed and an S&P bear market | 0.85 |
| 2022-07-21 | +15.9% | significant | sector-rotation | Mid-summer bear-market rally; Netflix came in better than feared | 0.70 |
| 2022-11-01 | **-30.8%** | **major** | guidance | Q3 2022: revenue declines a second quarter while capex guidance rises | 0.95 |
| 2022-11-10 | **+25.8%** | **major** | macro | 11,000 layoffs on 9 Nov, then the soft October CPI print on 10 Nov | 0.90 |
| 2023-02-07 | **+28.6%** | **major** | earnings | "Year of efficiency" and a $40bn buyback | 0.95 |
| 2023-05-02 | +15.3% | significant | earnings | Q1 2023: return to revenue growth, efficiency thesis confirmed | 0.85 |
| 2024-02-02 | +20.5% | significant | earnings | First-ever dividend plus a $50bn buyback; record one-day cap gain | 0.90 |
| 2025-11-04 | -16.5% | significant | earnings | $15.9bn one-time tax charge and a raised AI capex guide | 0.90 |
| 2026-04-14 | +15.2% | significant | product | Muse Spark model launch into an Iran-ceasefire risk rally | 0.85 |

## Major events

### 2012-08-01, -28.8%: the first earnings report as a public company

**Window:** 2012-07-25 close $29.34 to 2012-08-01 close $20.88.

**What happened.** Facebook reported its first quarter as a public company on 26 July 2012 after the close. Revenue grew but the company posted a GAAP loss on stock-compensation charges and, critically, gave the market no mobile monetization figure at a moment when usage was migrating to phones faster than the ad product could follow. The stock fell 8.5 percent on 26 July into the print and 11.7 percent on 27 July after it, then kept sliding to $20.88 on 1 August, a fresh all-time low and roughly 45 percent below the $38 IPO price.

**Why it moved.** The mechanism was not the reported quarter, it was the destruction of the IPO's core assumption. Facebook had been sold at 100x earnings on the premise that mobile would monetize at least as well as desktop, and the company declined to show evidence for that premise. In an auction-priced ad business, the terminal value is almost entirely in the monetization rate, so the absence of a number was itself the number. The lockup calendar amplified it: the first tranche of insider shares was scheduled to unlock on 16 August, so any holder who wanted out had a deadline.

Sources: [Wikipedia, Initial public offering of Facebook](https://en.wikipedia.org/wiki/Initial_public_offering_of_Facebook) (retrieved; confirms the $38 price, the 18 May $38.23 close, and the descent to about $20 by 20 August 2012). Price path independently verified from daily OHLC.

*Caveat: I could not retrieve a contemporaneous news source for the 26 July session specifically within this session's search budget. The 27 July gap is unambiguously the earnings reaction; the 26 July decline is attributed to pre-print positioning and is the weaker half of this explanation.*

### 2013-07-30, +44.0%: the mobile re-rating

**Window:** 2013-07-23 close $26.13 to 2013-07-30 close $37.63. Single-day gap of +29.6% on 25 July.

**What happened.** Facebook reported Q2 2013 on 24 July after the close. Revenue was $1.81bn, up 53 percent year over year, and mobile advertising reached 41 percent of total ad revenue, up from 30 percent the prior quarter, with mobile users up 51 percent to 819 million. The stock gapped up roughly 27 percent at the open on 25 July and kept climbing for four more sessions, retaking the $38 IPO price on 31 July for the first time in fourteen months.

**Why it moved.** This is the exact inverse of the 2012-08-01 event and the same variable is doing the work. The 2012 crash priced a mobile monetization rate near zero. The Q2 2013 print showed the rate was not only positive but compounding faster than desktop had, which meant the terminal ad-revenue curve had to be redrawn upward across every future year at once. A 44 percent move in five sessions is what happens when a single disclosure removes the dominant uncertainty in a discounted-cash-flow model rather than merely beating a quarterly estimate.

Sources: [CNBC, "Facebook earnings beat; shares jump 20%", 24 Jul 2013](https://www.cnbc.com/2013/07/24/facebook-earnings-beat-shares-jump-20.html); [TechCrunch, "Facebook Shares Return To Its IPO Price", 31 Jul 2013](https://techcrunch.com/2013/07/31/facebook-shares-return-to-its-ipo-price/); [CNN Money, Facebook Q2 2013 earnings](https://money.cnn.com/2013/07/24/technology/facebook-earnings/index.html) (URL returned by search; the page itself returned HTTP 503 on fetch).

### 2022-02-08, -31.0%: the ATT quarter

**Window:** 2022-02-01 close $319.00 to 2022-02-08 close $220.18. Single-day drop of -26.4% on 3 February.

**What happened.** Meta reported Q4 2021 on 2 February 2022 after the close and disclosed the first sequential decline in daily active users in company history, from 1.930bn to 1.929bn. Management guided Q1 revenue below consensus, quantified the 2022 revenue headwind from Apple's App Tracking Transparency at roughly $10bn, and named TikTok as a direct competitor for engagement. The stock fell 26 percent on 3 February, then kept falling for three more sessions to $220.18.

**Why it moved.** Two independent legs of the valuation broke on the same call. The user number killed the volume story, and the ATT headwind killed the price story, because losing the iOS signal degrades ad targeting and therefore the price per impression an advertiser will bid. The market had been treating Meta's targeting advantage as a moat; ATT demonstrated the moat was rented from Apple. That is a permanent multiple event, not a quarter event, which is why the selling continued for four sessions rather than gapping and stabilizing.

Sources: [CNBC, "Facebook stock plummets 26% in its biggest one-day drop ever", 3 Feb 2022](https://www.cnbc.com/2022/02/03/facebook-shares-plummet-22percent-after-reporting-weak-guidance.html); [CBS News, "Stocks tumble amid Facebook's record $237 billion rout"](https://www.cbsnews.com/news/stock-market-down-meta-facebook-earnings/).

### 2022-05-04, +27.7%: a beat and a Fed day stacked

**Window:** 2022-04-27 close $174.95 to 2022-05-04 close $223.41.

**What happened.** Two separate catalysts fell inside one five-day window. Meta reported Q1 2022 on 27 April after the close; daily active users came in above expectations, reversing the previous quarter's decline, and the stock rose 17.6 percent on 28 April off a badly beaten-down base. Then on 4 May the FOMC raised rates 50bp and Chair Powell explicitly ruled out a 75bp move, triggering a broad one-day risk rally in which Meta added a further 5.4 percent.

**Why it moved.** The earnings leg was a positioning unwind rather than a fundamental repricing: the stock had fallen from $323 to $175 in three months, so a simple confirmation that users had not kept shrinking was enough to force a short-cover. The Fed leg is pure duration: at a 12-month-forward multiple, a removal of tail risk on the discount rate mechanically lifts long-duration equity. This is the cleanest example in the ledger of a window that mixes idiosyncratic and macro drivers, and it is worth flagging to the model lane because an analog retrieved on "earnings beat" alone would over-attribute the size of this move.

Sources: [Al Jazeera, "Meta soars as Facebook reports stronger daily user growth", 27 Apr 2022](https://www.aljazeera.com/economy/2022/4/27/meta-soars-as-facebook-reports-better-than-expected-daily-users). The 4 May FOMC leg is inferred from the daily price path and the known FOMC calendar; no dedicated source was retrieved for it, so the split between the two legs is my attribution rather than a cited one.

### 2022-11-01, -30.8%: the capex revolt

**Window:** 2022-10-25 close $137.51 to 2022-11-01 close $95.20. Single-day drop of -24.6% on 27 October.

**What happened.** Meta reported Q3 2022 on 26 October after the close: revenue of $27.7bn, down more than 4 percent year over year and a second consecutive quarterly decline, profit down 52 percent to $4.4bn, and a Reality Labs loss of $3.7bn for the quarter, $9.4bn year to date. Management guided 2023 capital expenditure higher. Morgan Stanley, Cowen and KeyBanc downgraded the stock the next morning. Shares closed 27 October at $97.94, the lowest since 2016, and kept drifting to $95.20 by 1 November.

**Why it moved.** Declining revenue and rising spend at the same time is the specific combination equity markets punish hardest, because it removes both the growth case and the cash-return case in one print. The market's implicit demand was that Meta treat Reality Labs as a discretionary option to be cut when the core business slows; the guide said the opposite. That reframed the question from "what are Meta's earnings" to "who controls Meta's capital", which is a governance discount and therefore multiple-compressing rather than estimate-compressing.

Sources: [CNBC, "Meta stock falls 24% on earnings miss, analyst downgrades", 27 Oct 2022](https://www.cnbc.com/2022/10/27/meta-stock-falls-23percent-on-earnings-miss-analyst-downgrades.html); [CNBC, "Facebook parent Meta Q3 2022 earnings", 26 Oct 2022](https://www.cnbc.com/2022/10/26/facebook-parent-meta-earnings-q3-2022.html); [Forbes, "Meta Shares Plummet 20% In Pre-Market After Q3 Revenue Decline", 27 Oct 2022](https://www.forbes.com/sites/siladityaray/2022/10/27/meta-shares-plummet-20-in-pre-market-after-q3-revenue-decline/).

### 2022-11-10, +25.8%: layoffs on Wednesday, CPI on Thursday

**Window:** 2022-11-03 close $88.91 to 2022-11-10 close $111.87.

**What happened.** Three catalysts landed in sequence. A Wall Street Journal report over the weekend of 5 to 6 November said mass layoffs were imminent, and the stock rose 6.5 percent on Monday 7 November. On Wednesday 9 November Meta confirmed it was cutting more than 11,000 roles, about 13 percent of headcount, and the stock rose about 5.2 percent. On Thursday 10 November the October CPI printed at 7.7 percent against an 8.0 percent consensus, the Nasdaq Composite rose 7.35 percent in its best session since March 2020, and Meta added 10.2 percent.

**Why it moved.** The layoff leg is the direct answer to the 1 November event: the market had just marked the stock down for refusing to control spend, and the cut was read as management conceding the point. The CPI leg is the macro factor, and it is the larger of the two. This window is the clearest case in the ledger of a company-specific and a market-wide catalyst compounding in the same direction inside five days, and the ledger cannot separate them by construction. Roughly 40 percent of the move came on the CPI day alone.

Sources: [CNBC, "Meta stock up on report it's set to begin mass layoffs", 7 Nov 2022](https://www.cnbc.com/2022/11/07/meta-shares-up-on-report-its-set-to-begin-mass-layoffs.html); [CNBC, "3 takeaways from our daily meeting: CPI in focus, Disney's dismal quarter, Meta layoffs", 9 Nov 2022](https://www.cnbc.com/2022/11/09/takeaways-from-daily-meeting-cpi-disneys-bad-quarter-meta-layoffs.html); [CNBC, "Dow pops 1,200 points, S&P 500 jumps 5% in biggest rally in two years after light inflation report", 10 Nov 2022](https://www.cnbc.com/2022/11/09/stock-market-futures-open-to-close-news.html).

### 2023-02-07, +28.6%: the year of efficiency

**Window:** 2023-01-31 close $148.97 to 2023-02-07 close $191.62. Single-day gain of +23.3% on 2 February.

**What happened.** Meta reported Q4 2022 on 1 February 2023 after the close. Revenue of $32.2bn beat the $31.5bn consensus, daily active users reached 2bn, and the company authorized an incremental $40bn share repurchase while Zuckerberg declared 2023 a "year of efficiency". Shares rose more than 23 percent on 2 February and held the gain through 7 February.

**Why it moved.** This is the resolution of the governance discount opened on 1 November 2022. The buyback is the operative signal, not the revenue beat: a $40bn authorization is a binding statement about where marginal capital goes, and it removed the specific fear that Reality Labs would absorb every incremental dollar indefinitely. The market re-rated the same earnings stream at a higher multiple because the capital allocation policy changed, which is why the move dwarfs the size of the revenue beat.

Sources: [Quartz, "Wall Street loved Mark Zuckerberg's plans for 2023 to be a 'year of efficiency'"](https://qz.com/meta-earnings-2023-q4-share-buyback-layoffs-1850063732); [Motley Fool, "Why Meta Platforms Jumped 23.8% in January", 5 Feb 2023](https://www.fool.com/investing/2023/02/05/why-meta-platforms-jumped-238-in-january/); [Seeking Alpha, "Meta stock jumps 22%, nears $500B market cap as 'year of efficiency' gets praised"](https://seekingalpha.com/news/3931174-meta-platforms-soar-analysts-upgrade-praise-year-of-efficiency); [CNBC, "Meta lost $13.7 billion on Reality Labs in 2022", 1 Feb 2023](https://www.cnbc.com/2023/02/01/meta-lost-13point7-billion-on-reality-labs-in-2022-after-metaverse-pivot.html).

## Selected significant events

Only the ones where the mechanism adds something the table does not.

**2012-05-25, -16.5% (IPO break).** Window runs from the 18 May IPO close of $38.23 to $31.91. The IPO priced at $38 into a delayed and technically broken Nasdaq open; underwriters supported the price on day one, and once that support lifted the stock fell to $34.03 on 21 May and $31.00 on 22 May, tripping a circuit breaker. Within weeks more than 40 lawsuits alleged underwriters had cut estimates mid-roadshow and shared the revision selectively. This row is a market-microstructure event, not a fundamentals event: the price was administered on day one and then discovered over the following week. Source: [Wikipedia, Initial public offering of Facebook](https://en.wikipedia.org/wiki/Initial_public_offering_of_Facebook).

**2012-11-16, +22.6% (the lockup that did not break).** 804 million insider shares became sellable on 14 November 2012, the single largest unlock of the sequence, and the stock rose as much as 11 percent that day rather than falling. The mechanism is that the unlock had been shorted and hedged in advance, so the actual event removed the overhang instead of creating supply. Worth keeping as a seed: it is a case where the *known* scheduled catalyst produced the opposite sign to the consensus expectation, which is exactly the kind of case an ensemble should not collapse on. Sources: [CNN Money, "Facebook stock jumps despite 800 million shares set free", 14 Nov 2012](https://money.cnn.com/2012/11/14/technology/social/facebook-lockup-stock); [CNBC, "Why Facebook's Stock Soared on Biggest Lock-up Expiration", 14 Nov 2012](https://www.cnbc.com/2012/11/14/why-facebooks-stock-soared-on-biggest-lockup-expiration.html).

**2018-08-01, -21.1% (the guidance quarter).** Window from $217.50 on 25 July to $171.65 on 1 August; the single-day drop of 19.0 percent on 26 July was the largest one-day market-capitalization loss in US history at the time. Q2 2018 revenue was roughly in line but the CFO guided to decelerating revenue growth for several quarters and materially higher expense growth, tied to privacy and safety investment after Cambridge Analytica. The mechanism is identical to 2022-02-08 and 2022-11-01: it was the forward expense and revenue guide, not the reported quarter, that repriced the stock. *No contemporaneous source was retrieved for this row within budget; the price path is verified, the narrative is from prior knowledge.*

**2020-08-26, +15.7%.** Facebook closed at a then-record $303.91, up 8.2 percent on the day, after UBS analyst Eric Sheridan reiterated a buy rating and raised his target from $242 to $330 on the e-commerce opportunity. This is the only row in the ledger driven primarily by sell-side action, and it sits inside the August 2020 mega-cap melt-up, so the analyst note is best read as the proximate trigger for a move the tape was already primed for. Source: [Nasdaq / Motley Fool, "Why Facebook Stock Surged to a New All-Time High Today", 26 Aug 2020](https://www.nasdaq.com/articles/why-facebook-stock-surged-to-a-new-all-time-high-today-2020-08-26).

**2022-04-26, -16.7%.** Window from $217.31 on 19 April to $180.95. There is no Meta news in this window. Netflix reported a subscriber loss on 19 April and fell 35 percent on 20 April, which repriced the entire consumer-internet and advertising complex on read-across, and 26 April was a broad Nasdaq drawdown. Categorized sector-rotation. Note that this row is immediately adjacent to the 2022-05-04 major in the opposite direction, so the two are describing one round trip around a single earnings print.

**2022-07-21, +15.9%.** No Meta-specific catalyst. Netflix reported on 19 July having lost 970,000 subscribers against a guided 2 million, streaming and ad-adjacent names rallied hard, and the NYSE recorded a "90 percent up day" on 19 July. This is a bear-market rally row. Source: [CNBC, "Stocks rise, fueled by tech rally, as all major averages touch highest since early June", 19 Jul 2022](https://www.cnbc.com/2022/07/19/stock-futures-extend-dow-rally-as-netflix-earnings-beat-estimates-.html).

**2024-02-02, +20.5%.** Q4 2023 reported 1 February after the close, with the first dividend in company history plus a $50bn buyback authorization. Shares rose 20.3 percent on 2 February from $394.78 to $474.99, the largest single-day market-capitalization gain by any US company to that point. Same mechanism as 2023-02-07: a capital-return policy change, not an earnings surprise. Source: [CNN, "Meta stock surges 14%. Investors are loving its first-ever dividend", 1 Feb 2024](https://www.cnn.com/2024/02/01/tech/meta-earnings-q4-2023-dividend/index.html).

**2025-11-04, -16.5%.** Window from $751.67 on 29 October to $627.32. Meta reported Q3 2025 on 29 October after the close: record revenue of $51.24bn, up 26 percent and above the $49.41bn consensus, but a one-time non-cash tax charge of about $15.9bn arising from the US Corporate Alternative Minimum Tax, and 2025 capex guidance narrowed upward to $70bn to $72bn with a warning that 2026 capex would be "notably larger". Shares fell more than 11 percent on 30 October, the worst session since October 2022, and continued lower for three more days. The tax charge was the headline but not the cause: it was non-cash and one-time, and the capex guide was what analysts cut targets on. Sources: [CNBC, "Meta stock has worst day in 3 years, dropping 11% on higher AI spend", 30 Oct 2025](https://www.cnbc.com/2025/10/30/meta-stock-earnings-ai-spend.html); [CNBC, "Meta shares drop 9% despite earnings beat as company takes one-time tax charge", 29 Oct 2025](https://www.cnbc.com/2025/10/29/meta-q3-earnings-report-2025.html).

**2026-04-14, +15.2%.** Window from $575.05 on 7 April to $662.49. Two catalysts. On 8 April Meta launched Muse Spark, the first model from Meta Superintelligence Labs and its first major model since the $14bn Scale AI transaction, live in the Meta AI assistant in the US; the same session, President Trump announced a two-week suspension of strikes on Iran contingent on reopening the Strait of Hormuz, oil fell, and the Nasdaq rallied hard. Meta closed up 6.4 percent that day. The window then extended through 14 April, when the stock added a further 4.4 percent on an eMarketer projection that Meta would overtake Google as the world's largest digital advertising seller by net revenue in 2026, at roughly $243bn. The mechanism is a partial reversal of the November 2025 capex de-rating: a credible frontier model is the first evidence the AI spend buys something, so the same dollars stop being read as a loss and start being read as an investment. Sources: [CNBC, "Meta debuts new AI model, attempting to catch Google, OpenAI after spending billions", 8 Apr 2026](https://www.cnbc.com/2026/04/08/meta-debuts-first-major-ai-model-since-14-billion-deal-to-bring-in-alexandr-wang.html); [CNBC, "Alphabet, Meta, Amazon, Nvidia lead tech rally after Trump announces ceasefire with Iran", 8 Apr 2026](https://www.cnbc.com/2026/04/08/alphabet-nvidia-microsoft-tech-stocks-iran-ceasefire.html); [Motley Fool, "Why Meta Platforms Stock Jumped Today", 8 Apr 2026](https://www.fool.com/investing/2026/04/08/why-meta-platforms-stock-jumped-today/) (fetched directly); [Wikipedia, 2026 Iran war ceasefire](https://en.wikipedia.org/wiki/2026_Iran_war_ceasefire).

## Regime

META does not live in one regime. It lives in four, and they are separable, which is unusually good news for analog retrieval and unusually bad news for treating the ticker as homogeneous.

**Regime 1, IPO price discovery (May 2012 to Nov 2012).** Eight of the 29 rows, more than a quarter of the ledger, fall in the seven months after listing. These are microstructure events: an administered opening price, lockup calendars, underwriter litigation, and a float that tripled over six months. The moves are large because the equity had no established holder base, not because the business changed. **Analogs from this regime transfer only to other recently-listed companies**, and transferring them to a mature Meta is a category error.

**Regime 2, the mobile transition (Aug 2012 to Feb 2014).** Three rows including both training-period majors. The whole regime is one question, does mobile monetize, asked and answered. Moves are enormous (-28.8%, +44.0%) because the uncertainty is about the shape of the revenue curve rather than its level.

**Regime 3, mature ad platform (2014 to 2021).** Only four rows in eight calendar years, and the largest is 21 percent. This is the quiet regime. Every row is a quarterly print or a macro shock, and the ledger correctly finds almost nothing else. Meta was a low-event stock for most of its life.

**Regime 4, the capital-allocation era (2022 to present).** Fourteen rows, five of the seven majors, and every one of the sub-regimes traces to the same variable: how much Meta spends on something that is not the ad business, first Reality Labs, then AI infrastructure. 2022-02-08 and 2022-11-01 are the market saying no; 2022-11-10 and 2023-02-07 and 2024-02-02 are the market saying yes after the policy changed; 2025-11-04 is the same argument restarting with AI capex in the metaverse's chair; 2026-04-14 is the first evidence for the defense. **This regime is internally coherent and its analogs do transfer within itself.**

Two cross-cutting facts the model lane should hold:

- **The proximate cause is a guide, not a result.** In 2018, 2022 twice, and 2025, revenue was in line or ahead and the stock still fell double digits. An event description phrased as "Meta misses revenue" is the wrong conditioning variable for this ticker. "Meta raises capex guidance" is the right one.
- **2022 is a cluster, and clusters lie.** Nine of 29 rows are in calendar 2022 alone. Any calibration statistic computed over the whole ledger is dominated by one year in which the macro growth factor and the company's own crisis were correlated. That is fewer independent observations than the row count suggests.

## Ledger verdict

**The detection survives contact with reality, cleanly.** Every one of the 29 rows was independently re-derived from daily closing prices and every `move_pct` reproduced to within rounding. Examples: 2022-02-08 is $319.00 on 1 Feb to $220.18 on 8 Feb, which is -30.98 percent against a stored -0.309781; 2013-07-30 is $26.13 to $37.63, +44.01 percent against a stored +0.440107. There are no split artifacts (Meta has never split), no bad prints, and no rows that fail to correspond to something a person who followed the company would recognize.

**Twenty-seven of 29 rows have an identified cause; two do not.** That is a 93 percent explanation rate, and the two failures are both in the 2012 IPO-noise regime where a specific catalyst may genuinely not exist.

**The non-maximum suppression is behaving correctly.** The clearest test is 2022-04-26 (-16.7%) immediately followed by 2022-05-04 (+27.7%): these are not duplicates of one move, they are the drawdown into and the recovery out of a single earnings print, correctly separated with non-overlapping windows. Likewise 2022-11-01 and 2022-11-10 are the crash and the rebound, nine days apart, and both are real.

**Three cautions, none of them detection failures.**

1. **Windows blend causes.** By construction a 5-day window can contain two catalysts of different type. 2022-05-04 is an earnings beat plus an FOMC day; 2022-11-10 is a layoff announcement plus a CPI print; 2026-04-14 is a product launch plus a geopolitical de-escalation. Any single `category` label on those rows is a simplification, and the `cause` fields above say so explicitly. If the corpus needs one label per event, these three should carry a multi-cause flag rather than be forced.

2. **The train period is thin, and thin at the top.** Only 13 of 29 rows precede `TRAIN_END = 2019-12-31`, and only 2 of the 7 majors do. Worse, 8 of those 13 sit inside the 2012 IPO regime. So the training-period META corpus is effectively: one IPO cluster, two mobile-transition majors, and four ordinary earnings prints spread over 2014 to 2019. **META is a weak seed ticker for the 25 percent tier specifically**, and the contract's own justification for the 15 percent tier is visible here in miniature.

3. **The regime the model will be asked about is not the regime it can train on.** Every plausible user query about Meta today is a Regime 4 question, AI capex and model quality, and Regime 4 lies entirely on the test side of the boundary. This is not a leak, it is the opposite: it means honest lift on META has to come from analogs to the 2012 to 2013 platform-transition dynamic, which is a defensible transfer (both are "does the new modality monetize") but a non-obvious one. It should be stated in the results screen alongside the §8 disclosure rather than discovered by a reader.

## Unexplained

Listed honestly. Both are real price moves; what is missing is a verified cause, not a verified move.

**2012-06-19, +16.5%** (window 2012-06-12 close $27.40 to $31.91). The stock bounced off its post-IPO low with the gain concentrated on 15 June (+6.0%) and 18 June (+4.7%). Candidate explanations exist, including the 17 June Greek election result that produced a broad global relief rally on 18 June, and a Facebook acquisition announced in mid-June, but I exhausted this session's web-search budget before I could source either to the specific dates, and I am not willing to assert one without a retrieved source. Best available honest characterization: a mean-reversion bounce off an oversold post-IPO low, cause unverified.

**2012-11-30, +16.7%** (window 2012-11-23 close $24.00 to $28.00). No company-specific catalyst was found. The gain is spread across four sessions with the largest on 26 November (+8.1%). The most likely reading is continuation of the post-lockup re-rating that began on 14 November, running into a strong broad-market week around Thanksgiving 2012, but no source ties either to this specific ticker on these specific days. Searches for a 26 November 2012 Facebook catalyst returned only the 14 November lockup coverage.

**Additionally flagged as sourced-by-memory, not by retrieval** (explanations I believe are correct but for which I did not retrieve a contemporaneous article in this session, so downstream lanes should not treat them as anchored):

- **2012-09-14** (+15.9%): attributed to Zuckerberg's TechCrunch Disrupt appearance on 11 September 2012, his first public appearance since the IPO, in which he addressed mobile directly, combined with the Fed's QE3 announcement on 13 September. The 12 September (+7.7%) and 14 September (+6.2%) gains are consistent with that sequence but the attribution is uncited. Confidence 0.45.
- **2012-10-25** (+18.9%): the +19.1 percent gap on 24 October is unmistakably a reaction to the Q3 2012 report of 23 October, in which Facebook first disclosed a mobile advertising revenue figure. The gap is verified; the content of the report is uncited here.
- **2018-08-01** (-21.1%): the Q2 2018 guidance quarter, described above. Price path verified, narrative uncited.
- **2022-03-18, 2022-05-11, 2022-06-14, 2020-03-12**: macro rows attributed to, respectively, the 16 March 2022 FOMC, the post-FOMC reversal of 5 to 11 May 2022, the 10 June 2022 CPI print of 8.6 percent, and the 11 to 12 March 2020 WHO pandemic declaration and Europe travel ban. Each is a well-known market-wide event and each date lines up with a market-wide move, but no source was retrieved in this session tying META specifically to them.
