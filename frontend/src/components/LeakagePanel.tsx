"use client";

import { useState } from "react";
import { signedPct } from "@/lib/quant";

/**
 * CONTRACT §8 — LEAKAGE DISCLOSURE.
 * "State this limitation on the results screen. Out loud, in the product."
 * So it is a designed panel sitting directly under the score, not a footnote.
 */
export function LeakagePanel({
  famous, obscure, liftFamous, liftObscure, synthetic = false,
}: {
  famous?: number; obscure?: number; synthetic?: boolean;
  liftFamous?: number; liftObscure?: number;
}) {
  const [open, setOpen] = useState(false);
  const haveSplit =
    !synthetic &&
    famous !== undefined && obscure !== undefined &&
    liftFamous !== undefined && liftObscure !== undefined;

  return (
    /* DESIGN_AMEX §6: on a light ground the disclosure becomes a blue-tint
       callout with a solid blue left rule. Prominent, not fine print — it is
       still a full-width panel sitting directly under the score, which
       CONTRACT §8 requires and this reskin may not shrink or collapse. */
    <section
      className="rise overflow-hidden rounded-lg border border-[var(--color-blue-pale)] bg-[var(--color-blue-tint)]"
      style={{ borderLeft: "6px solid var(--color-blue)", boxShadow: "var(--shadow-card)" }}
    >
      <div className="px-8 py-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="label" style={{ color: "var(--color-blue)" }}>
              04 — Leakage disclosure · required by contract
            </div>
            <h3 className="display mt-3 max-w-[24ch] text-[clamp(1.6rem,3vw,2.5rem)]">
              The model has already read the future.
              <span className="block italic" style={{ color: "var(--color-blue)" }}>
                Here is exactly how much that is worth.
              </span>
            </h3>
          </div>
          <button
            onClick={() => setOpen((v) => !v)}
            className="btn-secondary shrink-0 bg-white"
            aria-expanded={open}
          >
            {open ? "collapse" : "read the full disclosure"}
          </button>
        </div>

        <p className="mt-6 max-w-[74ch] text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)]">
          Any LLM in this generator was trained on the post-2019 world. We cut the{" "}
          <em className="not-italic font-semibold text-[var(--color-ink)]">input</em> data at 2019-12-31.
          That does not cut the <em className="not-italic font-semibold text-[var(--color-ink)]">weights</em>.
          When we ask about a 2018 jump, the model may simply remember what happened.
          Memorization and forecasting are not separable from the outside — that is a published
          result, not a hedge we invented.
        </p>

        <div className="mt-8 grid gap-[1px] overflow-hidden rounded-lg border border-[var(--color-blue-pale)] bg-[var(--color-blue-pale)] md:grid-cols-3">
          <Guard
            n="01"
            head="Lift over a null, never raw accuracy"
            body="Remembering the outcome still has to beat a Gaussian with trailing 250-day sigma before it counts as anything. The null is frozen into the eval and may not be removed."
          />
          <Guard
            n="02"
            head="Obscure events sit beside famous ones"
            body="A model that only wins on the events that made headlines is recalling, not forecasting. The two sets are scored separately and both are shown."
          />
          <Guard
            n="03"
            head="Directional hit-rate is not a headline"
            body="A coin flip looks skilled when you report direction. Frozen out of the headline by contract; calibration is the win condition instead."
          />
        </div>

        {haveSplit && (
          <div className="mt-8 rounded-lg border border-[var(--color-blue-pale)] bg-white px-6 py-6">
            <div className="label" style={{ color: "var(--color-blue)" }}>
              The memorization test, live
            </div>
            <div className="mt-5 grid gap-8 sm:grid-cols-2">
              <Split label={`Famous events (n=${famous})`} v={liftFamous!} />
              <Split label={`Obscure events (n=${obscure})`} v={liftObscure!} />
            </div>
            <p className="mt-5 text-base leading-relaxed text-[var(--color-ink-dim)]">
              {liftFamous! - liftObscure! > 0.05
                ? "The gap is wide. Skill is concentrated in events the model could plausibly remember — read the headline lift down accordingly."
                : "The two are close. What lift exists is not obviously explained by recall alone."}
            </p>
          </div>
        )}

        {open && (
          <div className="mt-8 grid gap-8 border-t border-[var(--color-blue-pale)] pt-8 text-base leading-relaxed text-[var(--color-ink-dim)] md:grid-cols-2">
            <div>
              <div className="label" style={{ color: "var(--color-blue)" }}>Prior art we are standing on</div>
              <ul className="mt-3 space-y-3">
                <li>
                  <span className="font-semibold text-[var(--color-navy)]">Lopez-Lira, Tang &amp; Zhu — “The Memorization Problem”</span>{" "}
                  (arXiv:2504.14765). Proves forecasting ability is formally non-identified under
                  memorization. GPT-4o recalls pre-cutoff S&amp;P 500 daily levels at 0.61% MAPE and
                  post-cutoff at 16.87%; directional accuracy falls 80.6% → 45.7%. Prompting the
                  model to “ignore” what it knows does not work.
                </li>
                <li>
                  <span className="font-semibold text-[var(--color-navy)]">Gao, Jiang &amp; Yan — Lookahead Propensity</span>{" "}
                  (arXiv:2512.23847). A measured per-event contamination score. Our famous/obscure
                  split is a cheap discrete cousin of it, not an invention of ours.
                </li>
                <li>
                  <span className="font-semibold text-[var(--color-navy)]">Gneiting, Balabdaoui &amp; Raftery (2007)</span>.
                  Sharpness subject to calibration, PIT histograms. Our win condition is textbook,
                  and we say so rather than dressing it up.
                </li>
              </ul>
            </div>
            <div>
              <div className="label" style={{ color: "var(--color-blue)" }}>What else could explain a positive lift</div>
              <ul className="mt-3 space-y-3">
                <li>
                  <span className="font-semibold text-[var(--color-navy)]">Volatility clustering, not text.</span>{" "}
                  After a 25%-in-a-week move, trailing 250-day sigma is stale by construction.
                  Trailing vol measured 1.78× higher post-jump in our own train data. Some of any
                  lift is that, and an oracle using the realized post-jump sigma caps out at only
                  +2.0% — so a large headline number is a reason for suspicion, not celebration.
                </li>
                <li>
                  <span className="font-semibold text-[var(--color-navy)]">Drift, not dispersion.</span>{" "}
                  The train corpus is 30 up-jumps to 3 down-jumps with +5.77% mean forward return —
                  a bull decade. A naive analog-resampling generator scored +14.8% lift that became
                  −4.5% once demeaned. Every lift on this screen ships with its demeaned twin.
                </li>
                <li>
                  <span className="font-semibold text-[var(--color-navy)]">Sample size.</span>{" "}
                  The frozen definition is two-tier — 15% to give every ticker a corpus, 25% for the
                  black-swan tier the demo narrates — and even so some tickers have zero test events
                  while one name can dominate the pooled result. Per-ticker counts are shown, never
                  hidden behind a pooled average, and the tiers are never conflated in a number.
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function Guard({ n, head, body }: { n: string; head: string; body: string }) {
  return (
    <div className="bg-white px-6 py-6">
      <div className="num text-sm font-semibold" style={{ color: "var(--color-blue)" }}>{n}</div>
      <div className="mt-2 text-[1.0625rem] font-semibold leading-snug text-[var(--color-navy)]">{head}</div>
      <p className="mt-2 text-sm leading-relaxed text-[var(--color-ink-dim)]">{body}</p>
    </div>
  );
}

function Split({ label, v }: { label: string; v: number }) {
  return (
    <div>
      <div className="label">{label}</div>
      <div className="figure mt-2 text-[2.25rem]"
        style={{ color: v > 0 ? "var(--color-blue)" : "var(--color-neg)" }}>
        {signedPct(v)}
      </div>
      <div className="label mt-1">mean crps lift</div>
    </div>
  );
}
