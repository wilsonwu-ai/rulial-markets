"""
LANE-INVERSE tests -- rulial.inverse (CONTRACT.md s6b).

    cd backend && python3 -m pytest tests/test_inverse.py -q
    cd backend && python3 tests/test_inverse.py     # works without pytest

These tests are offline and deterministic: candidate drafting always runs with
`use_llm=False` and verification always runs on the forward model's
deterministic keyword prior, so nothing here touches the network.

The tests are organised around the FROZEN rules, because those are the ones an
optimizer would quietly break to make the endpoint look successful:

  * `achieved_prob` is COMPUTED by generator.generate_ensemble, never asserted.
  * `verified` is true only when the forward model actually ran.
  * `as_of_date` is a hard wall for every analog.
  * `vol_mult` is never touched to hit a target.
  * Missing model / missing corpus / missing LLM degrade, never 500.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import numpy as np
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from rulial import config as cfg  # noqa: E402
from rulial import generator as gen  # noqa: E402
from rulial.inverse import (  # noqa: E402
    MAX_FORWARD_EVALS,
    MAX_TARGET_PROB,
    MIN_TARGET_PROB,
    InverseResult,
    ScenarioRequest,
    _clean_cause,
    _looks_like_probability_claim,
    _template_candidate,
    load_research_causes,
    retrieve_analogs_for_target,
    solve_inverse,
)
from rulial.types import ForecastRequest  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixtures. The real ledger is loaded once -- these tests are about the
# real data path, since a synthetic corpus would not exercise the leak guard,
# the thin-history widening, or the research-doc grounding.
# ---------------------------------------------------------------------------
CORPUS = gen.load_seed_corpus()

NVDA_DOWN = ScenarioRequest("NVDA", "down", 0.75, "2018-11-15", 5, 3)
NVDA_UP = ScenarioRequest("NVDA", "up", 0.75, "2016-11-10", 5, 3)
XOM_DOWN = ScenarioRequest("XOM", "down", 0.57, "2019-09-13", 5, 3)


def _solve(req: ScenarioRequest, **kw) -> InverseResult:
    kw.setdefault("seed", 42)
    kw.setdefault("corpus", CORPUS)
    kw.setdefault("use_llm", False)          # offline: no candidate drafting call
    return solve_inverse(req, **kw)


# ===========================================================================
# 1.  THE FROZEN RULE: achieved_prob is computed, never asserted
# ===========================================================================
def test_achieved_prob_equals_a_fresh_forward_model_run():
    """The reported number must be reproducible by running the model again.

    This is the anchor for the whole feature: we re-run `generate_ensemble` on
    the returned `event_text`, from scratch, and require the directional
    fraction to come out identical. If `solve_inverse` ever started reporting
    an LLM's opinion, a smoothed value, or anything but the measurement, this
    test fails.
    """
    res = _solve(NVDA_DOWN)
    assert res.scenarios, "expected at least one verified scenario"
    for s in res.scenarios:
        ens = gen.generate_ensemble(
            ForecastRequest("NVDA", s.event_text, "2018-11-15", 5, cfg.DEFAULT_N_PATHS),
            seed=42, corpus=CORPUS, use_llm=False,
        )
        p = np.asarray(ens.paths, dtype=float)
        recomputed = float((p < 0.0).mean())
        assert recomputed == pytest.approx(s.achieved_prob, abs=1e-12), (
            f"achieved_prob {s.achieved_prob} does not reproduce ({recomputed}) "
            "-- the number is not coming from the forward model"
        )


def test_error_is_exactly_the_distance_to_target():
    res = _solve(XOM_DOWN)
    assert res.scenarios
    for s in res.scenarios:
        assert s.error == pytest.approx(abs(s.achieved_prob - res.target_prob), abs=1e-12)
    assert res.best_error == pytest.approx(min(s.error for s in res.scenarios), abs=1e-12)


def test_up_direction_measures_the_upper_tail():
    res = _solve(NVDA_UP)
    assert res.scenarios
    s = res.scenarios[0]
    ens = gen.generate_ensemble(
        ForecastRequest("NVDA", s.event_text, "2016-11-10", 5, cfg.DEFAULT_N_PATHS),
        seed=42, corpus=CORPUS, use_llm=False,
    )
    p = np.asarray(ens.paths, dtype=float)
    assert float((p > 0.0).mean()) == pytest.approx(s.achieved_prob, abs=1e-12)


def test_verified_is_true_only_when_the_model_ran(monkeypatch):
    """No forward model -> no scenarios, no probability, no placeholder number."""
    def _boom(*a, **k):
        raise RuntimeError("forward model down")

    monkeypatch.setattr(gen, "generate_ensemble", _boom)
    res = _solve(NVDA_DOWN)
    assert res.scenarios == []
    assert res.best_error is None, "an unverified search must not report a numeric error"
    assert "FORWARD MODEL UNAVAILABLE" in res.note


def test_every_returned_scenario_is_flagged_verified():
    res = _solve(NVDA_DOWN)
    assert res.scenarios
    assert all(s.verified is True for s in res.scenarios)


# ===========================================================================
# 2.  THE FROZEN RULE: the LLM proposes prose, never a probability
# ===========================================================================
@pytest.mark.parametrize("text", [
    "There is a 70% chance NVDA declines next week",
    "Probability of a decline is elevated",
    "The odds of a selloff are high",
    "We estimate the likelihood at two thirds",
    "80% probability of a miss",
    "chance of 60 percent",
])
def test_probability_claims_are_rejected(text):
    assert _looks_like_probability_claim(text) is True


@pytest.mark.parametrize("text", [
    "NVIDIA guides datacenter revenue 40% below consensus on a crypto inventory hangover",
    "Boeing grounds the 737 MAX fleet after a second fatal accident",
    "Exxon reports a 24% revenue shortfall as Brent slides",
])
def test_plausible_event_prose_is_not_rejected(text):
    """Magnitudes are the search's knob. Only probability language is banned."""
    assert _looks_like_probability_claim(text) is False


def test_no_returned_candidate_asserts_a_probability():
    for req in (NVDA_DOWN, NVDA_UP, XOM_DOWN):
        res = _solve(req)
        for s in res.scenarios:
            assert not _looks_like_probability_claim(s.event_text), s.event_text


# ===========================================================================
# 3.  THE FROZEN RULE: as_of_date is a hard wall
# ===========================================================================
def test_no_analog_forward_window_closes_after_as_of():
    for req in (NVDA_DOWN, NVDA_UP, XOM_DOWN):
        analogs, _ = retrieve_analogs_for_target(
            req.ticker, req.direction, req.as_of_date, req.horizon_days, corpus=CORPUS,
        )
        assert analogs, f"no analogs for {req.ticker}"
        for a in analogs:
            assert a.event.date <= req.as_of_date
            ser = gen._load_price_series(a.event.ticker)
            assert gen._forward_window_closes_by(
                a.event, req.as_of_date, req.horizon_days, ser
            ), f"{a.event.ticker} {a.event.date} window is not closed by {req.as_of_date}"


def test_reported_analogs_never_postdate_as_of():
    res = _solve(NVDA_DOWN)
    for s in res.scenarios:
        for ev in s.analogs_used:
            assert ev.date <= NVDA_DOWN.as_of_date


def test_an_earlier_as_of_cannot_see_a_later_event():
    """A 2016 request must not be grounded in the 2018 crypto-hangover event."""
    analogs, _ = retrieve_analogs_for_target("NVDA", "down", "2016-11-10", 5, corpus=CORPUS)
    dates = {(a.event.ticker, a.event.date) for a in analogs}
    assert ("NVDA", "2018-11-23") not in dates


# ===========================================================================
# 4.  THE FROZEN RULE: no widening of vol_mult to hit a target
# ===========================================================================
def test_module_never_touches_vol_mult_or_the_prior_width():
    """A source-level guard on the rule an optimizer would most want to break.

    Hitting a target by inflating ensemble width was measured at -52% CRPS
    lift. The search is allowed to vary the candidate TEXT and nothing else,
    so this module must never write to vol_mult, MAX_VOL_MULT,
    LLM_WIDTH_TRUST or HORIZON_CALIBRATION.
    """
    src = (Path(__file__).resolve().parents[1] / "rulial" / "inverse.py").read_text()
    code = "\n".join(
        line for line in src.splitlines()
        if not line.lstrip().startswith("#")
    )
    banned = ("vol_mult", "MAX_VOL_MULT", "MIN_VOL_MULT", "LLM_WIDTH_TRUST",
              "HORIZON_CALIBRATION", "MAX_PRIOR_DRIFT_5D")
    for name in banned:
        assert not re.search(rf"\b{name}\s*=", code), f"inverse.py assigns {name}"
        assert not re.search(rf"gen\.{name}\b", code), f"inverse.py reaches into gen.{name}"


def test_search_only_varies_the_event_text():
    """Every verification must use the same ticker / date / horizon / n_paths."""
    seen = []
    real = gen.generate_ensemble

    def _spy(req, **kw):
        seen.append((req.ticker, req.as_of_date, req.horizon_days, req.n_paths))
        return real(req, **kw)

    gen.generate_ensemble, saved = _spy, gen.generate_ensemble
    try:
        _solve(NVDA_DOWN)
    finally:
        gen.generate_ensemble = saved
    assert seen
    assert len(set(seen)) == 1, f"the search varied more than the text: {set(seen)}"


# ===========================================================================
# 5.  Reproducibility and budget
# ===========================================================================
def test_same_seed_gives_identical_probabilities():
    a = _solve(NVDA_DOWN)
    b = _solve(NVDA_DOWN)
    assert [s.achieved_prob for s in a.scenarios] == [s.achieved_prob for s in b.scenarios]
    assert [s.event_text for s in a.scenarios] == [s.event_text for s in b.scenarios]


def test_seed_is_threaded_through_to_the_forward_model():
    seeds = []
    real = gen.generate_ensemble

    def _spy(req, **kw):
        seeds.append(kw.get("seed"))
        return real(req, **kw)

    gen.generate_ensemble, saved = _spy, gen.generate_ensemble
    try:
        _solve(NVDA_DOWN, seed=1234)
    finally:
        gen.generate_ensemble = saved
    assert seeds and set(seeds) == {1234}


def test_evaluation_cap_is_respected():
    res = _solve(NVDA_DOWN)
    assert 0 < res.search_iterations <= MAX_FORWARD_EVALS
    tight = _solve(NVDA_DOWN, max_evals=6)
    assert tight.search_iterations <= 6
    assert tight.scenarios, "a tiny budget must still return something verified"


def test_demo_speed_under_twenty_seconds():
    t0 = time.time()
    res = _solve(NVDA_DOWN)
    elapsed = time.time() - t0
    assert res.scenarios
    assert elapsed < 20.0, f"n_candidates=3 took {elapsed:.1f}s"


def test_n_candidates_is_honoured_and_bounded():
    assert len(_solve(ScenarioRequest("NVDA", "down", 0.60, "2018-11-15", 5, 1)).scenarios) == 1
    res = _solve(ScenarioRequest("NVDA", "down", 0.60, "2018-11-15", 5, 3))
    assert 1 <= len(res.scenarios) <= 3


# ===========================================================================
# 6.  Graceful degradation -- never a 500, never a fabricated number
# ===========================================================================
def test_ticker_outside_the_frozen_universe():
    res = _solve(ScenarioRequest("FOO", "down", 0.60, "2018-11-15", 5, 3))
    assert res.scenarios == []
    assert res.best_error is None
    assert "not in the frozen universe" in res.note


def test_zero_analogs_still_returns_a_well_formed_result():
    """A 2001 as_of predates every ledger event: zero analogs, no crash."""
    res = _solve(ScenarioRequest("BA", "down", 0.60, "2001-01-05", 5, 2))
    assert isinstance(res, InverseResult)
    assert "ZERO ADMISSIBLE ANALOGS" in res.note
    for s in res.scenarios:
        assert s.verified is True          # the null-shaped ensemble still ran


def test_empty_corpus_degrades_loudly():
    res = _solve(NVDA_DOWN, corpus=[])
    assert "ZERO ADMISSIBLE ANALOGS" in res.note
    assert all(s.verified for s in res.scenarios)


def test_absent_llm_is_announced_loudly():
    res = _solve(NVDA_DOWN, use_llm=False)
    assert "NO LLM REACHED FOR CANDIDATE DRAFTING" in res.note
    assert "TEMPLATED RECOMBINATION" in res.note


def test_target_prob_and_direction_are_clamped():
    res = _solve(ScenarioRequest("NVDA", "sideways", 2.5, "2018-11-15", 5, 2))
    assert res.direction == "down"
    assert res.target_prob == MAX_TARGET_PROB
    assert "clamped" in res.note
    low = _solve(ScenarioRequest("NVDA", "down", 0.10, "2018-11-15", 5, 2))
    assert low.target_prob == MIN_TARGET_PROB


def test_missing_research_file_is_not_fatal(tmp_path):
    assert load_research_causes("NVDA", research_dir=tmp_path) == {}
    res = _solve(NVDA_DOWN, research_dir=tmp_path)
    assert res.scenarios


# ===========================================================================
# 7.  Honesty of the reported note
# ===========================================================================
def test_out_of_reach_target_is_declared_not_hidden():
    """0.75 is above the model's structural ceiling. Say so; do not fake it."""
    res = _solve(NVDA_DOWN)
    assert res.scenarios
    assert "REACHABLE BAND" in res.note
    assert "TARGET OUT OF REACH" in res.note
    assert res.best_error is not None and res.best_error > 0.10
    # and the reported band must actually contain what the search achieved
    m = re.search(r"P\(down\) spans ([0-9.]+) to ([0-9.]+)", res.note)
    assert m
    lo, hi = float(m.group(1)), float(m.group(2))
    for s in res.scenarios:
        assert lo - 1e-9 <= s.achieved_prob <= hi + 1e-9


def test_reachable_target_is_hit_and_not_declared_out_of_reach():
    res = _solve(XOM_DOWN)
    assert res.scenarios
    assert "TARGET OUT OF REACH" not in res.note
    assert res.best_error < 0.02, f"best_error {res.best_error}"


def test_note_reports_monte_carlo_error_and_non_uniqueness():
    res = _solve(XOM_DOWN)
    assert "MONTE CARLO ERROR" in res.note
    assert "not unique" in res.note.lower()
    assert "forward-model evaluation" in res.note


def test_thin_history_widens_cross_ticker_and_says_so():
    """META has no pre-2013 history of its own -- the motivating case."""
    res = _solve(ScenarioRequest("META", "down", 0.60, "2012-09-01", 5, 2))
    assert "CROSS-TICKER ANALOGS USED" in res.note
    assert res.scenarios


# ===========================================================================
# 8.  Grounding hygiene -- candidate texts must not leak the outcome
# ===========================================================================
def test_clean_cause_strips_the_realized_price_move():
    raw = ("Nov 15 Q3 FY2019: revenue below guidance on a crypto hangover; "
           "stock -18.8% Nov 16, -12% more Nov 19")
    out = _clean_cause(raw)
    assert "revenue below guidance" in out
    assert "18.8" not in out and "stock" not in out.lower()
    assert not out.startswith("Nov 15")


@pytest.mark.parametrize("raw,banned", [
    ("Third Model S battery fire; the stock loses 20.4% over November", "20.4"),
    ("Q1 FY2017 beat on datacenter and gaming; stock +15.2% on May 13", "15.2"),
    ("Guidance cut, shares closed down 9% on the session", "9%"),
    ("Nov 15 Q3 FY2019 below guidance. Stock -18.8% Nov 16", "18.8"),
])
def test_clean_cause_removes_any_clause_about_the_share_price(raw, banned):
    out = _clean_cause(raw)
    assert banned not in out
    for w in ("stock", "share"):
        assert w not in out.lower()
    assert out.strip(), f"cleaner emptied: {raw}"


def test_clean_cause_does_not_eat_a_bare_year():
    assert _clean_cause("July 2009 earnings-season rally").startswith("July 2009")


def test_candidate_texts_do_not_state_a_realized_stock_move():
    for req in (NVDA_DOWN, NVDA_UP, XOM_DOWN):
        for s in _solve(req).scenarios:
            low = s.event_text.lower()
            assert "stock fell" not in low and "stock rose" not in low
            assert "shares fell" not in low and "shares surged" not in low


def test_candidates_cite_a_real_dated_analog():
    """Provenance is inside the text so a judge can trace it to the ledger."""
    ledger = {(e.ticker, e.date) for e in CORPUS}
    res = _solve(XOM_DOWN)
    pat = re.compile(r"\b([A-Z]{1,5}) (\d{4}-\d{2}-\d{2})\b")
    for s in res.scenarios:
        hits = pat.findall(s.event_text)
        assert hits, f"no analog citation in: {s.event_text}"
        for tick, dt in hits:
            assert (tick, dt) in ledger, f"cited {tick} {dt} is not in the ledger"


def test_returned_scenarios_are_distinct():
    res = _solve(XOM_DOWN)
    texts = [s.event_text for s in res.scenarios]
    assert len(set(texts)) == len(texts)


def test_template_candidate_is_deterministic():
    analogs, _ = retrieve_analogs_for_target("NVDA", "down", "2018-11-15", 5, corpus=CORPUS)
    a = _template_candidate("NVDA", "down", 0.5, analogs[0])
    b = _template_candidate("NVDA", "down", 0.5, analogs[0])
    assert a == b and "NVDA" in a


def test_research_parser_is_header_driven_not_fixed_index():
    """The research files do not share one table shape.

    AAPL.md has an extra "Driver day inside window" column, and BA.md / MSFT.md
    contain ledger-reproduction tables whose rows are also date-led. A
    fixed-index parser read those as causes ("2008-10-03", "-0.223481"). The
    parser must key off the Headline column of a real header row.
    """
    aapl = load_research_causes("AAPL")
    assert "2008-10-03" in aapl
    cat, cause = aapl["2008-10-03"]
    assert cat == "macro" and "TARP" in cause

    ba = load_research_causes("BA")
    for dt, (_cat, cause) in ba.items():
        assert not re.fullmatch(r"[-+]?\d*\.?\d+", cause), f"BA {dt} parsed a number: {cause}"
        assert not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cause), f"BA {dt} parsed a date: {cause}"

    for t in cfg.UNIVERSE:
        for dt, (_cat, cause) in load_research_causes(t).items():
            assert len(cause) > 8, f"{t} {dt}: implausible cause {cause!r}"


def test_research_causes_parse_for_every_universe_ticker():
    total = 0
    for t in cfg.UNIVERSE:
        causes = load_research_causes(t)
        assert isinstance(causes, dict)
        total += len(causes)
    assert total > 250, f"only {total} sourced causes parsed from docs/research/"


# ===========================================================================
# 9.  Contract shape
# ===========================================================================
def test_result_has_the_contract_shape():
    res = _solve(XOM_DOWN)
    d = res.to_dict()
    assert set(d) == {"target_prob", "direction", "ticker", "scenarios",
                      "best_error", "search_iterations", "note"}
    for s in d["scenarios"]:
        assert set(s) == {"event_text", "achieved_prob", "error", "quantiles",
                          "analogs_used", "narrative", "verified"}
        assert set(s["quantiles"]) >= {"p5", "p25", "p50", "p75", "p95"}
        assert isinstance(s["analogs_used"], list) and s["analogs_used"]
        assert s["narrative"]


def test_quantiles_are_ordered():
    for s in _solve(NVDA_DOWN).scenarios:
        q = s.quantiles
        assert q["p5"] <= q["p25"] <= q["p50"] <= q["p75"] <= q["p95"]


# ===========================================================================
# 10. The HTTP route (CONTRACT.md s6b)
# ===========================================================================
def _client():
    from fastapi.testclient import TestClient
    from rulial.api import app
    return TestClient(app)


def test_scenario_route_returns_the_contract_shape():
    r = _client().post("/api/scenario", json={
        "ticker": "XOM", "direction": "down", "target_prob": 0.57,
        "as_of_date": "2019-09-13", "horizon_days": 5, "n_candidates": 3,
    })
    assert r.status_code == 200
    b = r.json()
    assert {"target_prob", "direction", "ticker", "scenarios",
            "best_error", "search_iterations", "note"} <= set(b)
    assert b["ticker"] == "XOM" and b["direction"] == "down"
    assert b["scenarios"]
    for s in b["scenarios"]:
        assert {"event_text", "achieved_prob", "error", "quantiles",
                "analogs_used", "narrative", "verified"} <= set(s)
        assert s["verified"] is True
        assert 0.0 <= s["achieved_prob"] <= 1.0
        assert s["error"] == pytest.approx(abs(s["achieved_prob"] - b["target_prob"]), abs=1e-9)


def test_scenario_route_is_stable_across_calls():
    c = _client()
    body = {"ticker": "XOM", "direction": "down", "target_prob": 0.57,
            "as_of_date": "2019-09-13", "n_candidates": 3}
    a = c.post("/api/scenario", json=body).json()
    b = c.post("/api/scenario", json=body).json()
    assert [s["achieved_prob"] for s in a["scenarios"]] == \
           [s["achieved_prob"] for s in b["scenarios"]]


def test_scenario_route_number_reproduces_through_the_forecast_route():
    """A judge can recompute the probability from a DIFFERENT endpoint."""
    c = _client()
    s = c.post("/api/scenario", json={
        "ticker": "XOM", "direction": "down", "target_prob": 0.57,
        "as_of_date": "2019-09-13", "n_candidates": 1,
    }).json()["scenarios"][0]
    f = c.post("/api/forecast", json={
        "ticker": "XOM", "event_text": s["event_text"], "as_of_date": "2019-09-13",
        "horizon_days": 5, "n_paths": cfg.DEFAULT_N_PATHS,
    }).json()
    paths = f["ensemble"]["paths"]
    recomputed = sum(1 for x in paths if x < 0) / len(paths)
    assert recomputed == pytest.approx(s["achieved_prob"], abs=1e-12)


def test_scenario_route_rejects_a_ticker_outside_the_universe():
    r = _client().post("/api/scenario", json={"ticker": "FOO", "direction": "down",
                                              "target_prob": 0.6, "as_of_date": "2018-11-15"})
    assert r.status_code == 200
    b = r.json()
    assert b["unavailable"] is True and b["scenarios"] == [] and b["best_error"] is None


def test_scenario_route_degrades_when_the_solver_raises(monkeypatch):
    from rulial import inverse as inv
    monkeypatch.setattr(inv, "solve_inverse",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    r = _client().post("/api/scenario", json={"ticker": "NVDA", "direction": "down",
                                              "target_prob": 0.6, "as_of_date": "2018-11-15"})
    assert r.status_code == 200
    b = r.json()
    assert b["scenarios"] == [] and b["best_error"] is None and "boom" in (b["error"] or "")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
