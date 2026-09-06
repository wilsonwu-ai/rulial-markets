"""
LANE-API tests.

These test the API's *contract compliance and refusal to crash*, not the
science. They must pass with every sibling lane missing (that is the point),
and must still pass once the siblings land.

    cd backend && python -m pytest tests/test_api.py -q
    cd backend && python tests/test_api.py        # no pytest needed
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from rulial import config as cfg  # noqa: E402
from rulial.api import app  # noqa: E402

client = TestClient(app)


# --- /api/health -----------------------------------------------------------
def test_health_ok():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert set(body["modules"]) == {"data", "events", "news", "generator", "evaluate"}


# --- /api/tickers ----------------------------------------------------------
def test_tickers_returns_full_frozen_universe():
    r = client.get("/api/tickers")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert [t["symbol"] for t in body] == cfg.UNIVERSE
    for t in body:
        assert {"symbol", "name", "sector", "has_data", "n_events"} <= set(t)
        assert isinstance(t["has_data"], bool)
        assert isinstance(t["n_events"], int) and t["n_events"] >= 0


# --- /api/events -----------------------------------------------------------
def test_events_returns_a_list_for_every_universe_ticker():
    for sym in cfg.UNIVERSE:
        r = client.get("/api/events", params={"ticker": sym})
        assert r.status_code == 200, sym
        body = r.json()
        assert isinstance(body, list), sym
        for e in body:
            assert e["ticker"] == sym
            # FROZEN leak guard: the seed ledger is train-period only.
            assert e["date"] <= cfg.TRAIN_END
            assert e["direction"] in ("up", "down", "")


def test_events_unknown_ticker_degrades_not_crashes():
    r = client.get("/api/events", params={"ticker": "FAKE"})
    assert r.status_code == 200
    assert r.json() == []
    assert r.headers.get("X-Rulial-Unavailable") == "true"


def test_events_missing_param_is_a_422_not_a_500():
    assert client.get("/api/events").status_code == 422


# --- /api/forecast ---------------------------------------------------------
def _forecast(**kw):
    body = {"ticker": "NVDA", "event_text": "NVDA announces a 40% datacenter revenue miss",
            "as_of_date": "2018-11-15", "horizon_days": 5, "n_paths": 500}
    body.update(kw)
    return client.post("/api/forecast", json=body)


def test_forecast_always_returns_a_renderable_ensemble():
    r = _forecast()
    assert r.status_code == 200
    body = r.json()
    assert body["unavailable"] is False
    ens = body["ensemble"]
    assert ens is not None
    assert ens["ticker"] == "NVDA"
    assert len(ens["paths"]) >= 100
    assert all(isinstance(p, float) for p in ens["paths"][:10])
    assert set(ens["quantiles"]) >= {"p5", "p50", "p95"}
    assert ens["quantiles"]["p5"] <= ens["quantiles"]["p50"] <= ens["quantiles"]["p95"]
    assert isinstance(body["fallback"], bool)
    # CONTRACT s8: leakage disclosure must be carried in the product, not a doc.
    assert cfg.TRAIN_END in body["leakage_disclosure"]


def test_forecast_synthetic_fallback_is_labelled_when_used():
    body = _forecast().json()
    if body["fallback"]:
        assert "SYNTHETIC FALLBACK" in body["ensemble"]["narrative"]


def test_forecast_score_is_null_or_contract_shaped():
    body = _forecast().json()
    score = body["score"]
    if score is not None:
        assert set(score) >= {"crps", "crps_null", "crps_lift", "pit",
                              "actual_return", "z_score"}
        # CONTRACT s7: the null may never be dropped from the eval.
        assert isinstance(score["crps_null"], float)


def test_forecast_future_date_has_no_score():
    body = _forecast(as_of_date="2035-01-02").json()
    assert body["score"] is None
    assert body["ensemble"] is not None


def test_forecast_unknown_ticker_degrades_not_crashes():
    r = _forecast(ticker="FAKE")
    assert r.status_code == 200
    body = r.json()
    assert body["unavailable"] is True
    assert body["ensemble"] is None
    assert "universe" in body["error"]


def test_forecast_absurd_n_paths_is_clamped_not_fatal():
    body = _forecast(n_paths=10_000_000).json()
    assert body["unavailable"] is False
    assert len(body["ensemble"]["paths"]) <= 20000


# --- /api/backtest ---------------------------------------------------------
def test_backtest_shape_for_every_universe_ticker():
    for sym in cfg.UNIVERSE:
        r = client.get("/api/backtest", params={"ticker": sym})
        assert r.status_code == 200, sym
        body = r.json()
        assert {"n_tests", "mean_crps_lift", "pit_histogram",
                "calibration_ok", "per_event"} <= set(body), sym
        assert isinstance(body["n_tests"], int) and body["n_tests"] >= 0
        assert len(body["pit_histogram"]) == 10
        assert isinstance(body["per_event"], list)


def test_backtest_unknown_ticker_degrades_not_crashes():
    r = client.get("/api/backtest", params={"ticker": "FAKE"})
    assert r.status_code == 200
    assert r.json()["unavailable"] is True


# --- the whole point: every route survives its siblings being broken --------
def test_all_routes_survive_every_sibling_lane_being_broken():
    """Simulate rulial.{data,events,news,generator,evaluate} all failing to
    import. Every route must still answer 200 with a renderable payload."""
    import rulial.api as api

    real_import, real_price_memo, real_df_memo = api._safe_import, api._PRICE_MEMO, api._DF_MEMO
    api._safe_import = lambda name: (None, "simulated ImportError: lane mid-write")
    api._PRICE_MEMO, api._DF_MEMO = {}, {}
    try:
        h = client.get("/api/health")
        assert h.status_code == 200 and h.json()["ok"] is True
        assert not any(h.json()["modules"].values())

        t = client.get("/api/tickers")
        assert t.status_code == 200
        assert [x["symbol"] for x in t.json()] == cfg.UNIVERSE

        e = client.get("/api/events", params={"ticker": "NVDA"})
        assert e.status_code == 200 and isinstance(e.json(), list)

        f = client.post("/api/forecast", json={"ticker": "NVDA", "event_text": "x",
                                               "as_of_date": "2018-11-15", "n_paths": 200})
        assert f.status_code == 200
        fb = f.json()
        assert fb["ensemble"] is not None and len(fb["ensemble"]["paths"]) >= 100
        assert fb["fallback"] is True
        assert "SYNTHETIC FALLBACK" in fb["ensemble"]["narrative"]
        assert fb["score"] is None          # no evaluate module -> no score, not a guess

        b = client.get("/api/backtest", params={"ticker": "NVDA"})
        assert b.status_code == 200
        assert b.json()["unavailable"] is True and b.json()["n_tests"] == 0
    finally:
        api._safe_import, api._PRICE_MEMO, api._DF_MEMO = real_import, real_price_memo, real_df_memo


def test_forecast_on_a_real_historical_event_scores_against_the_null():
    """Soft integration check: when LANE-DATA/LANE-EVAL are present and NVDA is
    cached, a 2018 as_of_date must produce a full contract-shaped Score."""
    import rulial.api as api
    if not api._price_cache_exists("NVDA"):
        return  # cache cold; covered by the shape test above
    body = _forecast(as_of_date="2018-11-15", n_paths=1000).json()
    if body["score"] is None:
        return  # sibling lane not landed yet; notes explain why
    sc = body["score"]
    assert sc["crps"] > 0 and sc["crps_null"] > 0
    assert abs(sc["crps_lift"] - (sc["crps_null"] - sc["crps"]) / sc["crps_null"]) < 1e-9
    assert 0.0 <= sc["pit"] <= 1.0


# --- route inventory: exactly the five frozen routes ------------------------
def test_only_the_frozen_routes_exist():
    api_routes = {(r.path, tuple(sorted(m for m in r.methods if m not in ("HEAD", "OPTIONS"))))
                  for r in app.routes if getattr(r, "path", "").startswith("/api")}
    assert api_routes == {
        ("/api/health", ("GET",)),
        ("/api/tickers", ("GET",)),
        ("/api/events", ("GET",)),
        ("/api/forecast", ("POST",)),
        ("/api/backtest", ("GET",)),
        ("/api/rulial", ("POST",)),
        # CONTRACT.md section 6b ("Pavel's inversion") freezes this route too.
        # The set above predated 6b; corrected by the INTEGRATOR after
        # rulial/inverse.py landed. The contract is the authority, not this list.
        ("/api/scenario", ("POST",)),
    }


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"\n{'ALL PASS' if failures == 0 else str(failures) + ' FAILURES'}")
    sys.exit(1 if failures else 0)
