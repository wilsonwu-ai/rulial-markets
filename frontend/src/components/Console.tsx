"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, apiSourced, probeHealth } from "@/lib/api";
import { mockTickers } from "@/lib/mock";
import { bakedAvailable } from "@/lib/baked";
import { type Atlas, loadAtlas } from "@/lib/atlas";
import type { Backtest, EventRec, Mode, TickerInfo } from "@/lib/types";
import { TRAIN_END } from "@/lib/types";
import { ModeToggle } from "./ModeToggle";
import { AtlasView } from "./atlas/AtlasView";
import { BranchView } from "./atlas/BranchView";
import { EvidenceView } from "./EvidenceView";
import { PRESETS } from "./presets";

/**
 * THE SHELL.
 *
 * Three states, in the order a person meets them:
 *
 *   ATLAS    every event that ever moved these ten names, on one axis.
 *            Almost no numbers. The chart IS the interface.
 *   BRANCH   pick a point, describe something that did not happen, watch the
 *            futures fan out of the real line.
 *   EVIDENCE walk-forward, inverse search, seed corpus, full disclosure.
 *
 * What changed from the previous build is ordering, not content. Every panel
 * that existed still exists and none of them lost a capability. They stopped
 * arriving all at once, in front of the chart, forty figures deep.
 *
 * Data-source honesty is unchanged in substance and stricter in placement:
 * live -> precomputed -> mock, decided by a health probe, stated in the
 * masthead, and re-stated PER PANEL by <SourceTag> so a page-level "real"
 * badge can never cover a panel that quietly fell back.
 */
export type ViewKey = "atlas" | "branch" | "evidence";

export function Console() {
  const [mode, setMode] = useState<Mode>("mock");
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(true);
  const decided = useRef(false);

  const [view, setView] = useState<ViewKey>("atlas");
  const [atlas, setAtlas] = useState<Atlas | null>(null);
  const [atlasFailed, setAtlasFailed] = useState(false);

  const [tickers, setTickers] = useState<TickerInfo[]>(mockTickers());
  const [ticker, setTicker] = useState(PRESETS[0].ticker);
  const [asOf, setAsOf] = useState(PRESETS[0].as_of);
  const [text, setText] = useState(PRESETS[0].text);
  const horizon = 5;

  const [ledger, setLedger] = useState<
    {
      key: string;
      events: EventRec[]; eventsSource: Mode;
      bt: Backtest | null; btSource: Mode | null;
    } | null
  >(null);
  const ledgerKey = `${mode}|${ticker}`;
  const fresh = ledger?.key === ledgerKey ? ledger : null;
  const events = fresh?.events ?? [];
  const bt = fresh?.bt ?? null;
  const eventsLoading = fresh === null;

  /* ---- health probe decides the initial mode, once ---- */
  const applyProbe = useCallback((ok: boolean) => {
    setHealthy(ok);
    setChecking(false);
    if (decided.current) return;
    decided.current = true;
    if (ok) { setMode("live"); return; }
    void bakedAvailable().then((has) => setMode(has ? "baked" : "mock"));
  }, []);

  const recheck = useCallback(async () => {
    setChecking(true);
    const ok = await probeHealth();
    applyProbe(ok);
    return ok;
  }, [applyProbe]);

  useEffect(() => {
    let dead = false;
    void probeHealth().then((ok) => { if (!dead) applyProbe(ok); });
    return () => { dead = true; };
  }, [applyProbe]);

  /* ---- the atlas bundle. Real, and independent of `mode`. ---- */
  useEffect(() => {
    let dead = false;
    void loadAtlas().then((a) => {
      if (dead) return;
      if (a) setAtlas(a); else setAtlasFailed(true);
    });
    return () => { dead = true; };
  }, []);

  /* ---- ticker list ---- */
  useEffect(() => {
    let dead = false;
    api.tickers(mode)
      .then((t) => { if (!dead && t.length) setTickers(t); })
      .catch(() => { if (!dead) setTickers(mockTickers()); });
    return () => { dead = true; };
  }, [mode]);

  /* ---- ledger + backtest follow the selected ticker ---- */
  useEffect(() => {
    let dead = false;
    const key = `${mode}|${ticker}`;
    Promise.all([
      apiSourced.events(mode, ticker).catch(() => ({ data: [] as EventRec[], source: mode })),
      apiSourced.backtest(mode, ticker).catch(() => null),
    ]).then(([e, b]) => {
      if (dead) return;
      setLedger({
        key,
        events: e.data, eventsSource: e.source,
        bt: b?.data ?? null, btSource: b?.source ?? null,
      });
    });
    return () => { dead = true; };
  }, [mode, ticker]);

  const goBranch = useCallback((t: string, date: string, headline?: string) => {
    setTicker(t);
    setAsOf(date);
    if (headline) setText(headline);
    setView("branch");
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
  }, []);

  return (
    <main className="mx-auto max-w-[1560px] px-4 pb-24 pt-6 sm:px-6 lg:px-10">
      <Masthead
        view={view} setView={setView}
        mode={mode} setMode={setMode}
        healthy={healthy} checking={checking}
        onRecheck={() => void recheck()}
      />

      {/* Not while the probe is still in flight. `mode` starts at "mock" so the
          conservative default is never a claim, but flashing "SYNTHETIC" for
          400ms on a machine whose backend is up and about to answer teaches
          the viewer something false about the run they are watching. */}
      {mode !== "live" && !checking && (
        <div
          className={`${mode === "baked" ? "callout" : "callout-notice"} rise mb-6 flex flex-wrap items-center gap-x-5 gap-y-2 px-5 py-3`}
        >
          <span className="label shrink-0"
            style={{ color: mode === "baked" ? "var(--color-blue)" : "var(--color-notice)" }}>
            {mode === "baked" ? "Precomputed · real" : "Synthetic · not model output"}
          </span>
          <span className="min-w-[20ch] flex-1 text-sm leading-snug text-[var(--color-ink-dim)]">
            {mode === "baked"
              ? healthy
                ? "Stored output of the real model, computed at build time. The live backend is up — switch to live for fresh runs."
                : "Stored output of the real model, computed at build time. The live backend is not reachable."
              : "No real forecast source answered, so forecast panels run an in-browser generator. The atlas is still real, and each panel states its own source."}
          </span>
          <button
            onClick={async () => { const ok = await recheck(); if (ok) setMode("live"); }}
            className="btn-secondary ml-auto shrink-0 bg-white"
          >
            Try live backend
          </button>
        </div>
      )}

      {view === "atlas" && (
        atlas ? (
          <AtlasView atlas={atlas} onBranch={goBranch} />
        ) : atlasFailed ? (
          <div className="callout-notice px-6 py-6">
            <div className="label" style={{ color: "var(--color-notice)" }}>Atlas bundle missing</div>
            <p className="mt-2 max-w-[70ch] text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)]">
              <span className="num">/data/atlas.json</span> did not load, so there is no price
              record and no event ledger to draw. Nothing is substituted for it. The branch and
              evidence tabs still work against the API.
            </p>
          </div>
        ) : (
          <div className="panel flex min-h-[420px] items-center justify-center">
            <span className="label-title" style={{ color: "var(--color-ink-faint)" }}>
              loading 64 years of closes…
            </span>
          </div>
        )
      )}

      {view === "branch" && (
        <BranchView
          atlas={atlas}
          mode={mode}
          tickers={tickers}
          ticker={ticker} setTicker={setTicker}
          asOf={asOf} setAsOf={setAsOf}
          text={text} setText={setText}
          onOpenEvidence={() => setView("evidence")}
        />
      )}

      {view === "evidence" && (
        <EvidenceView
          mode={mode}
          tickers={tickers}
          ticker={ticker} setTicker={setTicker}
          asOf={asOf} setAsOf={setAsOf}
          horizon={horizon}
          events={events}
          eventsSource={fresh?.eventsSource ?? mode}
          bt={bt}
          btSource={fresh?.btSource ?? null}
          eventsLoading={eventsLoading}
          onBranch={goBranch}
        />
      )}

      <footer className="mt-16 flex flex-wrap items-end justify-between gap-8 border-t border-[var(--color-rule)] pt-8">
        <div>
          <div className="display text-2xl">rulial-markets</div>
          <p className="mt-3 max-w-[68ch] text-sm leading-relaxed text-[var(--color-ink-faint)]">
            Built at Sundai Hack 139 with Wolfram Research. Inside a computationally irreducible
            process you cannot predict the trajectory, but there are pockets where the statistics
            are reducible. We measured ours: forward direction has no out-of-sample signal, forward
            dispersion does. That gap is the product.
          </p>
        </div>
        <div className="label text-right">
          <div>frozen interface · CONTRACT.md</div>
          <div className="mt-1">train ≤ {TRAIN_END} · test 2020+</div>
        </div>
      </footer>
    </main>
  );
}

function Masthead({
  view, setView, mode, setMode, healthy, checking, onRecheck,
}: {
  view: ViewKey; setView: (v: ViewKey) => void;
  mode: Mode; setMode: (m: Mode) => void;
  healthy: boolean | null; checking: boolean; onRecheck: () => void;
}) {
  const tabs: { k: ViewKey; label: string; hint: string }[] = [
    { k: "atlas", label: "Atlas", hint: "every event, one axis" },
    { k: "branch", label: "Branch", hint: "what if" },
    { k: "evidence", label: "Evidence", hint: "argue with it" },
  ];

  return (
    <header className="rise mb-6">
      <div className="flex flex-wrap items-center justify-between gap-x-8 gap-y-4 border-b border-[var(--color-rule)] pb-5">
        <div className="flex items-center gap-3">
          <span className="block h-2.5 w-2.5 rounded-full pulse-dot" style={{ background: "var(--color-blue)" }} />
          <span className="num text-lg font-bold tracking-tight text-[var(--color-navy)]">rulial-markets</span>
          <span className="label hidden sm:inline">sundai 139 · wolfram research</span>
        </div>

        <nav aria-label="Views" className="order-3 w-full lg:order-none lg:w-auto">
          <div className="flex overflow-hidden rounded-full border border-[var(--color-axis)] bg-white">
            {tabs.map((t) => {
              const on = view === t.k;
              return (
                <button
                  key={t.k}
                  onClick={() => setView(t.k)}
                  aria-current={on ? "page" : undefined}
                  className="flex-1 px-5 py-2.5 text-left transition sm:flex-none sm:text-center"
                  style={{ background: on ? "var(--color-blue)" : "transparent" }}
                >
                  <span className="block text-[0.9375rem] font-bold"
                    style={{ color: on ? "#fff" : "var(--color-navy)" }}>
                    {t.label}
                  </span>
                  <span className="block text-xs"
                    style={{ color: on ? "rgba(255,255,255,0.82)" : "var(--color-ink-faint)" }}>
                    {t.hint}
                  </span>
                </button>
              );
            })}
          </div>
        </nav>

        <ModeToggle mode={mode} setMode={setMode} healthy={healthy} checking={checking} onRecheck={onRecheck} />
      </div>
    </header>
  );
}
