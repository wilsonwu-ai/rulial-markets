"use client";

import type { Ensemble, Mode, Score } from "@/lib/types";
import { pct, signedPct, fixed } from "@/lib/quant";
import { Scorecard } from "./Scorecard";
import { FanChart } from "./FanChart";
import { TerminalHistogram } from "./TerminalHistogram";

/**
 * THE CLARITY PASS, in one component.
 *
 * The old results screen opened with `crps_lift` at 72px — frequently a large
 * red negative — followed by a paragraph explaining why a large red negative
 * was expected. Wilson's note was blunt and correct: "there's a lot of text and
 * it is difficult to fully understand the numbers... like what is CRPS?"
 *
 * Nothing about the scoring changed. The ORDER did:
 *
 *   1. THREE numbers, and only three. The range the model gave, what actually
 *      happened, and a plain-English verdict. That is the whole first view.
 *   2. CRPS is never an acronym on screen. The heading is a question a person
 *      would actually ask — "How good was that range?" — and the answer is a
 *      sentence. The score, the null, the lift and the PIT are all still here,
 *      all still exactly as computed, one disclosure down.
 *   3. The verdict leads, the figure follows. At n = 1 a negative lift is the
 *      expected case and is already explained; leading with the number taught
 *      the viewer the wrong thing before they read the sentence that fixes it.
 *
 * CONTRACT §7 is untouched: the null is present and never demoted, lift is
 * still the headline metric of record inside the disclosure, and directional
 * hit-rate appears nowhere.
 */
export function Verdict({
  score, ensemble, source,
}: {
  score: Score | null;
  ensemble: Ensemble;
  /** Which of the three sources produced these numbers. In `mock` the
   *  "realized" return is INVENTED by the in-browser generator, so a tile
   *  headed "What actually happened" would be the single most dishonest string
   *  on the site. It is relabelled rather than hidden. */
  source: Mode;
}) {
  const synthetic = source === "mock";
  const lo = ensemble.quantiles.p5;
  const hi = ensemble.quantiles.p95;
  const beat = score ? score.crps_lift > 0 : null;

  return (
    <div className="grid gap-6">
      {/* ---------------- the three numbers ---------------- */}
      <div className="grid gap-px overflow-hidden rounded-lg border border-[var(--color-rule)] bg-[var(--color-rule)] md:grid-cols-3">
        <div className="bg-[var(--color-panel)] px-7 py-6">
          <div className="label">The range the model gave</div>
          <div className="figure mt-2 text-[clamp(1.75rem,3.4vw,2.25rem)]" style={{ color: "var(--color-blue)" }}>
            {pct(lo)} <span className="text-[var(--color-ink-faint)]">to</span> {pct(hi)}
          </div>
          <div className="mt-2 text-sm leading-snug text-[var(--color-ink-faint)]">
            9 out of 10 sampled futures finished in here
          </div>
        </div>

        <div className="bg-[var(--color-panel)] px-7 py-6">
          <div className="label" style={synthetic ? { color: "var(--color-notice)" } : undefined}>
            {synthetic ? "Simulated outcome — not real" : "What actually happened"}
          </div>
          {score ? (
            <>
              <div
                className="figure mt-2 text-[clamp(1.75rem,3.4vw,2.25rem)]"
                style={{ color: score.actual_return < 0 ? "var(--color-neg)" : "var(--color-pos)" }}
              >
                {pct(score.actual_return, 1)}
              </div>
              <div className="mt-2 text-sm leading-snug text-[var(--color-ink-faint)]">
                {synthetic
                  ? "the in-browser generator invents this figure; it is not the return this stock produced"
                  : score.actual_return >= lo && score.actual_return <= hi
                    ? "inside the range"
                    : "outside the range"}
              </div>
            </>
          ) : (
            <>
              <div className="figure mt-2 text-[clamp(1.75rem,3.4vw,2.25rem)]" style={{ color: "var(--color-ink-faint)" }}>
                not known
              </div>
              <div className="mt-2 text-sm leading-snug text-[var(--color-ink-faint)]">
                the outcome for this date is not known, so there is nothing to compare against
              </div>
            </>
          )}
        </div>

        <div
          className="px-7 py-6"
          style={{
            background: beat === null ? "var(--color-panel)" : beat ? "var(--color-blue-tint)" : "var(--color-panel-2)",
          }}
        >
          <div className="label">How good was that range?</div>
          <div
            className="mt-2 text-[clamp(1.25rem,2.4vw,1.5rem)] font-bold leading-tight"
            style={{ color: beat === null ? "var(--color-ink-faint)" : beat ? "var(--color-blue)" : "var(--color-navy)" }}
          >
            {beat === null
              ? "Not scored"
              : beat
                ? "Better than the simple baseline"
                : "Worse than the simple baseline here"}
          </div>
          <div className="mt-2 text-sm leading-snug text-[var(--color-ink-faint)]">
            {beat === null
              ? "a verdict needs a known outcome, and we will not invent one"
              : synthetic
                ? "measured against the same baseline — but both sides of this comparison are synthetic, so it is a demonstration of the surface, not a result"
                : "the baseline is a bell curve built from this stock's own recent volatility, which knows nothing about the event"}
          </div>
        </div>
      </div>

      {score && !synthetic && (
        <p className="max-w-[86ch] text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)]">
          {score.crps_lift > 0
            ? "On this one event the conditioned range fitted the outcome better than the baseline did."
            : "On this one event the baseline fitted the outcome better than our conditioned range did, and that is reported rather than hidden."}{" "}
          One event decides almost nothing either way — a narrow range wins big whenever the outcome
          lands near its centre and loses big when it does not. The walk-forward tab is where this
          becomes a statistic.
        </p>
      )}

      {score && synthetic && (
        <p className="max-w-[86ch] text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)]">
          Every figure in this row was produced in the browser by a seeded random generator,
          including the outcome. Nothing here is a measurement of anything. Switch the source to the
          live backend or the precomputed bundle for numbers that mean something.
        </p>
      )}

      {/* ---------------- everything else, one disclosure down ---------------- */}
      {score && (
        <details className="group rounded-lg border border-[var(--color-rule)] bg-[var(--color-panel-2)]">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-6 py-4">
            <span className="label-title">Show the numbers behind this</span>
            <span className="flex flex-wrap items-center gap-4">
              <span className="label">
                lift{" "}
                <span
                  className="num font-semibold"
                  style={{ color: score.crps_lift > 0 ? "var(--color-blue)" : "var(--color-neg)" }}
                >
                  {signedPct(score.crps_lift)}
                </span>
              </span>
              <span className="label">
                score <span className="num font-semibold text-[var(--color-navy)]">{fixed(score.crps, 4)}</span>
                {" vs "}
                <span className="num font-semibold text-[var(--color-null)]">{fixed(score.crps_null, 4)}</span>
              </span>
              <span className="btn-secondary pointer-events-none bg-white">
                <span className="group-open:hidden">Open</span>
                <span className="hidden group-open:inline">Close</span>
              </span>
            </span>
          </summary>
          <div className="border-t border-[var(--color-rule)] bg-[var(--color-panel)] p-6 sm:p-8">
            <p className="mb-6 max-w-[86ch] text-[0.9375rem] leading-relaxed text-[var(--color-ink-dim)]">
              The score below is <span className="font-semibold text-[var(--color-navy)]">CRPS</span> —
              one number for how well a whole range matched a single outcome, in the same units as
              the return. Lower is better. It is reported against a frozen baseline that CONTRACT §7
              forbids us to remove, and the difference between the two is the lift.
            </p>
            <Scorecard score={score} />

            {/* The original forward surface, kept intact and moved here rather
                than deleted. It says the same thing as the branch chart in
                RETURN space instead of price space, and the histogram shows
                where the outcome fell among the sampled futures — both worth
                having, neither worth putting in front of the picture. */}
            <div className="mt-10 border-t border-[var(--color-rule)] pt-8">
              <div className="label mb-4">The same ensemble in return space</div>
              <FanChart ensemble={ensemble} actual={score.actual_return} />
            </div>
            <div className="mt-10 border-t border-[var(--color-rule)] pt-8">
              <div className="label mb-4">Where the outcome fell among the sampled futures</div>
              <TerminalHistogram ensemble={ensemble} actual={score.actual_return} />
            </div>
          </div>
        </details>
      )}
    </div>
  );
}
