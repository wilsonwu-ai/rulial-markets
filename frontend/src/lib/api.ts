/**
 * API client for the FROZEN routes in CONTRACT.md §6.
 * Dev proxies /api/* to :8000 (see next.config.ts rewrites); in production
 * set NEXT_PUBLIC_API_BASE to the deployed backend origin.
 *
 * Every call is mode-aware. In "mock" mode nothing leaves the browser.
 * In "live" mode a failure is returned as a typed error, never swallowed —
 * the UI shows the failure AND offers the mock, rather than silently
 * pretending a dead backend produced a result.
 */

import type {
  Backtest, EventRec, ForecastRequest, ForecastResponse, Mode, TickerInfo,
} from "./types";
import {
  bakedTickers, bakedEvents, bakedForecast, bakedBacktest,
} from "./baked";
import { mockBacktest, mockEvents, mockForecast, mockTickers } from "./mock";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";
const TIMEOUT_MS = 25000;

export class ApiError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...init,
      signal: ctrl.signal,
      headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
    if (!res.ok) {
      const body = await res.text().catch(() => "");
      throw new ApiError(
        `${res.status} ${res.statusText}${body ? ` — ${body.slice(0, 180)}` : ""}`,
        res.status,
      );
    }
    return (await res.json()) as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    const msg = e instanceof Error ? e.message : String(e);
    throw new ApiError(
      msg.includes("abort") ? `backend did not answer in ${TIMEOUT_MS / 1000}s` : msg,
    );
  } finally {
    clearTimeout(timer);
  }
}

export async function probeHealth(): Promise<boolean> {
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 2500);
    const res = await fetch(`${BASE}/api/health`, { signal: ctrl.signal, cache: "no-store" });
    clearTimeout(t);
    if (!res.ok) return false;
    const j = (await res.json()) as { ok?: boolean };
    return j?.ok === true;
  } catch {
    return false;
  }
}

export const api = {
  tickers(mode: Mode): Promise<TickerInfo[]> {
    if (mode === "mock") return Promise.resolve(mockTickers());
    if (mode === "baked") return bakedTickers().then((t) => t ?? mockTickers());
    return req<TickerInfo[]>("/api/tickers");
  },

  events(mode: Mode, ticker: string): Promise<EventRec[]> {
    if (mode === "mock") return Promise.resolve(mockEvents(ticker));
    if (mode === "baked") return bakedEvents(ticker).then((e) => e ?? mockEvents(ticker));
    return req<EventRec[]>(`/api/events?ticker=${encodeURIComponent(ticker)}`);
  },

  forecast(mode: Mode, body: ForecastRequest): Promise<ForecastResponse> {
    if (mode === "mock") {
      // small delay so the loading choreography is visible on stage
      return new Promise((r) => setTimeout(() => r(mockForecast(body)), 420));
    }
    if (mode === "baked") {
      // A precomputed hit is REAL model output. A miss falls through to mock
      // rather than showing a scenario the user did not ask for.
      return bakedForecast(body).then(
        (d) => d ?? new Promise<ForecastResponse>((r) => setTimeout(() => r(mockForecast(body)), 420)),
      );
    }
    return req<ForecastResponse>("/api/forecast", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  backtest(mode: Mode, ticker: string): Promise<Backtest> {
    if (mode === "mock") return Promise.resolve(mockBacktest(ticker));
    if (mode === "baked") return bakedBacktest(ticker).then((b) => b ?? mockBacktest(ticker));
    return req<Backtest>(`/api/backtest?ticker=${encodeURIComponent(ticker)}`);
  },
};

/* ================================================================
   SOURCE-REPORTING VARIANTS
   ================================================================
   `api.*` above returns bare data, which means a precomputed MISS silently
   becomes a synthetic answer and the caller cannot tell. That is how a page
   badge reading "precomputed · real" ended up sitting above a walk-forward
   panel rendering in-browser RNG — `/data/backtest_<T>.json` does not exist
   for any ticker, so EVERY baked backtest fell through to mock without a word.
   The fallback ORDER is unchanged and no fourth source is introduced; these
   wrappers only report which of the three actually answered, so the panel can
   say so on its own face.
   ================================================================ */

export interface Sourced<T> { data: T; source: Mode }

export const apiSourced = {
  async backtest(mode: Mode, ticker: string): Promise<Sourced<Backtest>> {
    if (mode === "mock") return { data: mockBacktest(ticker), source: "mock" };
    if (mode === "baked") {
      const b = await bakedBacktest(ticker);
      return b ? { data: b, source: "baked" } : { data: mockBacktest(ticker), source: "mock" };
    }
    return { data: await req<Backtest>(`/api/backtest?ticker=${encodeURIComponent(ticker)}`), source: "live" };
  },

  async events(mode: Mode, ticker: string): Promise<Sourced<EventRec[]>> {
    if (mode === "mock") return { data: mockEvents(ticker), source: "mock" };
    if (mode === "baked") {
      const e = await bakedEvents(ticker);
      return e ? { data: e, source: "baked" } : { data: mockEvents(ticker), source: "mock" };
    }
    return { data: await req<EventRec[]>(`/api/events?ticker=${encodeURIComponent(ticker)}`), source: "live" };
  },

  async forecast(mode: Mode, body: ForecastRequest): Promise<Sourced<ForecastResponse>> {
    if (mode === "mock") {
      await new Promise((r) => setTimeout(r, 420));
      return { data: mockForecast(body), source: "mock" };
    }
    if (mode === "baked") {
      const d = await bakedForecast(body);
      if (d) return { data: d, source: "baked" };
      await new Promise((r) => setTimeout(r, 420));
      return { data: mockForecast(body), source: "mock" };
    }
    return {
      data: await req<ForecastResponse>("/api/forecast", { method: "POST", body: JSON.stringify(body) }),
      source: "live",
    };
  },
};
