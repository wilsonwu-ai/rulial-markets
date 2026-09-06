# Notice

Companion to [`LICENSE`](LICENSE), which is plain MIT. These are disclosures, not licence terms.

## Contributors

Copyright 2026, the rulial-markets contributors:

| | |
|---|---|
| Guzal K. | [@guzalkhonkh-stack](https://github.com/guzalkhonkh-stack) · [LinkedIn](https://www.linkedin.com/in/guzalk/) |
| Harsh Kumar | [@harshk02](https://github.com/harshk02) · [LinkedIn](https://www.linkedin.com/in/harsh-kumar-mit/) |
| Luke Rast | [@lrast](https://github.com/lrast) · [LinkedIn](https://www.linkedin.com/in/luke-rast-2b5b5b56/) |
| Pavel Tkachyk | [@Pavel-Tk](https://github.com/Pavel-Tk) · [LinkedIn](https://www.linkedin.com/in/pavel-tkachyk/) |
| Wilson Wu | [@wilsonwu-ai](https://github.com/wilsonwu-ai) · [LinkedIn](https://www.linkedin.com/in/wilson1wu/) |

Built at [Sundai Hack 139](https://www.sundai.club/events/boston/wolfram-hack), Harvard iLabs,
6 September 2026.

## Not investment advice

This software produces statistical descriptions of historical market behaviour. It is a research
and educational tool. It does not constitute investment advice, and nobody involved is your
financial adviser.

Read the project's own findings before drawing conclusions from it. We measured, three
independent ways, that **direction over a five-day horizon is close to unpredictable**: forward
direction has an out-of-sample R-squared of approximately zero, P(down) caps near 0.54 for any
event text we could write, and the sign of the median is not invariant across our 144-rule
ensemble. What *is* predictable is dispersion. Anyone reading a directional trading signal out of
this tool is reading something the tool explicitly says is not there.

Markets can and do behave in ways no historical corpus contains.

## Third-party data

The MIT licence covers this repository's code and derived analysis. It does not cover the
underlying data, each source of which carries its own terms.

| Source | Used for | Terms |
|---|---|---|
| [yfinance](https://github.com/ranaroussi/yfinance) | daily OHLCV price history | Yahoo's terms; yfinance is Apache-2.0 |
| [OpenBB](https://openbb.co/) | price cross-checks | per-provider |
| [SEC EDGAR](https://www.sec.gov/edgar) submissions API | 8-K, 10-Q, 10-K, DEF 14A metadata and links | public domain, subject to SEC fair-access rules |
| Public news sources | event attribution | cited by link only |

**Article text is not redistributed in this repository.** `data/event_context.json` stores
headlines, our own summaries of cause, and source URLs. It does not store article bodies.

Price CSVs under `data/prices/` are committed so a clone is reproducible without refetching.
They are factual market data, and anyone redistributing them further should check the terms of
their own provider.

## Reproducibility

Every headline number in this repository was produced by running the code here, and the commit
messages record which corpus version each was pinned to. Where a number could not be reproduced
it was corrected rather than kept. See [`docs/BACKEND_LOGIC.md`](docs/BACKEND_LOGIC.md) and
[`docs/BOLTZMANN_VS_RULIAL.md`](docs/BOLTZMANN_VS_RULIAL.md).
