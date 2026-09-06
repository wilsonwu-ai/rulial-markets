"use client";

import { useState } from "react";

/**
 * CONTRACT §8 — LEAKAGE DISCLOSURE.
 * "State this limitation on the results screen. Out loud, in the product."
 * So it is a designed panel sitting directly under the score, not a footnote.
 */
export function LeakagePanel({
  famous, obscure, liftFamous, liftObscure,
}: {
  famous?: number; obscure?: number;
  liftFamous?: number; liftObscure?: number;
}) {
  const [open, setOpen] = useState(false);
  const haveSplit =
    famous !== undefined && obscure !== undefined &&
    liftFamous !== undefined && liftObscure !== undefined;

  return (
    <section className="panel rise border-[var(--color-hazard)]/40"
      style={{ borderColor: "rgba(255,207,74,0.34)" }}>
      <div className="hazard h-[10px] w-full" />
      <div className="px-6 py-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="label" style={{ color: "var(--color-hazard)" }}>
              04 — Leakage disclosure · required by contract
            </div>
            <h3 className="display mt-3 text-[clamp(1.75rem,3.4vw,2.8rem)] text-[var(--color-ink)]">
              The model has already read the future.
              <span className="block italic text-[var(--color-hazard)]">
                Here is exactly how much that is worth.
              </span>
            </h3>
          </div>
          <button
            onClick={() => setOpen((v) => !v)}
            className="label border border-[var(--color-rule-bright)] px-4 py-2 transition hover:border-[var(--color-hazard)] hover:text-[var(--color-hazard)]"
          >
            {open ? "collapse" : "read the full disclosure"}
          </button>
        </div>

        <p className="mt-5 max-w-[74ch] text-[1.08rem] leading-relaxed text-[var(--color-ink-dim)]">
          Any LLM in this generator was trained on the post-2019 world. We cut the{" "}
          <em className="not-italic text-[var(--color-ink)]">input</em> data at 2019-12-31.
          That does not cut the <em className="not-italic text-[var(--color-ink)]">weights</em>.
          When we ask about a 2018 jump, the model may simply remember what happened.
          Memorization and forecasting are not separable from the outside — that is a published
          result, not a hedge we invented.
        </p>

        <div className="mt-6 grid gap-[1px] bg-[rgba(255,207,74,0.22)] md:grid-cols-3">
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
          <div className="mt-6 border border-[rgba(255,207,74,0.3)] bg-[rgba(255,207,74,0.05)] px-5 py-5">
            <div className="label" style={{ color: "var(--color-hazard)" }}>
              The memorization test, live
            </div>
            <div className="mt-4 grid gap-6 sm:grid-cols-2">
              <Split label={`Famous events (n=${famous})`} v={liftFamous!} />
              <Split label={`Obscure events (n=${obscure})`} v={liftObscure!} />
            </div>
            <p className="mt-4 text-sm leading-relaxed text-[var(--color-ink-dim)]">
              {liftFamous! - liftObscure! > 0.05
                ? "The gap is wide. Skill is concentrated in events the model could plausibly remember — read the headline lift down accordingly."
                : "The two are close. What lift exists is not obviously explained by recall alone."}
            </p>
          </div>
        )}

        {open && (
          <div className="mt-6 grid gap-5 border-t border-[rgba(255,207,74,0.28)] pt-6 text-[0.95rem] leading-relaxed text-[var(--color-ink-dim)] md:grid-cols-2">
            <div>
              <div className="label" style={{ color: "var(--color-hazard)" }}>Prior art we are standing on</div>
              <ul className="mt-3 space-y-3">
                <li>
                  <span className="text-[var(--color-ink)]">Lopez-Lira, Tang &amp; Zhu — “The Memorization Problem”</span>{" "}
                  (arXiv:2504.14765). Proves forecasting ability is formally non-identified under
                  memorization. GPT-4o recalls pre-cutoff S&amp;P 500 daily levels at 0.61% MAPE and
                  post-cutoff at 16.87%; directional accuracy falls 80.6% → 45.7%. Prompting the
                  model to “ignore” what it knows does not work.
                </li>
                <li>
                  <span className="text-[var(--color-ink)]">Gao, Jiang &amp; Yan — Lookahead Propensity</span>{" "}
                  (arXiv:2512.23847). A measured per-event contamination score. Our famous/obscure
                  split is a cheap discrete cousin of it, not an invention of ours.
                </li>
                <li>
                  <span className="text-[var(--color-ink)]">Gneiting, Balabdaoui &amp; Raftery (2007)</span>.
                  Sharpness subject to calibration, PIT histograms. Our win condition is textbook,
                  and we say so rather than dressing it up.
                </li>
              </ul>
            </div>
            <div>
              <div className="label" style={{ color: "var(--color-hazard)" }}>What else could explain a positive lift</div>
              <ul className="mt-3 space-y-3">
                <li>
                  <span className="text-[var(--color-ink)]">Volatility clustering, not text.</span>{" "}
                  After a 25%-in-a-week move, trailing 250-day sigma is stale by construction.
                  Trailing vol measured 1.78× higher post-jump in our own train data. Some of any
                  lift is that, and an oracle using the realized post-jump sigma caps out at only
                  +2.0% — so a large headline number is a reason for suspicion, not celebration.
                </li>
                <li>
                  <span className="text-[var(--color-ink)]">Drift, not dispersion.</span>{" "}
                  The train corpus is 30 up-jumps to 3 down-jumps with +5.77% mean forward return —
                  a bull decade. A naive analog-resampling generator scored +14.8% lift that became
                  −4.5% once demeaned. Every lift on this screen ships with its demeaned twin.
                </li>
                <li>
                  <span className="text-[var(--color-ink)]">Sample size.</span>{" "}
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
    <div className="bg-[var(--color-panel)] px-5 py-5">
      <div className="num text-sm" style={{ color: "var(--color-hazard)" }}>{n}</div>
      <div className="mt-2 text-[1.05rem] font-medium leading-snug text-[var(--color-ink)]">{head}</div>
      <p className="mt-2 text-sm leading-relaxed text-[var(--color-ink-faint)]">{body}</p>
    </div>
  );
}

function Split({ label, v }: { label: string; v: number }) {
  return (
    <div>
      <div className="label">{label}</div>
      <div className="num mt-1 text-4xl"
        style={{ color: v > 0 ? "var(--color-phosphor)" : "var(--color-down)" }}>
        {v >= 0 ? "+" : "−"}{(Math.abs(v) * 100).toFixed(1)}%
      </div>
      <div className="label mt-1">mean crps lift</div>
    </div>
  );
}
