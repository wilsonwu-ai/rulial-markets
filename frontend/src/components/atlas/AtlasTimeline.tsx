"use client";

import { useCallback, useMemo, useRef } from "react";
import { type FlatEvent, type Span, clampSpan, toMs, yearOf } from "@/lib/atlas";

/**
 * The whole 64-year domain in one strip, with the current viewport drawn on
 * it as a window you can drag. Two jobs: it tells you where you are when the
 * main chart is zoomed into eighteen months, and its bars are themselves a
 * finding — events per year, which is why 2008 and 2020 look the way they do
 * before anyone says a word about them.
 *
 * The bars respect the same filters as the chart above. A strip that kept
 * showing all 329 while the chart showed 68 would be quietly lying about
 * what is on screen.
 */
const W = 1200;
const H = 74;
const PAD_L = 92;
const PAD_R = 76;
const BAR_TOP = 12;
const BAR_H = 34;

export function AtlasTimeline({
  events, view, domain, setView,
}: {
  events: FlatEvent[];
  view: Span;
  domain: Span;
  setView: (s: Span) => void;
}) {
  const ref = useRef<SVGSVGElement | null>(null);
  const drag = useRef<{ mode: "pan" | "lo" | "hi"; x: number; lo: number; hi: number } | null>(null);

  const span = Math.max(1, domain.hi - domain.lo);
  const x = useCallback(
    (ms: number) => PAD_L + ((ms - domain.lo) / span) * (W - PAD_L - PAD_R),
    [domain.lo, span],
  );
  const msAt = useCallback(
    (px: number) => domain.lo + ((px - PAD_L) / (W - PAD_L - PAD_R)) * span,
    [domain.lo, span],
  );
  const pxOf = useCallback((clientX: number) => {
    const el = ref.current;
    if (!el) return PAD_L;
    const r = el.getBoundingClientRect();
    return ((clientX - r.left) / Math.max(1, r.width)) * W;
  }, []);

  const { bars, maxN, years } = useMemo(() => {
    const counts = new Map<number, number>();
    for (const e of events) {
      const y = yearOf(toMs(e.date));
      counts.set(y, (counts.get(y) ?? 0) + 1);
    }
    const y0 = yearOf(domain.lo);
    const y1 = yearOf(domain.hi);
    const list: { year: number; n: number }[] = [];
    for (let y = y0; y <= y1; y++) list.push({ year: y, n: counts.get(y) ?? 0 });
    return { bars: list, maxN: Math.max(1, ...list.map((b) => b.n)), years: y1 - y0 + 1 };
  }, [events, domain.lo, domain.hi]);

  const bw = Math.max(2, (W - PAD_L - PAD_R) / Math.max(1, years) - 1);

  const vLo = x(view.lo);
  const vHi = x(view.hi);
  const EDGE = 9;

  const onDown = (ev: React.PointerEvent<SVGSVGElement>) => {
    const px = pxOf(ev.clientX);
    let mode: "pan" | "lo" | "hi" = "pan";
    if (Math.abs(px - vLo) <= EDGE) mode = "lo";
    else if (Math.abs(px - vHi) <= EDGE) mode = "hi";
    else if (px < vLo || px > vHi) {
      // outside the window: jump, keeping the current width
      const width = view.hi - view.lo;
      const c = msAt(px);
      setView(clampSpan({ lo: c - width / 2, hi: c + width / 2 }, domain));
      return;
    }
    drag.current = { mode, x: ev.clientX, lo: view.lo, hi: view.hi };
    (ev.currentTarget as SVGSVGElement).setPointerCapture(ev.pointerId);
  };

  const onMove = (ev: React.PointerEvent<SVGSVGElement>) => {
    const d = drag.current;
    if (!d) return;
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const dxMs = (((ev.clientX - d.x) / Math.max(1, r.width)) * W / (W - PAD_L - PAD_R)) * span;
    if (d.mode === "pan") setView(clampSpan({ lo: d.lo + dxMs, hi: d.hi + dxMs }, domain));
    else if (d.mode === "lo") setView(clampSpan({ lo: Math.min(d.lo + dxMs, d.hi - 60 * 86400000), hi: d.hi }, domain));
    else setView(clampSpan({ lo: d.lo, hi: Math.max(d.hi + dxMs, d.lo + 60 * 86400000) }, domain));
  };

  const onUp = (ev: React.PointerEvent<SVGSVGElement>) => {
    drag.current = null;
    try { (ev.currentTarget as SVGSVGElement).releasePointerCapture(ev.pointerId); } catch { /* noop */ }
  };

  return (
    <svg
      ref={ref}
      viewBox={`0 0 ${W} ${H}`}
      className="w-full touch-none select-none"
      role="img"
      aria-label={`Events per year across the whole record. Current window ${new Date(view.lo).getUTCFullYear()} to ${new Date(view.hi).getUTCFullYear()}.`}
      onPointerDown={onDown}
      onPointerMove={onMove}
      onPointerUp={onUp}
      onPointerCancel={onUp}
      style={{ cursor: "ew-resize" }}
    >
      <text
        x={PAD_L - 14} y={BAR_TOP + BAR_H - 4} textAnchor="end"
        fill="var(--color-ink-faint)"
        style={{ fontFamily: "var(--font-sans)", fontSize: 11, fontWeight: 600, letterSpacing: "0.08em" }}
      >
        EVENTS / YR
      </text>

      {bars.map((b) => {
        const h = b.n === 0 ? 0 : Math.max(3, (b.n / maxN) * BAR_H);
        return (
          <rect
            key={b.year}
            x={x(Date.UTC(b.year, 0, 1))}
            y={BAR_TOP + BAR_H - h}
            width={bw}
            height={h}
            fill="var(--color-blue-light)"
            opacity={0.85}
          />
        );
      })}

      <line
        x1={PAD_L} x2={W - PAD_R} y1={BAR_TOP + BAR_H} y2={BAR_TOP + BAR_H}
        stroke="var(--color-axis)" strokeWidth={2}
      />

      {[domain.lo, (domain.lo + domain.hi) / 2, domain.hi].map((ms, i) => (
        <text
          key={i} x={x(ms)} y={BAR_TOP + BAR_H + 20}
          textAnchor={i === 0 ? "start" : i === 2 ? "end" : "middle"}
          fill="var(--color-ink-faint)"
          style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontVariantNumeric: "tabular-nums" }}
        >
          {new Date(ms).getUTCFullYear()}
        </text>
      ))}

      {/* the viewport window */}
      <rect
        x={Math.min(vLo, vHi)} y={BAR_TOP - 8}
        width={Math.max(3, Math.abs(vHi - vLo))} height={BAR_H + 14}
        fill="var(--color-blue)" fillOpacity={0.13}
        stroke="var(--color-blue)" strokeWidth={2}
        style={{ cursor: "grab" }}
      />
      {[vLo, vHi].map((px, i) => (
        <rect
          key={i} x={px - 3} y={BAR_TOP - 12} width={6} height={BAR_H + 22}
          fill="var(--color-blue)" rx={3} style={{ cursor: "ew-resize" }}
        />
      ))}
    </svg>
  );
}
