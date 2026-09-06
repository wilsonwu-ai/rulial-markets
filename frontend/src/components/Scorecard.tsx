"use client";

import type { Score } from "@/lib/types";
import { fixed, pct } from "@/lib/quant";

/**
 * CONTRACT §7. crps_lift is the headline. crps_null may never be dropped.
 * Directional hit-rate is deliberately absent — it is not permitted as a
 * headline result and we do not compute it here at all.
 */
export function Scorecard({ score }: { score: Score }) {
  const lift = score.crps_lift;
  const beat = lift > 0;
  const liftColor = beat ? "var(--color-phosphor)" : "var(--color-down)";

  const zAbs = Math.abs(score.z_score);
  const zRead =
    zAbs < 1 ? "well inside the bulk of the ensemble"
    : zAbs < 2 ? "in the shoulder of the distribution"
    : zAbs < 3 ? "in the tail — the ensemble allowed it, barely"
    : "outside anything the ensemble seriously entertained";

  return (
    <div className="grid gap-5">
      {/* headline */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1.15fr_1fr]">
        <div className="border border-[var(--color-rule)] bg-[var(--color-panel-2)] px-6 py-6">
          <div className="label">Headline — CRPS lift over null</div>
          <div className="mt-2 flex items-end gap-4">
            <div className="display num text-[clamp(3rem,7vw,5.6rem)]" style={{ color: liftColor }}>
              {lift >= 0 ? "+" : "−"}{(Math.abs(lift) * 100).toFixed(1)}%
            </div>
            <div className="mb-3 max-w-[19ch] text-sm leading-snug text-[var(--color-ink-dim)]">
              {beat
                ? "the conditional ensemble scored better than the trailing-volatility null"
                : "the null beat us — reported as-is, because a hidden null is a lie"}
            </div>
          </div>
          <p className="mt-4 border-t border-[var(--color-rule)] pt-3 text-xs leading-relaxed text-[var(--color-ink-faint)]">
            <span style={{ color: "var(--color-hazard)" }}>Read this as n = 1.</span>{" "}
            Single-event CRPS lift is dominated by where the actual happened to land: a narrower
            distribution takes a large ratio win whenever the outcome falls near the centre, so this
            number has a fat left tail even for a perfectly calibrated ensemble. Across 500 synthetic
            events with a flat PIT histogram we measured median lift +10.4% against a mean of −6.8%.
            The walk-forward panel is where lift becomes a statistic.
          </p>
          {score.crps_lift_demeaned !== undefined && (
            <div className="mt-4 border-t border-[var(--color-rule)] pt-3">
              <div className="flex items-baseline justify-between gap-4">
                <span className="label">Demeaned (drift removed)</span>
                <span className="num text-lg"
                  style={{ color: score.crps_lift_demeaned > 0 ? "var(--color-phosphor)" : "var(--color-down)" }}>
                  {score.crps_lift_demeaned >= 0 ? "+" : "−"}
                  {(Math.abs(score.crps_lift_demeaned) * 100).toFixed(1)}%
                </span>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-[var(--color-ink-faint)]">
                Recon measured a naive analog-resampling generator at +14.8% raw lift that fell to
                −4.5% once the assumed drift was removed — pure bull-decade artifact. Both numbers
                ship together so that cannot happen quietly.
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-[1px] bg-[var(--color-rule)]">
          <Cell label="CRPS (ours)" value={fixed(score.crps, 5)} tone="phosphor" note="lower is better" />
          <Cell label="CRPS (null)" value={fixed(score.crps_null, 5)} tone="null" note="Gaussian, trailing 250d σ, zero drift" />
          <Cell label="Realized return" value={pct(score.actual_return, 2)} tone="actual" note="the outcome that happened" />
          <Cell label="PIT of actual" value={score.pit.toFixed(3)} tone="ink" note="uniform across events = calibrated" />
        </div>
      </div>

      {/* z-score ruler */}
      <div className="border border-[var(--color-rule)] bg-[var(--color-panel-2)] px-6 py-5">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <div className="label">Where the actual landed</div>
          <div className="text-lg text-[var(--color-ink-dim)]">
            the actual landed{" "}
            <span className="num text-2xl text-[var(--color-actual)]">
              {zAbs.toFixed(2)}σ
            </span>{" "}
            {score.z_score >= 0 ? "above" : "below"} our ensemble mean — {zRead}
          </div>
        </div>
        <ZRuler z={score.z_score} />
      </div>
    </div>
  );
}

function Cell({
  label, value, note, tone,
}: {
  label: string; value: string; note: string;
  tone: "phosphor" | "null" | "actual" | "ink";
}) {
  const color = {
    phosphor: "var(--color-phosphor)",
    null: "var(--color-null)",
    actual: "var(--color-actual)",
    ink: "var(--color-ink)",
  }[tone];
  return (
    <div className="bg-[var(--color-panel)] px-5 py-4">
      <div className="label">{label}</div>
      <div className="num mt-1 text-[1.75rem] leading-none" style={{ color }}>{value}</div>
      <div className="mt-2 text-[0.72rem] leading-snug text-[var(--color-ink-faint)]">{note}</div>
    </div>
  );
}

function ZRuler({ z }: { z: number }) {
  const clamp = Math.max(-3.6, Math.min(3.6, z));
  const posPct = ((clamp + 4) / 8) * 100;
  return (
    <div className="relative mt-5 h-16">
      <div className="absolute inset-x-0 top-7 h-[1px] bg-[var(--color-rule-bright)]" />
      {[-3, -2, -1, 0, 1, 2, 3].map((t) => (
        <div key={t} className="absolute top-0" style={{ left: `${((t + 4) / 8) * 100}%` }}>
          <div
            className="mx-auto w-[1px] bg-[var(--color-rule-bright)]"
            style={{ height: t === 0 ? 22 : 12, marginTop: t === 0 ? 18 : 22 }}
          />
          <div className="num mt-1 -translate-x-1/2 text-[0.7rem] text-[var(--color-ink-faint)]">
            {t > 0 ? `+${t}σ` : `${t}σ`}
          </div>
        </div>
      ))}
      {/* one-sigma shading */}
      <div className="absolute top-[18px] h-[20px] bg-[var(--color-phosphor)] opacity-[0.10]"
        style={{ left: "37.5%", width: "25%" }} />
      <div
        className="absolute top-2 -translate-x-1/2 transition-[left] duration-700 ease-out"
        style={{ left: `${posPct}%` }}
      >
        <div className="h-[34px] w-[3px] bg-[var(--color-actual)]" />
        <div className="mx-auto -mt-[3px] h-[9px] w-[9px] rotate-45 bg-[var(--color-actual)]" />
      </div>
    </div>
  );
}
