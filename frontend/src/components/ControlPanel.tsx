"use client";

import type { TickerInfo } from "@/lib/types";
import { PRESETS, type Preset } from "./presets";
import { TRAIN_END } from "@/lib/types";

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
    shock: "var(--color-hazard)",
    grind: "var(--color-null)",
  };

  return (
    <div className="grid gap-6">
      {/* presets first — the stage path */}
      <div>
        <div className="label mb-3">One-click scenarios</div>
        <div className="grid gap-[1px] bg-[var(--color-rule)] sm:grid-cols-2 xl:grid-cols-4">
          {PRESETS.map((p, i) => {
            const active = p.ticker === ticker && p.as_of === asOf && p.text === text;
            return (
              <button
                key={p.key}
                onClick={() => apply(p)}
                className="group relative bg-[var(--color-panel)] px-4 py-4 text-left transition hover:bg-[var(--color-panel-2)]"
                style={{ boxShadow: active ? `inset 0 0 0 1px ${toneColor[p.tone]}` : undefined }}
              >
                <span className="absolute left-0 top-0 h-full w-[3px] transition-opacity"
                  style={{ background: toneColor[p.tone], opacity: active ? 1 : 0.35 }} />
                <div className="flex items-baseline justify-between gap-2">
                  <span className="label" style={{ color: toneColor[p.tone] }}>{p.kind}</span>
                  <span className="num text-[0.7rem] text-[var(--color-ink-faint)]">0{i + 1}</span>
                </div>
                <div className="num mt-2 text-lg text-[var(--color-ink)]">
                  {p.ticker} <span className="text-[var(--color-ink-faint)]">· {p.as_of}</span>
                </div>
                <p className="mt-2 line-clamp-2 text-[0.82rem] leading-snug text-[var(--color-ink-faint)]">
                  {p.text}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[220px_180px_1fr]">
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
            <div className="mt-2 text-xs text-[var(--color-ink-faint)]">
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
          <div className="mt-2 text-xs" style={{ color: past ? "var(--color-phosphor)" : "var(--color-hazard)" }}>
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
            className="w-full resize-none px-3 py-3 text-[0.98rem] leading-relaxed"
          />
        </Field>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-5 border-t border-[var(--color-rule)] pt-5">
        <div className="flex flex-wrap gap-6">
          <Small label="Horizon">
            <select value={horizon} onChange={(e) => setHorizon(Number(e.target.value))}
              className="px-2 py-2">
              {[1, 3, 5, 10, 21].map((h) => <option key={h} value={h}>{h}d</option>)}
            </select>
          </Small>
          <Small label="Paths">
            <select value={nPaths} onChange={(e) => setNPaths(Number(e.target.value))}
              className="px-2 py-2">
              {[500, 1000, 2000, 4000].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </Small>
        </div>

        <button
          onClick={onRun}
          disabled={running || !text.trim()}
          className="group relative overflow-hidden border border-[var(--color-phosphor)] px-9 py-4 transition disabled:cursor-not-allowed disabled:opacity-35"
          style={{ background: "rgba(55,230,207,0.09)" }}
        >
          <span className="num relative z-10 text-lg tracking-[0.18em] text-[var(--color-phosphor)]">
            {running ? "SAMPLING…" : "SAMPLE THE ENSEMBLE"}
          </span>
          <span className="absolute inset-0 -translate-x-full bg-[var(--color-phosphor)] opacity-10 transition-transform duration-500 group-hover:translate-x-0" />
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
