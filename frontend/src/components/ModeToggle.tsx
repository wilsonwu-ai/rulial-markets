"use client";

import type { Mode } from "@/lib/types";

export function ModeToggle({
  mode, setMode, healthy, checking, onRecheck,
}: {
  mode: Mode; setMode: (m: Mode) => void;
  healthy: boolean | null; checking: boolean;
  onRecheck: () => void;
}) {
  const dot =
    checking ? "var(--color-ink-faint)"
    : healthy ? "var(--color-up)"
    : "var(--color-down)";

  return (
    <div className="flex items-center gap-4">
      <button
        onClick={onRecheck}
        title="re-probe GET /api/health"
        className="flex items-center gap-2 border border-[var(--color-rule)] px-3 py-2 transition hover:border-[var(--color-rule-bright)]"
      >
        <span className={`block h-2 w-2 rounded-full ${checking ? "pulse-dot" : ""}`}
          style={{ background: dot }} />
        <span className="label">
          {checking ? "probing :8000" : healthy ? "backend up" : "backend down"}
        </span>
      </button>

      <div className="flex border border-[var(--color-rule)]" role="group" aria-label="data source">
        {(["live", "mock"] as Mode[]).map((m) => {
          const on = mode === m;
          const color = m === "live" ? "var(--color-phosphor)" : "var(--color-hazard)";
          return (
            <button
              key={m}
              onClick={() => setMode(m)}
              aria-pressed={on}
              className="label px-4 py-2 transition"
              style={{
                background: on ? `color-mix(in srgb, ${color} 14%, transparent)` : "transparent",
                color: on ? color : "var(--color-ink-faint)",
                boxShadow: on ? `inset 0 0 0 1px ${color}` : undefined,
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
