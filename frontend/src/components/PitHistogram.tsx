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

  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
      <div>
        <svg viewBox="0 0 620 250" className="w-full" role="img"
          aria-label="PIT calibration histogram">
          {/* uniform reference */}
          <line x1={40} x2={604} y1={210 - (expected / max) * 170}
            y2={210 - (expected / max) * 170}
            stroke="var(--color-actual)" strokeWidth={2} strokeDasharray="8 5" opacity={0.9} />
          <line x1={40} x2={604} y1={210} y2={210} stroke="var(--color-rule-bright)" />

          {bins.map((c, i) => {
            const w = (604 - 40) / bins.length;
            const h = (c / max) * 170;
            const over = !tooSmall && c > expected * 1.45;
            return (
              <g key={i}>
                <rect x={40 + i * w + 3} y={210 - h} width={w - 6} height={Math.max(h, 0)}
                  fill={over ? "var(--color-hazard)" : "var(--color-phosphor)"}
                  opacity={over ? 0.75 : 0.6}
                  className="bloom" style={{ animationDelay: `${i * 45}ms` }} />
                <text x={40 + i * w + w / 2} y={232} textAnchor="middle"
                  className="num" fontSize="11" fill="var(--color-ink-faint)">
                  {(i / bins.length).toFixed(1)}
                </text>
                <text x={40 + i * w + w / 2} y={210 - h - 8} textAnchor="middle"
                  className="num" fontSize="12" fill="var(--color-ink-dim)">
                  {c || ""}
                </text>
              </g>
            );
          })}
          <text x={322} y={248} textAnchor="middle" className="label" fontSize="10"
            fill="var(--color-ink-faint)">PIT BUCKET</text>
        </svg>
        <div className="mt-2 flex flex-wrap items-center gap-x-6 gap-y-2">
          <span className="flex items-center gap-2">
            <span className="block h-[2px] w-7"
              style={{ backgroundImage: "repeating-linear-gradient(90deg, var(--color-actual) 0 6px, transparent 6px 11px)" }} />
            <span className="label">uniform reference — flat means calibrated</span>
          </span>
          {total !== n && (
            <span className="label" style={{ color: "var(--color-hazard)" }}>
              histogram sums to {total}, n_tests is {n} — backend inconsistency
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-col justify-center gap-4">
        <div>
          <div className="label">Plain English</div>
          <p className="mt-2 text-[1.05rem] leading-relaxed text-[var(--color-ink)]">{read}</p>
          {shape && (
            <p className="mt-3 border-l-2 border-[var(--color-hazard)] pl-3 text-sm leading-relaxed text-[var(--color-hazard)]">
              {shape}
            </p>
          )}
        </div>
        <div className="border-t border-[var(--color-rule)] pt-4">
          <div className="flex items-baseline justify-between">
            <span className="label">Scored events</span>
            <span className="num text-xl">{n}</span>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="label">calibration_ok</span>
            <span className="num text-xl"
              style={{ color: calibrationOk ? "var(--color-phosphor)" : "var(--color-ink-faint)" }}>
              {String(calibrationOk)}
            </span>
          </div>
          <p className="mt-3 text-xs leading-relaxed text-[var(--color-ink-faint)]">
            Power warning: at n≈12 a calibration test catches an ensemble that is 2× too narrow
            only about 30% of the time (measured, Phase-1 recon). Treat a single-ticker pass as
            weak evidence; the pooled universe is the number to trust.
          </p>
        </div>
      </div>
    </div>
  );
}
