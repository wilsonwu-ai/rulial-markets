/**
 * TypeScript mirrors of the FROZEN dataclasses in CONTRACT.md §5.
 * These are read-only shapes — do not "improve" them here.
 * Optional fields are extras a backend lane MAY add; the UI renders
 * them when present and never requires them.
 */

export const UNIVERSE = [
  "NVDA", "AAPL", "MSFT", "AMZN", "TSLA",
  "META", "GOOGL", "JPM", "XOM", "BA",
] as const;

export const TRAIN_END = "2019-12-31";
export const TEST_START = "2020-01-01";
/** CONTRACT §3 is now two-tier: 0.15 is the detection floor, 0.25 is the
 *  black-swan / stage-narrative tier. Every Event carries which one it is. */
export const TIER_MAJOR = 0.25;
export const TIER_SIGNIFICANT = 0.15;
export const JUMP_THRESHOLD = TIER_SIGNIFICANT;
export const WINDOW_DAYS = 5;

export interface Article {
  url: string;
  title: string;
  published: string;
  source: string;
  snippet?: string;
}

export interface EventRec {
  ticker: string;
  date: string;
  move_pct: number;
  direction: "up" | "down" | string;
  window_days: number;
  headline?: string;
  articles?: Article[];
  /** "major" (>=25%) | "significant" (>=15%), or the raw threshold as a number */
  tier?: string | number;
}

export interface TickerInfo {
  symbol: string;
  name: string;
  sector: string;
  has_data: boolean;
  n_events: number;
}

export interface ForecastRequest {
  ticker: string;
  event_text: string;
  as_of_date: string;
  horizon_days?: number;
  n_paths?: number;
}

export interface Quantiles {
  p5: number; p25: number; p50: number; p75: number; p95: number;
  [k: string]: number;
}

/**
 * CONTRACT §5 declares `paths: list  # list[float] simulated cumulative returns`.
 * Read literally that is a flat list of TERMINAL cumulative returns. Some
 * generators emit a full path matrix instead (list[list[float]]). The UI
 * accepts BOTH and says on screen which one it got.
 */
export type PathsPayload = number[] | number[][];

export interface Ensemble {
  ticker: string;
  as_of_date: string;
  horizon_days: number;
  paths: PathsPayload;
  quantiles: Quantiles;
  mean: number;
  std: number;
  analogs?: EventRec[];
  narrative?: string;
}

export interface Score {
  crps: number;
  crps_null: number;
  crps_lift: number;
  pit: number;
  actual_return: number;
  z_score: number;
  /** optional extras (LANE-EVAL may add; see recon: drift-decomposed lift) */
  crps_lift_demeaned?: number;
  salience?: "famous" | "obscure" | string;
}

export interface ForecastResponse {
  ensemble: Ensemble;
  score: Score | null;
}

export interface BacktestEvent {
  date: string;
  crps: number;
  crps_null: number;
  crps_lift: number;
  z_score: number;
  salience?: string;
}

export interface Backtest {
  n_tests: number;
  mean_crps_lift: number;
  pit_histogram: number[];
  calibration_ok: boolean;
  per_event: BacktestEvent[];
  /** optional extras */
  mean_crps_lift_demeaned?: number;
  n_famous?: number;
  n_obscure?: number;
  mean_crps_lift_famous?: number;
  mean_crps_lift_obscure?: number;
}

export type Mode = "live" | "mock";
