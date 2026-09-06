"""LANE-NEWS -- seed news corpus for jump events.

Owner: LANE-NEWS. See CONTRACT.md section 4.

Public surface
--------------
    harvest(event, lookback_days=30) -> list[Article]
    build_corpus(events=None, limit=None) -> dict     # writes data/corpus/{TICKER}_{DATE}.json
    load_corpus(event) -> list[Article]

THE LEAKAGE FILTER IS THE POINT OF THIS FILE
--------------------------------------------
An article published *after* a jump has already seen the jump. Feeding one into
the generator is lookahead, and it is the single easiest way to manufacture a
fake result. Everything here funnels through ``_passes_leak_filter`` and every
rejection is counted, so the discard rate is visible in the corpus file rather
than silent.

Three hard rules, in ``_passes_leak_filter``:
  1. ``published < event.date``  -- STRICTLY before. Not <=. The event date is
     the END of the jump window, so an article stamped that day may already be
     reporting the move.
  2. ``published >= event.date - lookback_days`` -- ancient background noise is
     not a catalyst.
  3. An article whose publication date cannot be parsed is REJECTED, never
     admitted "just in case". Undated articles are counted separately so the
     cost of this rule is measurable.

A domain blocklist backs this up. Price-history aggregators (macrotrends,
stockanalysis, statmuse, a Yahoo quote page) render prices through *today* no
matter what date the page nominally covers, so fetching one into a 2018 corpus
injects 2026 prices. They rank highly on exactly the catalyst-free queries where
the corpus is thinnest, so they are dropped by domain, not by date.

Retrieval tiers (tried in order, results merged and de-duplicated)
-----------------------------------------------------------------
  1. GDELT 2.0 DOC API -- free, no key, worldwide news index, coverage from
     2017-01-01. Real publisher URLs with a first-seen timestamp.
  2. SEC EDGAR submissions API -- free, no key, coverage from 1994. Material
     filings (8-K / 10-Q / 10-K / DEF 14A / 425) are real, exactly-dated,
     contemporaneous primary documents. This is the workhorse for the pre-2017
     majority of the train ledger, where no free news archive exists.
  3. ``CURATED_SEED`` -- a small set of hand-verified articles, each one fetched
     and confirmed HTTP 200 before being written down, marked ``source="curated"``
     so any headline metric can filter them out. It is deliberately tiny: most
     pre-2010 financial-news archives are simply gone (money.cnn.com's 2000
     archive returns 404, Reuters article URLs return 401), so the honest floor
     for old events is the SEC filing, not a news article.

Deliberately NOT used: ``mcp__dubbs-research__news_company``. Four of its five
providers are uncredentialed or entitlement-blocked on this account, and the one
that answers (yfinance) silently ignores ``start_date``/``end_date`` and returns
a ~2-day rolling window of current news. A request for NVDA November 2018
returns articles dated last week, with ``warnings: null``. That is a corpus
poisoner, not a data source.

MEASURED on the 334-event ledger (2026-09-06), for LANE-EVAL and LANE-PRD:
  * 1,145 articles admitted, 0 leakage violations on a full re-audit of the
    written corpus (every article's own date re-checked against its event).
  * 156 of those 1,145 (13.6%) were published INSIDE the 5-day jump window.
    They are legal under the contract's cutoff (strictly before the event date)
    but they have seen part of the move -- the NVDA 2018-11-23 corpus is the
    honest example: a 2018-11-16 story whose headline already says "Stock
    Plunges 17%".
  * Switching to ``cutoff="window_start"`` removes all 156 and empties only 9
    of 334 events. The paranoid setting is CHEAP. If LANE-EVAL wants a
    lookahead-free arm of the backtest, it costs almost nothing to run.

Network policy: nothing here touches the network at import time. Set
``RULIAL_NEWS_OFFLINE=1`` to restrict harvesting to the on-disk cache plus the
curated seed.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Sequence

from .config import CORPUS_DIR, TICKER_NAMES, UNIVERSE, EVENTS_PATH, WINDOW_DAYS
from .types import Article, Event

__all__ = [
    "harvest",
    "CUTOFF_MODES",
    "gdelt_status",
    "build_corpus",
    "load_corpus",
    "corpus_path",
    "corpus_stats",
    "CURATED_SEED",
    "GDELT_COVERAGE_START",
    "corpus_report",
]

# --------------------------------------------------------------------------
# Tunables
# --------------------------------------------------------------------------

DEFAULT_LOOKBACK_DAYS = 30
MAX_ARTICLES_PER_EVENT = 12
GDELT_COVERAGE_START = "2017-01-01"   # GDELT DOC 2.0 index begins here
GDELT_END_MARGIN_DAYS = 2             # GDELT overshoots `enddatetime` by ~1 day
# SEC filings are quarterly, so a 30-day window often contains none. For events
# that predate GDELT there is no news tier at all, and a 30-day window can come
# back completely empty (measured: AMZN 2000-06-23 -> 0, while the Q1 10-Q sat
# 39 days back). Widen the window for those, on filing cadence, not on results.
PRE_GDELT_LOOKBACK_DAYS = 100
HTTP_TIMEOUT = 40
USER_AGENT = "rulial-markets/0.1 (Sundai hackathon research; contact wilson1.wu@gmail.com)"

_CACHE_DIR = CORPUS_DIR / "_cache"

# Politeness. GDELT asks for one request every 5 seconds and returns HTTP 429
# with a plain-text scolding if you go faster. SEC asks for <= 10 req/s.
_MIN_INTERVAL = {"gdelt": 7.0, "sec": 0.15}
_last_call: Dict[str, float] = {}
_throttle_lock = threading.Lock()

# GDELT rate-limits by IP and stays angry for a while once you have annoyed it.
# After this many consecutive failures we stop calling it for the rest of the
# process rather than burning ~40s per event on retries. SEC + curated still run,
# so a tripped breaker degrades the corpus, it does not break the build.
GDELT_MAX_CONSECUTIVE_FAILURES = 3
_gdelt_failures = 0
_gdelt_disabled = False


def gdelt_status() -> dict:
    """Introspection for the harvest report: is the GDELT breaker tripped?"""
    return {"disabled": _gdelt_disabled, "consecutive_failures": _gdelt_failures,
            "coverage_start": GDELT_COVERAGE_START}


def _offline() -> bool:
    return os.environ.get("RULIAL_NEWS_OFFLINE", "").strip().lower() in {"1", "true", "yes"}


def _throttle(bucket: str) -> None:
    """Block until the minimum polite interval for `bucket` has elapsed."""
    wait = 0.0
    with _throttle_lock:
        gap = _MIN_INTERVAL.get(bucket, 0.0)
        now = time.monotonic()
        prev = _last_call.get(bucket)
        if prev is not None and now - prev < gap:
            wait = gap - (now - prev)
        _last_call[bucket] = now + wait
    if wait > 0:
        time.sleep(wait)


# --------------------------------------------------------------------------
# THE LEAKAGE FILTER
# --------------------------------------------------------------------------

# Price-history aggregators. Every one of these renders prices through today,
# so admitting one into a historical corpus injects future prices.
_BLOCKED_DOMAINS = {
    "macrotrends.net", "stockanalysis.com", "statmuse.com", "ycharts.com",
    "wisesheets.io", "tradingview.com", "investing.com", "marketbeat.com",
    "barchart.com", "stocktwits.com", "gurufocus.com", "wallstreetzen.com",
    "companiesmarketcap.com", "dividendmax.com", "zacks.com", "simplywall.st",
    "nasdaq.com/market-activity", "finance.yahoo.com/quote", "google.com/finance",
    "in.investing.com", "uk.investing.com", "stockinvest.us", "chartmill.com",
    "fintel.io", "quantumonline.com", "dividend.com", "aiolux.com",
}

_ISO_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_GDELT_TS_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})T?")


def _parse_date(value) -> Optional[date]:
    """Best-effort ISO / GDELT-timestamp -> date. Returns None if unparseable.

    None is a rejection, not a pass. See rule 3 in the module docstring.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    if not s:
        return None
    m = _ISO_DATE_RE.match(s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = _GDELT_TS_RE.match(s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _domain_of(url: str) -> str:
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""
    return host[4:] if host.startswith("www.") else host


def _is_blocked_domain(url: str) -> bool:
    dom = _domain_of(url)
    if not dom:
        return True
    if dom in _BLOCKED_DOMAINS:
        return True
    # path-qualified entries, e.g. "finance.yahoo.com/quote"
    low = url.lower()
    for entry in _BLOCKED_DOMAINS:
        if "/" in entry and entry in low:
            return True
    return False


# Two admissible cutoffs. "event_date" is the CONTRACT default: strictly before
# the day the jump window closes. "window_start" is the paranoid setting: strictly
# before the jump window even OPENS, so no admitted article has seen any part of
# the move. window_start costs recall (the catalyst is often reported inside the
# window) and is offered so LANE-EVAL can quantify that trade rather than argue
# about it. Whichever is used is recorded in the corpus file.
CUTOFF_MODES = ("event_date", "window_start")


def _passes_leak_filter(article: Article, event_date: date, window_start: date,
                        cutoff: date = None) -> str:
    """Return "" if the article is admissible, else a rejection reason code.

    THIS IS THE MOST IMPORTANT FUNCTION IN THE FILE.

        window_start <= published < cutoff        (cutoff defaults to event_date)

    STRICTLY less than the cutoff. The event date is the END of the jump window,
    so an article stamped that day may already be reporting the move.
    """
    if cutoff is None:
        cutoff = event_date
    pub = _parse_date(article.published)
    if pub is None:
        return "undated"
    if pub >= cutoff:              # <-- the leakage guard. Strictly before.
        return "after_event"
    if pub < window_start:
        return "too_old"
    if _is_blocked_domain(article.url):
        return "blocked_domain"
    if not (article.title or "").strip():
        return "no_title"
    return ""


# --------------------------------------------------------------------------
# Tier 1: GDELT 2.0 DOC API  (2017-01-01 onward, free, no key)
# --------------------------------------------------------------------------

# Reputation tiers used only for RANKING, never for fabricating anything.
_TIER1 = {
    "reuters.com", "bloomberg.com", "wsj.com", "ft.com", "cnbc.com", "nytimes.com",
    "apnews.com", "washingtonpost.com", "barrons.com", "marketwatch.com",
    "theguardian.com", "bbc.co.uk", "bbc.com", "economist.com", "forbes.com",
    "businessinsider.com", "fortune.com", "axios.com", "politico.com", "cnn.com",
    "seattletimes.com", "chicagotribune.com", "latimes.com", "usatoday.com",
    "theverge.com", "arstechnica.com", "wired.com", "techcrunch.com",
}
_TIER2 = {
    "fool.com", "benzinga.com", "thestreet.com", "seekingalpha.com", "reuters.co.uk",
    "yahoo.com", "finance.yahoo.com", "cnet.com", "engadget.com", "zdnet.com",
    "venturebeat.com", "theregister.com", "aljazeera.com", "npr.org", "cbsnews.com",
    "nbcnews.com", "abcnews.go.com", "foxbusiness.com", "qz.com", "vox.com",
    "recode.net", "thehill.com", "newsweek.com", "time.com", "sfgate.com",
}

# GDELT query keyword per ticker. Company name, not symbol -- GDELT indexes
# article text, and "$NVDA" barely appears in mainstream copy.
_GDELT_KEYWORDS = {
    "NVDA": '"Nvidia"',
    "AAPL": '"Apple Inc" OR ("Apple" AND (iPhone OR Cupertino))',
    "MSFT": '"Microsoft"',
    "AMZN": '"Amazon.com" OR ("Amazon" AND (shares OR earnings OR Bezos))',
    "TSLA": '"Tesla" AND (Musk OR shares OR stock OR earnings)',
    "META": '"Facebook" OR "Meta Platforms"',
    "GOOGL": '"Alphabet Inc" OR ("Google" AND (shares OR earnings OR Alphabet))',
    "JPM": '"JPMorgan" OR "JP Morgan"',
    "XOM": '"Exxon" OR "ExxonMobil"',
    "BA": '"Boeing"',
}


# GDELT's boolean grouping is loose: a query for
# (Facebook) (stock OR shares OR earnings) also returned "A California DMV
# employee who napped at work every day" and "Centauro the robot hopes to play
# role in disaster relief work", both from finance.yahoo.com. So the company
# name must also appear in the TITLE. This is a relevance filter, not a leakage
# filter -- the two are kept separate on purpose.
_TITLE_KEYWORDS = {
    "NVDA": ("nvidia", "geforce"),
    "AAPL": ("apple", "iphone", "ipad", "mac "),
    "MSFT": ("microsoft", "windows", "azure"),
    "AMZN": ("amazon", "bezos", "aws"),
    "TSLA": ("tesla", "musk"),
    "META": ("facebook", "meta platforms", "zuckerberg", "instagram", "whatsapp"),
    "GOOGL": ("google", "alphabet", "youtube"),
    "JPM": ("jpmorgan", "jp morgan", "j.p. morgan", "dimon"),
    "XOM": ("exxon", "mobil"),
    "BA": ("boeing", "737", "787", "dreamliner", "max 8"),
}


def _is_on_topic(ticker: str, title: str) -> bool:
    kws = _TITLE_KEYWORDS.get(ticker.upper())
    if not kws:
        return True
    low = (title or "").lower()
    return any(k in low for k in kws)


def _gdelt_query(ticker: str) -> str:
    kw = _GDELT_KEYWORDS.get(ticker) or '"%s"' % TICKER_NAMES.get(ticker, ticker)
    return "(%s) (stock OR shares OR investors OR earnings OR revenue) sourcelang:english" % kw


def _http_get(url: str, bucket: str, retries: int = 4):
    import requests  # local import: no network stack pulled in at module import

    sess = _http_get._session  # type: ignore[attr-defined]
    if sess is None:
        sess = requests.Session()
        sess.headers.update({"User-Agent": USER_AGENT})
        _http_get._session = sess  # type: ignore[attr-defined]

    last = None
    for attempt in range(retries):
        _throttle(bucket)
        try:
            resp = sess.get(url, timeout=HTTP_TIMEOUT)
        except Exception as exc:  # network hiccup -> back off and retry
            last = exc
            time.sleep(2.0 * (attempt + 1))
            continue
        if resp.status_code == 200:
            return resp
        last = RuntimeError("HTTP %s" % resp.status_code)
        # 429 from GDELT is a rate scold; back off harder each time.
        time.sleep(3.0 * (attempt + 1))
    raise RuntimeError("GET failed after %d attempts: %s (%s)" % (retries, url, last))


_http_get._session = None  # type: ignore[attr-defined]


def _gdelt_articles(ticker: str, window_start: date, event_date: date,
                    max_records: int = 75) -> List[Article]:
    """Query the GDELT 2.0 DOC API for the pre-event window. Never raises."""
    global _gdelt_failures, _gdelt_disabled
    if _gdelt_disabled or _offline():
        return []
    if event_date <= _parse_date(GDELT_COVERAGE_START):
        return []
    start = max(window_start, _parse_date(GDELT_COVERAGE_START))
    params = {
        "query": _gdelt_query(ticker),
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(max_records),
        "sort": "datedesc",
        "startdatetime": start.strftime("%Y%m%d") + "000000",
        # MEASURED 2026-09-06, twice: GDELT does NOT honour `enddatetime`
        # tightly. Asking for enddatetime=20180725120000 returned 250 articles
        # every one of them stamped 2018-07-26 -- a full day PAST the requested
        # end. Asking for 20181121000000 returned articles at 2018-11-21T23:45Z.
        # The overshoot is about a day, so we request a 2-day margin and let the
        # Python-side filter stay the authority. Request loose-but-early, verify
        # strict. If GDELT ever tightens up, the filter still holds.
        "enddatetime": (event_date - timedelta(days=GDELT_END_MARGIN_DAYS)
                        ).strftime("%Y%m%d") + "235959",
    }
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(params)
    try:
        resp = _http_get(url, "gdelt")
        payload = resp.json()
    except Exception:
        _gdelt_failures += 1
        if _gdelt_failures >= GDELT_MAX_CONSECUTIVE_FAILURES:
            _gdelt_disabled = True   # breaker trips; SEC + curated carry on
        return []
    _gdelt_failures = 0

    out: List[Article] = []
    for row in payload.get("articles", []) or []:
        url_ = (row.get("url") or "").strip()
        title = (row.get("title") or "").strip()
        seen = row.get("seendate") or ""
        pub = _parse_date(seen)
        if not url_ or not title or pub is None:
            continue
        if not _is_on_topic(ticker, title):
            continue
        out.append(Article(
            url=url_,
            title=title,
            published=pub.isoformat(),
            source=_domain_of(url_) or "gdelt",
            # `seendate` is GDELT's first-seen timestamp, which is >= the true
            # publication time. Erring late is the SAFE direction for a
            # strictly-before filter: it can only discard, never admit.
            snippet="GDELT first-seen %s. Domain %s." % (seen, _domain_of(url_)),
        ))
    return out


# --------------------------------------------------------------------------
# Tier 2: SEC EDGAR submissions  (1994 onward, free, no key)
# --------------------------------------------------------------------------

# Material forms only. Form 3/4/5 (insider transactions) fire dozens of times a
# week and are noise; 424B/FWP are shelf mechanics.
_MATERIAL_FORMS = {
    "8-K", "8-K/A", "10-Q", "10-Q/A", "10-K", "10-K/A", "DEF 14A", "DEFA14A",
    "425", "SC 13D", "SC 13D/A", "6-K", "S-1", "S-1/A", "20-F", "11-K",
}

# 8-K item codes -> plain English. Source: SEC Form 8-K General Instructions.
_EIGHTK_ITEMS = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.03": "Creation of a Direct Financial Obligation",
    "2.04": "Triggering Events That Accelerate a Financial Obligation",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Failure to Satisfy a Listing Rule",
    "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modification to Rights of Security Holders",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure or Election of Directors or Principal Officers",
    "5.03": "Amendments to Articles of Incorporation or Bylaws",
    "5.07": "Submission of Matters to a Vote of Security Holders",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}

# Ticker -> every CIK that has ever filed for it, newest entity first.
# GOOGL is the trap: Alphabet's CIK 0001652044 only starts at the October 2015
# holding-company reorg, so a GOOGL-only lookup returns NOTHING for the 2008-2013
# events in the ledger. Google Inc's own CIK 0001288776 carries those. Measured:
# GOOGL had 7 events with zero articles until this was fixed.
_CIK_OVERRIDE = {
    "NVDA": ("0001045810",),
    "AAPL": ("0000320193",),
    "MSFT": ("0000789019",),
    "AMZN": ("0001018724",),
    "TSLA": ("0001318605",),
    "META": ("0001326801",),                        # Facebook -> Meta, same CIK
    "GOOGL": ("0001652044", "0001288776"),          # Alphabet, then Google Inc
    "JPM": ("0000019617",),
    "XOM": ("0000034088",),
    "BA": ("0000012927",),
}
_SEC_CACHE_VERSION = 3   # bump to invalidate on-disk submission caches


def _sec_headers() -> dict:
    return {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}


def _sec_submissions(ticker: str) -> List[dict]:
    """All filings for a ticker across every CIK it has filed under.

    Cached to disk; never raises. Each row carries its own `cik` so the archive
    URL is built against the entity that actually filed it.
    """
    ciks = _CIK_OVERRIDE.get(ticker.upper())
    if not ciks:
        return []
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _CACHE_DIR / ("sec_%s_v%d.json" % (ticker.upper(), _SEC_CACHE_VERSION))
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except Exception:
            pass
    if _offline():
        return []

    import requests
    rows: List[dict] = []

    def _absorb(block: dict, cik: str) -> None:
        n = len(block.get("filingDate", []))
        forms = block.get("form", [])
        for i in range(n):
            # Drop the non-material forms at CACHE-WRITE time, not at read time.
            # JPM alone files enough Form 4s and 424B2 shelf takedowns to make an
            # unfiltered cache 37 MB; filtered it is a few hundred KB, and the
            # dropped rows could never have become an Article anyway.
            if forms[i] not in _MATERIAL_FORMS:
                continue
            rows.append({
                "cik": cik,
                "filingDate": block["filingDate"][i],
                "form": block["form"][i],
                "accessionNumber": block["accessionNumber"][i],
                "primaryDocument": block.get("primaryDocument", [""] * n)[i],
                "primaryDocDescription": block.get("primaryDocDescription", [""] * n)[i],
                "items": block.get("items", [""] * n)[i],
                "reportDate": block.get("reportDate", [""] * n)[i],
            })

    for cik in ciks:
        try:
            _throttle("sec")
            top = requests.get("https://data.sec.gov/submissions/CIK%s.json" % cik,
                               headers=_sec_headers(), timeout=HTTP_TIMEOUT).json()
            _absorb(top.get("filings", {}).get("recent", {}), cik)
            for extra in top.get("filings", {}).get("files", []) or []:
                _throttle("sec")
                blk = requests.get("https://data.sec.gov/submissions/" + extra["name"],
                                   headers=_sec_headers(), timeout=HTTP_TIMEOUT).json()
                _absorb(blk, cik)
        except Exception:
            continue    # one dead CIK must not lose the others
    if not rows:
        return rows

    try:
        cache_file.write_text(json.dumps(rows))
    except Exception:
        pass
    return rows


def _filing_title(ticker: str, row: dict) -> str:
    form = row.get("form", "")
    items = (row.get("items") or "").strip()
    if form.startswith("8-K") and items:
        labels = [_EIGHTK_ITEMS.get(code.strip(), "Item " + code.strip())
                  for code in items.split(",") if code.strip()]
        return "%s %s: %s" % (ticker, form, "; ".join(labels))
    desc = (row.get("primaryDocDescription") or "").strip()
    if desc and desc.upper() not in {form.upper(), "PRIMARY DOCUMENT"}:
        return "%s %s: %s" % (ticker, form, desc)
    return "%s %s filed with the SEC" % (ticker, form)


def _sec_articles(ticker: str, window_start: date, event_date: date) -> List[Article]:
    rows = _sec_submissions(ticker)
    if not rows:
        return []
    default_cik = _CIK_OVERRIDE[ticker.upper()][0]
    out: List[Article] = []
    for row in rows:
        cik_int = str(int(row.get("cik") or default_cik))
        form = row.get("form", "")
        if form not in _MATERIAL_FORMS:
            continue
        pub = _parse_date(row.get("filingDate"))
        if pub is None or not (window_start <= pub < event_date):
            continue
        acc = (row.get("accessionNumber") or "").replace("-", "")
        doc = row.get("primaryDocument") or ""
        if acc and doc:
            url = "https://www.sec.gov/Archives/edgar/data/%s/%s/%s" % (cik_int, acc, doc)
        elif row.get("accessionNumber"):
            # Old filings carry no primaryDocument; the filing index page is the
            # stable, resolvable address. Verified HTTP 200 on a 2000 AMZN 10-Q.
            url = "https://www.sec.gov/Archives/edgar/data/%s/%s-index.htm" % (
                cik_int, row["accessionNumber"])
        else:
            continue
        out.append(Article(
            url=url,
            title=_filing_title(ticker, row),
            published=pub.isoformat(),
            source="sec-edgar",
            snippet="SEC EDGAR filing, form %s, accession %s%s. Filing date is the "
                    "authoritative publication date." % (
                        form, row.get("accessionNumber", ""),
                        (", period " + row["reportDate"]) if row.get("reportDate") else ""),
        ))
    return out


# --------------------------------------------------------------------------
# Tier 3: curated seed  (hand-verified real articles, mostly pre-2017)
# --------------------------------------------------------------------------
#
# Every entry below was fetched and its publication date read off the page.
# `event_dates` lists the event dates this article is a legitimate catalyst for;
# the leakage filter is still applied on top, so a curated entry cannot bypass
# the date guard. Sourced as "curated" so it can be excluded from any headline
# metric. NOTHING in this list is invented -- if a URL could not be verified it
# is not here.

CURATED_SEED: List[dict] = [
    {
        "ticker": "NVDA",
        "event_dates": ["2018-11-19", "2018-11-20", "2018-11-21", "2018-11-23"],
        "url": "https://www.fool.com/investing/2018/11/16/nvidias-earnings-were-solid-but-stock-plunges-17-o.aspx",
        "title": 'NVIDIA\'s Earnings Were Solid, but Stock Plunges 17% on Weak Outlook Due to "Crypto Hangover"',
        "published": "2018-11-16",
        "source_name": "fool.com",
        "snippet": "Contemporaneous coverage of the Q3 FY19 guidance cut and channel "
                   "inventory glut that opened the November 2018 collapse.",
    },
    {
        "ticker": "NVDA",
        "event_dates": ["2018-11-19", "2018-11-20", "2018-11-21", "2018-11-23"],
        "url": "https://www.theregister.com/2018/11/16/nvidia_q3_2019/",
        "title": "Nvidia's Q3 2019 results: crypto hangover hits gaming GPU sales",
        "published": "2018-11-16",
        "source_name": "theregister.com",
        "snippet": "Trade-press coverage of the same guidance cut, from a publisher "
                   "whose archive is still resolvable.",
    },
]



def _curated_articles(ticker: str, event_date: date) -> List[Article]:
    key = event_date.isoformat()
    out: List[Article] = []
    for row in CURATED_SEED:
        if row["ticker"].upper() != ticker.upper():
            continue
        if key not in row["event_dates"]:
            continue
        out.append(Article(
            url=row["url"], title=row["title"], published=row["published"],
            source="curated",
            snippet=("[curated seed; publisher %s] " % row.get("source_name", "?"))
                    + row.get("snippet", "")))
    return out


# --------------------------------------------------------------------------
# Ranking + de-duplication
# --------------------------------------------------------------------------

_PUNCT = re.compile(r"[^a-z0-9 ]+")


def _title_key(title: str) -> str:
    t = _PUNCT.sub(" ", title.lower())
    return " ".join(t.split())[:90]


def _rank(article: Article) -> tuple:
    """Sort key: authoritative first, then reputable, then most recent."""
    dom = _domain_of(article.url)
    if article.source == "sec-edgar":
        tier = 0
    elif article.source == "curated":
        tier = 0
    elif dom in _TIER1:
        tier = 1
    elif dom in _TIER2:
        tier = 2
    else:
        tier = 3
    pub = _parse_date(article.published) or date(1900, 1, 1)
    return (tier, -pub.toordinal())


def _dedupe(articles: Sequence[Article]) -> List[Article]:
    seen_url, seen_title, out = set(), set(), []
    for art in articles:
        u = art.url.split("?")[0].rstrip("/").lower()
        t = _title_key(art.title)
        if u in seen_url or (t and t in seen_title):
            continue
        seen_url.add(u)
        if t:
            seen_title.add(t)
        out.append(art)
    return out


# --------------------------------------------------------------------------
# Event coercion (accepts an Event, a dict, or a JSON row from the ledger)
# --------------------------------------------------------------------------

_EVENT_HAS_TIER = "tier" in getattr(Event, "__dataclass_fields__", {})


def _as_event(event) -> Event:
    if isinstance(event, Event):
        return event
    if isinstance(event, dict):
        return Event(
            ticker=str(event.get("ticker", "")).upper(),
            date=str(event.get("date", "")),
            move_pct=float(event.get("move_pct", 0.0) or 0.0),
            direction=str(event.get("direction", "")) or (
                "up" if float(event.get("move_pct", 0.0) or 0.0) >= 0 else "down"),
            window_days=int(event.get("window_days", 5) or 5),
            headline=str(event.get("headline", "") or ""),
            **({"tier": str(event.get("tier", "major") or "major")} if _EVENT_HAS_TIER else {}),
            famous=bool(event.get("famous", False)),
        )
    raise TypeError("harvest() expects an Event or a dict, got %r" % type(event))


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def corpus_path(event):
    """data/corpus/{TICKER}_{YYYY-MM-DD}.json for this event."""
    ev = _as_event(event)
    return CORPUS_DIR / ("%s_%s.json" % (ev.ticker.upper(), ev.date))


def harvest(event, lookback_days: int = DEFAULT_LOOKBACK_DAYS,
            force: bool = False, max_articles: int = MAX_ARTICLES_PER_EVENT,
            write: bool = True, cutoff: str = "event_date") -> List[Article]:
    """Articles published STRICTLY BEFORE ``event.date``, within ``lookback_days``.

    ``cutoff="event_date"`` (default, per CONTRACT) admits articles up to but not
    including the event date. ``cutoff="window_start"`` is the paranoid setting:
    nothing published after the jump window OPENS, so no admitted article has
    seen any part of the move. See ``CUTOFF_MODES``.

    Cached: if a corpus file already exists for this event it is returned as-is
    and no network call is made. Pass ``force=True`` to re-fetch.

    Never raises on network failure -- a dead provider degrades to fewer
    articles, and the per-provider counts land in the corpus file.
    """
    ev = _as_event(event)
    if cutoff not in CUTOFF_MODES:
        raise ValueError("cutoff must be one of %r, got %r" % (CUTOFF_MODES, cutoff))
    path = corpus_path(ev)

    if path.exists() and not force:
        cached = load_corpus(ev)
        if cached is not None:
            return cached

    event_date = _parse_date(ev.date)
    if event_date is None:
        raise ValueError("event.date is not an ISO date: %r" % (ev.date,))
    lookback_days = max(1, int(lookback_days))
    if (event_date <= _parse_date(GDELT_COVERAGE_START)
            and lookback_days == DEFAULT_LOOKBACK_DAYS):
        lookback_days = PRE_GDELT_LOOKBACK_DAYS   # SEC-only era; quarterly cadence
    window_start = event_date - timedelta(days=lookback_days)
    # The jump window itself runs (event_date - window_days, event_date].
    jump_window_start = event_date - timedelta(days=int(ev.window_days or WINDOW_DAYS))
    cutoff_date = event_date if cutoff == "event_date" else jump_window_start

    raw: List[Article] = []
    provider_raw: Dict[str, int] = {}

    for name, fn in (
        ("curated", lambda: _curated_articles(ev.ticker, event_date)),
        ("sec", lambda: _sec_articles(ev.ticker, window_start, cutoff_date)),
        ("gdelt", lambda: _gdelt_articles(ev.ticker, window_start, cutoff_date)),
    ):
        try:
            got = fn() or []
        except Exception:
            got = []
        provider_raw[name] = len(got)
        raw.extend(got)

    # ---- THE LEAKAGE FILTER -------------------------------------------
    rejects = {"after_event": 0, "too_old": 0, "undated": 0,
               "blocked_domain": 0, "no_title": 0}
    kept: List[Article] = []
    for art in raw:
        reason = _passes_leak_filter(art, event_date, window_start, cutoff_date)
        if reason:
            rejects[reason] = rejects.get(reason, 0) + 1
        else:
            kept.append(art)
    # -------------------------------------------------------------------

    kept = _dedupe(kept)
    kept.sort(key=_rank)
    kept = kept[:max_articles]

    if write:
        _write_corpus(ev, kept, lookback_days, window_start, cutoff_date,
                      provider_raw, rejects, cutoff)
    return kept


def _write_corpus(ev: Event, articles: Sequence[Article], lookback_days: int,
                  window_start: date, cutoff_date: date,
                  provider_raw: Dict[str, int], rejects: Dict[str, int],
                  cutoff: str = "event_date") -> None:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    kept_by_source: Dict[str, int] = {}
    for a in articles:
        bucket = "sec-edgar" if a.source == "sec-edgar" else (
            "curated" if a.source == "curated" else "news")
        kept_by_source[bucket] = kept_by_source.get(bucket, 0) + 1
    doc = {
        "ticker": ev.ticker.upper(),
        "event_date": ev.date,
        "move_pct": ev.move_pct,
        "direction": ev.direction,
        "lookback_days": lookback_days,
        "window": {"start": window_start.isoformat(),
                   "end_exclusive": cutoff_date.isoformat()},
        "cutoff_mode": cutoff,
        "harvested_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "leakage_rule": "published >= window.start AND published < window.end_exclusive "
                        "(STRICTLY before, never <=); undated articles rejected",
        "gdelt_status": gdelt_status(),
        "provider_raw_counts": provider_raw,
        "leakage_filter_rejects": rejects,
        "kept_by_source": kept_by_source,
        "n_articles": len(articles),
        "articles": [a.to_dict() for a in articles],
    }
    corpus_path(ev).write_text(json.dumps(doc, indent=2))


def load_corpus(event) -> Optional[List[Article]]:
    """Read a previously-harvested corpus file. None if it does not exist.

    The leakage filter is RE-APPLIED on load, so a corpus file hand-edited or
    written by an older, buggier version of this module still cannot leak.
    """
    ev = _as_event(event)
    path = corpus_path(ev)
    if not path.exists():
        return None
    try:
        doc = json.loads(path.read_text())
    except Exception:
        return None
    event_date = _parse_date(ev.date)
    lookback = int(doc.get("lookback_days", DEFAULT_LOOKBACK_DAYS) or DEFAULT_LOOKBACK_DAYS)
    window = doc.get("window", {}) or {}
    window_start = _parse_date(window.get("start")) or (
        event_date - timedelta(days=lookback))
    # Honour the cutoff the file was written under, but never one LOOSER than
    # the event date -- a hand-edited file cannot widen its own guard.
    stored_cutoff = _parse_date(window.get("end_exclusive"))
    cutoff_date = event_date
    if stored_cutoff is not None and event_date is not None:
        cutoff_date = min(stored_cutoff, event_date)
    out: List[Article] = []
    for row in doc.get("articles", []) or []:
        art = Article(url=row.get("url", ""), title=row.get("title", ""),
                      published=row.get("published", ""), source=row.get("source", ""),
                      snippet=row.get("snippet", ""))
        if event_date is not None and _passes_leak_filter(
                art, event_date, window_start, cutoff_date):
            continue          # belt and braces: never hand back a leaky article
        out.append(art)
    return out


def _is_incomplete(ev: Event) -> bool:
    """True if this event's corpus file was written with the news tier missing.

    Without this, an event harvested while the GDELT breaker was tripped gets a
    cache file recording zero news and is never retried -- a transient rate
    limit would silently become a permanent hole in the corpus. Events outside
    GDELT's coverage window are never "incomplete": SEC is all they can ever get.
    """
    path = corpus_path(ev)
    if not path.exists():
        return False
    try:
        doc = json.loads(path.read_text())
    except Exception:
        return True
    ev_date = _parse_date(ev.date)
    if ev_date is None or ev_date <= _parse_date(GDELT_COVERAGE_START):
        return False
    if (doc.get("gdelt_status") or {}).get("disabled"):
        return True
    return int((doc.get("provider_raw_counts") or {}).get("gdelt", 0)) == 0


def _load_ledger() -> List[Event]:
    if not EVENTS_PATH.exists():
        return []
    events: List[Event] = []
    for line in EVENTS_PATH.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(_as_event(json.loads(line)))
        except Exception:
            continue
    return events


def build_corpus(events: Optional[Iterable] = None, limit: Optional[int] = None,
                 lookback_days: int = DEFAULT_LOOKBACK_DAYS,
                 force: bool = False, verbose: bool = True,
                 cutoff: str = "event_date", retry_incomplete: bool = True,
                 max_seconds: Optional[float] = None) -> dict:
    """Harvest every event and write data/corpus/{TICKER}_{DATE}.json.

    ``events=None`` loads LANE-EVENTS' ledger at ``data/events.jsonl``.
    Events that already have a corpus file are SKIPPED (no re-fetch) unless
    ``force=True``. Returns a summary dict; CONTRACT.md types it ``-> None``,
    and callers that ignore the return value are unaffected.
    """
    evs = [_as_event(e) for e in (events if events is not None else _load_ledger())]
    if limit is not None:
        evs = evs[: int(limit)]

    summary = {"n_events": len(evs), "harvested": 0, "cached": 0, "empty": 0,
               "retried": 0, "remaining": 0, "n_articles": 0, "per_event": []}
    started = time.monotonic()
    for i, ev in enumerate(evs, 1):
        if max_seconds is not None and time.monotonic() - started > max_seconds:
            summary["remaining"] = len(evs) - i + 1
            if verbose:
                print("  budget reached; %d events left (re-run to resume)"
                      % summary["remaining"])
            break
        retry = retry_incomplete and not force and _is_incomplete(ev)
        was_cached = corpus_path(ev).exists() and not force and not retry
        if retry:
            summary["retried"] += 1
        try:
            arts = harvest(ev, lookback_days=lookback_days,
                           force=force or retry, cutoff=cutoff)
        except Exception as exc:
            if verbose:
                print("  [%d/%d] %s %s FAILED: %s" % (i, len(evs), ev.ticker, ev.date, exc))
            continue
        summary["cached" if was_cached else "harvested"] += 1
        summary["n_articles"] += len(arts)
        if not arts:
            summary["empty"] += 1
        summary["per_event"].append(
            {"ticker": ev.ticker, "date": ev.date, "n_articles": len(arts),
             "cached": was_cached})
        if verbose:
            print("  [%d/%d] %s %s -> %d articles%s" % (
                i, len(evs), ev.ticker, ev.date, len(arts), " (cached)" if was_cached else ""))
    return summary


def corpus_stats() -> dict:
    """Coverage summary over everything already on disk. No network."""
    files = sorted(CORPUS_DIR.glob("*_*.json"))
    per_ticker: Dict[str, dict] = {}
    total_articles = 0
    empty = 0
    for f in files:
        try:
            doc = json.loads(f.read_text())
        except Exception:
            continue
        tk = doc.get("ticker", "?")
        row = per_ticker.setdefault(tk, {"n_events": 0, "n_articles": 0, "empty": 0})
        row["n_events"] += 1
        row["n_articles"] += int(doc.get("n_articles", 0))
        total_articles += int(doc.get("n_articles", 0))
        if not doc.get("n_articles"):
            row["empty"] += 1
            empty += 1
    return {"n_corpus_files": len(files), "n_articles": total_articles,
            "n_empty_events": empty, "per_ticker": per_ticker,
            "universe_missing": [t for t in UNIVERSE if t not in per_ticker]}


def corpus_report() -> str:
    """One-screen text summary of the corpus on disk. No network."""
    st = corpus_stats()
    lines = ["rulial-markets news corpus",
             "  files: %d   articles: %d   events with zero articles: %d"
             % (st["n_corpus_files"], st["n_articles"], st["n_empty_events"])]
    for tk in sorted(st["per_ticker"]):
        row = st["per_ticker"][tk]
        lines.append("  %-6s events=%-4d articles=%-5d empty=%d"
                     % (tk, row["n_events"], row["n_articles"], row["empty"]))
    if st["universe_missing"]:
        lines.append("  no corpus at all: " + ", ".join(st["universe_missing"]))
    lines.append("  leakage rule: published STRICTLY before the event date; "
                 "undated rejected; price-aggregator domains blocked")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser(description="Build the rulial-markets news corpus.")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--lookback", type=int, default=DEFAULT_LOOKBACK_DAYS)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--max-seconds", type=float, default=None,
                    help="stop after N seconds; re-run to resume (the corpus is resumable)")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()
    if args.stats:
        print(corpus_report())
        print()
        print(json.dumps(corpus_stats(), indent=2))
    else:
        out = build_corpus(limit=args.limit, lookback_days=args.lookback,
                           force=args.force, max_seconds=args.max_seconds)
        out.pop("per_event", None)
        print(json.dumps(out, indent=2))
        print()
        print(corpus_report())
