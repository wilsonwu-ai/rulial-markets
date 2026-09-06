"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  type Atlas, type AtlasEvent, type Span,
  DAY_MS, clampSpan, closeAt, isExplained, markerRadius, sliceSeries, toMs, yearOf,
} from "@/lib/atlas";

/**
 * THE ATLAS.
 *
 * Ten tickers, ten lanes, ONE shared time axis running from 1962 to today.
 * Every detected event is a mark on the line it happened to. Zoom and pan the
 * axis and all ten lanes move together, which is the only way a 1987 mark and
 * a 2020 mark are comparable at all.
 *
 * Deliberately almost numberless. In lane mode the chart carries ten ticker
 * symbols and a row of years, and nothing else. Shape first: you should be
 * able to see the 2008 column, the 2020 column and NVDA's 2016-2018 cluster
 * before you have read a single figure. The numbers live in the drill panel,
 * one click away, where they are attached to a cause.
 *
 * ENCODING — every channel is doubled so none of it depends on colour alone:
 *   direction   triangle up / triangle down, AND green / red, AND placed
 *               above / below the price line
 *   magnitude   marker size, 15% (the frozen detection floor) to 50%+
 *   explained   SOLID where we researched a cause, HOLLOW where we did not.
 *               96 of 329 are hollow and that is a fact about our corpus,
 *               not a rendering artifact.
 *
 * Per-lane y is log price, rescaled to what is IN VIEW. An absolute scale
 * would draw AAPL's first eighteen years as a flat line on the floor, because
 * the stock is up ~1,800x. Rescaling on zoom is what makes the early history
 * legible, and the axis is labelled "log price, rescaled to the window".
 */

const W = 1200;
const M = { l: 92, r: 76 };
const LANE_H = 74;
const LANE_GAP = 8;
const LANE_PAD = 11;
const TOP = 16;
const AXIS_H = 38;
const FOCUS_H = 430;

export interface AtlasChartProps {
  atlas: Atlas;
  order: string[];
  view: Span;
  domain: Span;
  setView: (s: Span) => void;
  /** null = all ten lanes; a symbol = one tall chart */
  focus: string | null;
  setFocus: (t: string | null) => void;
  selected: string | null;
  onSelect: (ticker: string, e: AtlasEvent) => void;
  /** "all" | "major" */
  tierFilter: "all" | "major";
  explainedOnly: boolean;
}

export function AtlasChart({
  atlas, order, view, domain, setView, focus, setFocus,
  selected, onSelect, tierFilter, explainedOnly,
}: AtlasChartProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const drag = useRef<{ x: number; lo: number; hi: number; moved: boolean } | null>(null);
  const suppressClick = useRef(false);
  /* The cursor is the one piece of drag state that has to reach the DOM, so it
     is state rather than a ref — reading `drag.current` during render is a
     lie about when React will repaint. */
  const [grabbing, setGrabbing] = useState(false);

  const lanes = useMemo(() => (focus ? [focus] : order), [focus, order]);
  const laneH = focus ? FOCUS_H : LANE_H;
  const H = TOP + lanes.length * (laneH + LANE_GAP) - LANE_GAP + AXIS_H;

  const span = Math.max(1, view.hi - view.lo);
  const x = useCallback(
    (ms: number) => M.l + ((ms - view.lo) / span) * (W - M.l - M.r),
    [view.lo, span],
  );
  const msAt = useCallback(
    (px: number) => view.lo + ((px - M.l) / (W - M.l - M.r)) * span,
    [view.lo, span],
  );

  const pxOf = useCallback((clientX: number) => {
    const el = svgRef.current;
    if (!el) return M.l;
    const r = el.getBoundingClientRect();
    return ((clientX - r.left) / Math.max(1, r.width)) * W;
  }, []);

  /* ---- wheel zoom. Registered by hand because React's onWheel is passive
     and cannot preventDefault, which would let the page scroll away under
     the cursor mid-zoom. ---- */
  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const onWheel = (ev: WheelEvent) => {
      ev.preventDefault();
      const anchor = msAt(pxOf(ev.clientX));
      const factor = Math.exp(ev.deltaY * 0.0016);
      const width = span * factor;
      const lo = anchor - (anchor - view.lo) * (width / span);
      setView(clampSpan({ lo, hi: lo + width }, domain));
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [msAt, pxOf, span, view.lo, domain, setView]);

  const onPointerDown = (ev: React.PointerEvent<SVGSVGElement>) => {
    if (ev.button !== 0) return;
    drag.current = { x: ev.clientX, lo: view.lo, hi: view.hi, moved: false };
    setGrabbing(true);
    (ev.currentTarget as SVGSVGElement).setPointerCapture(ev.pointerId);
  };
  const onPointerMove = (ev: React.PointerEvent<SVGSVGElement>) => {
    const d = drag.current;
    if (!d) return;
    const el = svgRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const dxPx = ((ev.clientX - d.x) / Math.max(1, r.width)) * W;
    if (Math.abs(ev.clientX - d.x) > 3) d.moved = true;
    const dxMs = (dxPx / (W - M.l - M.r)) * (d.hi - d.lo);
    setView(clampSpan({ lo: d.lo - dxMs, hi: d.hi - dxMs }, domain));
  };
  const endDrag = (ev: React.PointerEvent<SVGSVGElement>) => {
    if (drag.current?.moved) {
      suppressClick.current = true;
      // one frame is enough: the synthetic click fires immediately after
      // pointerup, and anything later is a genuine new click.
      requestAnimationFrame(() => { suppressClick.current = false; });
    }
    drag.current = null;
    setGrabbing(false);
    try { (ev.currentTarget as SVGSVGElement).releasePointerCapture(ev.pointerId); } catch { /* already released */ }
  };

  const onKeyDown = (ev: React.KeyboardEvent<SVGSVGElement>) => {
    const step = span * 0.18;
    if (ev.key === "ArrowRight") { ev.preventDefault(); setView(clampSpan({ lo: view.lo + step, hi: view.hi + step }, domain)); }
    else if (ev.key === "ArrowLeft") { ev.preventDefault(); setView(clampSpan({ lo: view.lo - step, hi: view.hi - step }, domain)); }
    else if (ev.key === "+" || ev.key === "=") { ev.preventDefault(); zoomAround((view.lo + view.hi) / 2, 0.7); }
    else if (ev.key === "-" || ev.key === "_") { ev.preventDefault(); zoomAround((view.lo + view.hi) / 2, 1.4); }
    else if (ev.key === "Home") { ev.preventDefault(); setView({ ...domain }); }
  };
  const zoomAround = (anchor: number, factor: number) => {
    const width = span * factor;
    const lo = anchor - (anchor - view.lo) * (width / span);
    setView(clampSpan({ lo, hi: lo + width }, domain));
  };

  /* ---- year gridlines at a round step for the visible span ---- */
  const yearTicks = useMemo(() => {
    const years = span / (365.25 * DAY_MS);
    const step = [1, 2, 5, 10, 20, 50].find((s) => years / s <= 12) ?? 100;
    const y0 = Math.ceil(yearOf(view.lo) / step) * step;
    const out: { year: number; ms: number }[] = [];
    for (let y = y0; ; y += step) {
      const ms = Date.UTC(y, 0, 1);
      if (ms > view.hi) break;
      out.push({ year: y, ms });
    }
    return out;
  }, [span, view.lo, view.hi]);

  /* ---- one lane's geometry, recomputed per view ---- */
  const laneData = useMemo(() => {
    return lanes.map((sym, i) => {
      const t = atlas.tickers[sym];
      const top = TOP + i * (laneH + LANE_GAP);
      if (!t) return { sym, top, pts: [], path: "", marks: [], lo: 0, hi: 0, y: () => top };

      const pts = sliceSeries(t.series, view.lo, view.hi);
      let lmin = Infinity;
      let lmax = -Infinity;
      for (const p of pts) {
        const l = Math.log(p.v);
        if (l < lmin) lmin = l;
        if (l > lmax) lmax = l;
      }
      if (!Number.isFinite(lmin) || lmax - lmin < 1e-9) { lmin = (lmin || 0) - 0.5; lmax = lmin + 1; }
      const padL = (lmax - lmin) * 0.14;
      lmin -= padL; lmax += padL;

      const y = (v: number) =>
        top + LANE_PAD + (1 - (Math.log(v) - lmin) / (lmax - lmin)) * (laneH - 2 * LANE_PAD);

      const path = pts.length
        ? pts.map((p, k) => `${k === 0 ? "M" : "L"}${x(p.ms).toFixed(1)},${y(p.v).toFixed(1)}`).join("")
        : "";

      const marks = t.events
        .filter((e) => {
          if (tierFilter === "major" && e.tier !== "major") return false;
          if (explainedOnly && !isExplained(e)) return false;
          const ms = toMs(e.date);
          return ms >= view.lo - DAY_MS * 4 && ms <= view.hi + DAY_MS * 4;
        })
        .map((e) => {
          const ms = toMs(e.date);
          const price = closeAt(t.series, ms);
          const r = markerRadius(e.move) * (focus ? 1.25 : 1);
          const py = price ? y(price) : top + laneH / 2;
          const up = e.dir === "up";
          /* Markers sit off the line on the side they moved, which is the
             third redundant channel for direction. Clamped inside the lane so
             a 90% NVDA week cannot draw itself over the ticker above it — an
             unclamped mark reads as belonging to the wrong company. */
          const rawCy = up ? py - r - 3.5 : py + r + 3.5;
          const cy = Math.min(top + laneH - r - 2, Math.max(top + r + 2, rawCy));
          return {
            e,
            cx: x(ms),
            cy,
            r,
            up,
            solid: isExplained(e),
          };
        })
        .sort((a, b) => a.r - b.r);

      return { sym, top, pts, path, marks, lo: pts.length ? Math.exp(lmin) : 0, hi: pts.length ? Math.exp(lmax) : 0, y };
    });
  }, [lanes, atlas, view.lo, view.hi, x, laneH, focus, tierFilter, explainedOnly]);

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${W} ${H}`}
      className="w-full touch-none select-none"
      style={{ cursor: grabbing ? "grabbing" : "grab" }}
      role="application"
      tabIndex={0}
      aria-label="Historical price atlas. Drag to pan, scroll to zoom, arrow keys to move, plus and minus to zoom, Home to reset."
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onKeyDown={onKeyDown}
    >
      {/* year gridlines — 1.5px, never darker than gray-200 (DESIGN_AMEX §5) */}
      {yearTicks.map((t) => (
        <g key={t.year}>
          <line
            x1={x(t.ms)} x2={x(t.ms)} y1={TOP - 6} y2={H - AXIS_H + 6}
            stroke="var(--color-gray-200)" strokeWidth={1.5}
          />
          <text
            x={x(t.ms)} y={H - AXIS_H + 26} textAnchor="middle"
            fill="var(--color-ink-faint)"
            style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontVariantNumeric: "tabular-nums" }}
          >
            {t.year}
          </text>
        </g>
      ))}

      {laneData.map((lane) => (
        <g key={lane.sym}>
          {/* lane ground */}
          <rect
            x={M.l} y={lane.top} width={W - M.l - M.r} height={laneH}
            fill={focus ? "var(--color-panel)" : "var(--color-panel-2)"}
            stroke="var(--color-rule-soft)" strokeWidth={1}
          />
          {/* Whole-lane double-click target, and it must be painted BEFORE the
              markers: `fill="transparent"` still receives pointer events, so
              drawn last it silently swallowed every marker click. */}
          <rect
            x={M.l} y={lane.top} width={W - M.l - M.r} height={laneH}
            fill="transparent"
            style={{ cursor: "pointer" }}
            onDoubleClick={() => setFocus(focus ? null : lane.sym)}
          />
          {/* clip so a marker on a lane edge cannot bleed into its neighbour */}
          <clipPath id={`lane-${lane.sym}`}>
            <rect x={M.l} y={lane.top} width={W - M.l - M.r} height={laneH} />
          </clipPath>

          {/* ticker symbol, the only standing text in lane mode */}
          <text
            x={M.l - 14} y={lane.top + laneH / 2 + 6} textAnchor="end"
            fill="var(--color-navy)"
            style={{
              fontFamily: "var(--font-mono)", fontSize: focus ? 22 : 16,
              fontWeight: 700, letterSpacing: "0.02em",
            }}
          >
            {lane.sym}
          </text>
          {!focus && (
            <text
              x={M.l - 14} y={lane.top + laneH / 2 + 24} textAnchor="end"
              fill="var(--color-ink-faint)"
              style={{ fontFamily: "var(--font-sans)", fontSize: 11, letterSpacing: "0.06em" }}
            >
              {atlas.tickers[lane.sym]?.n_events ?? 0} events
            </text>
          )}

          {/* the price line. 2.25px in lane mode, 3px focused — nothing here
              is ever a hairline. */}
          {lane.path ? (
            <path
              d={lane.path} fill="none"
              stroke="var(--color-navy)" strokeWidth={focus ? 3 : 2.25}
              strokeLinejoin="round" strokeLinecap="round" opacity={0.9}
            />
          ) : (
            <text
              x={(M.l + W - M.r) / 2} y={lane.top + laneH / 2 + 5} textAnchor="middle"
              fill="var(--color-ink-faint)"
              style={{ fontFamily: "var(--font-sans)", fontSize: 13 }}
            >
              {lane.sym} has no price history in this window
            </text>
          )}

          {/* focused mode gets a price axis; lane mode deliberately does not */}
          {focus && lane.hi > 0 && (
            <>
              <text x={W - M.r + 10} y={lane.top + LANE_PAD + 5} fill="var(--color-ink-faint)"
                style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontVariantNumeric: "tabular-nums" }}>
                ${fmtPrice(lane.hi)}
              </text>
              <text x={W - M.r + 10} y={lane.top + laneH - LANE_PAD + 5} fill="var(--color-ink-faint)"
                style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontVariantNumeric: "tabular-nums" }}>
                ${fmtPrice(lane.lo)}
              </text>
            </>
          )}

          {/* markers */}
          <g clipPath={`url(#lane-${lane.sym})`}>
          {lane.marks.map((m) => {
            const key = `${lane.sym}|${m.e.date}`;
            const on = selected === key;
            const color = m.up ? "var(--color-pos)" : "var(--color-neg)";
            return (
              <g key={key}>
                {on && (
                  <circle cx={m.cx} cy={m.cy} r={m.r + 7}
                    fill="none" stroke="var(--color-navy)" strokeWidth={2.5} />
                )}
                <path
                  d={tri(m.cx, m.cy, m.r, m.up)}
                  fill={m.solid ? color : "var(--color-panel)"}
                  stroke={color}
                  strokeWidth={2}
                  strokeLinejoin="round"
                  opacity={m.solid ? 0.92 : 1}
                />
                {/* hit target — always at least 22px across so a marker at the
                    detection floor is still clickable from a stage laptop */}
                <circle
                  cx={m.cx} cy={m.cy} r={Math.max(11, m.r + 5)}
                  fill="transparent"
                  style={{ cursor: "pointer" }}
                  onClick={() => { if (!suppressClick.current) onSelect(lane.sym, m.e); }}
                >
                  <title>
                    {`${lane.sym} ${m.e.date}  ${m.e.move >= 0 ? "+" : "−"}${(Math.abs(m.e.move) * 100).toFixed(1)}% over 5 sessions`}
                    {m.e.headline ? `\n${m.e.headline}` : "\ncause not researched"}
                  </title>
                </circle>
              </g>
            );
          })}
          </g>

        </g>
      ))}

      {/* baseline of the time axis — carries meaning, so 2px on the 3:1 token */}
      <line
        x1={M.l} x2={W - M.r} y1={H - AXIS_H + 6} y2={H - AXIS_H + 6}
        stroke="var(--color-axis)" strokeWidth={2}
      />
    </svg>
  );
}

/** Triangle, pointing up or down. Direction survives with colour switched off. */
function tri(cx: number, cy: number, r: number, up: boolean): string {
  const w = r * 0.95;
  return up
    ? `M${cx.toFixed(1)},${(cy - r).toFixed(1)}L${(cx + w).toFixed(1)},${(cy + r * 0.72).toFixed(1)}L${(cx - w).toFixed(1)},${(cy + r * 0.72).toFixed(1)}Z`
    : `M${cx.toFixed(1)},${(cy + r).toFixed(1)}L${(cx + w).toFixed(1)},${(cy - r * 0.72).toFixed(1)}L${(cx - w).toFixed(1)},${(cy - r * 0.72).toFixed(1)}Z`;
}

function fmtPrice(v: number): string {
  if (v >= 1000) return v.toFixed(0);
  if (v >= 10) return v.toFixed(1);
  return v.toFixed(2);
}
