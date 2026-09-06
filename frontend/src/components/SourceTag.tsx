"use client";

import type { Mode } from "@/lib/types";

export type SourceKind = Mode | "atlas";

/**
 * Per-panel provenance. A page-level banner reading "real" while one panel
 * quietly rendered an in-browser RNG grid is a defect QA already caught once,
 * so provenance is attached to the panel that has it, not to the page.
 *
 * "atlas" is its own kind on purpose: the bundled price-and-cause data is real
 * and is NOT governed by the live/precomputed/mock switch, and a badge that
 * inherited the page mode would be wrong in both directions.
 */
export function SourceTag({ source, detail }: { source: SourceKind; detail?: string }) {
  const s = {
    live: { text: "Live model", color: "var(--color-blue)", bg: "var(--color-blue-tint)" },
    baked: { text: "Precomputed · real", color: "var(--color-accent)", bg: "#EDF1F9" },
    mock: { text: "Synthetic · not model output", color: "var(--color-notice)", bg: "var(--color-notice-tint)" },
    atlas: { text: "Bundled real data", color: "var(--color-blue)", bg: "var(--color-blue-tint)" },
  }[source];

  return (
    <span className="inline-flex flex-wrap items-center gap-2">
      <span
        className="label rounded-full border px-3 py-1"
        style={{ color: s.color, background: s.bg, borderColor: s.color }}
      >
        {s.text}
      </span>
      {detail && <span className="text-sm text-[var(--color-ink-faint)]">{detail}</span>}
    </span>
  );
}

/** Stated on a panel that has no real data in the current mode. */
export function NoRealData({ what, mode }: { what: string; mode: Mode }) {
  return (
    <div className="callout-notice px-6 py-5">
      <div className="label" style={{ color: "var(--color-notice)" }}>Nothing real to show here</div>
      <p className="mt-2 max-w-[72ch] text-[0.9375rem] leading-relaxed text-[var(--color-ink-dim)]">
        {what} There is no precomputed bundle for this combination and the backend is not answering,
        so this panel is empty rather than filled with in-browser synthetic numbers. Current source:{" "}
        <span className="num font-semibold">{mode}</span>.
      </p>
    </div>
  );
}
