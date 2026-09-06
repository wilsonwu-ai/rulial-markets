"use client";

import type { EventRec } from "@/lib/types";
import { Empty } from "./Panel";
import { pct } from "@/lib/quant";
import { TIER_MAJOR } from "@/lib/types";

/** A tier badge. "major" is the >=25% black-swan tier the stage narrative uses;
 *  "significant" is the >=15% detection floor that gives every ticker a corpus. */
function tierOf(e: EventRec): "major" | "significant" {
  if (typeof e.tier === "string") return e.tier.toLowerCase().startsWith("maj") ? "major" : "significant";
  if (typeof e.tier === "number") return e.tier >= TIER_MAJOR ? "major" : "significant";
  return Math.abs(e.move_pct) >= TIER_MAJOR ? "major" : "significant";
}

/**
 * The seed ledger from GET /api/events (train period only).
 * Six of ten universe tickers can legitimately have ZERO events at the frozen
 * 25%/5-day definition — the empty state is a first-class screen here, not a
 * crash.
 */
export function EventLedger({
  events, ticker, onPick, loading,
}: {
  events: EventRec[]; ticker: string;
  onPick: (e: EventRec) => void;
  loading: boolean;
}) {
  if (loading) {
    return <div className="label py-8 text-center">loading ledger…</div>;
  }

  if (!events.length) {
    return (
      <Empty>
        <div className="num text-2xl text-[var(--color-ink-dim)]">0 events</div>
        <p className="mt-3 max-w-[48ch] text-sm leading-relaxed">
          <span className="text-[var(--color-ink-dim)]">{ticker}</span> has no five-session window
          in the train period that clears even the 15% detection floor. That is the frozen event
          definition doing its job, not a bug — and it is why the eval reports per-ticker counts
          instead of hiding behind one pooled average.
        </p>
      </Empty>
    );
  }

  return (
    <div className="max-h-[340px] overflow-y-auto">
      <table className="w-full border-collapse text-left">
        <thead className="sticky top-0 bg-[var(--color-panel)]">
          <tr className="border-b border-[var(--color-rule)]">
            <th className="label py-2 pr-3 font-normal">date</th>
            <th className="label py-2 pr-3 text-right font-normal">move</th>
            <th className="label py-2 pr-3 font-normal">tier</th>
            <th className="label py-2 pr-3 font-normal">headline</th>
            <th className="label py-2 text-right font-normal">art.</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e, i) => (
            <tr
              key={`${e.date}-${i}`}
              onClick={() => onPick(e)}
              className="cursor-pointer border-b border-[var(--color-rule)]/60 transition hover:bg-[var(--color-panel-2)]"
            >
              <td className="num py-2.5 pr-3 text-sm text-[var(--color-ink-dim)]">{e.date}</td>
              <td
                className="num py-2.5 pr-3 text-right text-sm"
                style={{ color: e.move_pct >= 0 ? "var(--color-up)" : "var(--color-down)" }}
              >
                {pct(e.move_pct, 1)}
              </td>
              <td className="py-2.5 pr-3">
                {tierOf(e) === "major" ? (
                  <span className="label" style={{ color: "var(--color-hazard)" }}>major</span>
                ) : (
                  <span className="label">signif.</span>
                )}
              </td>
              <td className="max-w-[1px] truncate py-2.5 pr-3 text-sm text-[var(--color-ink-faint)]">
                {e.headline || "—"}
              </td>
              <td className="num py-2.5 text-right text-sm text-[var(--color-ink-faint)]">
                {e.articles?.length ?? 0}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
