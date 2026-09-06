"use client";

import type { Score } from "@/lib/types";
import { fixed, pct, signedPct } from "@/lib/quant";

/**
 * CONTRACT §7. crps_lift is the headline. crps_null may never be dropped,
 * nor visually demoted — it sits in the top-left of the cell grid, same size
 * and same weight bracket as our own CRPS. Directional hit-rate is
 * deliberately absent: it is not permitted as a headline result and we do
 * not compute it here at all.
 */
export function Scorecard({ score }: { score: Score }) {
  const lift = score.crps_lift;
  const beat = lift > 0;
  // Blue when the conditional ensemble beat the frozen null, red when it did
  // not. The signed number and the sentence beside it say which either way, so
  // colour is never carrying the verdict alone.
  const liftColor = beat ? "var(--color-blue)" : "var(--color-neg)";

  const zAbs = Math.abs(score.z_score);
  // The realized outcome is coloured by its own sign — the same rule the two
  // charts use — and the signed return is printed beside it in the cell grid.
  const zColor = score.actual_return < 0 ? "var(--color-neg)" : "var(--color-pos)";
  const zRead =
    zAbs < 1 ? "well inside the bulk of the ensemble"
    : zAbs < 2 ? "in the shoulder of the distribution"
    : zAbs < 3 ? "in the tail — the ensemble allowed it, barely"
    : "outside anything the ensemble seriously entertained";

  return (
    <div className="grid min-w-0 gap-5">
      {/* headline */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1.15fr_1fr]">
        <div className="rounded-lg border border-[var(--color-rule)] bg-[var(--color-panel-2)] px-8 py-7">
          <div className="label">Headline — CRPS lift over null</div>
          <div className="mt-2 flex items-end gap-4">
            {/* `.num` only. This carried `display` as well, and because both
                are single-class selectors the later declaration won — which
                put the single most important number on the screen into a
                serif face with PROPORTIONAL figures, so it visibly changed
                width between runs. globals.css now orders `.num` after
                `.display` as a second line of defence. */}
            <div className="figure text-[clamp(2.75rem,6vw,4.5rem)]" style={{ color: liftColor }}>
              {signedPct(lift)}
            </div>
            <div className="mb-2 max-w-[22ch] text-sm leading-snug text-[var(--color-ink-dim)]">
              {beat
                ? "the conditional ensemble scored better than the trailing-volatility null"
                : "the null beat us — reported as-is, because a hidden null is a lie"}
            </div>
          </div>
          <p className="mt-5 border-t border-[var(--color-rule)] pt-4 text-sm leading-relaxed text-[var(--color-ink-faint)]">
            <span className="font-semibold" style={{ color: "var(--color-notice)" }}>Read this as n = 1.</span>{" "}
            Single-event CRPS lift is dominated by where the actual happened to land: a narrower
            distribution takes a large ratio win whenever the outcome falls near the centre, so this
            number has a fat left tail even for a perfectly calibrated ensemble. Across 500 synthetic
            events with a flat PIT histogram we measured median lift +10.4% against a mean of −6.8%.
            The walk-forward panel is where lift becomes a statistic.
          </p>
          {score.crps_lift_demeaned !== undefined && (
            <div className="mt-5 border-t border-[var(--color-rule)] pt-4">
              <div className="flex items-baseline justify-between gap-4">
                <span className="label">Demeaned (drift removed)</span>
                <span className="figure text-xl"
                  style={{ color: score.crps_lift_demeaned > 0 ? "var(--color-blue)" : "var(--color-neg)" }}>
                  {signedPct(score.crps_lift_demeaned)}
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-[var(--color-ink-faint)]">
                Recon measured a naive analog-resampling generator at +14.8% raw lift that fell to
                −4.5% once the assumed drift was removed — pure bull-decade artifact. Both numbers
                ship together so that cannot happen quietly.
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-[1px] overflow-hidden rounded-lg border border-[var(--color-rule)] bg-[var(--color-rule)] sm:grid-cols-2">
          <Cell label="CRPS (ours)" value={fixed(score.crps, 5)} tone="series" note="lower is better" />
          <Cell label="CRPS (null)" value={fixed(score.crps_null, 5)} tone="null" note="Gaussian, trailing 250d σ, zero drift" />
          <Cell label="Realized return" value={pct(score.actual_return, 2)} tone="actual" note="the outcome that happened" />
          <Cell label="PIT of actual" value={score.pit.toFixed(3)} tone="ink" note="uniform across events = calibrated" />
        </div>
      </div>

      {/* z-score ruler */}
      <div className="rounded-lg border border-[var(--color-rule)] bg-[var(--color-panel-2)] px-8 py-6">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <div className="label">Where the actual landed</div>
          <div className="text-lg text-[var(--color-ink-dim)]">
            the actual landed{" "}
            <span className="figure text-3xl" style={{ color: zColor }}>
              {zAbs.toFixed(2)}σ
            </span>{" "}
            {score.z_score >= 0 ? "above" : "below"} our ensemble mean — {zRead}
          </div>
        </div>
        <ZRuler z={score.z_score} color={zColor} />
      </div>
    </div>
  );
}

function Cell({
  label, value, note, tone,
}: {
  label: string; value: string; note: string;
  tone: "series" | "null" | "actual" | "ink";
}) {
  const color = {
    series: "var(--color-blue)",
    null: "var(--color-null)",
    actual: "var(--color-navy)",
    ink: "var(--color-navy)",
  }[tone];
  // The null is a different SERIES, not a dimmer version of ours. Hue alone
  // is a weak channel at 5.69:1, so weight carries the distinction too —
  // ours at 500, the baseline at 400. Neither is demoted in size or position;
  // CONTRACT §7 forbids that.
  const weight = tone === "null" ? 500 : 700;
  return (
    <div className="bg-[var(--color-panel)] px-6 py-5">
      <div className="label">{label}</div>
      <div className="figure mt-2 text-[1.75rem]"
        style={{ color, fontWeight: weight }}>{value}</div>
      <div className="mt-2 text-sm leading-snug text-[var(--color-ink-faint)]">{note}</div>
    </div>
  );
}

function ZRuler({ z, color }: { z: number; color: string }) {
  const clamp = Math.max(-3.6, Math.min(3.6, z));
  const posPct = ((clamp + 4) / 8) * 100;
  return (
    <div className="relative mt-5 h-16">
      <div className="absolute inset-x-0 top-7 h-[2px] bg-[var(--color-axis)]" />
      {[-3, -2, -1, 0, 1, 2, 3].map((t) => (
        <div key={t} className="absolute top-0" style={{ left: `${((t + 4) / 8) * 100}%` }}>
          <div
            className="mx-auto w-[2px] bg-[var(--color-axis)]"
            style={{ height: t === 0 ? 22 : 12, marginTop: t === 0 ? 18 : 22 }}
          />
          <div className="num mt-1 -translate-x-1/2 text-sm text-[var(--color-ink-faint)]">
            {t > 0 ? `+${t}σ` : `${t}σ`}
          </div>
        </div>
      ))}
      {/* one-sigma shading */}
      <div className="absolute top-[18px] h-[20px] bg-[var(--color-blue)] opacity-[0.14]"
        style={{ left: "37.5%", width: "25%" }} />
      <div
        className="absolute top-2 -translate-x-1/2 transition-[left] duration-700 ease-out"
        style={{ left: `${posPct}%` }}
      >
        <div className="h-[34px] w-[3px]" style={{ background: color }} />
        <div className="mx-auto -mt-[3px] h-[9px] w-[9px] rotate-45" style={{ background: color }} />
      </div>
    </div>
  );
}
