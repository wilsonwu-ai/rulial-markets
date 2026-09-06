"use client";

import type { Backtest, BacktestEvent } from "@/lib/types";
import { signedPct } from "@/lib/quant";
import { Empty } from "./Panel";
import { PitHistogram } from "./PitHistogram";

export function BacktestPanel({ bt, ticker }: { bt: Backtest | null; ticker: string }) {
  if (!bt) return <div className="label-title py-10 text-center" style={{ color: "var(--color-ink-faint)" }}>loading walk-forward…</div>;

  if (bt.n_tests === 0) {
    return (
      <Empty>
        <div className="figure text-3xl">n_tests = 0</div>
        <p className="mt-3 max-w-[54ch] text-base leading-relaxed">
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
      <div className="grid gap-[1px] overflow-hidden rounded-lg border border-[var(--color-rule)] bg-[var(--color-rule)] sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Events scored" value={String(bt.n_tests)} />
        <Stat
          label="Mean CRPS lift"
          value={signedPct(lift)}
          color={lift > 0 ? "var(--color-blue)" : "var(--color-neg)"}
        />
        {bt.mean_crps_lift_demeaned !== undefined ? (
          <Stat
            label="Mean lift, demeaned"
            value={signedPct(bt.mean_crps_lift_demeaned)}
            color={bt.mean_crps_lift_demeaned > 0 ? "var(--color-blue)" : "var(--color-neg)"}
            note="drift removed"
          />
        ) : (
          <Stat label="Mean lift, demeaned" value="not reported" color="var(--color-ink-faint)"
            note="ask LANE-EVAL for the drift-decomposed field" />
        )}
        <Stat label="Calibration" value={bt.calibration_ok ? "PASS" : "not established"}
          color={bt.calibration_ok ? "var(--color-blue)" : "var(--color-ink-faint)"} />
      </div>

      <PitHistogram counts={bt.pit_histogram} n={bt.n_tests} calibrationOk={bt.calibration_ok} />

      {/* per-event lift strip — a diverging bar chart around a zero line */}
      <div>
        <div className="label mb-3">Per-event lift · every scored event, none hidden</div>
        <PerEventStrip events={bt.per_event} />
        <div className="mt-4 flex flex-wrap gap-x-8 gap-y-1 text-sm text-[var(--color-ink-faint)]">
          <span>best: <span className="num font-semibold text-[var(--color-blue)]">{best.date} {(best.crps_lift * 100).toFixed(1)}%</span></span>
          <span>worst: <span className="num font-semibold text-[var(--color-neg)]">{worst.date} {(worst.crps_lift * 100).toFixed(1)}%</span></span>
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
  // One stagger budget for every chart in the app: the whole assembly
  // finishes inside 350ms regardless of how many marks there are. A chart
  // still building itself while the presenter is talking about it is a
  // liability, and motion on this build is deliberately dialled down.
  const stagger = 350 / Math.max(1, events.length);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
      aria-label="CRPS lift for each scored test event">
      <line x1={PAD} x2={W - PAD} y1={mid} y2={mid} stroke="var(--color-axis)" strokeWidth={2} />
      <text x={PAD - 4} y={mid - 8} className="num" fontSize="13" fill="var(--color-ink-faint)"
        textAnchor="start">0</text>
      <text x={PAD - 4} y={20} className="num" fontSize="13" fill="var(--color-blue)"
        textAnchor="start">+{(cap * 100).toFixed(0)}%</text>
      <text x={PAD - 4} y={H - 8} className="num" fontSize="13" fill="var(--color-neg)"
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
              fill={up ? "var(--color-blue)" : "var(--color-neg)"}
              opacity={0.85}
              className="bloom" style={{ animationDelay: `${i * stagger}ms` }}
            />
          </g>
        );
      })}
    </svg>
  );
}

function Stat({ label, value, color, note }: { label: string; value: string; color?: string; note?: string }) {
  return (
    <div className="bg-[var(--color-panel)] px-6 py-6">
      <div className="label">{label}</div>
      <div className="figure mt-2 text-[2.25rem]" style={{ color: color ?? "var(--color-navy)" }}>
        {value}
      </div>
      {note && <div className="mt-2 text-sm leading-snug text-[var(--color-ink-faint)]">{note}</div>}
    </div>
  );
}
