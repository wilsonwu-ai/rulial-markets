# Rulial Markets

**Can AI help an ordinary investor decide whether an event actually matters to a stock?**

Live: https://rulial-markets.wilson-af8.workers.dev
Code: https://github.com/wilsonwu-ai/rulial-markets (MIT)

---

## The problem

Every retail investor hits the same question and has no honest tool for it: *something just
happened to a company I own — does it matter?* Sell-side research answers with a price target,
which is a point prediction dressed as analysis. Screeners give ratios. Financial media supplies
a story invented after the fact. None of them answer the thing a long-horizon investor actually
needs, which is: given an event like this, what has historically happened, how much did it vary,
and how much should I trust that range?

## What we built

Describe an event in plain English. The app finds the closest situations that really happened,
shows you what the stock did each time with sources attached, and gives you a distribution of
outcomes rather than a number.

Three surfaces. **Atlas** puts every event that moved any of ten companies on one timeline from
1962 to today — 329 of them, each a week where the stock moved at least 15%. Click any mark and
you get what actually caused it, with links to the filings and articles. No model has spoken yet.
**Branch** is where the model appears: pick a point in history, type a counterfactual, and the
chart fans into two thousand possible futures with the realized path drawn through them.
**Evidence** is where you argue with it — calibration, walk-forward scoring, and the limitations
we found in our own work.

The critical detail: we do not sample from a fitted curve. Every path in that fan is a real
five-day window from that company's price history, resampled forward, hard-filtered so nothing
after your chosen date can leak in. The language model reads your event text and returns scenario
weights only. It never emits a probability.

## How Wolfram's work changed the build

We came in with a Monte Carlo: one generator, two thousand paths. Stephen Wolfram's November 2025
essay on the rulial ensemble says that is the gas case — an ensemble over *configurations under a
fixed rule*, which is exactly what he contrasts the rulial ensemble against. The rulial ensemble
is an ensemble over the *rules themselves*. Our project was named after something we had not
built.

Three things came out of reading it properly.

It told us where to look. Wolfram argues that in a computationally irreducible process you cannot
predict the trajectory but can still predict the statistics of the ensemble. That is falsifiable,
so we tested it on roughly nine thousand held-out observations. Forward direction came back with
an R-squared of approximately zero. Forward dispersion came back at about 0.10. We did not
discover volatility clustering — but Wolfram's scheme correctly predicted *where* in an
unpredictable system a bounded observer gets traction, and we checked rather than assumed.

Then we built the rulial version. We took our generator apart into four decisions — how it selects
analogs, what it conditions on, what drift it assumes, how it resamples — and ran all 144
combinations. That is an ensemble over rules.

And it found a bug we could not otherwise have seen. The drift axis dominates the variance, and on
some events it flips the sign of the answer entirely. Same event text, same data, change one rule,
and the forecast reverses. We had a result that looked like skill at plus 14.8% lift; remove the
assumed drift and it becomes minus 4.5%. A single-generator Monte Carlo reports one median and is
structurally blind to that. The rulial ensemble surfaces it without anyone remembering to check.

We kept both and ship them side by side, because the comparison is the argument.

## What we measured, including what went against us

329 events across ten companies, every one price-verified — ten independent checks reconciled the
arithmetic with zero mismatches. 233 carry a researched cause; 153 have a source you can click.

On NVIDIA, walk-forward scoring gives 1.26% improvement over a null model across 32 tests. That
sounds small until you build an oracle that cheats by looking at the volatility that actually
occurred: the cheater only reaches 2.0%, because the baseline already widens 1.78 times after a
jump. So the entire available headroom is about two percent, and we capture roughly 63% of it.

We ran a controlled experiment on memorization. Same stock, same date, same available history,
changing only the event text: a true story about a good quarter versus a fabricated story about a
bad one. The scores differ by 7.6 percentage points, so the model responds to what you tell it
rather than to what it remembers. We also split every test into famous events and obscure ones. A
model recalling its training data should do better on the famous ones. Ours does worse — minus
5.94% against minus 0.55%.

And the finding we did not want. Over five days, direction is close to a coin flip. The most
catastrophic news we could write only moves the probability of a decline to 0.54. Three
independent methods agree: the out-of-sample R-squared on direction is about zero, the reachable
probability band tops out near 0.59, and in the 144-rule ensemble the *sign* of the forecast is
not stable across rules while the *width* is stable across all of them. We could have hidden that.
It is on the results screen instead.

## Who this is for

Someone holding a business for years who wants to know whether a shock is survivable, grounded in
what actually happened to comparable companies in comparable situations, with the filings and
articles attached.

Explicitly not for high-frequency desks or hedge funds. Our horizon is five days, our data is
daily, and our edge over a naive baseline is about one percent. There is no alpha here for anyone
with a co-location cage, and we say so in the repository. A tool that knows what it cannot predict
is worth more than one that pretends.

## Built with

Python, FastAPI, numpy and pandas on the backend. Next.js and TypeScript on the front end,
deployed on Cloudflare Workers. Prices from yfinance cross-checked against OpenBB. Filings pulled
straight from the SEC EDGAR public API — 8-K, 10-Q, 10-K, DEF 14A, 1,129 documents. News from
public sources, always cited with a link. We do not use Bloomberg; it is paywalled and we never
accessed it.

MIT licensed, no API keys required. Clone it, run `make install && make demo`, and it works.
We tested that from a clean directory: 378 tests pass.

## Team

**Pavel Tkachyk** showed us the boss-and-worker agent pattern — one agent plans and delegates,
another executes, and the loop runs on its own. That became the shape of how we built.
https://www.linkedin.com/in/pavel-tkachyk/

**Guzal K.** proposed pointing that pattern at markets and building something that helps a person
allocate capital. Every downstream decision traces to her framing of the goal as investing rather
than trading. https://www.linkedin.com/in/guzalk/

**Luke Rast** drafted the data framework: how to generate scenarios from a real seed corpus, and
how to build evaluations that can declare the thing wrong. That discipline is why we found our own
bugs instead of a judge finding them. https://www.linkedin.com/in/luke-rast-2b5b5b56/

**Harsh Kumar** drove the interface — what a user sees, in what order, and how a probabilistic
result can be read at a glance without being misread. Also pushed for graceful degradation, which
is why the demo survives a dead backend. https://www.linkedin.com/in/harsh-kumar-mit/

**Wilson Wu** pulled four ideas into one buildable project, set the scope, ran the build, and held
the line on intellectual honesty: no fabricated numbers, no metric we could game, and every claim
reported at the weaker of two readings. https://www.linkedin.com/in/wilson1wu/

Built at Sundai Hack 139, Harvard iLabs, 6 September 2026.
