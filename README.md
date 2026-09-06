# rulial-markets

**What happens to a stock when something unprecedented happens to it?**

`rulial-markets` takes a plain-English conditional event ("NVDA announces a 40%
datacenter revenue miss") and returns an **ensemble of possible forward return
paths** rather than a single number. It then scores that ensemble against
held-out history and reports how much better it is than a dumb baseline.

Built at [Sundai Hack 139](https://www.sundai.club/events/boston/wolfram-hack),
"AI Agents That Adapt and Evolve", Harvard, 6 Sep 2026.

---


## Live demo

**https://rulial-markets.wilson-af8.workers.dev**

The deployed frontend is a static export on Cloudflare Workers. It ships with a bundled mock
response so the UI is fully demoable with no backend running. To point it at a live backend,
set `NEXT_PUBLIC_API_BASE` to the API origin and redeploy; the API itself (FastAPI, Python) is
run locally with `make api`.

To redeploy the frontend:

```bash
cd frontend && STATIC_EXPORT=1 npm run build && cd .. && npx wrangler deploy
```


## The honest version

This is **not** a crystal ball, and the repo is arranged so it cannot quietly
become one.

Wolfram's argument is that when a process is computationally irreducible you
cannot predict its trajectory, but you can still say something about the
statistics of the ensemble it lives in. We tested whether that actually holds
for equities before we built on it. On the train period (2010 to 2019, 10
tickers, ~21,900 observations) we regressed forward 5-day returns on trailing
move and trailing volatility:

| Target | Out-of-sample R² |
|---|---|
| Forward **direction** (signed return) | -0.0008 to +0.0007 |
| Forward **dispersion** (absolute return) | +0.098 to +0.105 |

Direction is noise. Dispersion is not. That gap is the only thing this project
claims, and everything downstream is built to keep us honest about it:

- The headline metric is **CRPS lift over a null model**, never accuracy.
- The null model (Gaussian, trailing 250-day sigma, zero drift) is **frozen into
  the eval and may not be removed**, however good dropping it would make us look.
- **Directional hit-rate may not be a headline result.** It makes a coin flip
  look like skill. Appendix only, labelled.
- A **flat PIT histogram is the win condition**, not "we called the crash."

See `CONTRACT.md` sections 7 and 8. Those rules are frozen, not aspirational.

### Leakage disclosure

Any LLM in the generator has already read the post-2019 world. **Cutting the
input data at 2019 does not cut the weights.** This is a known, formal problem:
under memorization, forecasting ability is not identifiable
([Lopez-Lira, Tang & Zhu 2025](https://arxiv.org/abs/2504.14765)). We do not
claim to have solved it. We do three things about it:

1. Report lift over a null. Memorization has to beat a baseline to count.
2. Keep obscure, low-salience events in the test set next to famous ones and
   **report them separately**. A model that only wins on famous events is
   remembering, not forecasting.
3. State this on the results screen, in the product, where users see it.

### What we already know is weak

Measured during recon, before any of the model code was written. Recorded here
so nobody rediscovers it at 6pm:

- **The null is harder to beat than it looks.** Trailing volatility already
  auto-expands about 1.78x after a jump, so "it was a big move" is largely
  priced into the baseline. An oracle that cheats by using the *realized*
  post-jump sigma still gets only about +2% CRPS lift. A generator that only
  widens a Gaussian has nowhere to go.
- **The obvious generator is a trap.** Resampling historical analog outcomes
  scores +14.8% lift, but the lift is 100% drift: demeaned, it goes to -4.5%,
  significantly *worse* than null. The train corpus is 30 up-jumps to 3
  down-jumps because 2010 to 2019 was a bull decade. The test window opens with
  COVID. Lift is therefore reported **raw and demeaned**, so this cannot be
  mistaken for skill.
- **The sample is small.** Under the frozen event definition, 6 of the 10
  universe tickers (AAPL, MSFT, AMZN, JPM, XOM, BA) have **zero** train-period
  events, and one ticker supplies over half the test events. Per-ticker
  calibration at n≈12 has roughly 30% power against an ensemble that is 2x too
  narrow, so calibration is judged pooled, not per ticker.

---

## Quickstart

Requires Python 3.10+ and Node 18+.

```bash
git clone <this repo> && cd rulial-markets
./scripts/bootstrap.sh
```

That installs everything, builds the dataset if it is missing, runs the tests,
and starts the demo. On a warm clone it takes well under a minute, because the
price CSVs and the event ledger are **committed to the repo** and nobody should
have to refetch them.

Prefer to do it by hand:

```bash
make install     # create .venv, install python + node deps
make data        # prices -> event ledger -> news corpus  (hits the network)
make demo        # api on :8000 + ui on :3000, Ctrl-C stops both
```

Other targets:

```bash
make api         # backend only, with reload, on :8000  (docs at /docs)
make ui          # frontend only, on :3000
make test        # pytest
make check       # curl the health endpoint of a running api
make clean       # drop caches and .venv, leaves data/ alone
make             # help
```

If the generator's narrative step is enabled you will need an API key. Put it in
`.env` at the repo root, which is gitignored:

```
ANTHROPIC_API_KEY=sk-ant-...
```

The app runs without it. The generator falls back to a deterministic keyword
heuristic and says so loudly in `Ensemble.narrative` and in the diagnostics. The
narrative degrades, the scoring does not.

---

## Architecture

A straight pipeline. Each stage is one module with one owner.

```
data.py       daily OHLCV for 10 tickers, cached to data/prices/*.csv
   |
events.py     scan for jumps -> data/events.jsonl        (the event ledger)
   |
news.py       harvest contemporaneous articles per event -> data/corpus/
   |
generator.py  event text + analogs -> ensemble of N forward return paths
   |
evaluate.py   CRPS vs null, PIT histogram, walk-forward backtest
   |
api.py        FastAPI on :8000
   |
frontend/     Next.js on :3000, proxies /api/* to :8000
```

**Frozen constants** (`backend/rulial/config.py`, do not edit):

| | |
|---|---|
| Universe | NVDA, AAPL, MSFT, AMZN, TSLA, META, GOOGL, JPM, XOM, BA |
| Train end | `2019-12-31` (this is the leak guard) |
| Test start | `2020-01-01`, with a 5-day embargo |
| Event | 25%+ absolute move over a rolling 5-day window |

**Moving `TRAIN_END` for better results is the leak.** Nobody moves it.

### API

```
GET  /api/tickers                  symbols, names, event counts
GET  /api/events?ticker=NVDA       the seed ledger, train period only
POST /api/forecast                 ForecastRequest -> {ensemble, score}
GET  /api/backtest?ticker=NVDA     n_tests, mean_crps_lift, pit_histogram
GET  /api/health                   {"ok": true}
```

Full request and response shapes are in `CONTRACT.md` sections 5 and 6.

Note for anyone touching the API or UI: several tickers legitimately return an
**empty event list** and `n_tests: 0`. That is a real property of the frozen
threshold, not a bug. Handle it, do not paper over it.

---

## Who owns what

`CONTRACT.md` section 4 is the frozen module boundary table. **One owner per
module.** Write only the files your lane owns; reading anyone else's is fine.
Import signatures from `CONTRACT.md`, not from someone's half-written source.

| Lane | Owns | What it does |
|---|---|---|
| parent | `CONTRACT.md`, `backend/rulial/config.py`, `backend/rulial/types.py` | **Frozen.** Nobody edits these. |
| LANE-DATA | `backend/rulial/data.py` | `load_prices(ticker)`, `load_fundamentals(ticker)` |
| LANE-EVENTS | `backend/rulial/events.py` | `detect_events(prices)`, `build_ledger()` |
| LANE-NEWS | `backend/rulial/news.py` | `harvest(event)`, `build_corpus()` |
| LANE-MODEL | `backend/rulial/generator.py` | `generate_ensemble(req) -> Ensemble` |
| LANE-EVAL | `backend/rulial/evaluate.py` | `crps`, `null_ensemble`, `pit`, `walk_forward` |
| LANE-API | `backend/rulial/api.py` | the FastAPI app and the routes above |
| LANE-UI | `frontend/**` | the Next.js app |
| LANE-PRD | `docs/PRD.md` | the PRD |
| LANE-DIAGRAM | `docs/diagrams/*.html` | architecture diagrams |
| LANE-SCAFFOLD | `README.md`, `requirements.txt`, `.gitignore`, `Makefile`, `scripts/bootstrap.sh` | this file and the build |
| **LANE-DEPLOY** | **unassigned** | **see below. This one is open.** |

### Open lane: deployment

`CONTRACT.md` specifies localhost only, `:8000` and `:3000`. Sundai's number one
non-negotiable launch requirement is a **working deployed application at a
public URL**, due between 18:00 and 19:00. No lane owns this. It is the single
highest-value thing an arriving teammate can pick up.

Scope: get the backend onto a host (Railway, Render, or Fly), the frontend onto
Vercel, point the frontend at the deployed API, and confirm a stranger can click
through it on their own phone. Feature freeze is 17:30, not 19:30.

---

## Contributing / claim a lane

We are adding collaborators through the day. To take a lane without colliding
with anyone:

1. **Read `CONTRACT.md` first.** It is the frozen interface and it is short.
   It exists so that people who have not read each other's code can still ship
   compatible modules.
2. **Claim your lane** in the team Discord channel before you start, and check
   the table above. If a lane is already listed as owned, an agent or a person is
   writing it right now. Ask first.
3. **Write only the files your lane owns.** This is the whole reason parallel
   work is possible here. Need something from another module? Import the
   signature from `CONTRACT.md`.
4. **Never edit** `CONTRACT.md`, `backend/rulial/config.py`, or
   `backend/rulial/types.py`. If you think the contract is wrong, say so in your
   PR description and code to the contract anyway. The parent reconciles.
5. **Never fabricate a number.** If real data is not available, ship a working
   code path with a clearly labelled synthetic fallback and say so out loud.
   A fake number that reaches the demo is worse than a missing feature.
6. **Run it before you push.** `make test` and `make demo`. "It should work" is
   not verification.
7. Open a PR against `main`. Small and mergeable beats complete and late.

Every module must import cleanly **with no network access at import time**. Fetch
lazily, inside functions.

---

## Status

Hack-day build, moving fast. As of the last scaffold check: all eight pipeline
modules import cleanly with no network at import time, the API boots and serves
`/api/health` and `/api/tickers`, and the test suite passes (114 tests) against
the dependency set in `requirements.txt`. Deployment is not done and is
unclaimed, see the open lane above.

Because lanes land continuously, run `ls backend/rulial/` and `make test` to see
what is actually true right now rather than trusting this paragraph.

Nothing in this README describes a feature that does not exist. If you find
something here that is not true, that is a bug, please fix it.
