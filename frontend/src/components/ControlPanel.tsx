"use client";

import type { TickerInfo } from "@/lib/types";
import { PRESETS, type Preset } from "./presets";
import { TRAIN_END } from "@/lib/types";

/**
 * Forward path controls. Props, state and the four presets are unchanged —
 * this is the Amex reskin of an already-working panel (DESIGN_AMEX §7).
 */
export function ControlPanel({
  tickers, ticker, setTicker, asOf, setAsOf, text, setText,
  horizon, setHorizon, nPaths, setNPaths, onRun, running,
}: {
  tickers: TickerInfo[];
  ticker: string; setTicker: (v: string) => void;
  asOf: string; setAsOf: (v: string) => void;
  text: string; setText: (v: string) => void;
  horizon: number; setHorizon: (v: number) => void;
  nPaths: number; setNPaths: (v: number) => void;
  onRun: () => void;
  running: boolean;
}) {
  const info = tickers.find((t) => t.symbol === ticker);
  const past = asOf <= TRAIN_END;

  const apply = (p: Preset) => {
    setTicker(p.ticker);
    setAsOf(p.as_of);
    setText(p.text);
  };

  const toneColor: Record<Preset["tone"], string> = {
    down: "var(--color-down)",
    up: "var(--color-up)",
    shock: "var(--color-notice)",
    grind: "var(--color-null)",
  };

  return (
    <div className="grid gap-8">
      {/* presets first — the stage path */}
      <div>
        <div className="label mb-3">One-click scenarios</div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {PRESETS.map((p, i) => {
            const active = p.ticker === ticker && p.as_of === asOf && p.text === text;
            return (
              <button
                key={p.key}
                onClick={() => apply(p)}
                aria-pressed={active}
                className="group relative overflow-hidden rounded-lg border bg-white px-5 py-4 text-left transition hover:shadow-[var(--shadow-lift)]"
                style={{
                  borderColor: active ? "var(--color-blue)" : "var(--color-rule)",
                  boxShadow: active ? "0 0 0 1px var(--color-blue)" : undefined,
                }}
              >
                <span
                  className="absolute left-0 top-0 h-full w-[4px]"
                  style={{ background: toneColor[p.tone], opacity: active ? 1 : 0.55 }}
                />
                <div className="flex items-baseline justify-between gap-2">
                  <span className="label" style={{ color: toneColor[p.tone] }}>{p.kind}</span>
                  <span className="num text-xs text-[var(--color-ink-faint)]">0{i + 1}</span>
                </div>
                <div className="num mt-2 text-lg font-semibold text-[var(--color-navy)]">
                  {p.ticker} <span className="font-normal text-[var(--color-ink-faint)]">· {p.as_of}</span>
                </div>
                <p className="mt-2 line-clamp-3 text-sm leading-snug text-[var(--color-ink-dim)]">
                  {p.text}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[220px_240px_1fr]">
        <Field label="Ticker">
          <select
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            className="w-full px-3 py-3 text-lg"
          >
            {tickers.map((t) => (
              <option key={t.symbol} value={t.symbol}>
                {t.symbol} — {t.n_events} ev
              </option>
            ))}
          </select>
          {info && (
            <div className="mt-2 text-sm text-[var(--color-ink-faint)]">
              {info.name} · {info.sector}
            </div>
          )}
        </Field>

        <Field label="As-of date">
          <input
            type="date"
            value={asOf}
            max="2026-12-31"
            onChange={(e) => setAsOf(e.target.value)}
            className="w-full px-3 py-3 text-lg"
          />
          <div
            className="mt-2 text-sm leading-snug"
            style={{ color: past ? "var(--color-blue)" : "var(--color-notice)" }}
          >
            {past
              ? "inside train window — the actual is known, so it gets scored"
              : "past the frozen boundary — forecast only, no score"}
          </div>
        </Field>

        <Field label="Event description — free text">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            placeholder="Describe the event the market is about to be handed…"
            className="w-full resize-none px-3 py-3 text-base leading-relaxed"
          />
        </Field>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-6 border-t border-[var(--color-rule)] pt-6">
        <div className="flex flex-wrap gap-8">
          <Small label="Horizon">
            <select value={horizon} onChange={(e) => setHorizon(Number(e.target.value))}
              className="px-3 py-2">
              {[1, 3, 5, 10, 21].map((h) => <option key={h} value={h}>{h}d</option>)}
            </select>
          </Small>
          <Small label="Paths">
            <select value={nPaths} onChange={(e) => setNPaths(Number(e.target.value))}
              className="px-3 py-2">
              {[500, 1000, 2000, 4000].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </Small>
        </div>

        <button
          onClick={onRun}
          disabled={running || !text.trim()}
          className="btn-primary text-base"
        >
          {running ? "Sampling…" : "Sample the ensemble"}
        </button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="label mb-2">{label}</div>
      {children}
    </div>
  );
}

function Small({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3">
      <span className="label">{label}</span>
      {children}
    </div>
  );
}
