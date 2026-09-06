"use client";

import type { Backtest, BacktestEvent } from "@/lib/types";
import { Empty } from "./Panel";
import { PitHistogram } from "./PitHistogram";

export function BacktestPanel({ bt, ticker }: { bt: Backtest | null; ticker: string }) {
  if (!bt) return <div className="label py-8 text-center">loading walk-forward…</div>;

  if (bt.n_tests === 0) {
    return (
      <Empty>
        <div className="num text-2xl text-[var(--color-ink-dim)]">n_tests = 0</div>
        <p className="mt-3 max-w-[52ch] text-sm leading-relaxed">
          <span className="text-[var(--color-ink-dim)]">{ticker}</span> produced no qualifying event
          in the 2020+ test window at the frozen threshold, so there is nothing to walk forward and
          nothing to calibrate. We show the empty result rather than borrowing another ticker&rsquo;s
          number.
        </p>
      </Empty>
    );
  }

  const lift = bt.mean_crps_lift;
  const worst = [...bt.per_event].sort((a, b) => a.crps_lift - b.crps_lift)[0];
  const best = [...bt.per_event].sort((a, b) => b.crps_lift - a.crps_lift)[0];

  return (
    <div className="grid gap-7">
      <div className="grid gap-[1px] bg-[var(--color-rule)] sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Events scored" value={String(bt.n_tests)} />
        <Stat
          label="Mean CRPS lift"
          value={`${lift >= 0 ? "+" : "−"}${(Math.abs(lift) * 100).toFixed(1)}%`}
          color={lift > 0 ? "var(--color-phosphor)" : "var(--color-down)"}
        />
        {bt.mean_crps_lift_demeaned !== undefined ? (
          <Stat
            label="Mean lift, demeaned"
            value={`${bt.mean_crps_lift_demeaned >= 0 ? "+" : "−"}${(Math.abs(bt.mean_crps_lift_demeaned) * 100).toFixed(1)}%`}
            color={bt.mean_crps_lift_demeaned > 0 ? "var(--color-phosphor)" : "var(--color-down)"}
            note="drift removed"
          />
        ) : (
          <Stat label="Mean lift, demeaned" value="not reported" color="var(--color-ink-faint)"
            note="ask LANE-EVAL for the drift-decomposed field" />
        )}
        <Stat label="Calibration" value={bt.calibration_ok ? "PASS" : "not established"}
          color={bt.calibration_ok ? "var(--color-phosphor)" : "var(--color-ink-faint)"} />
      </div>

      <PitHistogram counts={bt.pit_histogram} n={bt.n_tests} calibrationOk={bt.calibration_ok} />

      {/* per-event lift strip — a diverging bar chart around a zero line */}
      <div>
        <div className="label mb-3">Per-event lift · every scored event, none hidden</div>
        <PerEventStrip events={bt.per_event} />
        <div className="mt-3 flex flex-wrap gap-x-8 gap-y-1 text-sm text-[var(--color-ink-faint)]">
          <span>best: <span className="num text-[var(--color-phosphor)]">{best.date} {(best.crps_lift * 100).toFixed(1)}%</span></span>
          <span>worst: <span className="num text-[var(--color-down)]">{worst.date} {(worst.crps_lift * 100).toFixed(1)}%</span></span>
          <span className="ml-auto">above the line beat the null · the spread is the story, not the mean</span>
        </div>
      </div>
    </div>
  );
}

function PerEventStrip({ events }: { events: BacktestEvent[] }) {
  const W = 1000, H = 170, PAD = 26;
  const cap = Math.max(0.25, ...events.map((e) => Math.abs(e.crps_lift)));
  const mid = H / 2;
  const bw = (W - PAD * 2) / Math.max(1, events.length);
  const scale = (v: number) => (v / cap) * (H / 2 - 14);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
      aria-label="CRPS lift for each scored test event">
      <line x1={PAD} x2={W - PAD} y1={mid} y2={mid} stroke="var(--color-rule-bright)" strokeWidth={1} />
      <text x={PAD - 4} y={mid - 6} className="num" fontSize="11" fill="var(--color-ink-faint)"
        textAnchor="start">0</text>
      <text x={PAD - 4} y={20} className="num" fontSize="11" fill="var(--color-phosphor)"
        textAnchor="start">+{(cap * 100).toFixed(0)}%</text>
      <text x={PAD - 4} y={H - 8} className="num" fontSize="11" fill="var(--color-down)"
        textAnchor="start">−{(cap * 100).toFixed(0)}%</text>

      {events.map((e, i) => {
        const h = Math.abs(scale(e.crps_lift));
        const up = e.crps_lift >= 0;
        const x = PAD + i * bw + Math.min(3, bw * 0.12);
        const w = Math.max(2, bw - Math.min(6, bw * 0.24));
        return (
          <g key={i}>
            <title>{`${e.date}  lift ${(e.crps_lift * 100).toFixed(1)}%  z ${e.z_score.toFixed(2)}`}</title>
            <rect
              x={x} y={up ? mid - h : mid}
              width={w} height={Math.max(2, h)}
              fill={up ? "var(--color-phosphor)" : "var(--color-down)"}
              opacity={0.78}
              className="bloom" style={{ animationDelay: `${i * 28}ms` }}
            />
          </g>
        );
      })}
    </svg>
  );
}

function Stat({ label, value, color, note }: { label: string; value: string; color?: string; note?: string }) {
  return (
    <div className="bg-[var(--color-panel)] px-5 py-5">
      <div className="label">{label}</div>
      <div className="num mt-2 text-[1.9rem] leading-none" style={{ color: color ?? "var(--color-ink)" }}>
        {value}
      </div>
      {note && <div className="mt-2 text-[0.72rem] text-[var(--color-ink-faint)]">{note}</div>}
    </div>
  );
}
