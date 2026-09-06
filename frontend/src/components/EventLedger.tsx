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
    return <div className="label-title py-10 text-center" style={{ color: "var(--color-ink-faint)" }}>loading ledger…</div>;
  }

  if (!events.length) {
    return (
      <Empty>
        <div className="figure text-3xl">0 events</div>
        <p className="mt-3 max-w-[52ch] text-base leading-relaxed">
          <span className="text-[var(--color-ink-dim)]">{ticker}</span> has no five-session window
          in the train period that clears even the 15% detection floor. That is the frozen event
          definition doing its job, not a bug — and it is why the eval reports per-ticker counts
          instead of hiding behind one pooled average.
        </p>
      </Empty>
    );
  }

  return (
    <div className="max-h-[380px] overflow-auto rounded-lg border border-[var(--color-rule)]">
      <table className="w-full min-w-[560px] border-collapse text-left">
        {/* opaque, and after the rule-ramp shift the boundary between the
            frozen header and the scrolling body needs to be unambiguous at
            distance — hence the axis token rather than a hairline. */}
        <thead className="sticky top-0 bg-[var(--color-panel-2)]">
          <tr className="border-b-2 border-[var(--color-axis)]">
            <th className="label border-l-[3px] border-transparent py-3 pr-3 pl-3">date</th>
            <th className="label py-3 pr-6 text-right">move</th>
            <th className="label py-3 pr-3">tier</th>
            <th className="label py-3 pr-3">headline</th>
            <th className="label py-3 pr-3 text-right">art.</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e, i) => (
            <tr
              key={`${e.date}-${i}`}
              onClick={() => onPick(e)}
              onKeyDown={(k) => {
                if (k.key === "Enter" || k.key === " ") {
                  k.preventDefault();
                  onPick(e);
                }
              }}
              tabIndex={0}
              role="button"
              aria-label={`Load ${e.ticker} ${e.date}, ${pct(e.move_pct, 1)} into the control panel`}
              className="group cursor-pointer border-b border-[var(--color-rule)] transition hover:bg-[var(--color-blue-tint)] focus-visible:bg-[var(--color-blue-tint)]"
            >
              <td className="num border-l-[3px] border-transparent py-3 pr-3 pl-3 text-sm text-[var(--color-ink-dim)] transition-colors group-hover:border-[var(--color-blue)] group-focus-visible:border-[var(--color-blue)]">{e.date}</td>
              <td
                className="num py-3 pr-6 text-right text-sm font-semibold"
                style={{ color: e.move_pct >= 0 ? "var(--color-pos)" : "var(--color-neg)" }}
              >
                {/* pct() always emits the sign, so the direction survives with
                    colour switched off entirely. */}
                {pct(e.move_pct, 1)}
              </td>
              <td className="py-3 pr-3">
                {tierOf(e) === "major" ? (
                  <span
                    className="label rounded-full px-2 py-0.5"
                    style={{ background: "var(--color-notice-tint)", color: "var(--color-notice)" }}
                  >
                    major
                  </span>
                ) : (
                  <span className="label">signif.</span>
                )}
              </td>
              <td className="max-w-[1px] truncate py-3 pr-3 text-sm text-[var(--color-ink-dim)]">
                {e.headline || "—"}
              </td>
              <td className="num py-3 pr-3 text-right text-sm text-[var(--color-ink-faint)]">
                {e.articles?.length ?? 0}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
