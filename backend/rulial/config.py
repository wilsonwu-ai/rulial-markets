"""Frozen configuration. See CONTRACT.md section 1-3. No lane may edit this file."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
PRICES_DIR = DATA_DIR / "prices"
CORPUS_DIR = DATA_DIR / "corpus"
EVENTS_PATH = DATA_DIR / "events.jsonl"

# --- FROZEN: universe -------------------------------------------------------
UNIVERSE = ["NVDA", "AAPL", "MSFT", "AMZN", "TSLA", "META", "GOOGL", "JPM", "XOM", "BA"]

TICKER_NAMES = {
    "NVDA": "NVIDIA Corporation", "AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com Inc.", "TSLA": "Tesla Inc.", "META": "Meta Platforms Inc.",
    "GOOGL": "Alphabet Inc.", "JPM": "JPMorgan Chase & Co.", "XOM": "Exxon Mobil Corporation",
    "BA": "The Boeing Company",
}

# --- FROZEN: time boundary (leak guard) -------------------------------------
TRAIN_END = "2019-12-31"
TEST_START = "2020-01-01"
TEST_END = "2024-12-31"
EMBARGO_DAYS = 5
# Inception. A floor date, not a real start: each ticker's series naturally
# begins at its own IPO (META 2012-05-18, TSLA 2010-06-29). Kept as a parseable
# ISO date because data.py uses it as a lower bound via date.fromisoformat.
HISTORY_START = "1900-01-01"

# --- FROZEN: event definition -----------------------------------------------
# Two tiers over the same WINDOW_DAYS window. MAJOR is the stage narrative
# (black-swan scale moves); SIGNIFICANT widens the training corpus so every
# ticker in the universe contributes seed events. Neither may be tuned by a
# lane -- moving them silently changes every number downstream.
TIER_MAJOR = 0.25
TIER_SIGNIFICANT = 0.15
JUMP_THRESHOLD = TIER_SIGNIFICANT   # detection floor; tier is labelled per event
WINDOW_DAYS = 5

def tier_for(move_pct):
    """Classify a move. Returns 'major' | 'significant' | None."""
    a = abs(move_pct)
    if a >= TIER_MAJOR: return "major"
    if a >= TIER_SIGNIFICANT: return "significant"
    return None

# --- Forecast defaults ------------------------------------------------------
DEFAULT_HORIZON_DAYS = 5
DEFAULT_N_PATHS = 2000
NULL_VOL_LOOKBACK = 250

for _d in (DATA_DIR, PRICES_DIR, CORPUS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
