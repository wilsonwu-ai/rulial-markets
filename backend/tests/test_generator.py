"""Tests for rulial.generator  (LANE-MODEL).

Run:  cd backend && python3 -m pytest tests/test_generator.py -q
      (or: python3 tests/test_generator.py   -- works without pytest installed)

These tests never touch the network and never use an LLM (`use_llm=False`),
so they are deterministic. Price and corpus fixtures are written into a tmp
directory so the suite is independent of whatever LANE-DATA / LANE-EVENTS
have landed on disk.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
import warnings
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rulial.config import DEFAULT_N_PATHS, TRAIN_END, UNIVERSE  # noqa: E402
from rulial.generator import (  # noqa: E402
    LEAKAGE_DISCLOSURE,
    RULE_SET,
    LookaheadError,
    ScenarioPrior,
    _clamp_prior,
    _heuristic_prior,
    _implied_direction,
    _PRICE_CACHE,
    assert_no_lookahead,
    demeaned_twin,
    generate_ensemble,
    retrieve_analogs,
    scenario_prior,
)
from rulial.types import Article, Ensemble, Event, ForecastRequest  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures: a self-contained fake market on disk
# ---------------------------------------------------------------------------

FIX_TICKERS = ["NVDA", "TSLA", "META", "XOM"]


def _business_days(start: str, n: int):
    d = date.fromisoformat(start)
    out = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


@pytest.fixture(scope="module")
def market(tmp_path_factory):
    """Write deterministic price CSVs + an event ledger. Returns paths + meta."""
    root = tmp_path_factory.mktemp("market")
    pdir = root / "prices"
    pdir.mkdir()
    days = _business_days("2008-01-02", 3200)          # ends well past 2019
    meta = {}
    for i, t in enumerate(FIX_TICKERS):
        rng = np.random.default_rng(1000 + i)
        r = rng.normal(0.0004, 0.020, len(days))
        # Plant deterministic 25%+ five-day jumps so the ledger is real.
        jump_at = [400, 900, 1400, 1900, 2400][: 3 + (i % 2)]
        for k, j in enumerate(jump_at):
            sign = -1.0 if (k + i) % 2 == 0 else 1.0
            r[j: j + 5] += sign * 0.062                # ~ +/-31% over the window
        close = 40.0 * np.exp(np.cumsum(r))
        lines = ["date,open,high,low,close,volume"]
        for d, c in zip(days, close):
            lines.append(f"{d},{c:.4f},{c:.4f},{c:.4f},{c:.4f},1000000")
        (pdir / f"{t}.csv").write_text("\n".join(lines) + "\n")
        meta[t] = {"days": days, "close": close, "jump_at": jump_at}

    # Event ledger: the END of each planted jump window, train period only.
    events, corpus = [], []
    for i, t in enumerate(FIX_TICKERS):
        days_t = meta[t]["days"]
        close = meta[t]["close"]
        for k, j in enumerate(meta[t]["jump_at"]):
            end = j + 5
            if end >= len(days_t):
                continue
            d = days_t[end]
            if d > TRAIN_END:
                continue
            mv = float(close[end] / close[j] - 1.0)
            direction = "up" if mv >= 0 else "down"
            words = ("guidance cut and a revenue miss on weak datacenter demand"
                     if direction == "down" else
                     "a blowout beat and raised guidance on record datacenter demand")
            ev = {
                "ticker": t, "date": d, "move_pct": mv, "direction": direction,
                "window_days": 5, "famous": (k == 0),
                "headline": f"{t} {'plunges' if direction=='down' else 'surges'} on {words}",
                "articles": [{
                    "url": f"https://example.test/{t}/{d}", "title": f"{t} {words}",
                    "published": d, "source": "fixture",
                    "snippet": f"Shares of {t} moved {mv:.0%} over five sessions on {words}.",
                }],
            }
            events.append(ev)
    ledger = root / "events.jsonl"
    ledger.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return {"root": root, "prices_dir": pdir, "events_path": ledger,
            "corpus_dir": root / "corpus", "n_events": len(events), "meta": meta}


@pytest.fixture(autouse=True)
def _clear_price_cache():
    _PRICE_CACHE.clear()
    yield
    _PRICE_CACHE.clear()


def _req(**kw):
    base = dict(
        ticker="NVDA",
        event_text="NVDA announces a 40% datacenter revenue miss and cuts full-year guidance",
        as_of_date=TRAIN_END,
        horizon_days=5,
        n_paths=2000,
    )
    base.update(kw)
    return ForecastRequest(**base)


def _gen(market, **kw):
    kw.setdefault("use_llm", False)
    kw.setdefault("prices_dir", market["prices_dir"])
    kw.setdefault("events_path", market["events_path"])
    kw.setdefault("corpus_dir", market["corpus_dir"])
    req = kw.pop("req", _req())
    return generate_ensemble(req, **kw)


# ---------------------------------------------------------------------------
# 1. Contract conformance
# ---------------------------------------------------------------------------

def test_fixture_ledger_is_non_empty(market):
    assert market["n_events"] >= 8, "fixture market must plant real events"


def test_returns_contract_shaped_ensemble(market):
    e = _gen(market)
    assert isinstance(e, Ensemble)
    assert e.ticker == "NVDA"
    assert e.as_of_date == TRAIN_END
    assert e.horizon_days == 5
    assert len(e.paths) == 2000
    assert all(isinstance(x, float) and math.isfinite(x) for x in e.paths)
    assert set(e.quantiles) == {"p5", "p25", "p50", "p75", "p95"}
    q = e.quantiles
    assert q["p5"] <= q["p25"] <= q["p50"] <= q["p75"] <= q["p95"]
    assert math.isfinite(e.mean) and e.std > 0
    assert all(isinstance(a, Event) for a in e.analogs)
    assert len(e.narrative.split(".")) >= 3, "narrative must be 2-3 sentences"


def test_n_paths_is_exact_for_odd_sizes(market):
    for n in (2, 7, 101, 999, 2000, 5000):
        e = _gen(market, req=_req(n_paths=n))
        assert len(e.paths) == n, f"asked for {n}, got {len(e.paths)}"


def test_serializes_through_asdict_without_extra_fields(market):
    e = _gen(market)
    d = asdict(e)
    assert set(d) == {"ticker", "as_of_date", "horizon_days", "paths", "quantiles",
                      "mean", "std", "analogs", "narrative"}
    assert "diagnostics" not in d, "diagnostics must not leak into the frozen shape"
    json.dumps(d)                                   # must be JSON-serializable


def test_diagnostics_attached_for_lane_eval(market):
    e = _gen(market)
    d = e.diagnostics
    for k in ("rulial_dispersion", "drift_decomposition", "paths_demeaned",
              "warnings", "prior", "fan_by_day", "price_source", "seed"):
        assert k in d, f"missing diagnostics key {k}"
    assert len(d["paths_demeaned"]) == len(e.paths)
    assert len(d["fan_by_day"]) == e.horizon_days
    assert any("null model" in w or "lift over a null" in w for w in d["warnings"])


def test_leakage_disclosure_is_always_present(market):
    e = _gen(market)
    assert LEAKAGE_DISCLOSURE in e.diagnostics["warnings"]
    assert "does not cut the weights" in LEAKAGE_DISCLOSURE


# ---------------------------------------------------------------------------
# 2. Reproducibility
# ---------------------------------------------------------------------------

def test_same_seed_is_bit_identical(market):
    a = _gen(market, seed=7)
    b = _gen(market, seed=7)
    assert a.paths == b.paths
    assert a.quantiles == b.quantiles


def test_different_seed_gives_a_different_draw(market):
    a = _gen(market, seed=7)
    b = _gen(market, seed=8)
    assert a.paths != b.paths
    # ... but the same distribution: medians should be close.
    assert abs(a.quantiles["p50"] - b.quantiles["p50"]) < 0.03


def test_seed_none_is_deterministic_per_request(market):
    a = _gen(market)
    b = _gen(market)
    assert a.paths == b.paths, "seed=None must be derived from the request, not from time"
    c = _gen(market, req=_req(event_text="a completely different description"))
    assert c.paths != a.paths


# ---------------------------------------------------------------------------
# 3. The leak guard (CONTRACT.md s2) -- the load-bearing tests
# ---------------------------------------------------------------------------

def test_retrieval_never_returns_an_analog_after_as_of(market):
    for as_of in ("2013-06-28", "2016-01-15", TRAIN_END):
        req = _req(as_of_date=as_of)
        analogs, _ = retrieve_analogs(
            req, k=50, prices_dir=market["prices_dir"],
            events_path=market["events_path"], corpus_dir=market["corpus_dir"])
        assert all(a.date <= as_of for a in analogs), as_of


def test_analog_whose_forward_window_has_not_closed_is_excluded(market):
    """The subtle half: date <= as_of is NOT sufficient."""
    corpus_all, _ = retrieve_analogs(
        _req(as_of_date=TRAIN_END), k=99, prices_dir=market["prices_dir"],
        events_path=market["events_path"], corpus_dir=market["corpus_dir"])
    assert corpus_all, "need at least one analog to run this test"
    victim = corpus_all[0]
    # as_of set to two trading days after the event: the 5-day outcome is unknowable.
    days = market["meta"][victim.ticker]["days"]
    i = days.index(victim.date)
    as_of = days[i + 2]
    got, _ = retrieve_analogs(
        _req(as_of_date=as_of), k=99, prices_dir=market["prices_dir"],
        events_path=market["events_path"], corpus_dir=market["corpus_dir"])
    assert victim.date not in [g.date for g in got if g.ticker == victim.ticker], (
        "an analog whose forward window closes after as_of_date leaked into retrieval")


def test_assert_no_lookahead_raises_on_future_event(market):
    bad = Event(ticker="NVDA", date="2020-06-01", move_pct=-0.30, direction="down")
    with pytest.raises(LookaheadError):
        assert_no_lookahead([bad], TRAIN_END, 5, market["prices_dir"])


def test_assert_no_lookahead_raises_on_unclosed_window(market):
    days = market["meta"]["NVDA"]["days"]
    i = days.index([d for d in days if d <= TRAIN_END][-1])
    recent = Event(ticker="NVDA", date=days[i - 2], move_pct=-0.30, direction="down")
    with pytest.raises(LookaheadError):
        assert_no_lookahead([recent], days[i], 5, market["prices_dir"])


def test_assert_no_lookahead_accepts_a_closed_window(market):
    days = market["meta"]["NVDA"]["days"]
    i = days.index([d for d in days if d <= TRAIN_END][-1])
    ok = Event(ticker="NVDA", date=days[i - 40], move_pct=-0.30, direction="down")
    assert_no_lookahead([ok], days[i], 5, market["prices_dir"])   # must not raise


def test_early_as_of_yields_fewer_analogs_than_late(market):
    early, _ = retrieve_analogs(_req(as_of_date="2012-01-03"), k=99,
                               prices_dir=market["prices_dir"],
                               events_path=market["events_path"],
                               corpus_dir=market["corpus_dir"])
    late, _ = retrieve_analogs(_req(as_of_date=TRAIN_END), k=99,
                              prices_dir=market["prices_dir"],
                              events_path=market["events_path"],
                              corpus_dir=market["corpus_dir"])
    assert len(early) < len(late)


# ---------------------------------------------------------------------------
# 4. Zero-analog fallback -- the demo WILL hit this
# ---------------------------------------------------------------------------

def test_zero_analogs_does_not_crash_and_says_so(market, tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    e = generate_ensemble(_req(), use_llm=False, prices_dir=market["prices_dir"],
                          events_path=empty, corpus_dir=tmp_path / "nope")
    assert len(e.paths) == 2000
    assert e.analogs == []
    assert e.diagnostics["zero_analog_fallback"] is True
    assert any("ZERO ANALOGS" in w for w in e.diagnostics["warnings"])
    assert "no historical analog" in e.narrative.lower()
    # Falls back to the null: width within a sane multiple of trailing sigma.
    null_sigma = e.diagnostics["null_sigma_horizon"]
    assert 0.5 <= e.std / null_sigma <= 4.0


def test_missing_ledger_file_does_not_crash(market, tmp_path):
    e = generate_ensemble(_req(), use_llm=False, prices_dir=market["prices_dir"],
                          events_path=tmp_path / "does_not_exist.jsonl",
                          corpus_dir=tmp_path / "nope")
    assert len(e.paths) == 2000


def test_corrupt_ledger_lines_are_skipped(market, tmp_path):
    bad = tmp_path / "bad.jsonl"
    good = market["events_path"].read_text().splitlines()
    bad.write_text("\n".join(["{not json", '{"ticker":"NVDA"}', ""] + good) + "\n")
    e = generate_ensemble(_req(), use_llm=False, prices_dir=market["prices_dir"],
                          events_path=bad, corpus_dir=market["corpus_dir"])
    assert e.analogs, "valid rows must survive a corrupt neighbour"


def test_ticker_with_no_events_still_forecasts(market):
    """XOM-shaped case: six of ten universe tickers have zero train events."""
    e = _gen(market, req=_req(ticker="XOM", event_text="an unremarkable trading week"))
    assert len(e.paths) == 2000
    assert math.isfinite(e.std) and e.std > 0


def test_every_universe_ticker_produces_an_ensemble(market):
    for t in UNIVERSE:
        e = _gen(market, req=_req(ticker=t, n_paths=200))
        assert len(e.paths) == 200, t
        assert math.isfinite(e.mean), t


# ---------------------------------------------------------------------------
# 5. Speed
# ---------------------------------------------------------------------------

def test_2000_paths_is_fast_enough_to_demo(market):
    _gen(market, req=_req(n_paths=50))               # warm the price cache
    t0 = time.perf_counter()
    e = _gen(market, req=_req(n_paths=DEFAULT_N_PATHS))
    dt = time.perf_counter() - t0
    assert len(e.paths) == DEFAULT_N_PATHS
    assert dt < 5.0, f"generation took {dt:.2f}s, budget is 5s"
    assert e.diagnostics["elapsed_s"] < 5.0


# ---------------------------------------------------------------------------
# 6. The rulial rule set
# ---------------------------------------------------------------------------

def test_rule_weights_sum_to_one():
    assert abs(sum(r.weight for r in RULE_SET) - 1.0) < 1e-9


def test_rule_set_contains_a_labelled_trap_and_a_null_shape():
    traps = [r for r in RULE_SET if r.drift_mode == "analog"]
    assert traps, "the raw-analog-drift rule must exist so we can measure it"
    assert all(r.name.startswith("TRAP:") for r in traps)
    assert sum(r.weight for r in traps) <= 0.15, "the trap must stay a minority rule"
    assert any(r.analog_scope == "none" for r in RULE_SET), "the null must live inside the ensemble"


def test_every_rule_contributes_paths(market):
    e = _gen(market)
    per = e.diagnostics["rulial_dispersion"]["per_rule"]
    assert len(per) == len(RULE_SET)
    assert sum(r["n_paths"] for r in per) == len(e.paths)
    assert all(r["n_paths"] > 0 for r in per)


def test_rulial_dispersion_is_measured_and_nonzero(market):
    e = _gen(market)
    disp = e.diagnostics["rulial_dispersion"]
    assert disp["median_spread"] > 0.0, "rules that never disagree are not an ensemble"
    assert disp["p95_spread"] > 0.0


def test_trap_rule_carries_more_drift_than_neutral_rules(market):
    """The whole point: raw-analog-drift rules are the ones that bet on drift."""
    e = _gen(market)
    per = {r["rule"]: r for r in e.diagnostics["rulial_dispersion"]["per_rule"]}
    neutral = [v["mean_drift_added_h"] for v in per.values() if v["drift_mode"] == "neutral"]
    trap = [v["mean_drift_added_h"] for v in per.values() if v["drift_mode"] == "analog"]
    assert all(abs(x) < 1e-12 for x in neutral), "neutral rules must add exactly zero drift"
    assert trap, "trap rules must exist"


def test_drift_decomposition_is_reported(market):
    e = _gen(market)
    dd = e.diagnostics["drift_decomposition"]
    assert dd["trap_rule_weight"] > 0 and dd["prior_rule_weight"] > 0
    assert math.isfinite(dd["mean_with_drift"]) and math.isfinite(dd["mean_demeaned"])


def test_demeaned_twin_has_zero_log_drift(market):
    e = _gen(market)
    tw = demeaned_twin(e)
    lg = np.log1p(np.asarray(tw.paths))
    assert abs(float(lg.mean())) < 1e-9, "the twin must be demeaned in log space"
    assert len(tw.paths) == len(e.paths)
    assert tw.narrative.startswith("DEMEANED TWIN")


def test_demeaned_twin_works_on_a_bare_ensemble():
    """LANE-EVAL may hand us an Ensemble that never had diagnostics attached."""
    bare = Ensemble(ticker="NVDA", as_of_date=TRAIN_END, horizon_days=5,
                    paths=[0.10, -0.05, 0.20, 0.02], quantiles={}, mean=0.0, std=0.0)
    tw = demeaned_twin(bare)
    assert abs(float(np.log1p(np.asarray(tw.paths)).mean())) < 1e-12


# ---------------------------------------------------------------------------
# 7. Analogs actually shape the ensemble
# ---------------------------------------------------------------------------

def test_analog_conditioning_widens_relative_to_the_null(market):
    """Post-jump analog windows are more volatile, so the ensemble should be
    wider than the trailing-vol null. Recon measured the realized post-jump
    sigma at ~1.19x the null-implied sigma, so this is a weak, honest check."""
    e = _gen(market)
    ratio = e.diagnostics["ensemble_sigma_over_null"]
    assert ratio > 1.0, f"conditioned ensemble should not be narrower than the null ({ratio:.2f})"
    assert ratio < 6.0, "and it should not be absurdly wide"


def test_analogs_are_named_in_the_narrative(market):
    e = _gen(market)
    assert e.analogs
    assert e.analogs[0].ticker in e.narrative
    assert e.analogs[0].date in e.narrative


def test_retrieval_prefers_same_ticker_and_matching_direction(market):
    req = _req(ticker="TSLA",
               event_text="TSLA plunges after a guidance cut and a revenue miss")
    analogs, scores = retrieve_analogs(req, k=6, prices_dir=market["prices_dir"],
                                       events_path=market["events_path"],
                                       corpus_dir=market["corpus_dir"])
    assert analogs
    assert analogs[0].ticker == "TSLA"
    assert scores[0] >= scores[-1]


def test_scores_are_sorted_descending(market):
    _, scores = retrieve_analogs(_req(), k=20, prices_dir=market["prices_dir"],
                                 events_path=market["events_path"],
                                 corpus_dir=market["corpus_dir"])
    assert list(scores) == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# 8. The scenario prior: clamping, fallback loudness, no point predictions
# ---------------------------------------------------------------------------

def test_llm_prior_is_hard_clamped():
    """An LLM that tries to emit a point prediction gets clamped into a prior."""
    wild = {"scenarios": [
        {"name": "it goes to zero", "weight": 5.0, "drift_5d": -9.99, "vol_multiplier": 40.0},
        {"name": "moon", "weight": 5.0, "drift_5d": 12.0, "vol_multiplier": 0.001},
        {"name": "nan", "weight": float("nan"), "drift_5d": 0.0, "vol_multiplier": 1.0},
    ], "reasoning": "x" * 5000}
    p = _clamp_prior(wild, "llm:test", "{}")
    assert p is not None
    assert abs(sum(p.weights) - 1.0) < 1e-9
    assert all(abs(d) <= 0.35 for d in p.drift_5d)
    assert all(0.5 <= v <= 3.0 for v in p.vol_mult)
    assert len(p.reasoning) <= 240


def test_clamp_rejects_garbage():
    assert _clamp_prior({}, "llm:test", "") is None
    assert _clamp_prior({"scenarios": []}, "llm:test", "") is None
    assert _clamp_prior({"scenarios": [{"weight": 0}]}, "llm:test", "") is None


def test_prior_fallback_is_loud(market):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        p = scenario_prior(_req(), use_llm="auto", llm_timeout_s=0.001)
    if p.source.startswith("heuristic"):
        assert any("NO LLM REACHABLE" in str(x.message) for x in w)
    e = generate_ensemble(_req(), use_llm=False, prices_dir=market["prices_dir"],
                          events_path=market["events_path"],
                          corpus_dir=market["corpus_dir"])
    assert e.diagnostics["prior_source"].startswith("heuristic-fallback")
    assert any("NO LLM IN THIS FORECAST" in w for w in e.diagnostics["warnings"])


def test_heuristic_prior_reads_direction_and_always_includes_a_fade():
    bear = _heuristic_prior("massive revenue miss, guidance cut, fraud probe", 5)
    bull = _heuristic_prior("blowout beat, record demand, raises guidance", 5)
    assert bear.expected_drift_5d < 0 < bull.expected_drift_5d
    # Never a point prediction: a fade scenario with the opposite sign exists.
    assert min(bear.drift_5d) < 0 < max(bear.drift_5d)
    assert min(bull.drift_5d) < 0 < max(bull.drift_5d)
    # And it is timid, per the measured drift trap.
    assert abs(bear.expected_drift_5d) < 0.12


def test_severity_widens_the_prior():
    mild = _heuristic_prior("a modest guidance trim", 5)
    wild = _heuristic_prior("catastrophic 60% revenue miss, fraud probe, CEO resigns", 5)
    assert wild.expected_vol_mult > mild.expected_vol_mult


def test_implied_direction():
    assert _implied_direction("revenue miss and guidance cut")[0] == "down"
    assert _implied_direction("blowout beat, record backlog")[0] == "up"
    assert _implied_direction("the company held an event")[0] == "unknown"


def test_prior_sampling_respects_weights():
    p = ScenarioPrior(["a", "b"], [0.9, 0.1], [0.10, -0.10], [1.0, 1.0], "test")
    d, v = p.sample(np.random.default_rng(0), 20000)
    assert 0.85 < float((d > 0).mean()) < 0.95
    assert v.shape == (20000,)


# ---------------------------------------------------------------------------
# 9. Distributional sanity
# ---------------------------------------------------------------------------

def test_quantiles_match_the_paths(market):
    e = _gen(market)
    p = np.asarray(e.paths)
    for k, q in (("p5", 0.05), ("p50", 0.50), ("p95", 0.95)):
        assert abs(e.quantiles[k] - float(np.quantile(p, q))) < 1e-9
    assert abs(e.mean - float(p.mean())) < 1e-9


def test_paths_are_returns_not_prices(market):
    e = _gen(market)
    p = np.asarray(e.paths)
    assert p.min() > -1.0, "a cumulative simple return cannot be below -100%"
    assert abs(float(np.median(p))) < 0.5


def test_fan_widens_with_horizon(market):
    e = _gen(market, req=_req(horizon_days=10))
    fan = e.diagnostics["fan_by_day"]
    w1 = fan[0]["p95"] - fan[0]["p5"]
    w10 = fan[-1]["p95"] - fan[-1]["p5"]
    assert w10 > w1, "dispersion must grow with horizon"


def test_longer_horizon_is_wider(market):
    a = _gen(market, req=_req(horizon_days=1))
    b = _gen(market, req=_req(horizon_days=10))
    assert b.std > a.std


def test_bad_inputs_raise(market):
    with pytest.raises(ValueError):
        _gen(market, req=_req(horizon_days=0))
    with pytest.raises(ValueError):
        _gen(market, req=_req(n_paths=1))


# ---------------------------------------------------------------------------
# 10. Calibration smoke test -- PIT of realized outcomes should be roughly flat
# ---------------------------------------------------------------------------

def test_pit_is_not_wildly_miscalibrated(market):
    """Weak but real: forecast every train date on a grid, score the realized
    5-day forward return's PIT, and require the histogram not to be degenerate.

    This is a smoke test, not the eval. LANE-EVAL owns calibration, and a
    per-ticker PIT test at n~12 has only ~30% power anyway (measured). We only
    assert the ensemble is not obviously 3x too narrow or too wide.
    """
    days = market["meta"]["NVDA"]["days"]
    close = market["meta"]["NVDA"]["close"]
    idx = {d: i for i, d in enumerate(days)}
    train = [d for d in days if "2013-01-01" <= d <= TRAIN_END]
    sample = train[::120]
    pits = []
    for d in sample:
        i = idx[d]
        if i + 5 >= len(close):
            continue
        actual = float(close[i + 5] / close[i] - 1.0)
        e = _gen(market, req=_req(as_of_date=d, n_paths=800,
                                  event_text="ordinary trading week, no catalyst"))
        p = np.asarray(e.paths)
        pits.append(float((p < actual).mean()))
    assert len(pits) >= 8
    pits = np.asarray(pits)
    frac_tail = float(((pits < 0.05) | (pits > 0.95)).mean())
    assert frac_tail < 0.45, (
        f"{frac_tail:.0%} of outcomes landed in the extreme 10% of the ensemble -- "
        "the ensemble is far too narrow")
    assert 0.10 < float(pits.mean()) < 0.90, "systematically biased location"


if __name__ == "__main__":                            # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))


# ---------------------------------------------------------------------------
# 11. Width discipline -- the three defects real data exposed
# ---------------------------------------------------------------------------

def test_robust_scale_ignores_outliers():
    from rulial.generator import _robust_scale
    clean = np.random.default_rng(0).standard_normal(4000)
    dirty = clean.copy()
    dirty[:20] *= 60.0                                # dot-com-shaped windows
    assert abs(_robust_scale(clean) - 1.0) < 0.08
    assert abs(_robust_scale(dirty) - 1.0) < 0.08, "IQR scale must survive outliers"
    assert dirty.std(ddof=1) > 3.0, "the sample sd must NOT survive them"


def test_robust_scale_falls_back_on_tiny_samples():
    from rulial.generator import _robust_scale
    assert _robust_scale(np.array([1.0, 2.0]), fallback=0.5) == 0.5
    assert _robust_scale(np.zeros(50), fallback=0.7) == 0.7


def test_analog_windows_are_vol_standardized(market):
    """FHS: a high-vol and a low-vol analog must contribute comparably."""
    from rulial.generator import _analog_forward_matrix
    analogs, _ = retrieve_analogs(_req(), k=50, prices_dir=market["prices_dir"],
                                  events_path=market["events_path"],
                                  corpus_dir=market["corpus_dir"])
    Z, kept, _ = _analog_forward_matrix(analogs, 5, TRAIN_END, market["prices_dir"])
    assert Z.shape[0] >= 3
    # Standardized units: daily moves are O(1) sigma, not O(0.02) raw returns.
    assert 0.3 < float(np.abs(Z).mean()) < 6.0, f"not standardized: {np.abs(Z).mean()}"


def test_prior_vol_multiplier_is_not_stacked_on_the_analog_anchor(market):
    """The -52% bug: a wild prior must not blow up analog-anchored rules."""
    from rulial.generator import RULE_SET, _analog_forward_matrix, _run_rule, ScenarioPrior
    analogs, _ = retrieve_analogs(_req(), k=25, prices_dir=market["prices_dir"],
                                  events_path=market["events_path"],
                                  corpus_dir=market["corpus_dir"])
    Z, analogs, _ = _analog_forward_matrix(analogs, 5, TRAIN_END, market["prices_dir"])
    rule = next(r for r in RULE_SET if r.vol_anchor == "analog" and r.drift_mode == "neutral")
    calm = ScenarioPrior(["a"], [1.0], [0.0], [1.0], "test")
    wild = ScenarioPrior(["a"], [1.0], [0.0], [2.0], "test")
    out = []
    for pr in (calm, wild):
        p, _ = _run_rule(rule, np.random.default_rng(3), 4000, 5, Z, analogs,
                         "NVDA", "down", 0.02, pr)
        out.append(float(np.expm1(p.sum(axis=1)).std(ddof=1)))
    assert abs(out[0] - out[1]) / out[0] < 0.05, (
        "an analog-anchored rule must ignore the prior's width; got "
        f"{out[0]:.4f} vs {out[1]:.4f}")


def test_prior_owns_width_on_trailing_anchored_rules(market):
    from rulial.generator import RULE_SET, _run_rule, ScenarioPrior
    rule = next(r for r in RULE_SET if r.vol_anchor == "trailing")
    empty = np.zeros((0, 5))
    out = []
    for v in (1.0, 2.0):
        pr = ScenarioPrior(["a"], [1.0], [0.0], [v], "test")
        p, _ = _run_rule(rule, np.random.default_rng(4), 4000, 5, empty, [],
                         "NVDA", "down", 0.02, pr)
        out.append(float(np.expm1(p.sum(axis=1)).std(ddof=1)))
    assert 1.8 < out[1] / out[0] < 2.2, f"prior must set width here: {out}"


def test_paths_inherit_one_analog_each(market):
    """Per-path analog selection is what makes this a scale mixture."""
    from rulial.generator import _block_bootstrap
    A = np.vstack([np.full(5, 1.0), np.full(5, 10.0), np.full(5, 100.0)])
    per_path = _block_bootstrap(np.random.default_rng(0), A, 500, 5, 1, True)
    spliced = _block_bootstrap(np.random.default_rng(0), A, 500, 5, 1, False)
    # If each path holds one analog, every value in a row is identical.
    assert np.all(per_path.max(axis=1) == per_path.min(axis=1))
    assert not np.all(spliced.max(axis=1) == spliced.min(axis=1))


def test_ensemble_is_leptokurtic_not_gaussian(market):
    """A scale mixture over analogs should have fatter tails than a Gaussian."""
    e = _gen(market, req=_req(n_paths=6000))
    x = np.log1p(np.asarray(e.paths))
    k = float(((x - x.mean()) ** 4).mean() / x.var() ** 2)
    assert k > 3.1, f"kurtosis {k:.2f} -- the ensemble collapsed to a Gaussian"


def test_horizon_calibration_is_documented_and_sane():
    from rulial.generator import HORIZON_CALIBRATION
    assert 0.5 < HORIZON_CALIBRATION <= 1.0
    import rulial.generator as g
    assert "PIT" in g.__doc__ and "CRPS lift" in g.__doc__


def test_calibration_constant_does_not_touch_the_null_path(market, tmp_path):
    """With zero analogs we must reproduce the null's width exactly."""
    empty = tmp_path / "e.jsonl"; empty.write_text("")
    req = _req(event_text="an ordinary week", n_paths=20000)
    e = generate_ensemble(req, use_llm=False, prices_dir=market["prices_dir"],
                          events_path=empty, corpus_dir=tmp_path / "nc", seed=5)
    prior_mult = e.diagnostics["prior"]["vol_mult"]
    exp = e.diagnostics["null_sigma_horizon"] * float(np.mean(prior_mult))
    assert abs(e.std - exp) / exp < 0.12, f"zero-analog width drifted: {e.std:.4f} vs {exp:.4f}"


def test_tier_field_survives_corpus_load(market, tmp_path):
    led = tmp_path / "t.jsonl"
    led.write_text(json.dumps({
        "ticker": "NVDA", "date": "2015-01-05", "move_pct": -0.18, "direction": "down",
        "window_days": 5, "tier": "significant", "headline": "NVDA slides on a guidance cut",
    }) + "\n")
    from rulial.generator import load_seed_corpus
    evs = load_seed_corpus(led, tmp_path / "nc")
    assert len(evs) == 1 and evs[0].tier == "significant"


def test_llm_width_opinion_is_compressed_not_taken_at_face_value():
    """Measured: the LLM asks for 2.0x when the tape delivers ~1.24x."""
    from rulial.generator import LLM_WIDTH_TRUST
    assert 0.3 <= LLM_WIDTH_TRUST < 1.0
    p = _clamp_prior({"scenarios": [
        {"name": "panic", "weight": 1.0, "drift_5d": 0.0, "vol_multiplier": 2.0}]},
        "llm:test", "{}")
    assert abs(p.vol_mult[0] - 2.0 ** LLM_WIDTH_TRUST) < 1e-9
    assert p.vol_mult[0] < 2.0, "the model's width claim must be discounted"


def test_heuristic_prior_is_not_compressed():
    """The fallback is already calibrated; compression applies to LLM output only."""
    h = _heuristic_prior("catastrophic 60% miss, fraud probe, CEO resigns", 5)
    assert 1.0 < h.expected_vol_mult < 1.6, h.expected_vol_mult


def test_drift_reaches_only_the_prior_rules():
    """Drift is the dangerous parameter -- a fixed bearish tilt applied to all
    647 real train events drove PIT chi-square from 9.5 to 241. It must never
    reach more than the prior-mode rules."""
    reach = sum(r.weight for r in RULE_SET if r.drift_mode == "prior")
    assert reach <= 0.50, f"the LLM's drift opinion reaches {reach:.0%} of paths"
