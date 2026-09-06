import type { ReactNode } from "react";

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
      className={`panel rise ${className}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <header className="flex items-baseline justify-between gap-4 border-b border-[var(--color-rule)] px-5 py-3">
        <div className="flex items-baseline gap-3 min-w-0">
          {index && (
            <span className="num text-[0.7rem] text-[var(--color-phosphor)] opacity-70">
              {index}
            </span>
          )}
          <h2 className="label label-bright truncate">{title}</h2>
        </div>
        {right && <div className="shrink-0">{right}</div>}
      </header>
      <div className="p-5">{children}</div>
    </section>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-[120px] flex-col items-center justify-center gap-2 border border-dashed border-[var(--color-rule)] px-6 py-8 text-center">
      <div className="text-[var(--color-ink-faint)]">{children}</div>
    </div>
  );
}
