"""Frozen shared types. See CONTRACT.md section 5. No lane may edit this file."""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


def _d(o):
    return asdict(o)


@dataclass
class Article:
    url: str
    title: str
    published: str
    source: str
    snippet: str = ""
    to_dict = _d


@dataclass
class Event:
    ticker: str
    date: str
    move_pct: float
    direction: str
    window_days: int = 5
    headline: str = ""
    articles: List[Article] = field(default_factory=list)
    tier: str = "major"           # "major" (>=25%) | "significant" (>=15%)
    famous: bool = False          # salience flag -- see CONTRACT.md s8.2
    to_dict = _d


@dataclass
class ForecastRequest:
    ticker: str
    event_text: str
    as_of_date: str
    horizon_days: int = 5
    n_paths: int = 2000
    to_dict = _d


@dataclass
class Ensemble:
    ticker: str
    as_of_date: str
    horizon_days: int
    paths: List[float]
    quantiles: Dict[str, float]
    mean: float
    std: float
    analogs: List[Event] = field(default_factory=list)
    narrative: str = ""
    to_dict = _d


@dataclass
class Score:
    crps: float
    crps_null: float
    crps_lift: float
    pit: float
    actual_return: float
    z_score: float
    to_dict = _d
