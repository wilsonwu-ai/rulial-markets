# Demo script — Sundai 139, 20:00

**Live:** https://rulial-markets.wilson-af8.workers.dev
**Repo:** https://github.com/wilsonwu-ai/rulial-markets

Every number below is real and reproducible. If you are unsure of one, say "I'd have to check"
rather than guess. That is on-brand for this project.

---

## The 30-second version

> "We asked whether AI could help a regular investor. We built a thing that shows you what
> actually happened, historically, when events like the one you're describing hit a stock.
> Then we spent most of the day trying to prove our own model was fooling us. It mostly was,
> and the interesting part is what survived."

---

## The 3-minute demo, beat by beat

**Beat 1 — the atlas (30s).** Open the app. Don't touch anything.
> "Ten companies. Every week since 1962 where any of them moved more than 15%. 329 of them.
> Green is up, red is down. We know what caused 233 of these, with sources."

**Beat 2 — drill (30s).** Click the Boeing 2020 mark.
> "Boeing, March 2020, down 46% in a week. Here's why, and here are the three articles.
> No model has said anything yet. This is just what happened."

**Beat 3 — branch (60s).** Go to Branch. Pick BA, 2019-03-08.
> "Now the model. I type an event — a second 737 MAX crash, regulators ground the fleet.
> Watch the chart branch. Each of these 2,000 lines is a real five-day window from history,
> replayed forward. The solid line is what actually happened."
>
> "It landed inside the range. And the score says we beat the simple baseline by 23%."

**Beat 4 — the honest bit (60s).** This is the part that wins or loses it.
> "But here's what we found and didn't hide. Ask it for a 75% chance the stock falls. It can't
> do it. The most catastrophic news we can write only gets to 54%. Over five days, direction is
> basically a coin flip — and that's not our model failing, that's the market. What IS
> predictable is how *big* the move will be. We measured that three separate ways and they all
> agree."

---

# Q & A

## The easy ones

**"What does it actually do?"**
> You describe something that might happen to a company. It finds the closest things that
> really did happen, shows you what the stock did each time, and gives you the range — plus a
> score for how much to trust that range.

**"Who is it for?"**
> Someone who owns a business for years and wants to know if a shock is survivable. Not a
> trading desk. Our edge over a dumb baseline is about one percent. Nobody at a hedge fund
> should care about that, and we say so in the README.

**"Where does the data come from?"**
> Prices from yfinance, cross-checked against OpenBB, back to 1962. Filings straight from SEC
> EDGAR — 8-K, 10-Q, 10-K — that's 1,129 documents. News from CNBC, CNN Money, Fortune,
> Forbes and others, always cited with a link. We don't use Bloomberg. It's paywalled and we
> never touched it.

**"Is it open source?"**
> MIT. Clone it and run `make install && make demo`. We tested that from a clean directory
> tonight: 378 tests pass, the API boots, no API keys needed.

---

## The sharp ones

**"You called it rulial-markets. But a Monte Carlo over paths from one generator is an ensemble
over configurations under a fixed rule. That's Boltzmann — the gas case Wolfram contrasts
*against* the rulial ensemble. Where are the rules?"**

*(This is the best question anyone can ask. Concede immediately. Do not defend.)*

> You're completely right, and we flagged it in our own docs before you asked. Our path cloud
> is statistical mechanics, not rulial.
>
> So we built the rulial one too. We took our generator apart into four decisions — how it picks
> analogs, what it conditions on, what drift it assumes, how it resamples — and ran all 144
> combinations. That's an ensemble over *rules*.
>
> And it caught a real bug. One of those four axes — the drift assumption — dominates the
> variance, and on some events it *flips the sign of the answer*. Same event text, same data,
> change one rule, and the forecast reverses. A Boltzmann ensemble can't see that. It reports one
> median and has no idea the sign is an artifact of an assumption we made.
>
> So the rulial version isn't a rebrand. It's the fix for our actual bug.

**"How do you know the model isn't just remembering what happened? Any LLM you use already read
about COVID."**

> That's the strongest objection and we can't fully eliminate it. Cutting the input data at 2019
> doesn't cut the weights. So we did three things.
>
> First, we only report improvement over a dumb baseline — memorizing still has to beat a
> Gaussian before it counts.
>
> Second, we ran a controlled experiment. Same stock, same date, same available history — we only
> changed the *text*. True story about a good quarter versus a fabricated story about a bad one.
> The scores differed by 7.6 percentage points. The model responds to what you tell it, not to
> what it remembers.
>
> Third — and this one surprised us — we split every test into famous events and obscure ones.
> If it were recalling, it should do better on the famous ones. It does **worse**: −5.94% versus
> −0.55%. That's measured from the shipped data, not asserted.

**"Your lift is 1.26%. Isn't that noise?"**

> It's small, and here's the honest frame. We built an oracle that *cheats* — it looks at the
> actual volatility that occurred after the event, which no real forecaster can do. That cheater
> gets +2.0%. So the whole available headroom is about two percent, because the baseline already
> auto-widens 1.78× after a jump.
>
> We get 1.26% of a 2.0% ceiling. That's about 63% of what's actually there. Small number, most
> of the room.

**"What's CRPS?"**

> It scores a *range* against one thing that happened. If you said "somewhere between −13% and
> +13%, probably near zero," and the stock did −0.2%, CRPS asks: did you put your weight near
> what happened, and did you waste weight far away? Lower is better. We always show ours next to
> a dumb baseline, and when the baseline wins we print that.

**"Why not just report whether you got the direction right?"**

> Because a coin flip looks skilled that way. It's frozen out of our headline by contract. A
> model that says "down" and is right 55% of the time sounds impressive and means nothing. We
> score the whole distribution instead, and we check calibration — whether our 90% ranges
> actually contain the outcome 90% of the time.

---

## The killer

**"So can it predict the market or not?"**

*(Say this plainly. Don't hedge, don't oversell.)*

> No, and we can tell you exactly what it can't do.
>
> Direction over five days is close to a coin flip. We measured that three independent ways:
> the out-of-sample R² on direction is about zero; the most extreme news we could write only
> moves P(down) to 0.54; and in our 144-rule ensemble, the *sign* of the forecast isn't stable
> across rules.
>
> But the same three methods say the *size* of the move is predictable. Dispersion R² is about
> 0.10. The width of our range is stable across 100% of rules even when the direction isn't.
>
> That's the honest product. It won't tell you whether to buy. It will tell you how violent the
> next week is likely to be, and how much to trust that answer.

---

## If someone asks about the team

> Pavel showed us the boss-and-worker agent pattern. Guzal said point it at finance. Luke
> insisted we build evaluations that could declare us wrong — that's why we found our own bugs
> instead of a judge finding them. Harsh made the interface readable. I scoped it and kept
> everyone honest about the numbers.

---

## Things NOT to say

- Don't say "we predict" anything. We estimate ranges.
- Don't quote a number you can't point at in the repo.
- Don't claim Bloomberg data. We don't have it.
- Don't call directional hit-rate a result.
- If asked something you don't know: **"I'd have to check"** is a strong answer in a room that
  just watched you disclose your own weaknesses.
