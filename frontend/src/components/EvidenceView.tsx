"use client";

import { useState } from "react";
import type { Backtest, EventRec, Mode, TickerInfo } from "@/lib/types";
import { TRAIN_END } from "@/lib/types";
import { signedPct } from "@/lib/quant";
import { BacktestPanel } from "./BacktestPanel";
import { EventLedger } from "./EventLedger";
import { ScenarioPanel } from "./ScenarioPanel";
import { LeakagePanel } from "./LeakagePanel";
import { Panel } from "./Panel";
import { SourceTag } from "./SourceTag";

/**
 * STATE 4 (not one of the three, and deliberately last) — THE EVIDENCE.
 *
 * Nothing here is new and nothing here was removed. The walk-forward backtest,
 * the inverse-scenario search, the seed ledger and the full leakage disclosure
 * all kept every capability they had; they moved off the first screen, which
 * is where they were doing damage. A viewer who wants to argue with the claim
 * comes here on purpose.
 *
 * The one plain-English addition is the verdict line at the top: across every
 * scored event for this ticker, did the conditioned ensemble beat the frozen
 * baseline or not. Same number as before, stated as a sentence first.
 */
export function EvidenceView({
  mode, tickers, ticker, setTicker, asOf, setAsOf, horizon,
  events, eventsSource, bt, btSource, eventsLoading, onBranch,
}: {
  mode: Mode;
  tickers: TickerInfo[];
  ticker: string; setTicker: (v: string) => void;
  asOf: string; setAsOf: (v: string) => void;
  horizon: number;
  events: EventRec[];
  /** which of the three sources actually answered, per panel */
  eventsSource: Mode;
  bt: Backtest | null;
  btSource: Mode | null;
  eventsLoading: boolean;
  onBranch: (ticker: string, date: string, headline?: string) => void;
}) {
  const [tab, setTab] = useState<"walk" | "inverse" | "ledger" | "limits">("walk");

  const lift = bt?.mean_crps_lift;
  const verdict =
    !bt ? null
    : bt.n_tests === 0 ? "no scored events"
    : (lift ?? 0) > 0 ? "beat the simple baseline"
    : "lost to the simple baseline";

  return (
    <div className="grid gap-6 [&>*]:min-w-0">
      <header className="rise">
        <h1 className="display text-[clamp(2rem,4.4vw,3rem)]">
          Argue with it
        </h1>
        <p className="mt-4 max-w-[70ch] text-[1.125rem] leading-relaxed text-[var(--color-ink-dim)]">
          Every scored event, the search that runs the model backwards, the seed corpus, and the
          limitation we are contractually required to state. Nothing here is folded away.
        </p>
      </header>

      <div className="panel flex flex-wrap items-center gap-x-6 gap-y-4 px-5 py-4 sm:px-6">
        <div className="flex overflow-hidden rounded-full border border-[var(--color-axis)] bg-white">
          {([
            ["walk", "Walk-forward"],
            ["inverse", "Run it backwards"],
            ["ledger", "Seed corpus"],
            ["limits", "What could be wrong"],
          ] as const).map(([k, label]) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              aria-pressed={tab === k}
              className="px-3 py-2 text-[0.8125rem] font-semibold transition sm:px-5 sm:text-sm"
              style={{
                background: tab === k ? "var(--color-blue)" : "transparent",
                color: tab === k ? "#fff" : "var(--color-ink-dim)",
              }}
            >
              {label}
            </button>
          ))}
        </div>

        <label className="ml-auto flex items-center gap-3">
          <span className="label">Ticker</span>
          <select value={ticker} onChange={(e) => setTicker(e.target.value)} className="px-3 py-2">
            {tickers.map((t) => (
              <option key={t.symbol} value={t.symbol}>{t.symbol} — {t.n_events} ev</option>
            ))}
          </select>
        </label>
      </div>

      {tab === "walk" && (
        <Panel
          title={`Walk-forward — ${ticker} on the 2020+ test window`}
          right={<SourceTag source={btSource ?? mode} />}
        >
          {btSource === "mock" && mode !== "mock" && (
            <div className="callout-notice mb-7 px-6 py-5">
              <div className="label" style={{ color: "var(--color-notice)" }}>
                This panel fell back to synthetic
              </div>
              <p className="mt-2 max-w-[76ch] text-[0.9375rem] leading-relaxed text-[var(--color-ink-dim)]">
                The page is in <span className="num font-semibold">{mode}</span> mode, but no
                walk-forward result answered for {ticker} — the precomputed bundle ships no
                <span className="num"> backtest_{ticker}.json</span>. The chart below is
                in-browser synthetic and is not evidence of anything. Switch to the live backend for
                real walk-forward numbers.
              </p>
            </div>
          )}
          {/* A verdict sentence over synthetic numbers is the single most
              misleading thing this page could print, so it is gated on the
              panel's OWN source rather than the page's. */}
          {bt && bt.n_tests > 0 && btSource !== "mock" && (
            <div className="mb-7 rounded-lg border border-[var(--color-rule)] bg-[var(--color-panel-2)] px-6 py-5">
              <div className="label">Across every scored event for {ticker}</div>
              <div
                className="mt-2 text-[clamp(1.25rem,2.6vw,1.625rem)] font-bold leading-tight"
                style={{ color: (lift ?? 0) > 0 ? "var(--color-blue)" : "var(--color-navy)" }}
              >
                {ticker} {verdict}
              </div>
              <p className="mt-3 max-w-[80ch] text-[0.9375rem] leading-relaxed text-[var(--color-ink-dim)]">
                {bt.n_tests} events, mean lift{" "}
                <span className="num font-semibold">{signedPct(lift ?? 0)}</span>. The bar chart
                below is every one of them, none hidden — the spread is the finding, not the mean.
                A flat histogram is the win condition; calling the crash is not.
              </p>
            </div>
          )}
          <BacktestPanel bt={bt} ticker={ticker} />
        </Panel>
      )}

      {tab === "inverse" && (
        <Panel
          title="Run it backwards — what event would produce this probability?"
          right={<SourceTag source={mode} detail="many events give the same probability" />}
        >
          <p className="mb-7 max-w-[80ch] text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)]">
            Set a probability, and the search proposes events that would produce it. Every
            probability shown is <span className="font-semibold text-[var(--color-navy)]">computed</span> by
            running the candidate back through the forward model, never asserted by a language
            model. Where the search misses the target, it says so.
          </p>
          <ScenarioPanel ticker={ticker} asOf={asOf} horizon={horizon} mode={mode} />
        </Panel>
      )}

      {tab === "ledger" && (
        <Panel
          title={`Seed corpus — ${ticker} train events (≤ ${TRAIN_END})`}
          right={<SourceTag source={eventsSource} detail="|Δ| ≥ 15% over 5 sessions · frozen" />}
        >
          <p className="mb-5 max-w-[80ch] text-[0.9375rem] leading-relaxed text-[var(--color-ink-dim)]">
            These are the analogs the generator is allowed to draw on. Click a row to branch from
            it.
            {eventsSource === "mock" && mode !== "mock" && (
              <span className="mt-2 block font-semibold" style={{ color: "var(--color-notice)" }}>
                No real ledger answered for {ticker} in {mode} mode, so these rows are synthetic
                placeholders rather than detected events.
              </span>
            )}
          </p>
          <EventLedger
            events={events} ticker={ticker} loading={eventsLoading}
            onPick={(e) => { setAsOf(e.date); onBranch(ticker, e.date, e.headline); }}
          />
        </Panel>
      )}

      {tab === "limits" && (
        <LeakagePanel
          famous={bt?.n_famous}
          obscure={bt?.n_obscure}
          liftFamous={bt?.mean_crps_lift_famous}
          liftObscure={bt?.mean_crps_lift_obscure}
          // The split is only a measurement when the backtest itself is one.
          // In mock mode these come from an in-browser RNG and must never be
          // rendered as a result. QA caught this shipping unlabelled.
          synthetic={mode === "mock"}
        />
      )}
    </div>
  );
}
