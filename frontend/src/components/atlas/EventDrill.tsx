"use client";

import type { AtlasEvent } from "@/lib/atlas";
import { categoryLabel, isExplained } from "@/lib/atlas";

/**
 * DRILL — one event, facts only.
 *
 * There is deliberately NO model output on this panel. Not a quantile, not a
 * lift, not a probability. The date, what the stock actually did, the
 * researched headline, the cause, the category and the source links: things
 * that happened, with somewhere to go and check.
 *
 * This is the strongest material in the project and it was previously not on
 * screen anywhere. Mixing a forecast into it would put the one part a viewer
 * can verify next to the part they cannot, and the honest thing is to keep the
 * two apart until the viewer chooses to branch.
 *
 * 96 of the 329 events have no researched cause. That state is designed, not
 * degraded: it says so plainly instead of showing an empty field.
 */
export function EventDrill({
  ticker, event, onBranch, onClose,
}: {
  ticker: string;
  event: AtlasEvent;
  onBranch: () => void;
  onClose: () => void;
}) {
  const up = event.dir === "up";
  const color = up ? "var(--color-pos)" : "var(--color-neg)";
  const explained = isExplained(event);

  return (
    <aside
      className="panel rise flex min-w-0 flex-col overflow-hidden"
      aria-label={`Event detail for ${ticker} on ${event.date}`}
    >
      <header className="flex items-start justify-between gap-4 border-b border-[var(--color-rule)] px-6 py-5">
        <div className="min-w-0">
          <div className="label" style={{ color: "var(--color-blue)" }}>What happened</div>
          <div className="num mt-2 text-2xl font-bold text-[var(--color-navy)]">
            {ticker} <span className="font-normal text-[var(--color-ink-faint)]">· {event.date}</span>
          </div>
        </div>
        <button onClick={onClose} className="btn-secondary shrink-0" aria-label="Close event detail">
          Close
        </button>
      </header>

      <div className="grid min-w-0 gap-6 overflow-y-auto px-6 py-6">
        {/* the one number this panel is allowed: the realized move */}
        <div className="flex flex-wrap items-end gap-x-5 gap-y-2">
          <div className="figure text-[clamp(2.5rem,6vw,3.25rem)]" style={{ color }}>
            {event.move >= 0 ? "+" : "−"}{(Math.abs(event.move) * 100).toFixed(1)}%
          </div>
          <div className="mb-2 text-[1.0625rem] leading-snug text-[var(--color-ink-dim)]">
            <span aria-hidden>{up ? "▲" : "▼"}</span>{" "}
            {up ? "up" : "down"} over five sessions
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Chip
            text={event.tier === "major" ? "major ≥ 25%" : "significant ≥ 15%"}
            tone={event.tier === "major" ? "notice" : "plain"}
          />
          <Chip text={categoryLabel(event.category)} tone="blue" />
          {event.famous && <Chip text="famous" tone="blue" />}
          {!explained && <Chip text="cause not researched" tone="notice" />}
        </div>

        {explained ? (
          <>
            <h3 className="max-w-[52ch] text-[1.375rem] font-semibold leading-snug text-[var(--color-navy)]">
              {event.headline}
            </h3>
            {event.cause && (
              <p className="max-w-[62ch] border-l-[3px] border-[var(--color-blue)] pl-5 text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)]">
                {event.cause}
              </p>
            )}
          </>
        ) : (
          <div className="rounded-lg border border-dashed border-[var(--color-gray-400)] bg-[var(--color-panel-2)] px-5 py-5">
            <div className="label">No researched cause on file</div>
            <p className="mt-2 max-w-[56ch] text-[0.9375rem] leading-relaxed text-[var(--color-ink-dim)]">
              The move is measured from real closes. The explanation is not something we have for
              this one, and we would rather show the gap than write a plausible sentence into it.
            </p>
          </div>
        )}

        {event.sources && event.sources.length > 0 && (
          <div className="border-t border-[var(--color-rule)] pt-5">
            <div className="label mb-3">Sources · {event.sources.length}</div>
            <ul className="grid gap-2">
              {event.sources.map((s) => (
                <li key={s} className="min-w-0">
                  <a
                    href={s}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block truncate text-[0.9375rem] font-medium text-[var(--color-blue)] underline decoration-[var(--color-blue-pale)] underline-offset-4 hover:decoration-[var(--color-blue)]"
                    title={s}
                  >
                    {hostOf(s)} <span className="text-[var(--color-ink-faint)]">{pathOf(s)}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <footer className="mt-auto border-t border-[var(--color-rule)] bg-[var(--color-panel-2)] px-6 py-5">
        <button onClick={onBranch} className="btn-primary w-full">
          Branch from {event.date}
        </button>
        <p className="mt-3 text-sm leading-snug text-[var(--color-ink-faint)]">
          Nothing above came from the model. Branching is where the model starts.
        </p>
      </footer>
    </aside>
  );
}

function Chip({ text, tone }: { text: string; tone: "blue" | "notice" | "plain" }) {
  const s = {
    blue: { color: "var(--color-blue)", background: "var(--color-blue-tint)", borderColor: "var(--color-blue-pale)" },
    notice: { color: "var(--color-notice)", background: "var(--color-notice-tint)", borderColor: "var(--color-notice-rule)" },
    plain: { color: "var(--color-ink-dim)", background: "var(--color-gray-100)", borderColor: "var(--color-gray-200)" },
  }[tone];
  return (
    <span className="label rounded-full border px-3 py-1" style={s}>
      {text}
    </span>
  );
}

function hostOf(u: string): string {
  try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return u; }
}
function pathOf(u: string): string {
  try {
    const p = new URL(u).pathname;
    return p.length > 1 ? p : "";
  } catch { return ""; }
}
