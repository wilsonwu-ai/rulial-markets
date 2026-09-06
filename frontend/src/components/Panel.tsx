import type { ReactNode } from "react";

/**
 * The structural unit of the console: a white card on the tinted ground,
 * carrying an index chip, a title, and a right-hand slot for a standing
 * caveat. The right slot is doing real work — Console.tsx uses it to keep the
 * contract's own restrictions ("directional hit-rate withheld by contract §7",
 * "flat PIT is the win condition") permanently on screen next to the numbers
 * they qualify.
 *
 * Amex direction: 8px radius, 1px --color-rule, very soft shadow, and a
 * generous 32px gutter. Density drops from 8/10 to ~4/10 by widening this one
 * value, so no component has to be re-laid-out to breathe.
 */
export function Panel({
  title, index, right, children, className = "", delay = 0,
}: {
  title: string;
  index?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <section
      className={`panel rise min-w-0 ${className}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2 border-b border-[var(--color-rule)] px-5 py-4 sm:px-8">
        <div className="flex min-w-0 items-baseline gap-3">
          {index && (
            <span
              className="num shrink-0 rounded-full bg-[var(--color-blue-tint)] px-2 py-0.5 text-xs font-semibold"
              style={{ color: "var(--color-blue)" }}
            >
              {index}
            </span>
          )}
          <h2 className="label-title truncate">{title}</h2>
        </div>
        {/* The caveat slot may wrap and may shrink. It carries long contract
            strings ("directional hit-rate withheld by contract §7"), and a
            `shrink-0` here forces the whole card wider than a phone screen. */}
        {right && <div className="min-w-0 max-w-full sm:text-right">{right}</div>}
      </header>
      <div className="p-5 sm:p-8">{children}</div>
    </section>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-[120px] flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-[var(--color-gray-400)] bg-[var(--color-panel-2)] px-6 py-10 text-center">
      <div className="text-[var(--color-ink-faint)]">{children}</div>
    </div>
  );
}
