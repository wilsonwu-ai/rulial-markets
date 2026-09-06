"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  type Atlas, type AtlasEvent, type Span,
  ATLAS_NOTICE, atlasDomain, clampSpan, flattenEvents, isExplained, toMs,
} from "@/lib/atlas";
import { UNIVERSE } from "@/lib/types";
import { AtlasChart } from "./AtlasChart";
import { AtlasTimeline } from "./AtlasTimeline";
import { EventDrill } from "./EventDrill";

/**
 * STATE 1 — THE ATLAS. The default view, and the one that has to work with the
 * sound off.
 *
 * Three numbers on this screen: how far back the record goes, how many events
 * are marked, and how many of those we can explain. Everything else is shape.
 * The previous build opened with roughly forty figures and three caveat
 * paragraphs before the first chart, which is the complaint this whole view
 * exists to answer.
 */
export function AtlasView({
  atlas, onBranch,
}: {
  atlas: Atlas;
  onBranch: (ticker: string, date: string, headline?: string) => void;
}) {
  const domain = useMemo(() => atlasDomain(atlas), [atlas]);
  const [view, setViewRaw] = useState<Span>(() => ({ ...domain }));
  const [focus, setFocus] = useState<string | null>(null);
  const [tierFilter, setTierFilter] = useState<"all" | "major">("all");
  const [explainedOnly, setExplainedOnly] = useState(false);
  const [sel, setSel] = useState<{ ticker: string; event: AtlasEvent } | null>(null);
  const drillRef = useRef<HTMLDivElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const setView = useCallback(
    (s: Span) => setViewRaw(clampSpan(s, domain)),
    [domain],
  );

  /**
   * Focusing a ticker fits the axis to that ticker's own life. Otherwise
   * opening NVDA leaves two-thirds of the chart showing 1962-1998, a period in
   * which NVDA did not exist — technically true and useless. Clearing the
   * focus goes back to the whole record.
   *
   * Done in the handler rather than an effect on `focus`: this is a response to
   * a user action, not a synchronisation with an external system, and an effect
   * here would be a cascading render for no reason.
   */
  const changeFocus = useCallback((sym: string | null) => {
    setFocus(sym);
    if (!sym) { setViewRaw({ ...domain }); return; }
    const t = atlas.tickers[sym];
    if (!t?.first || !t?.last) return;
    const lo = toMs(t.first);
    const hi = toMs(t.last);
    const pad = Math.max((hi - lo) * 0.02, 30 * 86400000);
    setViewRaw(clampSpan({ lo: lo - pad, hi: hi + pad }, domain));
  }, [atlas, domain]);

  // The universe order is frozen in CONTRACT §1; render in that order so the
  // lanes never reshuffle between sessions.
  const order = useMemo(
    () => UNIVERSE.filter((s) => atlas.tickers[s]),
    [atlas],
  );

  const allEvents = useMemo(
    () => flattenEvents(atlas, focus ? [focus] : order),
    [atlas, focus, order],
  );
  const filtered = useMemo(
    () => allEvents.filter(
      (e) => (tierFilter === "all" || e.tier === "major") && (!explainedOnly || isExplained(e)),
    ),
    [allEvents, tierFilter, explainedOnly],
  );

  const explainedCount = useMemo(() => filtered.filter(isExplained).length, [filtered]);
  const startYear = new Date(domain.lo).getUTCFullYear();
  const endYear = new Date(domain.hi).getUTCFullYear();

  const pick = useCallback((ticker: string, event: AtlasEvent) => {
    setSel({ ticker, event });
  }, []);

  useEffect(() => {
    if (!sel) return;
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // On a narrow screen the drill lands below the fold; a marker click that
    // appears to do nothing is worse than no drill at all.
    if (typeof window !== "undefined" && window.innerWidth < 1280) {
      drillRef.current?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
    }
  }, [sel]);

  /* On a phone the chart is wider than the screen and its scroller opens at
     the left — which is 1962, where nine of the ten tickers do not exist yet
     and there is not a single marker. Open at the right instead, where the
     events are, so the first thing a phone shows is the thing worth seeing. */
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (el.scrollWidth > el.clientWidth) el.scrollLeft = el.scrollWidth;
  }, [atlas, focus]);

  const eras: { label: string; from: number }[] = [
    { label: "All", from: startYear },
    { label: "1990+", from: 1990 },
    { label: "2000+", from: 2000 },
    { label: "2010+", from: 2010 },
    { label: "2020+", from: 2020 },
  ];

  return (
    /* `[&>*]:min-w-0` is load-bearing: a grid item defaults to
       min-width:auto, so one rigid segmented control refused to shrink and
       pushed the ENTIRE page into horizontal scroll on a phone. */
    <div className="grid gap-6 [&>*]:min-w-0">
      {/* ---------- the only figures on first view ---------- */}
      <header className="rise">
        <h1 className="display text-[clamp(2rem,4.4vw,3rem)]">
          Every move that mattered,
          <span className="italic" style={{ color: "var(--color-blue)" }}> on one axis</span>
        </h1>
        <p className="mt-4 max-w-[68ch] text-[1.125rem] leading-relaxed text-[var(--color-ink-dim)]">
          Ten tickers, one shared timeline. Each mark is a week in which the stock moved at least
          15%. Click one to see what caused it. Then branch, and ask what else could have happened.
        </p>

        <div className="mt-7 flex flex-wrap items-stretch gap-px overflow-hidden rounded-lg border border-[var(--color-rule)] bg-[var(--color-rule)]">
          <Fact k="Record covers" v={`${startYear}–${endYear}`} />
          <Fact k={focus ? `${focus} events marked` : "Events marked"} v={String(filtered.length)} />
          <Fact k="With a researched cause" v={`${explainedCount}`} sub={`of ${filtered.length}`} />
          <div className="flex min-w-[240px] flex-1 items-center gap-3 bg-[var(--color-blue-tint)] px-6 py-5">
            <span className="mt-[3px] block h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: "var(--color-blue)" }} />
            <div className="min-w-0">
              <div className="label" style={{ color: "var(--color-blue)" }}>Real data</div>
              <p className="mt-1 text-sm leading-snug text-[var(--color-ink-dim)]">
                Real closes and researched causes, bundled. No model output on this screen.
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* ---------- controls ---------- */}
      <div className="panel flex flex-wrap items-center gap-x-6 gap-y-4 px-5 py-4 sm:px-6">
        <Seg label="Era">
          {eras.map((e) => {
            const on =
              e.label === "All"
                ? view.lo <= domain.lo + 86400000 && view.hi >= domain.hi - 86400000
                : new Date(view.lo).getUTCFullYear() === e.from;
            return (
              <SegBtn
                key={e.label}
                on={on}
                onClick={() =>
                  setView(
                    e.label === "All"
                      ? { ...domain }
                      : { lo: Date.UTC(e.from, 0, 1), hi: domain.hi },
                  )
                }
              >
                {e.label}
              </SegBtn>
            );
          })}
        </Seg>

        <Seg label="Size">
          <SegBtn on={tierFilter === "all"} onClick={() => setTierFilter("all")}>All ≥15%</SegBtn>
          <SegBtn on={tierFilter === "major"} onClick={() => setTierFilter("major")}>Major ≥25%</SegBtn>
        </Seg>

        <Seg label="Cause">
          <SegBtn on={!explainedOnly} onClick={() => setExplainedOnly(false)}>Show all</SegBtn>
          <SegBtn on={explainedOnly} onClick={() => setExplainedOnly(true)}>Explained only</SegBtn>
        </Seg>

        <label className="ml-auto flex items-center gap-3">
          <span className="label">Ticker</span>
          <select
            value={focus ?? ""}
            onChange={(e) => changeFocus(e.target.value || null)}
            className="px-3 py-2"
          >
            <option value="">All ten</option>
            {order.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>
      </div>

      {/* ---------- chart + drill ---------- */}
      <div className={sel ? "grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_380px]" : "grid min-w-0 gap-6"}>
        <div className="panel min-w-0 overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-b border-[var(--color-rule)] px-5 py-3 sm:px-6">
            <span className="label">
              {focus ? `${focus} · log price, rescaled to the window` : "Log price per lane, rescaled to the window"}
            </span>
            <span className="text-sm text-[var(--color-ink-faint)]">
              drag to pan · scroll to zoom · double-click a lane to open it
            </span>
          </div>

          <div ref={scrollRef} className="overflow-x-auto">
            <div className="min-w-[720px] px-2 py-3 sm:px-4">
              <AtlasChart
                atlas={atlas}
                order={order}
                view={view}
                domain={domain}
                setView={setView}
                focus={focus}
                setFocus={changeFocus}
                selected={sel ? `${sel.ticker}|${sel.event.date}` : null}
                onSelect={pick}
                tierFilter={tierFilter}
                explainedOnly={explainedOnly}
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-x-7 gap-y-3 border-t border-[var(--color-rule)] px-5 py-4 sm:px-6">
            <Key glyph="up" color="var(--color-pos)" solid label="up week, cause known" />
            <Key glyph="down" color="var(--color-neg)" solid label="down week, cause known" />
            <Key glyph="down" color="var(--color-neg)" solid={false} label="hollow = cause not researched" />
            <span className="label">bigger mark = bigger move</span>
            <button
              className="btn-secondary ml-auto"
              onClick={() => changeFocus(null)}
            >
              Reset view
            </button>
          </div>
        </div>

        {sel && (
          <div ref={drillRef} className="min-w-0 xl:sticky xl:top-6 xl:self-start">
            <EventDrill
              ticker={sel.ticker}
              event={sel.event}
              onClose={() => setSel(null)}
              onBranch={() => onBranch(sel.ticker, sel.event.date, sel.event.headline)}
            />
          </div>
        )}
      </div>

      {/* ---------- overview strip ---------- */}
      <div className="panel min-w-0 overflow-hidden">
        <div className="overflow-x-auto">
          <div className="min-w-[720px] px-2 py-3 sm:px-4">
            <AtlasTimeline events={filtered} view={view} domain={domain} setView={setView} />
          </div>
        </div>
        <p className="border-t border-[var(--color-rule)] px-5 py-3 text-sm leading-snug text-[var(--color-ink-faint)] sm:px-6">
          {ATLAS_NOTICE} Drag the blue window to move the chart above.
        </p>
      </div>

      {!sel && (
        <p className="text-center text-[1.0625rem] leading-relaxed text-[var(--color-ink-faint)]">
          Pick any mark to see the headline, the cause and the sources behind it.
        </p>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- pieces */

function Fact({ k, v, sub }: { k: string; v: string; sub?: string }) {
  return (
    <div className="min-w-[150px] flex-1 bg-[var(--color-panel)] px-6 py-5">
      <div className="label">{k}</div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="figure text-[2rem]">{v}</span>
        {sub && <span className="num text-sm text-[var(--color-ink-faint)]">{sub}</span>}
      </div>
    </div>
  );
}

function Seg({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex min-w-0 items-center gap-2 sm:gap-3">
      <span className="label shrink-0">{label}</span>
      <div className="flex min-w-0 overflow-hidden rounded-full border border-[var(--color-axis)] bg-white">
        {children}
      </div>
    </div>
  );
}

function SegBtn({
  on, onClick, children,
}: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      aria-pressed={on}
      className="px-3 py-1.5 text-[0.8125rem] font-semibold transition sm:px-4 sm:text-sm"
      style={{
        background: on ? "var(--color-blue)" : "transparent",
        color: on ? "#fff" : "var(--color-ink-dim)",
      }}
    >
      {children}
    </button>
  );
}

function Key({
  glyph, color, solid, label,
}: { glyph: "up" | "down"; color: string; solid: boolean; label: string }) {
  const d = glyph === "up" ? "M9,2 L16,14 L2,14 Z" : "M9,16 L16,4 L2,4 Z";
  return (
    <span className="flex items-center gap-2">
      <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden>
        <path d={d} fill={solid ? color : "var(--color-panel)"} stroke={color} strokeWidth={2} strokeLinejoin="round" />
      </svg>
      <span className="label">{label}</span>
    </span>
  );
}
