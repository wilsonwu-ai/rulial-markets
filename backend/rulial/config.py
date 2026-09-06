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
HISTORY_START = "2010-01-01"

# --- FROZEN: event definition -----------------------------------------------
JUMP_THRESHOLD = 0.25
WINDOW_DAYS = 5

# --- Forecast defaults ------------------------------------------------------
DEFAULT_HORIZON_DAYS = 5
DEFAULT_N_PATHS = 2000
NULL_VOL_LOOKBACK = 250

for _d in (DATA_DIR, PRICES_DIR, CORPUS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
