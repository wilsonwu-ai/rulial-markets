"""
Tests for rulial.rulial -- the 144-generator rulial ensemble (CONTRACT.md s6d).

These tests are deliberately weighted toward the things an optimizer would
break to look successful:

  * the grid is 144 and no code path may shrink it;
  * `reducible` and every agreement fraction are MEASURED from the runs that
    actually completed, never asserted;
  * a failed rule is EXCLUDED from consensus and never counted as agreement;
  * Boltzmann stays in the response;
  * a property that flips across the grid lands in `rule_dependent`, never in
    `invariants`;
  * as_of_date is a hard wall -- no analog's forward window may close after it.
"""
from __future__ import annotations

import math
import time

import numpy as np
import pytest

from rulial import generator as G
from rulial import rulial as R
from rulial.types import ForecastRequest

REQ_BULL = ForecastRequest(
    ticker="NVDA",
    event_text="NVDA announces a 40% datacenter revenue beat and raises guidance",
    as_of_date="2016-11-10", horizon_days=5, n_paths=500,
)
REQ_BEAR = ForecastRequest(
    ticker="NVDA",
    event_text="NVDA warns of a 40% datacenter revenue miss and cuts guidance on a crypto glut",
    as_of_date="2018-11-15", horizon_days=5, n_paths=500,
)
REQ_XOM = ForecastRequest(
    ticker="XOM",
    event_text="XOM refinery outage after a drone strike on Gulf capacity",
    as_of_date="2019-09-13", horizon_days=5, n_paths=500,
)


@pytest.fixture(scope="module")
def corpus():
    return G.load_seed_corpus()


@pytest.fixture(scope="module")
def result_bull(corpus):
    return R.rulial_ensemble(REQ_BULL, n_paths_per_rule=120, seed=11, corpus=corpus)


# --------------------------------------------------------------------------
# The frozen grid
# --------------------------------------------------------------------------
def test_grid_axes_are_exactly_the_contract():
    assert R.RULE_AXES == {
        "analog_selection": ["tfidf_magnitude", "ticker_only", "tier_only", "text_only"],
        "conditioning": ["cross_ticker", "same_ticker", "same_era"],
        "drift_prior": ["scenario", "zero", "unconditional", "sign_only"],
        "resampling": ["block", "iid", "stationary"],
    }
    assert R.GRID_SIZE == 144


def test_enumerate_grid_is_144_unique_points():
    g = R.enumerate_grid()
    assert len(g) == 144
    assert len({tuple(sorted(r.items())) for r in g}) == 144
    for axis, levels in R.RULE_AXES.items():
        # every level appears exactly 144/len(levels) times -- a balanced design,
        # which is what makes the eta^2 decomposition meaningful
        for lv in levels:
            assert sum(1 for r in g if r[axis] == lv) == 144 // len(levels)


def test_enumerate_grid_is_deterministically_ordered():
    assert R.enumerate_grid() == R.enumerate_grid()


def test_every_grid_point_actually_runs(result_bull):
    d = result_bull.diagnostics
    assert d["grid_size_run"] == 144
    assert d["n_generators_ok"] + d["n_generators_failed"] == 144
    assert len(result_bull.rulial["per_generator"]) == d["n_generators_ok"]


def test_no_axis_is_pruned_in_the_output(result_bull):
    seen = {a: set() for a in R.AXIS_ORDER}
    for g in result_bull.rulial["per_generator"]:
        for a in R.AXIS_ORDER:
            seen[a].add(g.rule[a])
    for a in R.AXIS_ORDER:
        assert seen[a] == set(R.RULE_AXES[a]), f"axis {a} lost a level"


# --------------------------------------------------------------------------
# Consensus is measured, not asserted
# --------------------------------------------------------------------------
def test_sign_agreement_is_recomputable_from_per_generator(result_bull):
    meds = [g.median for g in result_bull.rulial["per_generator"]]
    n = len(meds)
    n_neg = sum(1 for m in meds if m < 0)
    n_pos = sum(1 for m in meds if m > 0)
    expected = max(n_neg, n_pos) / n
    assert result_bull.rulial["consensus"]["sign_agreement"] == pytest.approx(expected)


def test_reducible_is_exactly_the_measured_threshold(result_bull):
    c = result_bull.rulial["consensus"]
    assert c["reducible"] is (c["sign_agreement"] >= 0.90)


def test_bands_bracket_every_generator(result_bull):
    c = result_bull.rulial["consensus"]
    lo, hi = c["median_band"]
    plo, phi = c["p_down_band"]
    for g in result_bull.rulial["per_generator"]:
        assert lo - 1e-12 <= g.median <= hi + 1e-12
        assert plo - 1e-12 <= g.p_down <= phi + 1e-12


def test_p_down_is_a_probability(result_bull):
    for g in result_bull.rulial["per_generator"]:
        assert 0.0 <= g.p_down <= 1.0


def test_quantiles_are_monotone(result_bull):
    for g in result_bull.rulial["per_generator"]:
        q = g.quantiles
        assert q["p5"] <= q["p25"] <= q["p50"] <= q["p75"] <= q["p95"]
        assert g.median == pytest.approx(q["p50"])


# --------------------------------------------------------------------------
# Boltzmann stays in the response
# --------------------------------------------------------------------------
def test_boltzmann_is_present_and_populated(result_bull):
    b = result_bull.boltzmann
    assert b["n_paths"] > 0
    assert set(b["quantiles"]) >= {"p5", "p25", "p50", "p75", "p95"}
    assert math.isfinite(b["median"])
    assert 0.0 <= b["p_down"] <= 1.0


def test_boltzmann_survives_serialization(result_bull):
    assert "boltzmann" in result_bull.to_dict()
    assert result_bull.to_dict()["boltzmann"]["n_paths"] > 0


# --------------------------------------------------------------------------
# Invariants vs rule-dependence
# --------------------------------------------------------------------------
def test_invariants_all_clear_the_90_percent_bar(result_bull):
    for rec in result_bull.diagnostics["property_detail"]:
        f = rec["fraction_true"]
        if rec["verdict"] == "invariant":
            assert f >= R.INVARIANT_THRESHOLD
        elif rec["verdict"] == "invariant_negated":
            assert f <= 1.0 - R.INVARIANT_THRESHOLD
        else:
            assert 1.0 - R.INVARIANT_THRESHOLD < f < R.INVARIANT_THRESHOLD


def test_rule_dependent_statements_name_the_axis(result_bull):
    for s in result_bull.rule_dependent:
        assert "RULE-DEPENDENT" in s
        assert any(f"`{a}`" in s for a in R.AXIS_ORDER), s
        assert "NOT skill" in s


def test_a_flipping_property_never_lands_in_invariants(result_bull):
    flipping = {rec["key"] for rec in result_bull.diagnostics["property_detail"]
                if rec["verdict"] == "rule_dependent"}
    for rec in result_bull.diagnostics["property_detail"]:
        if rec["key"] in flipping:
            assert not any(rec["statement"] in inv for inv in result_bull.invariants)


# --------------------------------------------------------------------------
# Variance decomposition
# --------------------------------------------------------------------------
def test_eta_squared_is_a_fraction_and_sums_sanely(result_bull):
    for metric in ("median", "p_down"):
        dec = result_bull.variance_decomposition[metric]
        tot = 0.0
        for a in R.AXIS_ORDER:
            e = dec["axes"][a]["eta_squared"]
            assert 0.0 <= e <= 1.0 + 1e-9
            tot += e
        assert tot <= 1.0 + 1e-6, "main effects cannot explain more than all the variance"
        assert dec["dominant_axis"] in R.AXIS_ORDER


def test_eta_squared_matches_a_hand_rolled_anova(result_bull):
    reps = result_bull.rulial["per_generator"]
    vals = np.array([g.median for g in reps])
    labs = [g.rule["drift_prior"] for g in reps]
    grand = vals.mean()
    ss_tot = ((vals - grand) ** 2).sum()
    ss_b = 0.0
    for lv in set(labs):
        idx = [i for i, l in enumerate(labs) if l == lv]
        ss_b += len(idx) * (vals[idx].mean() - grand) ** 2
    assert result_bull.variance_decomposition["median"]["axes"]["drift_prior"][
        "eta_squared"] == pytest.approx(ss_b / ss_tot, rel=1e-9)


# --------------------------------------------------------------------------
# Reproducibility and budget
# --------------------------------------------------------------------------
def test_same_seed_gives_identical_grid(corpus):
    a = R.rulial_ensemble(REQ_BULL, n_paths_per_rule=60, seed=5, corpus=corpus,
                          noise_floor=False)
    b = R.rulial_ensemble(REQ_BULL, n_paths_per_rule=60, seed=5, corpus=corpus,
                          noise_floor=False)
    assert [g.median for g in a.rulial["per_generator"]] == \
           [g.median for g in b.rulial["per_generator"]]
    assert a.rulial["consensus"] == b.rulial["consensus"]


def test_different_seed_moves_the_numbers(corpus):
    a = R.rulial_ensemble(REQ_BULL, n_paths_per_rule=60, seed=5, corpus=corpus,
                          noise_floor=False)
    b = R.rulial_ensemble(REQ_BULL, n_paths_per_rule=60, seed=6, corpus=corpus,
                          noise_floor=False)
    assert [g.median for g in a.rulial["per_generator"]] != \
           [g.median for g in b.rulial["per_generator"]]


def test_no_seed_still_reproduces_from_the_request(corpus):
    a = R.rulial_ensemble(REQ_BULL, n_paths_per_rule=60, corpus=corpus, noise_floor=False)
    b = R.rulial_ensemble(REQ_BULL, n_paths_per_rule=60, corpus=corpus, noise_floor=False)
    assert a.diagnostics["seed"] == b.diagnostics["seed"]
    assert [g.median for g in a.rulial["per_generator"]] == \
           [g.median for g in b.rulial["per_generator"]]


def test_full_grid_at_250_paths_is_well_under_the_budget(corpus):
    t = time.perf_counter()
    res = R.rulial_ensemble(REQ_BULL, n_paths_per_rule=250, seed=1, corpus=corpus)
    wall = time.perf_counter() - t
    assert res.diagnostics["n_generators_ok"] == 144
    assert res.diagnostics["total_paths"] == 144 * 250
    assert wall < 90.0, f"144 x 250 took {wall:.1f}s"
    # the returned wall clock is the real one, not a claim
    assert res.diagnostics["wall_clock_s"] == pytest.approx(wall, rel=0.5)


# --------------------------------------------------------------------------
# The leak guard
# --------------------------------------------------------------------------
def test_no_analog_forward_window_closes_after_as_of(corpus):
    as_of = REQ_XOM.as_of_date
    pool = R._admissible_pool(corpus, as_of, 5, None)
    assert pool, "expected a non-empty admissible pool for this request"
    for ev in pool:
        assert ev.date <= as_of
        ser = G._load_price_series(ev.ticker, None)
        assert G._forward_window_closes_by(ev, as_of, 5, ser)


def test_admissible_pool_shrinks_as_as_of_moves_back(corpus):
    early = len(R._admissible_pool(corpus, "2010-01-04", 5, None))
    late = len(R._admissible_pool(corpus, "2019-12-31", 5, None))
    assert early < late


def test_same_era_filter_respects_as_of(corpus):
    pool = R._admissible_pool(corpus, "2019-09-13", 5, None)
    sub, notes = R._condition_pool("same_era", pool, "XOM", "2019-09-13")
    if not notes:                       # notes non-empty means it widened
        cutoff = f"{2019 - R.ERA_YEARS}-09-13"
        assert all(e.date >= cutoff for e in sub)
        assert len(sub) <= len(pool)


def test_generator_leak_guard_still_fires_under_a_rule_set_override(corpus):
    """The RULE_SET override must not weaken the leak guard.

    Two halves, because the generator defends twice: `retrieve_analogs` drops a
    post-as_of event before it is ever an analog (so the ensemble degrades to
    the null shape rather than raising), and `assert_no_lookahead` raises if one
    is handed to it directly. Both must still hold with our rules installed.
    """
    future = [e for e in corpus if e.date > "2016-11-10"][:3]
    assert future
    with R._rule_set_override(R._generator_rules(R._BASELINE_RULE, 5)):
        ens = G.generate_ensemble(REQ_BULL, seed=1, corpus=future, use_llm=False)
        assert ens.analogs == [], "a post-as_of event reached the ensemble"
        assert ens.diagnostics["zero_analog_fallback"] is True
        with pytest.raises(G.LookaheadError):
            G.assert_no_lookahead(future, "2016-11-10", 5, None)


# --------------------------------------------------------------------------
# The RULE_SET override
# --------------------------------------------------------------------------
def test_rule_set_is_restored_even_on_exception():
    original = G.RULE_SET
    with pytest.raises(RuntimeError):
        with R._rule_set_override(R._generator_rules(R._BASELINE_RULE, 5)):
            assert G.RULE_SET != original
            raise RuntimeError("boom")
    assert G.RULE_SET is original


def test_rule_set_is_restored_after_a_full_run(corpus):
    original = G.RULE_SET
    R.rulial_ensemble(REQ_BULL, n_paths_per_rule=20, seed=3, corpus=corpus, noise_floor=False)
    assert G.RULE_SET is original


def test_vol_anchor_and_scope_are_held_fixed_across_the_grid():
    for rule in R.enumerate_grid():
        for gr in R._generator_rules(rule, 5):
            assert gr.vol_anchor == R.FIXED_VOL_ANCHOR
            assert gr.analog_scope == R.FIXED_ANALOG_SCOPE


def test_resampling_axis_maps_to_real_block_lengths():
    iid = R._generator_rules({**R._BASELINE_RULE, "resampling": "iid"}, 5)
    blk = R._generator_rules({**R._BASELINE_RULE, "resampling": "block"}, 5)
    sta = R._generator_rules({**R._BASELINE_RULE, "resampling": "stationary"}, 5)
    assert [r.block_len for r in iid] == [1]
    assert [r.block_len for r in blk] == [5]
    assert [r.block_len for r in sta] == [1, 2, 3, 4, 5]
    assert sum(r.weight for r in sta) == pytest.approx(1.0)
    # geometric: shorter blocks get more weight
    assert sta[0].weight > sta[-1].weight


def test_drift_axis_maps_to_the_generators_own_modes():
    assert R._DRIFT_MODE["scenario"] == "prior"
    assert R._DRIFT_MODE["zero"] == "neutral"
    assert R._DRIFT_MODE["unconditional"] == "analog"   # the generator's labelled trap
    assert R._DRIFT_MODE["sign_only"] == "neutral"      # base; the sign is added post-hoc


def test_sign_only_shift_is_signed_by_the_text_and_sized_by_the_data(corpus):
    """sign_only must carry the text's sign, and only the text's sign."""
    rules = {"analog_selection": "tfidf_magnitude", "conditioning": "cross_ticker",
             "resampling": "block"}
    bear = R._run_grid_point({**rules, "drift_prior": "sign_only"}, REQ_BEAR,
                             pool=R._admissible_pool(corpus, REQ_BEAR.as_of_date, 5, None),
                             seed=7, n_paths=250, n_analogs=25, use_llm=False, prices_dir=None)
    bull = R._run_grid_point({**rules, "drift_prior": "sign_only"}, REQ_BULL,
                             pool=R._admissible_pool(corpus, REQ_BULL.as_of_date, 5, None),
                             seed=7, n_paths=250, n_analogs=25, use_llm=False, prices_dir=None)
    assert bear.drift_shift_log <= 0.0
    assert bull.drift_shift_log >= 0.0
    zero = R._run_grid_point({**rules, "drift_prior": "zero"}, REQ_BEAR,
                             pool=R._admissible_pool(corpus, REQ_BEAR.as_of_date, 5, None),
                             seed=7, n_paths=250, n_analogs=25, use_llm=False, prices_dir=None)
    assert zero.drift_shift_log == 0.0
    if bear.drift_shift_log != 0.0:
        assert bear.median < zero.median


# --------------------------------------------------------------------------
# Failure handling -- a bad rule is excluded, never counted as agreement
# --------------------------------------------------------------------------
def test_a_failing_rule_is_excluded_and_counted(monkeypatch, corpus):
    real = R._run_grid_point
    calls = {"n": 0}

    def flaky(rule, req, **kw):
        calls["n"] += 1
        if rule["drift_prior"] == "unconditional":
            raise ValueError("synthetic failure for test")
        return real(rule, req, **kw)

    monkeypatch.setattr(R, "_run_grid_point", flaky)
    res = R.rulial_ensemble(REQ_BULL, n_paths_per_rule=40, seed=2, corpus=corpus,
                            noise_floor=False)
    assert len(res.failures) == 36                     # 144/4 drift levels
    assert res.diagnostics["n_generators_ok"] == 108
    assert len(res.rulial["per_generator"]) == 108
    assert all("unconditional" in f["rule"] for f in res.failures)
    # the excluded rules are NOT silently counted as agreement
    meds = [g.median for g in res.rulial["per_generator"]]
    n_neg = sum(1 for m in meds if m < 0)
    n_pos = sum(1 for m in meds if m > 0)
    assert res.rulial["consensus"]["sign_agreement"] == pytest.approx(
        max(n_neg, n_pos) / 108)
    assert "excluded from consensus" in res.note


def test_total_failure_does_not_raise_and_does_not_claim_reducible(monkeypatch, corpus):
    monkeypatch.setattr(R, "_run_grid_point",
                        lambda *a, **k: (_ for _ in ()).throw(ValueError("all dead")))
    res = R.rulial_ensemble(REQ_BULL, n_paths_per_rule=20, seed=2, corpus=corpus,
                            noise_floor=False)
    assert len(res.failures) == 144
    assert res.rulial["n_generators"] == 0
    assert res.rulial["consensus"]["reducible"] is False
    assert res.invariants == []
    assert "EVERY generator failed" in " ".join(res.diagnostics["warnings"])
    assert res.boltzmann["n_paths"] > 0          # Boltzmann still on screen


def test_empty_corpus_degrades_rather_than_crashing():
    res = R.rulial_ensemble(REQ_BULL, n_paths_per_rule=40, seed=4, corpus=[],
                            noise_floor=False)
    assert res.diagnostics["n_generators_ok"] == 144
    assert res.diagnostics["admissible_pool_size"] == 0
    assert any("ZERO admissible" in w for w in res.diagnostics["warnings"])


# --------------------------------------------------------------------------
# The drift headline -- measured, on three real requests
# --------------------------------------------------------------------------
@pytest.mark.parametrize("req", [REQ_BULL, REQ_BEAR, REQ_XOM],
                         ids=["nvda-2016-bull", "nvda-2018-bear", "xom-2019"])
def test_drift_axis_dominates_median_variance(req, corpus):
    """The headline claim, tested as a measurement rather than stated.

    If this ever fails it is a real finding about that request, not a broken
    test -- the note reports the honest miss in that case.
    """
    res = R.rulial_ensemble(req, n_paths_per_rule=250, seed=99, corpus=corpus,
                            noise_floor=False)
    dec = res.variance_decomposition["median"]
    assert dec["dominant_axis"] == "drift_prior", (
        f"{req.ticker} {req.as_of_date}: dominant axis was {dec['dominant_axis']} "
        f"with eta^2 " + str({a: round(dec['axes'][a]['eta_squared'], 3)
                              for a in R.AXIS_ORDER})
    )
    assert dec["axes"]["drift_prior"]["eta_squared"] > sum(
        dec["axes"][a]["eta_squared"] for a in R.AXIS_ORDER if a != "drift_prior")


def test_note_mentions_the_drift_finding_and_the_wall_clock(result_bull):
    n = result_bull.note
    assert "drift_prior" in n
    assert "wall clock" in n
    assert "144" in n
    assert "LLM OFF" in n


# --------------------------------------------------------------------------
# API route
# --------------------------------------------------------------------------
def test_api_rulial_route():
    from fastapi.testclient import TestClient
    from rulial.api import app

    c = TestClient(app)
    r = c.post("/api/rulial", json={
        "ticker": "NVDA",
        "event_text": REQ_BEAR.event_text,
        "as_of_date": "2018-11-15",
        "horizon_days": 5,
        "n_paths_per_rule": 60,
        "n_paths": 500,
        "seed": 21,
    })
    assert r.status_code == 200
    d = r.json()
    assert d["unavailable"] is False
    assert d["rulial"]["n_generators"] == 144
    assert len(d["rulial"]["per_generator"]) == 144
    assert d["boltzmann"]["n_paths"] == 500
    assert isinstance(d["rulial"]["consensus"]["reducible"], bool)
    assert 0.0 <= d["rulial"]["consensus"]["sign_agreement"] <= 1.0
    assert d["diagnostics"]["grid_size_run"] == 144
    assert d["leakage_disclosure"]


def test_api_rulial_rejects_off_universe_ticker():
    from fastapi.testclient import TestClient
    from rulial.api import app

    c = TestClient(app)
    r = c.post("/api/rulial", json={"ticker": "GME", "as_of_date": "2018-11-15"})
    assert r.status_code == 200
    assert r.json()["unavailable"] is True
    assert r.json()["rulial"]["n_generators"] == 0


# --------------------------------------------------------------------------
# Degeneracies are REPORTED, never tuned away
# --------------------------------------------------------------------------
def test_structural_collapse_is_detected_and_left_in_the_grid(corpus):
    """XOM has 3 admissible train analogs; resampling=block collapses on them.

    block_len == horizon plus one-analog-per-path means a circular rotation of a
    whole window has the same sum, so the terminal distribution has one point
    per analog. The fix would be to move block_len off the horizon -- i.e. tune
    a frozen axis. It must be reported and left alone instead.
    """
    res = R.rulial_ensemble(REQ_XOM, n_paths_per_rule=250, seed=2026, corpus=corpus,
                            noise_floor=False)
    assert res.diagnostics["n_generators_ok"] == 144, "no generator may be dropped"
    collapsed = [g for g in res.rulial["per_generator"]
                 if g.n_distinct_terminals < 10]
    assert collapsed, "expected the block/same-ticker corner to collapse on XOM"
    assert res.diagnostics["n_generators_collapsed"] == len(collapsed)
    assert all(g.rule["resampling"] == "block" for g in collapsed)
    assert any("STRUCTURAL COLLAPSE" in w for w in res.diagnostics["warnings"])
    assert all(any("STRUCTURAL COLLAPSE" in n for n in g.notes) for g in collapsed)


def test_drift_axis_coincidence_is_flagged_when_the_text_has_no_direction(corpus):
    assert G._implied_direction(REQ_XOM.event_text)[0] == "unknown"
    res = R.rulial_ensemble(REQ_XOM, n_paths_per_rule=120, seed=8, corpus=corpus,
                            noise_floor=False)
    assert res.diagnostics["implied_direction"] == "unknown"
    assert any("DRIFT-AXIS COINCIDENCE" in w for w in res.diagnostics["warnings"])
    # and the coincidence is real: three drift levels are the same generator
    meds = {lv: [g.median for g in res.rulial["per_generator"]
                 if g.rule["drift_prior"] == lv]
            for lv in R.RULE_AXES["drift_prior"]}
    assert meds["scenario"] == meds["zero"] == meds["sign_only"]
    assert meds["unconditional"] != meds["zero"]


def test_a_directional_text_does_not_trigger_the_coincidence(corpus):
    res = R.rulial_ensemble(REQ_BEAR, n_paths_per_rule=120, seed=8, corpus=corpus,
                            noise_floor=False)
    assert res.diagnostics["implied_direction"] == "down"
    assert not any("DRIFT-AXIS COINCIDENCE" in w for w in res.diagnostics["warnings"])
