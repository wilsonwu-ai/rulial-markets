"use client";

/**
 * PIT calibration histogram. CONTRACT §7: a FLAT histogram is the win
 * condition, not "we called the crash". The plain-English read is rendered
 * next to it so a non-quant judge gets the point in one look.
 *
 * Recon caveat surfaced on screen: at ~12 events per ticker a calibration
 * test has roughly 30% power against an ensemble that is 2x too narrow, so a
 * per-ticker pass is close to meaningless. We say the sample size out loud.
 */
export function PitHistogram({
  counts, n, calibrationOk,
}: {
  counts: number[]; n: number; calibrationOk: boolean;
}) {
  const bins = counts.length ? counts : Array(10).fill(0);
  const total = bins.reduce((a, b) => a + b, 0);
  const expected = total / bins.length;
  const max = Math.max(1, ...bins, expected * 1.6);

  const dev = total > 0
    ? Math.max(...bins.map((c) => Math.abs(c - expected))) / (expected || 1)
    : 0;

  /** Below this many events the histogram simply cannot tell calibrated from
   *  badly mis-dispersed — measured power against a 2x-too-narrow ensemble is
   *  ~30% at n=12 and ~92% at n=60. So we refuse to render a verdict instead of
   *  reading tea leaves out loud. */
  const UNDIAGNOSTIC_BELOW = 30;   // ~30% power at n=12, still weak at 20
  const CONCLUSIVE_AT = 60;        // ~92% power against a 2x-too-narrow ensemble
  const tooSmall = n > 0 && n < UNDIAGNOSTIC_BELOW;
  const suggestive = n >= UNDIAGNOSTIC_BELOW && n < CONCLUSIVE_AT;

  const read =
    n === 0 || total === 0
      ? "No scored events yet for this ticker — nothing to calibrate against."
    : tooSmall
      ? `Only ${n} scored event${n === 1 ? "" : "s"}. At this sample size the histogram cannot separate a well-calibrated ensemble from a badly mis-dispersed one, so the shape below is not evidence either way — it is drawn, not interpreted.`
    : dev < 0.35
      ? `Close to flat across ${n} events. The ensemble's stated uncertainty is roughly the uncertainty it actually has.${suggestive ? " At this n that is encouraging rather than settled." : ""}`
    : dev < 0.8
      ? `Lumpy across ${n} events. Some over- or under-dispersion, though a deviation this size is still within what noise produces at this sample size.`
    : suggestive
      ? `Visibly not flat across ${n} events. That points at mis-dispersion — the width being wrong rather than the location — but ${n} events is short of the ~60 needed to call it conclusively.`
      : `Clearly not flat across ${n} events. The ensemble is mis-dispersed — the width is wrong, not just the location.`;

  const shape =
    n === 0 || total === 0 || tooSmall || suggestive ? null
    : bins[0] + bins[bins.length - 1] > expected * 2.9
      ? "U-shaped: too many actuals in the tails → ensemble is TOO NARROW (overconfident)."
      : bins.slice(3, 7).reduce((a, b) => a + b, 0) > expected * 5.2
        ? "Peaked in the middle: too many actuals near the median → ensemble is TOO WIDE (underconfident)."
        : null;

  // This chart is the contract's stated win condition and the one most
  // likely to be misread, so it is legible without narration: the reference
  // line is labelled ON the line, and a legitimately empty bucket renders a
  // visible 0 rather than nothing — a zero is evidence.
  const uniformY = 210 - (expected / max) * 170;
  const stagger = 350 / Math.max(1, bins.length);
  // The plot stops short of the viewBox so the reference line can be labelled
  // in a clear right margin. Annotating the line where it ends beats a legend
  // for the one mark a judge has to understand, and a margin tag can never be
  // occluded by a tall bar the way an in-plot callout would be.
  const L = 40;
  const R = 516;
  const bw = (R - L) / bins.length;

  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
      <div>
        <svg viewBox="0 0 620 258" className="w-full" role="img"
          aria-label="PIT calibration histogram">
          {/* uniform reference, labelled at the end of the line itself.
              DESIGN_AMEX §5 asks for exactly this: a dashed grey line at the
              uniform expectation, labelled "flat = calibrated" so the meaning
              is legible without narration. */}
          <line x1={L} x2={R} y1={uniformY} y2={uniformY}
            stroke="var(--color-gray-500)" strokeWidth={2.5} strokeDasharray="10 6" />
          <text x={R + 10} y={uniformY - 2} className="num" fontSize="14"
            fontWeight={600} fill="var(--color-ink-dim)">flat =</text>
          <text x={R + 10} y={uniformY + 16} className="num" fontSize="14"
            fontWeight={600} fill="var(--color-ink-dim)">calibrated</text>

          <line x1={L} x2={R} y1={210} y2={210}
            stroke="var(--color-axis)" strokeWidth={2} />

          {bins.map((c, i) => {
            const h = (c / max) * 170;
            const over = !tooSmall && c > expected * 1.45;
            return (
              <g key={i}>
                <rect x={L + i * bw + 3} y={210 - h} width={bw - 6} height={Math.max(h, 0)}
                  fill={over ? "var(--color-notice)" : "var(--color-blue-light)"}
                  opacity={over ? 0.9 : 1}
                  className="bloom" style={{ animationDelay: `${i * stagger}ms` }} />
                <text x={L + i * bw + bw / 2} y={234} textAnchor="middle"
                  className="num" fontSize="14" fill="var(--color-ink-faint)">
                  {(i / bins.length).toFixed(1)}
                </text>
                {/* a legitimately empty bucket renders a visible 0 — at n≈12
                    across 10 buckets several will be zero, and a zero is
                    evidence, not an absence of data */}
                <text x={L + i * bw + bw / 2} y={210 - h - 8} textAnchor="middle"
                  className="num" fontSize="15"
                  fill={c ? "var(--color-navy)" : "var(--color-ink-faint)"}>
                  {c}
                </text>
              </g>
            );
          })}

          <text x={(L + R) / 2} y={252} textAnchor="middle"
            fill="var(--color-ink-faint)"
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "14px",
              fontWeight: 600,
              letterSpacing: "0.08em",
            }}>PIT BUCKET</text>
        </svg>
        <div className="mt-2 flex flex-wrap items-center gap-x-6 gap-y-2">
          <span className="flex items-center gap-2">
            <span className="block h-[2px] w-7"
              style={{ backgroundImage: "repeating-linear-gradient(90deg, var(--color-gray-500) 0 6px, transparent 6px 11px)" }} />
            <span className="label">uniform reference — flat means calibrated</span>
          </span>
          {total !== n && (
            <span className="label" style={{ color: "var(--color-notice)" }}>
              histogram sums to {total}, n_tests is {n} — backend inconsistency
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-col justify-center gap-4">
        <div>
          <div className="label">Plain English</div>
          <p className="mt-2 text-[1.0625rem] leading-relaxed text-[var(--color-ink)]">{read}</p>
          {shape && (
            <p className="mt-3 border-l-[3px] border-[var(--color-notice-rule)] bg-[var(--color-notice-tint)] py-2 pl-3 text-sm leading-relaxed text-[var(--color-notice)]">
              {shape}
            </p>
          )}
        </div>
        <div className="rounded-lg border border-[var(--color-rule)] bg-[var(--color-panel-2)] p-5">
          <div className="flex items-baseline justify-between">
            <span className="label">Scored events</span>
            <span className="figure text-2xl">{n}</span>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="label">calibration_ok</span>
            <span className="figure text-2xl"
              style={{ color: calibrationOk ? "var(--color-blue)" : "var(--color-ink-faint)" }}>
              {String(calibrationOk)}
            </span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-[var(--color-ink-faint)]">
            Power warning: at n≈12 a calibration test catches an ensemble that is 2× too narrow
            only about 30% of the time (measured, Phase-1 recon). Treat a single-ticker pass as
            weak evidence; the pooled universe is the number to trust.
          </p>
        </div>
      </div>
    </div>
  );
}
