"use client";

import type { Mode } from "@/lib/types";

/**
 * Mock vs live, stated honestly, with a health-probe dot that means exactly
 * what it says: grey while the probe is in flight, green/red only once
 * GET /api/health has actually answered. It never defaults to "live".
 *
 * Colour is never the only channel here either — the dot is always paired with
 * the words "backend up" / "backend down" / "probing :8000", and the selected
 * mode carries a filled pill rather than a hue difference alone.
 */
export function ModeToggle({
  mode, setMode, healthy, checking, onRecheck,
}: {
  mode: Mode; setMode: (m: Mode) => void;
  healthy: boolean | null; checking: boolean;
  onRecheck: () => void;
}) {
  const dot =
    checking ? "var(--color-gray-500)"
    : healthy ? "var(--color-up)"
    : "var(--color-down)";

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        onClick={onRecheck}
        title="re-probe GET /api/health"
        className="flex items-center gap-2 rounded-full border border-[var(--color-axis)] bg-white px-4 py-2 transition hover:border-[var(--color-blue)] hover:bg-[var(--color-blue-tint)]"
      >
        <span className={`block h-2.5 w-2.5 rounded-full ${checking ? "pulse-dot" : ""}`}
          style={{ background: dot }} />
        <span className="label-title" style={{ color: "var(--color-ink-dim)" }}>
          {checking ? "probing :8000" : healthy ? "backend up" : "backend down"}
        </span>
      </button>

      <div
        className="flex overflow-hidden rounded-full border border-[var(--color-axis)] bg-white"
        role="group"
        aria-label="data source"
      >
        {(["live", "mock"] as Mode[]).map((m) => {
          const on = mode === m;
          return (
            <button
              key={m}
              onClick={() => setMode(m)}
              aria-pressed={on}
              className="label-title px-5 py-2 transition"
              style={{
                background: on
                  ? m === "live" ? "var(--color-blue)" : "var(--color-notice)"
                  : "transparent",
                color: on ? "#fff" : "var(--color-ink-faint)",
              }}
            >
              {m}
            </button>
          );
        })}
      </div>
    </div>
  );
}
