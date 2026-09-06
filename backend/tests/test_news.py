"""LANE-NEWS tests.

Run:  cd backend && python3 -m pytest tests/test_news.py -q

Every test here is OFFLINE. `RULIAL_NEWS_OFFLINE=1` plus a redirected corpus
directory means the suite never touches the network and never writes into the
real data/corpus. The one live-network check is marked `network` and skipped by
default: `python3 -m pytest tests/test_news.py -q -m network` runs it.

The bulk of this file hammers ONE function -- `_passes_leak_filter` -- because
that is the function whose failure silently manufactures a result.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("RULIAL_NEWS_OFFLINE", "1")

from rulial import news  # noqa: E402
from rulial.types import Article, Event  # noqa: E402


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolated_corpus(tmp_path, monkeypatch):
    """Point the module at a throwaway corpus dir and force offline mode."""
    monkeypatch.setenv("RULIAL_NEWS_OFFLINE", "1")
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    monkeypatch.setattr(news, "CORPUS_DIR", corpus)
    monkeypatch.setattr(news, "_CACHE_DIR", corpus / "_cache")
    yield corpus


@pytest.fixture
def event():
    return Event(ticker="NVDA", date="2018-11-20", move_pct=-0.252,
                 direction="down", window_days=5)


def _art(published, url="https://www.reuters.com/a", title="T", source="reuters.com"):
    return Article(url=url, title=title, published=published, source=source)


EV_DATE = date(2018, 11, 20)
WIN_START = EV_DATE - timedelta(days=30)


# ==========================================================================
# THE LEAKAGE FILTER -- the reason this module exists
# ==========================================================================

def test_article_published_after_the_event_is_rejected():
    assert news._passes_leak_filter(_art("2018-11-21"), EV_DATE, WIN_START) == "after_event"
    assert news._passes_leak_filter(_art("2019-01-14"), EV_DATE, WIN_START) == "after_event"


def test_article_published_ON_the_event_date_is_rejected_strictly_before_not_lte():
    """The single most important assertion in the repo.

    The event date is the END of the jump window. An article stamped that day
    may already be reporting the move, so the guard is `<`, never `<=`.
    """
    assert news._passes_leak_filter(_art("2018-11-20"), EV_DATE, WIN_START) == "after_event"


def test_article_published_the_day_before_is_admitted():
    assert news._passes_leak_filter(_art("2018-11-19"), EV_DATE, WIN_START) == ""


def test_article_older_than_the_lookback_is_rejected():
    assert news._passes_leak_filter(_art("2018-09-01"), EV_DATE, WIN_START) == "too_old"


def test_window_start_boundary_is_inclusive():
    assert news._passes_leak_filter(_art(WIN_START.isoformat()), EV_DATE, WIN_START) == ""
    day_before = (WIN_START - timedelta(days=1)).isoformat()
    assert news._passes_leak_filter(_art(day_before), EV_DATE, WIN_START) == "too_old"


@pytest.mark.parametrize("bad", ["", None, "n/a", "sometime in 2018", "20181119",
                                 "11/19/2018", "yesterday"])
def test_undated_articles_are_rejected_never_admitted_just_in_case(bad):
    """An unparseable date is a rejection. Recon's recommendation, enforced.

    "20181119" IS parseable (GDELT format) and is deliberately excluded below.
    """
    if bad == "20181119":
        assert news._passes_leak_filter(_art(bad), EV_DATE, WIN_START) == ""
        return
    assert news._passes_leak_filter(_art(bad), EV_DATE, WIN_START) == "undated"


def test_gdelt_timestamp_format_parses():
    assert news._parse_date("20181119T234500Z") == date(2018, 11, 19)
    assert news._parse_date("2018-11-19T23:45:00Z") == date(2018, 11, 19)
    assert news._parse_date("2018-11-19") == date(2018, 11, 19)
    assert news._parse_date("garbage") is None
    assert news._parse_date(None) is None


@pytest.mark.parametrize("url", [
    "https://www.macrotrends.net/stocks/charts/NVDA/nvidia/stock-price-history",
    "https://stockanalysis.com/stocks/nvda/history/",
    "https://www.statmuse.com/money/ask/nvidia-stock-price-in-november-2018",
    "https://finance.yahoo.com/quote/NVDA/history/",
    "https://www.zacks.com/stock/quote/NVDA",
])
def test_price_history_aggregators_are_blocked_by_domain(url):
    """These pages render prices through TODAY regardless of nominal date.

    Admitting one into a 2018 corpus injects 2026 prices. Date filtering cannot
    catch them because their own publication date looks fine.
    """
    art = _art("2018-11-19", url=url)
    assert news._passes_leak_filter(art, EV_DATE, WIN_START) == "blocked_domain"


def test_untitled_article_is_rejected():
    art = _art("2018-11-19", title="   ")
    assert news._passes_leak_filter(art, EV_DATE, WIN_START) == "no_title"


def test_cutoff_window_start_mode_is_stricter_than_event_date_mode():
    """`cutoff="window_start"` excludes articles published inside the jump window."""
    jump_start = EV_DATE - timedelta(days=5)          # 2018-11-15
    inside = _art("2018-11-16")                       # inside the jump window
    assert news._passes_leak_filter(inside, EV_DATE, WIN_START) == ""
    assert news._passes_leak_filter(inside, EV_DATE, WIN_START,
                                    cutoff=jump_start) == "after_event"


# ==========================================================================
# harvest()
# ==========================================================================

def test_harvest_offline_returns_only_pre_event_articles(event, monkeypatch):
    """Poison every provider with post-event articles; none may survive."""
    leaky = [
        _art("2018-11-20", url="https://www.reuters.com/on-the-day"),
        _art("2018-11-21", url="https://www.cnbc.com/day-after"),
        _art("2019-01-14", url="https://www.fool.com/why-nvidia-plunged-in-2018"),
    ]
    clean = [_art("2018-11-16", url="https://www.cnbc.com/pre-event",
                  title="Nvidia guides Q4 revenue well below consensus")]
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: list(leaky) + list(clean))
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_offline", lambda: False)

    got = news.harvest(event, force=True)
    assert [a.url for a in got] == ["https://www.cnbc.com/pre-event"]
    for a in got:
        assert a.published < event.date


def test_harvest_records_every_rejection_in_the_corpus_file(event, monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [
        _art("2018-11-25", url="https://www.reuters.com/late"),
        _art("2018-01-01", url="https://www.reuters.com/ancient"),
        _art("", url="https://www.reuters.com/undated"),
        _art("2018-11-18", url="https://www.macrotrends.net/x"),
        _art("2018-11-18", url="https://www.reuters.com/ok"),
    ])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_offline", lambda: False)

    news.harvest(event, force=True)
    doc = json.loads(news.corpus_path(event).read_text())
    rej = doc["leakage_filter_rejects"]
    assert rej["after_event"] == 1
    assert rej["too_old"] == 1
    assert rej["undated"] == 1
    assert rej["blocked_domain"] == 1
    assert doc["n_articles"] == 1
    # The discard rate must be visible, not silent.
    assert sum(rej.values()) == 4


def test_harvest_is_cached_and_does_not_refetch(event, monkeypatch):
    calls = {"n": 0}

    def _fake(*a, **k):
        calls["n"] += 1
        return [_art("2018-11-16", url="https://www.cnbc.com/x")]

    monkeypatch.setattr(news, "_gdelt_articles", _fake)
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_offline", lambda: False)

    news.harvest(event, force=True)
    assert calls["n"] == 1
    news.harvest(event)          # cache hit
    news.harvest(event)
    assert calls["n"] == 1, "cached event was re-fetched"
    news.harvest(event, force=True)
    assert calls["n"] == 2


def test_harvest_survives_a_dead_provider(event, monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("network on fire")

    monkeypatch.setattr(news, "_gdelt_articles", _boom)
    monkeypatch.setattr(news, "_sec_articles",
                        lambda *a, **k: [_art("2018-11-15",
                                              url="https://www.sec.gov/Archives/x.htm",
                                              title="NVDA 8-K", source="sec-edgar")])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_offline", lambda: False)

    got = news.harvest(event, force=True)
    assert len(got) == 1 and got[0].source == "sec-edgar"


def test_harvest_dedupes_by_url_and_by_title(event, monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [
        _art("2018-11-16", url="https://www.cnbc.com/a", title="Nvidia guides lower"),
        _art("2018-11-16", url="https://www.cnbc.com/a/", title="Nvidia guides lower"),
        _art("2018-11-16", url="https://www.cnbc.com/a?utm=x", title="Nvidia guides lower"),
        _art("2018-11-16", url="https://www.kvia.com/b", title="Nvidia guides lower!"),
        _art("2018-11-16", url="https://www.kvia.com/c", title="Something else entirely"),
    ])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_offline", lambda: False)
    got = news.harvest(event, force=True)
    assert len(got) == 2


def test_harvest_ranks_filings_and_reputable_sources_first(event, monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [
        _art("2018-11-19", url="https://randomblog.blogspot.com/z", title="Blog take"),
        _art("2018-11-18", url="https://www.reuters.com/r", title="Reuters take"),
    ])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [
        _art("2018-11-15", url="https://www.sec.gov/Archives/x.htm",
             title="NVDA 8-K", source="sec-edgar")])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_offline", lambda: False)
    got = news.harvest(event, force=True)
    assert got[0].source == "sec-edgar"
    assert news._domain_of(got[1].url) == "reuters.com"
    assert "blogspot" in got[2].url


def test_harvest_respects_max_articles(event, monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [
        _art("2018-11-1%d" % (i % 10), url="https://www.reuters.com/%d" % i,
             title="Headline %d" % i) for i in range(1, 10)])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_offline", lambda: False)
    assert len(news.harvest(event, force=True, max_articles=3)) == 3


def test_harvest_rejects_a_bad_cutoff_mode(event):
    with pytest.raises(ValueError):
        news.harvest(event, cutoff="whenever")


def test_harvest_rejects_a_non_iso_event_date():
    with pytest.raises(ValueError):
        news.harvest(Event(ticker="NVDA", date="Nov 20 2018", move_pct=-0.25,
                           direction="down", window_days=5), force=True)


def test_harvest_accepts_a_plain_dict_event(monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    got = news.harvest({"ticker": "tsla", "date": "2018-08-10", "move_pct": 0.16,
                        "direction": "up", "window_days": 5}, force=True)
    assert got == []
    assert (news.CORPUS_DIR / "TSLA_2018-08-10.json").exists()


def test_offline_mode_makes_no_network_call(event, monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("network call in offline mode")

    monkeypatch.setattr(news, "_http_get", _boom)
    monkeypatch.setenv("RULIAL_NEWS_OFFLINE", "1")
    news.harvest(event, force=True)   # must not raise


# ==========================================================================
# load_corpus() / build_corpus() / corpus_stats()
# ==========================================================================

def test_load_corpus_returns_none_when_absent(event):
    assert news.load_corpus(event) is None


def test_load_corpus_reapplies_the_leak_filter_to_a_tampered_file(event, monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    news.harvest(event, force=True)

    path = news.corpus_path(event)
    doc = json.loads(path.read_text())
    doc["articles"] = [
        {"url": "https://www.reuters.com/leak", "title": "After the fact",
         "published": "2018-11-29", "source": "reuters.com", "snippet": ""},
        {"url": "https://www.reuters.com/clean", "title": "Before the fact",
         "published": "2018-11-14", "source": "reuters.com", "snippet": ""},
    ]
    doc["n_articles"] = 2
    path.write_text(json.dumps(doc))

    got = news.load_corpus(event)
    assert [a.url for a in got] == ["https://www.reuters.com/clean"]


def test_load_corpus_cannot_have_its_guard_widened_by_editing_the_file(event, monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    news.harvest(event, force=True)
    path = news.corpus_path(event)
    doc = json.loads(path.read_text())
    doc["window"]["end_exclusive"] = "2019-06-01"       # attacker widens the guard
    doc["window"]["start"] = "2000-01-01"
    doc["articles"] = [{"url": "https://www.reuters.com/leak", "title": "Leak",
                        "published": "2018-12-05", "source": "reuters.com", "snippet": ""}]
    path.write_text(json.dumps(doc))
    assert news.load_corpus(event) == []


def test_load_corpus_survives_corrupt_json(event):
    news.corpus_path(event).write_text("{not json")
    assert news.load_corpus(event) is None


def test_build_corpus_writes_one_file_per_event(monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    evs = [
        Event(ticker="NVDA", date="2018-11-20", move_pct=-0.25, direction="down", window_days=5),
        Event(ticker="TSLA", date="2019-01-18", move_pct=-0.16, direction="down", window_days=5),
    ]
    summary = news.build_corpus(evs, verbose=False)
    assert summary["n_events"] == 2
    assert summary["harvested"] == 2
    assert (news.CORPUS_DIR / "NVDA_2018-11-20.json").exists()
    assert (news.CORPUS_DIR / "TSLA_2019-01-18.json").exists()

    # Post-2017 events whose GDELT tier came back empty are treated as
    # INCOMPLETE and retried, so they do not count as cached.
    again = news.build_corpus(evs, verbose=False, retry_incomplete=False)
    assert again["cached"] == 2 and again["harvested"] == 0


def test_events_harvested_while_the_gdelt_breaker_was_tripped_are_retried(monkeypatch):
    """A transient rate limit must not become a permanent hole in the corpus."""
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    modern = Event(ticker="NVDA", date="2018-11-20", move_pct=-0.25,
                   direction="down", window_days=5)
    old = Event(ticker="AMZN", date="2000-06-23", move_pct=-0.27,
                direction="down", window_days=5)
    news.build_corpus([modern, old], verbose=False)

    # The modern event got no news -> retryable. The 2000 event never could have
    # had news (GDELT starts 2017), so it is complete, not incomplete.
    assert news._is_incomplete(modern) is True
    assert news._is_incomplete(old) is False

    again = news.build_corpus([modern, old], verbose=False)
    assert again["retried"] == 1
    assert again["cached"] == 1

    # Once the news tier answers, the event stops being retried.
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [
        _art("2018-11-16", url="https://www.bbc.com/x", title="Nvidia guides lower")])
    monkeypatch.setattr(news, "_offline", lambda: False)
    news.build_corpus([modern], verbose=False)
    assert news._is_incomplete(modern) is False


def test_build_corpus_stops_at_the_time_budget_and_resumes(monkeypatch):
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])

    def _slow(*a, **k):
        import time as _t
        _t.sleep(0.05)
        return []

    monkeypatch.setattr(news, "_gdelt_articles", _slow)
    monkeypatch.setattr(news, "_offline", lambda: False)
    evs = [Event(ticker="NVDA", date="2018-11-%02d" % d, move_pct=-0.25,
                 direction="down", window_days=5) for d in range(10, 26)]
    out = news.build_corpus(evs, verbose=False, max_seconds=0.10)
    assert out["remaining"] > 0
    assert out["harvested"] < len(evs)


def test_build_corpus_honours_limit(monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    evs = [Event(ticker="NVDA", date="2018-11-%02d" % d, move_pct=-0.25,
                 direction="down", window_days=5) for d in (10, 15, 20, 25)]
    assert news.build_corpus(evs, limit=2, verbose=False)["n_events"] == 2


def test_build_corpus_on_empty_ledger_is_a_noop(monkeypatch):
    monkeypatch.setattr(news, "_load_ledger", lambda: [])
    assert news.build_corpus(verbose=False)["n_events"] == 0


def test_corpus_stats_reports_empty_events_and_missing_tickers(monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    news.harvest(Event(ticker="XOM", date="2018-11-20", move_pct=-0.16,
                       direction="down", window_days=5), force=True)
    stats = news.corpus_stats()
    assert stats["n_corpus_files"] == 1
    assert stats["n_empty_events"] == 1
    assert "NVDA" in stats["universe_missing"]
    assert stats["per_ticker"]["XOM"]["n_events"] == 1


# ==========================================================================
# Provider plumbing (no network)
# ==========================================================================

def test_gdelt_is_skipped_entirely_before_its_coverage_starts(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("GDELT called for a pre-2017 event")

    monkeypatch.setattr(news, "_http_get", _boom)
    monkeypatch.setattr(news, "_offline", lambda: False)
    assert news._gdelt_articles("AMZN", date(2000, 5, 24), date(2000, 6, 23)) == []


def test_gdelt_circuit_breaker_trips_after_repeated_failures(monkeypatch):
    monkeypatch.setattr(news, "_offline", lambda: False)
    monkeypatch.setattr(news, "_gdelt_failures", 0, raising=False)
    monkeypatch.setattr(news, "_gdelt_disabled", False, raising=False)
    calls = {"n": 0}

    def _fail(*a, **k):
        calls["n"] += 1
        raise RuntimeError("429")

    monkeypatch.setattr(news, "_http_get", _fail)
    for _ in range(6):
        news._gdelt_articles("NVDA", date(2018, 10, 21), date(2018, 11, 20))
    assert news.gdelt_status()["disabled"] is True
    assert calls["n"] == news.GDELT_MAX_CONSECUTIVE_FAILURES, "breaker did not stop the retries"


def test_gdelt_end_window_backs_off_from_the_cutoff(monkeypatch):
    """Regression guard for a MEASURED GDELT bug.

    GDELT overshoots `enddatetime` by about a day. Asking for 20180725120000
    returned 250 articles every one stamped 2018-07-26; asking for
    20181121000000 returned articles at 2018-11-21T23:45Z. So the request backs
    off GDELT_END_MARGIN_DAYS from the cutoff, and the Python-side filter stays
    the authority regardless of what GDELT decides to send.
    """
    seen = {}
    monkeypatch.setattr(news, "_offline", lambda: False)
    monkeypatch.setattr(news, "_gdelt_disabled", False, raising=False)

    class _R:
        @staticmethod
        def json():
            return {"articles": []}

    def _capture(url, bucket, **k):
        seen["url"] = url
        return _R

    monkeypatch.setattr(news, "_http_get", _capture)
    news._gdelt_articles("META", date(2018, 6, 26), date(2018, 7, 26))
    assert "enddatetime=20180724235959" in seen["url"]      # cutoff minus 2 days
    assert "enddatetime=20180726" not in seen["url"]
    assert "enddatetime=20180725" not in seen["url"]


def test_pre_gdelt_events_get_a_wider_lookback_because_filings_are_quarterly(monkeypatch):
    """MEASURED: AMZN 2000-06-23 returned 0 at 30 days; its Q1 10-Q sat 39 days
    back. SEC-only events need a window sized to filing cadence, not news cadence."""
    seen = {}

    def _sec(ticker, window_start, cutoff):
        seen["window_start"] = window_start
        return []

    monkeypatch.setattr(news, "_sec_articles", _sec)
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    news.harvest(Event(ticker="AMZN", date="2000-06-23", move_pct=-0.271,
                       direction="down", window_days=5), force=True)
    assert seen["window_start"] == date(2000, 6, 23) - timedelta(
        days=news.PRE_GDELT_LOOKBACK_DAYS)

    # a modern event keeps the default 30-day window
    news.harvest(Event(ticker="AMZN", date="2018-06-23", move_pct=-0.16,
                       direction="down", window_days=5), force=True)
    assert seen["window_start"] == date(2018, 6, 23) - timedelta(
        days=news.DEFAULT_LOOKBACK_DAYS)

    # an explicit lookback is never overridden
    news.harvest(Event(ticker="AMZN", date="2000-06-23", move_pct=-0.271,
                       direction="down", window_days=5), force=True, lookback_days=10)
    assert seen["window_start"] == date(2000, 6, 23) - timedelta(days=10)


def test_old_sec_filings_without_a_primary_document_get_the_index_url(monkeypatch,
                                                                     _isolated_corpus):
    cache = _isolated_corpus / "_cache"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / ("sec_AMZN_v%d.json" % news._SEC_CACHE_VERSION)).write_text(json.dumps([
        {"filingDate": "2000-05-15", "form": "10-Q",
         "accessionNumber": "0000891020-00-001049", "primaryDocument": "",
         "primaryDocDescription": "", "items": "", "reportDate": ""},
    ]))
    got = news._sec_articles("AMZN", date(2000, 3, 15), date(2000, 6, 23))
    assert len(got) == 1
    assert got[0].url == ("https://www.sec.gov/Archives/edgar/data/1018724/"
                          "0000891020-00-001049-index.htm")


def test_gdelt_offtopic_noise_is_dropped_by_title(monkeypatch):
    """Real titles GDELT actually returned for a META query on 2018-07-25.

    GDELT's boolean grouping is loose: the finance.yahoo.com noise below came
    back from a query that already said (Facebook) AND (stock OR shares ...).
    """
    on_topic = [
        "Facebook shares tumble as growth disappoints",
        "Facebook value falls $130 billion after Q2 earnings call",
        "Facebook shares plunge more than 20 percent on warnings for future",
        "Facebook stock falls 24 percent on forecast for slowing growth",
    ]
    off_topic = [
        "Asian Stocks to Gain on Trade Deal ; Dollar Falls : Markets Wrap",
        "Five Things You Need to Know to Start Your Day",
        "A California DMV employee who napped at work every day for 3 hours",
        "Centauro the robot hopes to play role in disaster relief work",
        "It should worry China a lot more than tariffs",
    ]
    for t in on_topic:
        assert news._is_on_topic("META", t), t
    for t in off_topic:
        assert not news._is_on_topic("META", t), t

    rows = [{"url": "https://www.bbc.com/%d" % i, "title": t,
             "seendate": "20180725T120000Z"}
            for i, t in enumerate(on_topic + off_topic)]

    class _R:
        @staticmethod
        def json():
            return {"articles": rows}

    monkeypatch.setattr(news, "_offline", lambda: False)
    monkeypatch.setattr(news, "_gdelt_disabled", False, raising=False)
    monkeypatch.setattr(news, "_http_get", lambda url, bucket, **k: _R)
    got = news._gdelt_articles("META", date(2018, 6, 26), date(2018, 7, 26))
    assert len(got) == len(on_topic)
    assert all(news._is_on_topic("META", a.title) for a in got)


def test_every_universe_ticker_has_gdelt_query_and_title_keywords():
    for tk in news.UNIVERSE:
        assert tk in news._GDELT_KEYWORDS, tk
        assert tk in news._TITLE_KEYWORDS, tk
        assert news._gdelt_query(tk)


def test_corpus_report_is_a_string_and_names_the_leakage_rule(monkeypatch):
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_sec_articles", lambda *a, **k: [])
    monkeypatch.setattr(news, "_curated_articles", lambda *a, **k: [])
    news.harvest(Event(ticker="NVDA", date="2018-11-20", move_pct=-0.25,
                       direction="down", window_days=5), force=True)
    rep = news.corpus_report()
    assert "NVDA" in rep and "STRICTLY before" in rep


def test_sec_filing_title_renders_8k_item_codes_in_english():
    row = {"form": "8-K", "items": "2.02,9.01", "primaryDocDescription": "FORM 8-K"}
    title = news._filing_title("NVDA", row)
    assert "Results of Operations and Financial Condition" in title
    assert "Financial Statements and Exhibits" in title


def test_sec_provider_reads_from_cache_without_network(monkeypatch, _isolated_corpus):
    cache = _isolated_corpus / "_cache"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / ("sec_NVDA_v%d.json" % news._SEC_CACHE_VERSION)).write_text(json.dumps([
        {"filingDate": "2018-11-15", "form": "8-K", "accessionNumber": "0001045810-18-000148",
         "primaryDocument": "form8-kq3fy19.htm", "primaryDocDescription": "FORM 8-K",
         "items": "2.02,9.01", "reportDate": "2018-11-15"},
        {"filingDate": "2018-11-15", "form": "4", "accessionNumber": "x",
         "primaryDocument": "d.xml", "primaryDocDescription": "", "items": "",
         "reportDate": ""},
        {"filingDate": "2018-11-22", "form": "8-K", "accessionNumber": "y",
         "primaryDocument": "d.htm", "primaryDocDescription": "", "items": "8.01",
         "reportDate": ""},
    ]))
    got = news._sec_articles("NVDA", date(2018, 10, 21), date(2018, 11, 20))
    assert len(got) == 1, "Form 4 noise or the post-event 8-K leaked through"
    assert got[0].source == "sec-edgar"
    assert got[0].published == "2018-11-15"
    assert got[0].url == ("https://www.sec.gov/Archives/edgar/data/1045810/"
                          "000104581018000148/form8-kq3fy19.htm")


def test_googl_resolves_both_alphabet_and_legacy_google_inc_ciks():
    """MEASURED BUG: Alphabet's CIK only starts 2015-10-02, so a GOOGL-only
    lookup returned nothing for the seven 2008-2013 GOOGL events in the ledger."""
    ciks = news._CIK_OVERRIDE["GOOGL"]
    assert "0001652044" in ciks and "0001288776" in ciks


def test_sec_rows_build_urls_against_the_cik_that_actually_filed(monkeypatch,
                                                                _isolated_corpus):
    cache = _isolated_corpus / "_cache"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / ("sec_GOOGL_v%d.json" % news._SEC_CACHE_VERSION)).write_text(json.dumps([
        {"cik": "0001288776", "filingDate": "2008-10-06", "form": "8-K",
         "accessionNumber": "0001193125-08-000001", "primaryDocument": "d8k.htm",
         "primaryDocDescription": "", "items": "8.01", "reportDate": ""},
    ]))
    got = news._sec_articles("GOOGL", date(2008, 9, 8), date(2008, 10, 8))
    assert len(got) == 1
    # 1288776 (Google Inc), not 1652044 (Alphabet)
    assert "/data/1288776/" in got[0].url


def test_every_universe_ticker_has_a_cik_tuple():
    for tk in news.UNIVERSE:
        ciks = news._CIK_OVERRIDE[tk]
        assert isinstance(ciks, tuple) and ciks
        for c in ciks:
            assert len(c) == 10 and c.isdigit(), (tk, c)


def test_every_curated_seed_entry_is_well_formed_and_dated_before_its_events():
    assert news.CURATED_SEED, "curated seed is empty"
    for row in news.CURATED_SEED:
        assert row["url"].startswith("https://")
        assert row["ticker"] in news.UNIVERSE
        pub = news._parse_date(row["published"])
        assert pub is not None, row["url"]
        for ed in row["event_dates"]:
            assert pub < news._parse_date(ed), \
                "curated entry %s is not before event %s" % (row["url"], ed)


def test_curated_articles_are_labelled_so_they_can_be_excluded_from_metrics():
    arts = news._curated_articles("NVDA", date(2018, 11, 20))
    assert arts, "expected curated NVDA entries for 2018-11-20"
    for a in arts:
        assert a.source == "curated"
        assert "curated seed" in a.snippet


def test_module_imports_without_network_access():
    """CONTRACT s9: every module must import cleanly with no network at import."""
    import importlib
    importlib.reload(news)
    assert callable(news.harvest)


# ==========================================================================
# Live network -- opt in with: pytest -m network
# ==========================================================================

@pytest.mark.network
def test_live_sec_harvest_returns_only_pre_event_filings(monkeypatch, _isolated_corpus):
    """Live check against SEC EDGAR. Self-skips when the network is unavailable,
    so an offline machine sees a skip rather than a red suite."""
    monkeypatch.setenv("RULIAL_NEWS_OFFLINE", "0")
    monkeypatch.setattr(news, "_offline", lambda: False)
    monkeypatch.setattr(news, "_gdelt_articles", lambda *a, **k: [])
    ev = Event(ticker="NVDA", date="2018-11-20", move_pct=-0.252,
               direction="down", window_days=5)
    try:
        got = news.harvest(ev, force=True)
    except Exception as exc:                      # pragma: no cover
        pytest.skip("network unavailable: %s" % exc)
    if not got:
        pytest.skip("SEC EDGAR unreachable or returned nothing")
    # These are REAL filings. The assertion that matters is the date guard.
    for a in got:
        assert a.published < ev.date, "live harvest leaked %r" % (a.published,)
    assert any(a.source == "sec-edgar" for a in got)
    assert any(a.url.startswith("https://www.sec.gov/Archives/") for a in got)
