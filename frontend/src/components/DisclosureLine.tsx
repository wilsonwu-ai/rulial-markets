"use client";

import { useState } from "react";
import { LeakagePanel } from "./LeakagePanel";

/**
 * CONTRACT §8 requires the leakage limitation to be stated on the results
 * screen, out loud, in the product. It does not require four paragraphs above
 * the chart, which is what it had become.
 *
 * So: ONE line, always visible, in a blue-tint callout that cannot be mistaken
 * for chrome — plus a control that opens the full disclosure, unchanged, in
 * place. The requirement is prominence, and a one-line callout with the whole
 * thing one click away is more prominent than a wall people scroll past.
 */
export function DisclosureLine({
  famous, obscure, liftFamous, liftObscure,
}: {
  famous?: number; obscure?: number;
  liftFamous?: number; liftObscure?: number;
}) {
  const [open, setOpen] = useState(false);

  if (open) {
    return (
      <div className="grid gap-3">
        <LeakagePanel
          famous={famous} obscure={obscure}
          liftFamous={liftFamous} liftObscure={liftObscure}
        />
        <button className="btn-secondary justify-self-start" onClick={() => setOpen(false)}>
          Collapse the disclosure
        </button>
      </div>
    );
  }

  return (
    <div className="callout flex flex-wrap items-center gap-x-6 gap-y-3 px-6 py-5">
      <span className="label shrink-0" style={{ color: "var(--color-blue)" }}>Required disclosure</span>
      <p className="min-w-[24ch] flex-1 text-[1.0625rem] leading-snug text-[var(--color-ink-dim)]">
        The language model behind this has already read the post-2019 world, so some of any apparent
        skill on a historical event may be memory rather than forecasting.
      </p>
      <button className="btn-secondary shrink-0 bg-white" onClick={() => setOpen(true)}>
        Read the full disclosure
      </button>
    </div>
  );
}
