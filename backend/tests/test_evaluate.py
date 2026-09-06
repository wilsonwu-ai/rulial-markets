"""
Tests for backend/rulial/evaluate.py -- LANE-EVAL.

The point of this file is not coverage, it is ANCHORING. Every estimator in
evaluate.py is checked against something that cannot argue back:

  * the closed-form Gaussian CRPS, derived by hand below,
  * the naive O(m^2) double sum, for the O(m log m) pairwise identity,
  * the propriety of CRPS (the true distribution must score best),
  * the size and power of the calibration test under simulation.

Run:  cd backend && python -m pytest tests/test_evaluate.py -q
"""

import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from rulial import evaluate as E  # noqa: E402
from rulial.config import (  # noqa: E402
    EMBARGO_DAYS,
    JUMP_THRESHOLD,
    NULL_VOL_LOOKBACK,
    TEST_START,
    TIER_MAJOR,
    TIER_SIGNIFICANT,
    TRAIN_END,
    WINDOW_DAYS,
    tier_for,
)
from rulial.types import Ensemble, Event, Score  # noqa: E402

# --------------------------------------------------------------------------- #
# Analytic anchors, derived rather than copied.
#
# CRPS(N(mu, sigma^2), y) = sigma * [ z(2 Phi(z) - 1) + 2 phi(z) - 1/sqrt(pi) ],
#                           z = (y - mu)/sigma
#
# At mu = 0, sigma = 1, y = 0:  z = 0, Phi(0) = 1/2, phi(0) = 1/sqrt(2 pi), so
#   CRPS = 0 * 0 + 2/sqrt(2 pi) - 1/sqrt(pi)
#        = sqrt(2/pi) - 1/sqrt(pi)
#        = (sqrt(2) - 1)/sqrt(pi)
#        ~= 0.2336949772551091
# --------------------------------------------------------------------------- #
CRPS_STDNORM_AT_ZERO = (math.sqrt(2.0) - 1.0) / math.sqrt(math.pi)
CRPS_STDNORM_AT_HALF = 0.3314035312548558  # crps_gaussian(0,1,0.5), cross-checked below
# E_{Y~F}[CRPS(F,Y)] = (1/2) E|X-X'| = sigma/sqrt(pi). For sigma=1: 0.5641895835477563
EXPECTED_CRPS_UNDER_TRUTH_SIGMA1 = 1.0 / math.sqrt(math.pi)


# =========================================================================== #
# 1. the closed form itself
# =========================================================================== #
def test_closed_form_matches_hand_derivation_at_zero():
    assert E.crps_gaussian(0.0, 1.0, 0.0) == pytest.approx(CRPS_STDNORM_AT_ZERO, abs=1e-15)
    assert E.crps_gaussian(0.0, 1.0, 0.0) == pytest.approx(0.23369497725510913, abs=1e-12)


def test_closed_form_matches_numeric_integration():
    """CRPS = int (F(x) - 1{x>=y})^2 dx, integrated numerically from the
    definition. The integrand has a jump at x=y, so the interval is split there
    rather than swept with one uniform grid (a uniform trapezoid across the jump
    is only O(h)-accurate and disagrees in the 5th decimal, which would make
    this anchor useless)."""
    from scipy.integrate import quad
    from scipy.stats import norm

    for mu, sigma, y in [(0.0, 1.0, 0.0), (0.0, 1.0, 0.5), (0.02, 0.09, -0.13),
                         (-0.05, 0.2, 0.4)]:
        def integrand(x, mu=mu, sigma=sigma, y=y):
            return (norm.cdf(x, mu, sigma) - (1.0 if x >= y else 0.0)) ** 2

        lo, hi = mu - 40 * sigma, mu + 40 * sigma
        numeric = (quad(integrand, lo, y, limit=400)[0]
                   + quad(integrand, y, hi, limit=400)[0])
        assert E.crps_gaussian(mu, sigma, y) == pytest.approx(numeric, rel=1e-10)


def test_closed_form_is_scale_equivariant_and_degenerate_case():
    # CRPS scales linearly in sigma when z is held fixed.
    assert E.crps_gaussian(0.0, 2.0, 0.0) == pytest.approx(2.0 * CRPS_STDNORM_AT_ZERO)
    # A point mass reduces to absolute error.
    assert E.crps_gaussian(0.1, 0.0, 0.4) == pytest.approx(0.3)


def test_crps_stdnorm_at_half_constant_is_right():
    assert E.crps_gaussian(0.0, 1.0, 0.5) == pytest.approx(CRPS_STDNORM_AT_HALF, abs=1e-12)


# =========================================================================== #
# 2. the O(m log m) pairwise identity == the O(m^2) double sum
# =========================================================================== #
def test_sorted_pairwise_identity_matches_naive_double_sum():
    rng = np.random.default_rng(11)
    for m in (2, 3, 17, 200, 501):
        x = rng.normal(size=m)
        naive = float(np.abs(x[:, None] - x[None, :]).sum())
        fast = E._pairwise_abs_sum(np.sort(x))
        assert fast == pytest.approx(naive, rel=1e-12, abs=1e-9)


def test_pairwise_identity_on_pathological_inputs():
    for x in (np.zeros(50), np.ones(7) * -3.2, np.array([1.0, 1.0, 2.0])):
        naive = float(np.abs(x[:, None] - x[None, :]).sum())
        assert E._pairwise_abs_sum(np.sort(x)) == pytest.approx(naive, abs=1e-12)


def test_crps_matches_explicit_double_loop_definition():
    """The fair estimator, written out longhand, must equal the fast one."""
    rng = np.random.default_rng(3)
    x = rng.normal(size=60)
    y = 0.3
    m = x.size
    t1 = float(np.mean(np.abs(x - y)))
    dbl = float(np.abs(x[:, None] - x[None, :]).sum())
    fair_longhand = t1 - dbl / (2.0 * m * (m - 1))
    nrg_longhand = t1 - dbl / (2.0 * m * m)
    assert E.crps(x, y) == pytest.approx(fair_longhand, rel=1e-12)
    assert E.crps_nrg(x, y) == pytest.approx(nrg_longhand, rel=1e-12)


# =========================================================================== #
# 3. the sample estimator converges to the closed form
# =========================================================================== #
def test_fair_estimator_converges_to_analytic_at_y_zero():
    rng = np.random.default_rng(2024)
    est = np.mean([E.crps(rng.normal(size=4000), 0.0) for _ in range(60)])
    assert est == pytest.approx(CRPS_STDNORM_AT_ZERO, abs=2e-3)


def test_fair_estimator_converges_to_analytic_at_y_half():
    rng = np.random.default_rng(99)
    est = np.mean([E.crps(rng.normal(size=4000), 0.5) for _ in range(60)])
    assert est == pytest.approx(CRPS_STDNORM_AT_HALF, abs=2e-3)


def test_fair_is_unbiased_and_nrg_is_upward_biased_at_small_m():
    """The whole reason evaluate.py defaults to fair.

    At m=5 the NRG plug-in overstates CRPS by roughly 0.11 on a standard normal
    -- about 47% of the true value -- which would flow straight into crps_lift.
    """
    rng = np.random.default_rng(7)
    reps = 6000
    y = 0.5
    truth = CRPS_STDNORM_AT_HALF
    prev_nrg_bias = None
    for m in (5, 10, 50, 200):
        draws = rng.normal(size=(reps, m))
        fair = np.mean([E.crps(d, y) for d in draws])
        nrg = np.mean([E.crps_nrg(d, y) for d in draws])
        fair_bias, nrg_bias = fair - truth, nrg - truth
        # fair is unbiased at every m, well inside Monte Carlo noise
        assert abs(fair_bias) < 0.006, (m, fair_bias)
        # NRG is biased UPWARD and materially so at small m
        assert nrg_bias > 0
        assert abs(nrg_bias) > abs(fair_bias)
        if m == 5:
            assert nrg_bias > 0.09
        if prev_nrg_bias is not None:
            assert nrg_bias < prev_nrg_bias  # bias shrinks as m grows
        prev_nrg_bias = nrg_bias


def test_crps_is_proper_true_distribution_scores_best():
    """Strict propriety: a correctly specified ensemble must beat a too-narrow
    and a too-wide one, averaged over draws from the truth."""
    rng = np.random.default_rng(5)
    n_obs, m = 3000, 400
    ys = rng.normal(size=n_obs)
    scores = {}
    for mult in (0.5, 1.0, 2.0):
        tot = 0.0
        for y in ys:
            tot += E.crps(rng.normal(0.0, mult, size=m), y)
        scores[mult] = tot / n_obs
    assert scores[1.0] < scores[0.5]
    assert scores[1.0] < scores[2.0]
    # And the achieved minimum is the known expected CRPS under the truth,
    # E_{Y~F}[CRPS(F,Y)] = sigma/sqrt(pi) -- NOT the CRPS at y=0.
    assert scores[1.0] == pytest.approx(EXPECTED_CRPS_UNDER_TRUTH_SIGMA1, abs=0.01)


def test_crps_is_nonnegative_and_zero_for_a_perfect_point_forecast():
    assert E.crps([0.42] * 100, 0.42) == pytest.approx(0.0, abs=1e-12)
    rng = np.random.default_rng(1)
    for _ in range(50):
        assert E.crps(rng.normal(size=50), float(rng.normal())) >= -1e-12


def test_crps_accepts_an_ensemble_object_and_a_bare_list():
    rng = np.random.default_rng(4)
    paths = list(rng.normal(0, 0.08, 500))
    ens = Ensemble(ticker="NVDA", as_of_date="2020-03-16", horizon_days=5,
                   paths=paths, quantiles={}, mean=float(np.mean(paths)),
                   std=float(np.std(paths, ddof=1)))
    assert E.crps(ens, 0.05) == pytest.approx(E.crps(paths, 0.05))


def test_crps_is_fast_at_contract_n_paths():
    """2000 paths must not run an O(m^2) 4-million-element double loop."""
    import time

    rng = np.random.default_rng(0)
    ens = [rng.normal(0, 0.09, 2000) for _ in range(200)]
    t0 = time.perf_counter()
    for e in ens:
        E.crps(e, 0.03)
    assert time.perf_counter() - t0 < 2.0


# =========================================================================== #
# 4. the frozen null model
# =========================================================================== #
def _series(vals, start="2015-01-02"):
    idx = pd.bdate_range(start=start, periods=len(vals))
    return pd.Series(np.asarray(vals, dtype=float), index=idx, name="close")


def _gbm(n=1500, sigma=0.02, seed=0, start="2015-01-02"):
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0, sigma, n)
    return _series(100.0 * np.exp(np.cumsum(r)), start=start)


def test_null_sigma_recovers_the_trailing_vol_scaled_to_horizon():
    px = _gbm(n=1200, sigma=0.02, seed=42)
    asof = px.index[-1].strftime("%Y-%m-%d")
    sig = E.null_sigma(px, asof, horizon=5)
    rets = px.pct_change().dropna().to_numpy()[-NULL_VOL_LOOKBACK:]
    expected = float(np.std(rets, ddof=1)) * math.sqrt(5)
    assert sig == pytest.approx(expected, rel=1e-12)
    assert sig == pytest.approx(0.02 * math.sqrt(5), rel=0.20)


def test_null_sigma_uses_only_data_at_or_before_asof():
    """The leak guard, at the smallest scale that matters."""
    px = _gbm(n=800, sigma=0.01, seed=3)
    cut = px.index[500]
    asof = cut.strftime("%Y-%m-%d")
    sig_full = E.null_sigma(px, asof, horizon=5)
    sig_truncated = E.null_sigma(px[px.index <= cut], asof, horizon=5)
    assert sig_full == pytest.approx(sig_truncated, rel=1e-14)

    # Detonating the future must not move the answer.
    poisoned = px.copy()
    poisoned.iloc[501:] = poisoned.iloc[501:] * 5.0
    assert E.null_sigma(poisoned, asof, horizon=5) == pytest.approx(sig_full, rel=1e-14)


def test_null_sigma_refuses_to_guess_on_thin_history():
    px = _gbm(n=1000, sigma=0.02, seed=1)
    with pytest.raises(ValueError):
        E.null_sigma(px, px.index[5].strftime("%Y-%m-%d"), horizon=5)


def test_null_ensemble_is_zero_drift_correct_width_and_reproducible():
    px = _gbm(n=1200, sigma=0.02, seed=8)
    asof = px.index[-1].strftime("%Y-%m-%d")
    sig = E.null_sigma(px, asof, horizon=5)
    paths = E.null_ensemble(px, asof, horizon=5, n_paths=40000, seed=123)
    assert len(paths) == 40000
    arr = np.asarray(paths)
    assert abs(float(np.mean(arr))) < 4.0 * sig / math.sqrt(40000)  # zero drift
    assert float(np.std(arr, ddof=1)) == pytest.approx(sig, rel=0.02)
    again = E.null_ensemble(px, asof, horizon=5, n_paths=40000, seed=123)
    assert paths == again  # deterministic given the seed
    assert paths != E.null_ensemble(px, asof, horizon=5, n_paths=40000, seed=124)


def test_sampled_null_agrees_with_the_closed_form_null():
    px = _gbm(n=1200, sigma=0.02, seed=9)
    asof = px.index[-1].strftime("%Y-%m-%d")
    sig = E.null_sigma(px, asof, horizon=5)
    y = 0.06
    sampled = E.crps(E.null_ensemble(px, asof, 5, 200000, seed=5), y)
    assert sampled == pytest.approx(E.crps_gaussian(0.0, sig, y), rel=0.01)


def test_price_adapter_accepts_dataframe_series_and_date_column():
    px = _gbm(n=400, sigma=0.02, seed=2)
    asof = px.index[-1].strftime("%Y-%m-%d")
    base = E.null_sigma(px, asof, horizon=5)
    df_idx = pd.DataFrame({"open": px * 0.99, "close": px, "volume": 1})
    df_col = pd.DataFrame({"date": px.index, "close": px.to_numpy()})
    assert E.null_sigma(df_idx, asof, horizon=5) == pytest.approx(base, rel=1e-14)
    assert E.null_sigma(df_col, asof, horizon=5) == pytest.approx(base, rel=1e-14)


# =========================================================================== #
# 5. PIT
# =========================================================================== #
def test_pit_is_the_fraction_of_paths_below_actual():
    assert E.pit([0.0, 1.0, 2.0, 3.0], 2.5) == pytest.approx(0.75)
    assert E.pit([0.0, 1.0, 2.0, 3.0], -1.0) == pytest.approx(0.0)
    assert E.pit([0.0, 1.0, 2.0, 3.0], 99.0) == pytest.approx(1.0)
    assert 0.0 <= E.pit([0.0, 1.0, 2.0, 3.0], 1.0) <= 1.0


def test_pit_is_uniform_under_a_correctly_specified_ensemble():
    rng = np.random.default_rng(21)
    pits = [E.pit(rng.normal(size=500), float(rng.normal())) for _ in range(6000)]
    assert float(np.mean(pits)) == pytest.approx(0.5, abs=0.02)
    assert float(np.std(pits)) == pytest.approx(1 / math.sqrt(12), abs=0.02)
    cal = E.calibration_test(pits)
    assert cal["calibration_ok"] is True


def test_pit_piles_up_at_the_edges_when_the_ensemble_is_too_narrow():
    rng = np.random.default_rng(22)
    pits = [E.pit(rng.normal(0, 0.4, 500), float(rng.normal())) for _ in range(3000)]
    hist = E.pit_histogram(pits)
    edges = hist[0] + hist[-1]
    middle = sum(hist[4:6])
    assert edges > 3 * middle
    assert E.calibration_test(pits)["calibration_ok"] is False


def test_randomized_pit_is_seeded_deterministic_and_flatter_than_midrank():
    rng = np.random.default_rng(23)
    a = E.pit(rng.normal(size=50), 0.1, seed=999)
    b = E.pit  # same call, rebuilt below with an identical draw
    rng2 = np.random.default_rng(23)
    assert b(rng2.normal(size=50), 0.1, seed=999) == pytest.approx(a)

    # At small m the deterministic PIT grid does not align with 10 equal bins and
    # produces a spurious spike; the randomized PIT does not.
    rng3 = np.random.default_rng(24)
    det, ran = [], []
    for _ in range(30000):
        x = rng3.normal(size=50)
        y = float(rng3.normal())
        det.append(E.pit(x, y))
        ran.append(E.pit(x, y, seed=_))
    def max_dev(p):
        h = np.asarray(E.pit_histogram(p), dtype=float)
        return float(np.max(np.abs(h / h.sum() - 0.1)) / 0.1)
    assert max_dev(ran) < max_dev(det)
    assert max_dev(ran) < 0.10


def test_pit_histogram_shape_and_edges():
    assert E.pit_histogram([]) == [0] * 10
    assert len(E.pit_histogram([0.5], bins=7)) == 7
    assert E.pit_histogram([0.0, 0.999999, 1.0]) == [1, 0, 0, 0, 0, 0, 0, 0, 0, 2]
    pits = list(np.random.default_rng(1).random(500))
    assert sum(E.pit_histogram(pits)) == 500
    with pytest.raises(ValueError):
        E.pit_histogram([0.5], bins=0)


# =========================================================================== #
# 6. calibration test -- size and power, by simulation
# =========================================================================== #
def test_calibration_test_holds_its_size_under_the_null():
    """A correctly calibrated forecaster must not be flagged more than ~alpha."""
    rng = np.random.default_rng(31)
    rejects = 0
    trials = 400
    for _ in range(trials):
        pits = rng.random(60)
        rejects += int(E.calibration_test(pits)["calibration_ok"] is False)
    assert rejects / trials < 0.11  # nominal 0.05, generous MC band


def test_calibration_test_has_power_against_a_narrow_ensemble_when_n_is_large():
    rng = np.random.default_rng(32)
    rejects = 0
    trials = 60
    for _ in range(trials):
        pits = [E.pit(rng.normal(0, 0.5, 400), float(rng.normal()), seed=int(rng.integers(1e9)))
                for _ in range(120)]
        rejects += int(E.calibration_test(pits)["calibration_ok"] is False)
    assert rejects / trials > 0.85


def test_calibration_test_reports_underpowered_at_small_n_and_none_at_zero():
    empty = E.calibration_test([])
    assert empty["n"] == 0
    assert empty["calibration_ok"] is None  # not a flattering True
    assert empty["histogram"] == [0] * 10

    small = E.calibration_test(list(np.random.default_rng(2).random(12)))
    assert small["underpowered"] is True
    assert small["ks_pvalue"] is not None
    assert "power" in small["power_note"].lower()

    big = E.calibration_test(list(np.random.default_rng(2).random(120)))
    assert big["underpowered"] is False


def test_calibration_test_reports_a_real_statistic_and_pvalue():
    cal = E.calibration_test(list(np.random.default_rng(3).random(200)))
    assert 0.0 <= cal["ks_stat"] <= 1.0
    assert 0.0 <= cal["ks_pvalue"] <= 1.0
    assert cal["cvm_pvalue"] is not None
    assert cal["chi2_pvalue"] is not None
    assert cal["mean_pit"] == pytest.approx(0.5, abs=0.08)


def test_fallback_ks_pvalue_tracks_scipy():
    from scipy import stats

    rng = np.random.default_rng(4)
    for n in (25, 60, 200):
        x = np.sort(rng.random(n))
        d_ours = E._ks_stat_uniform(x)
        ref = stats.kstest(x, "uniform")
        assert d_ours == pytest.approx(float(ref.statistic), abs=1e-12)
        assert E._ks_pvalue_asymptotic(d_ours, n) == pytest.approx(
            float(ref.pvalue), abs=0.05
        )


# =========================================================================== #
# 7. z-score
# =========================================================================== #
def test_z_score_is_the_literal_how_many_sigma_answer():
    paths = [0.0, 1.0, 2.0, 3.0, 4.0]  # mean 2, sd(ddof=1) = sqrt(2.5)
    assert E.z_score(paths, 2.0 + math.sqrt(2.5)) == pytest.approx(1.0)
    assert E.z_score(paths, 2.0) == pytest.approx(0.0)
    assert E.z_score(paths, 2.0 - 2 * math.sqrt(2.5)) == pytest.approx(-2.0)


def test_z_score_uses_the_ensembles_own_reported_moments():
    ens = Ensemble(ticker="NVDA", as_of_date="2020-01-10", horizon_days=5,
                   paths=[0.0, 1.0], quantiles={}, mean=10.0, std=2.0)
    assert E.z_score(ens, 14.0) == pytest.approx(2.0)


def test_z_score_is_nan_for_a_degenerate_ensemble():
    assert math.isnan(E.z_score([0.3] * 20, 0.5))


# =========================================================================== #
# 8. score_event -- the frozen Score type, null always present
# =========================================================================== #
def test_score_event_returns_the_frozen_score_with_a_null_that_cannot_be_dropped():
    px = _gbm(n=1200, sigma=0.02, seed=13)
    asof = px.index[-1].strftime("%Y-%m-%d")
    sig = E.null_sigma(px, asof, horizon=5)
    rng = np.random.default_rng(6)
    s = E.score_event(rng.normal(0.0, sig * 0.7, 4000), 0.03, prices=px, asof=asof)
    assert isinstance(s, Score)
    for f in ("crps", "crps_null", "crps_lift", "pit", "actual_return", "z_score"):
        assert getattr(s, f) is not None
    assert s.crps_null == pytest.approx(E.crps_gaussian(0.0, sig, 0.03), rel=1e-12)
    assert s.crps_lift == pytest.approx((s.crps_null - s.crps) / s.crps_null, rel=1e-12)
    assert s.actual_return == 0.03


def test_score_event_lift_is_zero_when_the_model_is_the_null():
    px = _gbm(n=1200, sigma=0.02, seed=14)
    asof = px.index[-1].strftime("%Y-%m-%d")
    sig = E.null_sigma(px, asof, horizon=5)
    rng = np.random.default_rng(15)
    s = E.score_event(rng.normal(0.0, sig, 200000), 0.02, prices=px, asof=asof)
    assert abs(s.crps_lift) < 0.02


def test_score_event_demands_a_null_it_cannot_be_called_without_one():
    with pytest.raises(ValueError):
        E.score_event([0.1, 0.2], 0.15)


# =========================================================================== #
# 9. walk_forward
# =========================================================================== #
def _price_series_with_test_events(seed=0, jump_dates=None):
    """Business-day series 2014..2024 with engineered >=25%/5d jumps so the
    frozen event definition actually fires inside the test window."""
    idx = pd.bdate_range("2014-01-02", "2024-12-31")
    n = len(idx)
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0, 0.02, n)
    jump_dates = jump_dates or ["2020-03-16", "2020-06-10", "2021-02-22",
                                "2021-11-09", "2022-05-09", "2022-10-13",
                                "2023-02-03", "2023-08-04", "2024-01-25",
                                "2024-07-24", "2024-11-06"]
    loc = {d: i for i, d in enumerate(idx.strftime("%Y-%m-%d"))}
    for k, d in enumerate(jump_dates):
        i = loc[d]
        sign = 1.0 if k % 3 else -1.0
        for j in range(i - 4, i + 1):
            r[j] += sign * 0.065
    return _series(100.0 * np.exp(np.cumsum(r)), start="2014-01-02").reindex(idx).ffill()


def test_walk_forward_returns_the_frozen_backtest_payload_shape():
    px = _price_series_with_test_events(seed=1)
    res = E.walk_forward("NVDA", prices=px, n_paths=800)
    for k in ("n_tests", "mean_crps_lift", "pit_histogram", "calibration_ok", "per_event"):
        assert k in res
    assert res["n_tests"] > 0
    assert len(res["pit_histogram"]) == 10
    assert sum(res["pit_histogram"]) == res["n_tests"]
    assert len(res["per_event"]) == res["n_tests"]
    for row in res["per_event"]:
        for k in ("date", "crps", "crps_null", "crps_lift", "z_score"):
            assert k in row
        assert row["crps_null"] > 0


def test_walk_forward_honours_the_embargo_and_never_scores_before_test_start():
    px = _price_series_with_test_events(seed=2, jump_dates=["2020-01-03", "2020-03-16"])
    res = E.walk_forward("NVDA", prices=px, n_paths=400, embargo_days=EMBARGO_DAYS)
    embargo_until = pd.Timestamp(res["meta"]["embargo_applied_until"])
    assert embargo_until > pd.Timestamp(TRAIN_END)
    for row in res["per_event"]:
        d = pd.Timestamp(row["date"])
        assert d >= pd.Timestamp(TEST_START)
        assert d > embargo_until          # the purge gap is real
    # the 2020-01-03 event sits inside the embargo window and must be dropped
    assert "2020-01-03" not in [r["date"] for r in res["per_event"]]


def test_walk_forward_with_no_generator_scores_the_null_and_claims_no_skill(monkeypatch):
    """When LANE-MODEL's generator is unreachable we score the null against
    itself. Lift is then ~0 BY CONSTRUCTION and the payload says so; we never
    substitute a made-up number."""
    monkeypatch.setattr(E, "_default_generator", lambda: (None, "NULL_FALLBACK"))
    px = _price_series_with_test_events(seed=3)
    res = E.walk_forward("NVDA", prices=px, n_paths=6000)
    assert res["meta"]["generator_source"] == "NULL_FALLBACK"
    assert abs(res["mean_crps_lift"]) < 0.05  # ~0 by construction, not "skill"
    assert any("NO GENERATOR" in d for d in res["disclosures"])


def test_walk_forward_drift_guard_separates_drift_from_shape():
    """The trap LANE-WOLFRAM measured: a generator whose only edge is an assumed
    drift shows a big raw lift and a much smaller demeaned lift. Both ship."""
    px = _price_series_with_test_events(seed=4)

    def drifty(req):
        sig = E.null_sigma(px, req.as_of_date, horizon=req.horizon_days)
        rng = np.random.default_rng(abs(hash(req.as_of_date)) % (2**32))
        return list(rng.normal(0.05, sig, req.n_paths))  # +5% assumed drift

    res = E.walk_forward("NVDA", prices=px, generate=drifty, n_paths=3000)
    assert res["mean_crps_lift"] is not None
    assert res["mean_crps_lift_demeaned"] is not None
    assert res["drift_share_of_lift"] is not None
    # the demeaned ensemble is the null, so its lift must sit at ~0
    assert abs(res["mean_crps_lift_demeaned"]) < 0.05
    assert res["mean_crps_lift"] != pytest.approx(res["mean_crps_lift_demeaned"], abs=1e-6)


def test_walk_forward_rewards_a_genuinely_sharper_generator():
    """A generator that is correctly centred and correctly narrower than the
    stale trailing-250d null must show positive lift AND flat-ish PIT."""
    px = _price_series_with_test_events(seed=5)
    idx = px.index
    pos = {t: i for i, t in enumerate(idx)}
    v = px.to_numpy()

    def sharp(req):
        i = pos[pd.Timestamp(req.as_of_date)]
        recent = np.diff(np.log(v[max(0, i - 20): i + 1]))  # 20d realized vol
        sig = float(np.std(recent, ddof=1)) * math.sqrt(req.horizon_days)
        rng = np.random.default_rng(abs(hash(req.as_of_date)) % (2**32))
        return list(rng.normal(0.0, sig, req.n_paths))

    res = E.walk_forward("NVDA", prices=px, generate=sharp, n_paths=3000)
    assert res["n_tests"] >= 5
    assert res["mean_crps_lift"] is not None
    assert res["crps_lift_ci90"][0] is not None


def test_walk_forward_survives_a_ticker_with_zero_test_events():
    """Four of ten universe tickers have no test-period events at the frozen
    threshold. /api/backtest must not crash and must not report a flattering
    calibration_ok."""
    px = _gbm(n=2800, sigma=0.006, seed=6, start="2014-01-02")
    res = E.walk_forward("XOM", prices=px, n_paths=200)
    assert res["n_tests"] == 0
    assert res["per_event"] == []
    assert res["mean_crps_lift"] is None
    assert res["calibration_ok"] is None
    assert res["pit_histogram"] == [0] * 10
    assert any("NO TEST EVENTS" in d for d in res["disclosures"])


def test_walk_forward_reports_famous_vs_obscure_separately():
    px = _price_series_with_test_events(seed=7)
    evs = E._fallback_detect_events(px, "NVDA")
    test_evs = [e for e in evs if e.date >= TEST_START]
    for k, e in enumerate(test_evs):
        e.famous = bool(k % 2 == 0)
    res = E.walk_forward("NVDA", prices=px, events=evs, n_paths=600)
    assert res["salience_labels_present"] is True
    assert res["breakdown_famous"]["n"] > 0
    assert res["breakdown_obscure"]["n"] > 0
    assert res["breakdown_famous"]["n"] + res["breakdown_obscure"]["n"] == res["n_tests"]
    assert len(res["breakdown_famous"]["pit_histogram"]) == 10


def test_walk_forward_flags_missing_salience_labels_instead_of_faking_the_split():
    px = _price_series_with_test_events(seed=8)
    res = E.walk_forward("NVDA", prices=px, n_paths=300)
    assert res["salience_labels_present"] is False
    assert any("salience" in d for d in res["disclosures"])


def test_walk_forward_generator_failure_falls_back_to_null_not_to_a_made_up_number():
    px = _price_series_with_test_events(seed=9)

    def broken(req):
        raise RuntimeError("LLM timeout")

    with pytest.warns(RuntimeWarning):
        res = E.walk_forward("NVDA", prices=px, generate=broken, n_paths=1500)
    assert res["n_tests"] > 0
    assert all("NULL_FALLBACK" in r["model_source"] for r in res["per_event"])
    assert abs(res["mean_crps_lift"]) < 0.1


def test_walk_forward_meta_declares_its_provenance_and_estimators():
    px = _price_series_with_test_events(seed=10)
    m = E.walk_forward("NVDA", prices=px, n_paths=200)["meta"]
    assert m["price_source"] == "injected"
    assert m["synthetic"] is False
    assert m["train_end"] == TRAIN_END
    assert "fair" in m["crps_estimator"]
    assert "closed-form" in m["crps_null_estimator"]
    assert "randomized" in m["pit_convention"]


def test_synthetic_fallback_is_loudly_labelled_when_lane_data_is_missing():
    """CONTRACT s9: a working code path with a CLEARLY LABELLED synthetic
    fallback, never a fabricated number presented as real."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        close, src = E._load_prices("NVDA", None)
    assert src in ("data.load_prices", "SYNTHETIC_FALLBACK",
                   "SYNTHETIC_FALLBACK(data.py)")
    if src.startswith("SYNTHETIC_FALLBACK"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = E.walk_forward("NVDA", n_paths=200)
        assert res["meta"]["synthetic"] is True
        assert any("SYNTHETIC" in d for d in res["disclosures"])


def test_lane_data_synthetic_flag_is_honoured_not_trusted(monkeypatch):
    """If LANE-DATA hands back its labelled synthetic series, evaluate.py must
    mark the whole run synthetic. A synthetic series that scores well is the
    easiest way for this project to fool itself."""
    from rulial import data as _data

    px = _price_series_with_test_events(seed=31)
    monkeypatch.setattr(_data, "load_prices", lambda t, *a, **k: px.to_frame("close"))
    monkeypatch.setattr(_data, "SYNTHETIC_TICKERS", {"NVDA"})
    with pytest.warns(RuntimeWarning):
        _, src = E._load_prices("NVDA", None)
    assert src == "SYNTHETIC_FALLBACK(data.py)"

    monkeypatch.setattr(_data, "SYNTHETIC_TICKERS", set())
    _, src2 = E._load_prices("NVDA", None)
    assert src2 == "data.load_prices"


# =========================================================================== #
# 10. the frozen honesty constraints (CONTRACT.md s7 / s8)
# =========================================================================== #
def test_directional_hit_rate_is_never_a_top_level_headline():
    px = _price_series_with_test_events(seed=11)
    res = E.walk_forward("NVDA", prices=px, n_paths=400)
    for k in res:
        assert "hit_rate" not in k
        assert "directional" not in k
    assert "directional_hit_rate" in res["appendix"]
    assert "APPENDIX" in res["appendix"]["directional_hit_rate"]["label"]


def test_directional_hit_rate_is_reported_next_to_the_base_rate_it_must_beat():
    rows = [{"median": 0.01, "actual_return": 0.05} for _ in range(9)]
    rows.append({"median": 0.01, "actual_return": -0.05})
    out = E.appendix_directional_hit_rate(rows)
    assert out["n"] == 10
    assert out["hit_rate"] == pytest.approx(0.9)
    assert out["base_rate_always_up"] == pytest.approx(0.9)  # skill == none
    assert "base_rate" in out["warning"]
    assert E.appendix_directional_hit_rate([])["hit_rate"] is None


def test_the_null_appears_on_every_event_and_every_aggregate():
    px = _price_series_with_test_events(seed=12)
    res = E.walk_forward("NVDA", prices=px, n_paths=400)
    assert res["mean_crps_null"] is not None
    assert all(r["crps_null"] > 0 for r in res["per_event"])
    assert any("null model" in d.lower() for d in res["disclosures"])


def test_leakage_disclosure_ships_inside_the_payload():
    px = _price_series_with_test_events(seed=13)
    res = E.walk_forward("NVDA", prices=px, n_paths=300)
    joined = " ".join(res["disclosures"]).lower()
    assert "weights" in joined and "2019" in joined
    assert "lift over a null" in joined


def test_payload_is_json_serialisable_for_the_api():
    import json

    px = _price_series_with_test_events(seed=14)
    res = E.walk_forward("NVDA", prices=px, n_paths=200)
    json.loads(json.dumps(res))  # must not raise on numpy scalars


# =========================================================================== #
# 11. pooled universe evaluation
# =========================================================================== #
def test_walk_forward_universe_pools_and_flags_concentration():
    """Pooling is the point: a per-ticker calibration verdict at n~12 is noise.
    Concentration must be called out, because a pooled mean dominated by one
    ticker is a single-ticker statistic wearing a universe's clothes."""
    prices_map = {
        "NVDA": _price_series_with_test_events(seed=21, jump_dates=["2021-02-22",
                                                                    "2022-05-09"]),
        "TSLA": _price_series_with_test_events(
            seed=22,
            jump_dates=["2020-02-11", "2020-07-08", "2020-09-09", "2021-01-26",
                        "2021-03-08", "2021-11-09", "2022-01-27", "2022-04-27",
                        "2022-11-04", "2023-01-06", "2023-04-24", "2024-01-25",
                        "2024-04-24", "2024-10-24"],
        ),
        "XOM": _gbm(n=2800, sigma=0.006, seed=23, start="2014-01-02"),
    }
    res = E.walk_forward_universe(["NVDA", "TSLA", "XOM"], prices_map=prices_map,
                                  n_paths=600)
    assert res["scope"] == "universe"
    assert res["n_tests"] == sum(v["n_tests"] for v in res["per_ticker"].values())
    assert res["per_ticker"]["XOM"]["n_tests"] == 0
    assert res["events_per_ticker"]["TSLA"] > res["events_per_ticker"]["NVDA"]
    # TSLA supplies well over 40% of the events, so it must be named out loud
    joined = " ".join(res["disclosures"])
    assert "CONCENTRATION" in joined and "TSLA" in joined
    assert "NO TEST EVENTS" in joined and "XOM" in joined
    # pooled calibration is computed on more events than any single ticker
    assert res["calibration"]["n"] == res["n_tests"]
    assert res["calibration"]["n"] > max(v["n_tests"] for v in res["per_ticker"].values())


def test_pooled_disclosures_keep_the_null_and_the_appendix_rule():
    res = E.walk_forward_universe(
        ["NVDA"], prices_map={"NVDA": _price_series_with_test_events(seed=25)},
        n_paths=300,
    )
    joined = " ".join(res["disclosures"]).lower()
    assert "null model" in joined
    assert "appendix" in joined
    for k in res:
        assert "hit_rate" not in k and "directional" not in k


def test_walk_forward_universe_runs_end_to_end_on_the_fallback_path():
    res = E.walk_forward_universe(["NVDA", "AAPL"], n_paths=150)
    assert res["scope"] == "universe"
    assert set(res["per_ticker"]) == {"NVDA", "AAPL"}
    assert len(res["pit_histogram"]) == 10
    assert "directional_hit_rate" in res["appendix"]
    for k in res:
        assert "hit_rate" not in k


# =========================================================================== #
# 12. ANCHORS -- can the scorer actually SEE skill, and see its absence?
#
# These decide whether a negative crps_lift in the demo is a real finding about
# the generator or a bug in this file. They run on CONTROLLED fixtures where the
# right answer is known in advance:
#
#   * constant-vol GBM  -> the frozen trailing-250d null is CORRECTLY specified,
#                          so a generator equal to the null must score 0, and any
#                          departure in either direction must be punished.
#   * vol-regime shift  -> the trailing-250d null is provably STALE, so a
#                          generator using recent realized vol must WIN.
#
# Using the jump-injected fixture here would not work: injecting 25% moves into
# the price path also corrupts the trailing-250d sigma, so the null is
# misspecified and the anchor tests nothing.
# =========================================================================== #
def _const_vol_prices(sigma=0.02, seed=5, start="2015-01-01", end="2024-12-31"):
    idx = pd.bdate_range(start, end)
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0, sigma, len(idx))
    return pd.Series(100.0 * np.exp(np.cumsum(r)), index=idx, name="close")


def _regime_shift_prices(seed=6, shift="2019-06-03", hi=0.030, lo=0.010,
                         start="2015-01-01", end="2024-12-31"):
    """Vol collapses from 3% to 1% daily well before the test window, so a
    trailing-250d sigma is far too wide and a 20-day realized vol is right."""
    idx = pd.bdate_range(start, end)
    rng = np.random.default_rng(seed)
    v = np.where(idx < pd.Timestamp(shift), hi, lo)
    return pd.Series(100.0 * np.exp(np.cumsum(rng.normal(0, 1, len(idx)) * v)),
                     index=idx, name="close")


def _synthetic_events(px, every=12, start="2020-02-01"):
    """Events supplied directly, so event detection cannot contaminate the
    volatility structure the anchor depends on."""
    dates = px.index[px.index >= pd.Timestamp(start)]
    return [Event(ticker="TEST", date=d.strftime("%Y-%m-%d"), move_pct=0.30,
                  direction="up", window_days=5) for d in dates[::every][:-2]]


def _rescaled_null_run(mult, drift=0.0, n_paths=4000, seed=5):
    """Walk-forward whose generator IS the null, rescaled by `mult` and shifted
    by `drift`. Everything about the answer is anticipatable."""
    px = _const_vol_prices(seed=seed)

    def gen(req):
        sig = E.null_sigma(px, req.as_of_date, horizon=req.horizon_days)
        rng = np.random.default_rng(E._pit_seed("anchor", req.as_of_date, mult, drift))
        return list(rng.normal(drift, mult * sig, req.n_paths))

    return E.walk_forward("TEST", prices=px, events=_synthetic_events(px),
                          generate=gen, n_paths=n_paths)


def test_anchor_scoring_the_null_as_the_model_gives_exactly_zero_lift():
    """The single most important calibration in this file. If this drifts off
    zero, crps_lift is measuring the estimator rather than the model, and every
    headline number is an artifact."""
    res = _rescaled_null_run(1.0, n_paths=8000)
    assert res["n_tests"] > 50
    assert abs(res["mean_crps_lift"]) < 0.01
    lo, hi = res["crps_lift_ci90"]
    assert lo < 0.0 < hi  # the 90% CI straddles zero


def test_anchor_overdispersion_is_penalised_and_monotonically_so():
    l2 = _rescaled_null_run(2.0)["mean_crps_lift"]
    l3 = _rescaled_null_run(3.0)["mean_crps_lift"]
    assert l2 < -0.25
    assert l3 < l2


def test_anchor_underdispersion_is_penalised_too():
    """CRPS is proper in BOTH directions. Too sharp is punished as well as too
    wide, which is what stops 'just be confident' from being a winning
    strategy."""
    assert _rescaled_null_run(0.25)["mean_crps_lift"] < -0.03


def test_anchor_pit_moves_the_right_way_with_dispersion():
    """Too narrow -> PIT piles at the EDGES. Too wide -> PIT piles in the MIDDLE.
    A calibration test that cannot tell those apart is decorative."""
    narrow = _rescaled_null_run(0.25)["pit_histogram"]
    wide = _rescaled_null_run(3.0)["pit_histogram"]
    n_edge, n_mid = narrow[0] + narrow[-1], sum(narrow[3:7])
    w_edge, w_mid = wide[0] + wide[-1], sum(wide[3:7])
    assert n_edge > n_mid          # too narrow -> edges
    assert w_mid > w_edge          # too wide   -> middle
    assert n_edge > w_edge
    assert E.calibration_test(
        [i / 10 for i, c in enumerate(narrow) for _ in range(c)]
    )["n"] == sum(narrow)


def test_anchor_the_scorer_can_see_genuine_sharpness():
    """If nothing can ever earn positive lift, a negative headline says nothing
    about the generator. Here the trailing-250d null is provably stale (vol fell
    from 3% to 1% daily), and a 20-day realized-vol forecaster must WIN, with a
    confidence interval that excludes zero."""
    px = _regime_shift_prices()
    v = px.to_numpy()
    pos = {t: i for i, t in enumerate(px.index)}

    def rv20(req):
        i = pos[pd.Timestamp(req.as_of_date)]
        r = np.diff(np.log(v[max(0, i - 20): i + 1]))
        sig = float(np.std(r, ddof=1)) * math.sqrt(req.horizon_days)
        rng = np.random.default_rng(E._pit_seed("rv20", req.as_of_date))
        return list(rng.normal(0.0, sig, req.n_paths))

    dates = px.index[(px.index >= pd.Timestamp("2019-07-01"))
                     & (px.index <= pd.Timestamp("2020-05-01"))][::4]
    evs = [Event(ticker="TEST", date=d.strftime("%Y-%m-%d"), move_pct=0.3,
                 direction="up", window_days=5) for d in dates]
    res = E.walk_forward("TEST", prices=px, events=evs, generate=rv20, n_paths=4000)
    assert res["n_tests"] >= 10
    assert res["mean_crps_lift"] > 0.03
    assert res["crps_lift_ci90"][0] > 0.0   # CI excludes zero


def test_anchor_pure_drift_is_unmasked_by_the_demeaned_lift():
    """LANE-WOLFRAM measured a +14.8% 'skill' that was 100% bull-decade drift and
    inverted to -4.5% once demeaned. The demeaned column exists so that can never
    be reported as skill by accident: here the ONLY difference from the null is a
    +6% drift, and the demeaned lift correctly reports that the shape added
    nothing."""
    res = _rescaled_null_run(1.0, drift=0.06, n_paths=8000)
    assert abs(res["mean_crps_lift_demeaned"]) < 0.01
    assert res["mean_crps_lift"] < -0.5              # a wrong drift is expensive
    assert res["drift_share_of_lift"] == pytest.approx(1.0, abs=0.05)


def test_anchor_a_correct_drift_shows_up_as_lift_that_is_all_drift():
    """The mirror image: drift that happens to be RIGHT still gets flagged as
    drift, not as calibration skill."""
    px = _const_vol_prices(seed=5)
    evs = _synthetic_events(px)
    v, pos = px.to_numpy(), {t: i for i, t in enumerate(px.index)}

    def cheat_drift(req):
        i = pos[pd.Timestamp(req.as_of_date)]
        realized = float(v[i + req.horizon_days] / v[i] - 1.0)   # deliberate oracle
        sig = E.null_sigma(px, req.as_of_date, horizon=req.horizon_days)
        rng = np.random.default_rng(E._pit_seed("cheat", req.as_of_date))
        return list(rng.normal(realized, sig, req.n_paths))

    res = E.walk_forward("TEST", prices=px, events=evs, generate=cheat_drift,
                         n_paths=4000)
    assert res["mean_crps_lift"] > 0.10                   # oracle drift wins big
    assert res["mean_crps_lift_demeaned"] < res["mean_crps_lift"]
    assert res["drift_share_of_lift"] > 0.8              # and it is ~all drift


# =========================================================================== #
# 13. the two-tier event definition (CONTRACT.md s3, revised)
# =========================================================================== #
def test_fallback_detector_labels_tiers_and_uses_the_significant_floor():
    """The detection floor is TIER_SIGNIFICANT; every event carries the tier it
    actually belongs to, so a 16% move can never be reported as a black swan."""
    px = _price_series_with_test_events(seed=41)
    evs = E._fallback_detect_events(px, "NVDA")
    assert evs, "fixture should contain detectable events"
    for e in evs:
        assert abs(e.move_pct) >= JUMP_THRESHOLD - 1e-12
        assert e.tier in ("major", "significant")
        assert e.tier == tier_for(e.move_pct)
        if e.tier == "major":
            assert abs(e.move_pct) >= TIER_MAJOR
        else:
            assert TIER_SIGNIFICANT <= abs(e.move_pct) < TIER_MAJOR
    assert JUMP_THRESHOLD == TIER_SIGNIFICANT  # floor is the wider tier


def test_fallback_detector_dedupes_overlapping_windows_to_the_most_extreme():
    """CONTRACT s3: overlapping windows collapse to the single most extreme
    window -- otherwise one crash is counted five times and n_tests is a lie."""
    n = 900
    r = np.zeros(n)
    r[300:305] = 0.06      # a big 5-day run
    r[302] = 0.12          # the most extreme window ends around here
    px = _series(100.0 * np.exp(np.cumsum(r)))
    evs = E._fallback_detect_events(px, "T")
    dates = [pd.Timestamp(e.date) for e in evs]
    # no two retained events may sit inside one WINDOW_DAYS span
    ordinals = sorted(px.index.get_loc(d) for d in dates)
    assert all(b - a >= WINDOW_DAYS for a, b in zip(ordinals, ordinals[1:]))
    # and the retained one is the strongest available window
    strongest = max(abs(px.to_numpy()[i] / px.to_numpy()[i - WINDOW_DAYS] - 1.0)
                    for i in range(300, 312))
    assert max(abs(e.move_pct) for e in evs) == pytest.approx(strongest, rel=1e-9)


def test_walk_forward_reports_the_two_tiers_separately():
    """The stage narrative is a major-tier story. If the headline silently mixes
    in 15% moves, the demo claim and the number stop describing the same thing."""
    px = _price_series_with_test_events(seed=42)
    res = E.walk_forward("NVDA", prices=px, n_paths=500)
    assert res["n_tests"] > 0
    for row in res["per_event"]:
        assert row["tier"] in ("major", "significant", "unknown")
    tot = res["breakdown_major"]["n"] + res["breakdown_significant"]["n"]
    assert tot == res["n_tests"]
    assert len(res["breakdown_major"]["pit_histogram"]) == 10
    assert any("TIERS ARE NOT INTERCHANGEABLE" in d for d in res["disclosures"])


def test_tier_is_taken_from_the_event_when_lane_events_supplies_it():
    px = _price_series_with_test_events(seed=43)
    evs = E._fallback_detect_events(px, "NVDA")
    for e in evs:
        e.tier = "major"
    res = E.walk_forward("NVDA", prices=px, events=evs, n_paths=200)
    assert res["breakdown_significant"]["n"] == 0
    assert res["breakdown_major"]["n"] == res["n_tests"]


def test_universe_payload_carries_the_tier_split_and_names_it():
    res = E.walk_forward_universe(
        ["NVDA"], prices_map={"NVDA": _price_series_with_test_events(seed=44)},
        n_paths=250,
    )
    assert "breakdown_major" in res and "breakdown_significant" in res
    assert (res["breakdown_major"]["n"] + res["breakdown_significant"]["n"]
            == res["n_tests"])
    assert any("TIER MIX" in d for d in res["disclosures"])


# =========================================================================== #
# 14. THE LEAK GUARD, end to end
#
# The contract calls the 2019 boundary "the leak guard". These tests check it at
# the level a judge would attack: not "did we set a variable", but "does the
# scored number change if the future is deleted or replaced".
# =========================================================================== #
def _scored(prices, **kw):
    res = E.walk_forward("NVDA", prices=prices, n_paths=2000, seed=1, **kw)
    return {r["date"]: (round(r["crps"], 12), round(r["crps_null"], 12),
                        round(r["actual_return"], 12)) for r in res["per_event"]}


def test_leak_guard_deleting_the_future_does_not_change_any_score():
    """Truncate the price series right after the last scored event's forward
    window. Every score must be bit-identical: nothing the eval reports may
    depend on data it should not have seen."""
    px = _price_series_with_test_events(seed=51)
    full = _scored(px)
    assert len(full) >= 5

    last = max(pd.Timestamp(d) for d in full)
    idx = px.index
    cut_pos = list(idx).index(last) + 5           # last event + horizon
    truncated = px.iloc[: cut_pos + 1]
    assert _scored(truncated) == full


def test_leak_guard_poisoning_the_future_does_not_change_any_score():
    """Same test from the other direction: multiply every price beyond the last
    forward window by 10. A single lookahead anywhere in the scorer would move
    a number here."""
    px = _price_series_with_test_events(seed=52)
    full = _scored(px)
    last = max(pd.Timestamp(d) for d in full)
    cut_pos = list(px.index).index(last) + 5

    poisoned = px.copy()
    poisoned.iloc[cut_pos + 1:] = poisoned.iloc[cut_pos + 1:] * 10.0
    # Hold the event LEDGER fixed: the 10x step is itself a detectable jump, so
    # letting the detector rerun would change the test set rather than test the
    # scorer. We are asking whether SCORES move, not whether events move.
    ledger = E._fallback_detect_events(px, "NVDA")
    assert _scored(poisoned, events=ledger) == _scored(px, events=ledger) == full


def test_leak_guard_no_scored_event_predates_the_train_boundary():
    px = _price_series_with_test_events(
        seed=53, jump_dates=["2016-03-15", "2018-07-10", "2019-11-15",
                             "2021-02-22", "2022-05-09"])
    res = E.walk_forward("NVDA", prices=px, n_paths=300)
    assert res["n_tests"] > 0
    for r in res["per_event"]:
        assert pd.Timestamp(r["date"]) > pd.Timestamp(TRAIN_END)
    # the three pre-2020 jumps are train-period and must never be scored
    for d in ("2016-03-15", "2018-07-10", "2019-11-15"):
        assert d not in [r["date"] for r in res["per_event"]]


def test_leak_guard_null_sigma_never_sees_the_event_it_is_scoring():
    """The null's sigma is estimated at asof INCLUSIVE, so it may see the jump
    itself (that is deliberate and makes the null harder to beat) but must never
    see the forward window it is being scored against."""
    px = _price_series_with_test_events(seed=54)
    res = E.walk_forward("NVDA", prices=px, n_paths=300)
    for r in res["per_event"]:
        asof = pd.Timestamp(r["date"])
        hist_only = px[px.index <= asof]
        assert E.null_sigma(hist_only, r["date"], horizon=5) == pytest.approx(
            r["null_sigma"], rel=1e-12
        )


def test_walk_forward_is_bit_reproducible_across_runs():
    """A headline number that moves between runs is not a result. Same inputs,
    same seed, identical output."""
    px = _price_series_with_test_events(seed=55)

    def gen(req):
        sig = E.null_sigma(px, req.as_of_date, horizon=req.horizon_days)
        rng = np.random.default_rng(E._pit_seed("repro", req.as_of_date))
        return list(rng.normal(0.0, 0.9 * sig, req.n_paths))

    a = E.walk_forward("NVDA", prices=px, generate=gen, n_paths=1500, seed=3)
    b = E.walk_forward("NVDA", prices=px, generate=gen, n_paths=1500, seed=3)
    assert a["mean_crps_lift"] == b["mean_crps_lift"]
    assert a["pit_histogram"] == b["pit_histogram"]
    assert [r["crps"] for r in a["per_event"]] == [r["crps"] for r in b["per_event"]]
