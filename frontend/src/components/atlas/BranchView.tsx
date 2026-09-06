"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiSourced } from "@/lib/api";
import { bakedAvailable, bakedMatchLabel } from "@/lib/baked";
import type { Atlas } from "@/lib/atlas";
import type { ForecastResponse, Mode, TickerInfo } from "@/lib/types";
import { TRAIN_END } from "@/lib/types";
import { PRESETS } from "../presets";
import { Verdict } from "../Verdict";
import { DisclosureLine } from "../DisclosureLine";
import { MethodDisclosure } from "../MethodDisclosure";
import { RulialPanel } from "../RulialPanel";
import { SourceTag } from "../SourceTag";
import { BranchChart } from "./BranchChart";

/**
 * STATE 3 — THE MULTIVERSE.
 *
 * Pick a point on the record, describe something that did not happen, and the
 * ensemble fans out FROM THAT POINT on the same axes as the price history.
 * The chart is the argument; everything below it is evidence for the chart.
 *
 * Reading order is deliberate and is the fix for "a lot of text and hard to
 * understand the numbers":
 *
 *     picture  ->  three numbers  ->  one-line disclosure  ->  the rest, folded
 *
 * The forward, scenario and rulial surfaces all still exist and none of them
 * lost a capability. They stopped competing for the top of the page.
 */
export function BranchView({
  atlas, mode, tickers,
  ticker, setTicker, asOf, setAsOf, text, setText,
  onOpenEvidence,
}: {
  atlas: Atlas | null;
  mode: Mode;
  tickers: TickerInfo[];
  ticker: string; setTicker: (v: string) => void;
  asOf: string; setAsOf: (v: string) => void;
  text: string; setText: (v: string) => void;
  onOpenEvidence: () => void;
}) {
  const [horizon, setHorizon] = useState(5);
  const [nPaths, setNPaths] = useState(2000);
  const [running, setRunning] = useState(false);
  const [res, setRes] = useState<ForecastResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [showTail, setShowTail] = useState(false);
  const [fit, setFit] = useState<"auto" | "all" | "futures">("auto");
  const [ranWith, setRanWith] = useState<{ ticker: string; asOf: string } | null>(null);
  /* Which of the three sources actually produced the fan on screen. A
     precomputed MISS falls through to the synthetic generator by design, and
     the panel has to say so — the page badge cannot. */
  const [resSource, setResSource] = useState<Mode | null>(null);
  const [bakedLabel, setBakedLabel] = useState<string | null>(null);
  const [showRulial, setShowRulial] = useState(false);
  const resultRef = useRef<HTMLDivElement | null>(null);

  const series = atlas?.tickers[ticker]?.series ?? [];
  const scoreable = asOf <= TRAIN_END;

  // A result belongs to the request that produced it. Changing the ticker or
  // the date without re-running must not leave the previous fan drawn against
  // a different company's price line.
  const stale = res != null && ranWith != null && (ranWith.ticker !== ticker || ranWith.asOf !== asOf);

  const run = useCallback(async () => {
    setRunning(true);
    setErr(null);
    try {
      const body = { ticker, event_text: text, as_of_date: asOf, horizon_days: horizon, n_paths: nPaths };
      const r = await apiSourced.forecast(mode, body);
      setRes(r.data);
      setResSource(r.source);
      setRanWith({ ticker, asOf });
      setBakedLabel(r.source === "baked" ? await bakedMatchLabel(body) : null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }, [mode, ticker, text, asOf, horizon, nPaths]);

  useEffect(() => {
    if (!res || stale) return;
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    resultRef.current?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  }, [res, stale]);

  const ens = !stale ? res?.ensemble ?? null : null;
  const score = !stale ? res?.score ?? null : null;
  const shownSource: Mode = (!stale && resSource) || mode;
  const fellBack = !stale && resSource === "mock" && mode !== "mock";

  return (
    <div className="grid gap-6 [&>*]:min-w-0">
      <header className="rise">
        <h1 className="display text-[clamp(2rem,4.4vw,3rem)]">
          Pull a branch,
          <span className="italic" style={{ color: "var(--color-blue)" }}> and watch it fan</span>
        </h1>
        <p className="mt-4 max-w-[70ch] text-[1.125rem] leading-relaxed text-[var(--color-ink-dim)]">
          Everything left of the blue line happened. Everything right of it is the set of futures
          the model thinks were reachable from that point. One of them is the one we got.
        </p>
      </header>

      {/* ---------------- the control ---------------- */}
      <section className="panel min-w-0">
        <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-b border-[var(--color-rule)] px-5 py-4 sm:px-8">
          <h2 className="label-title">Branch point and counterfactual</h2>
          <SourceTag source={shownSource} detail={bakedLabel ?? undefined} />
        </div>

        <div className="grid gap-6 p-5 sm:p-8">
          <div className="grid gap-5 lg:grid-cols-[180px_190px_minmax(0,1fr)]">
            <label className="block">
              <span className="label mb-2 block">Ticker</span>
              <select value={ticker} onChange={(e) => setTicker(e.target.value)} className="w-full px-3 py-3 text-lg">
                {(tickers.length ? tickers.map((t) => t.symbol) : Object.keys(atlas?.tickers ?? {})).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="label mb-2 block">Branch date</span>
              <input type="date" value={asOf} max="2026-12-31"
                onChange={(e) => setAsOf(e.target.value)} className="w-full px-3 py-3 text-lg" />
              {/* The old copy here read "forecast only, no score" for any date
                  past 2019-12-31, which is simply wrong: that is the HELD-OUT
                  window and the backend scores it whenever the outcome exists.
                  The boundary governs what the generator may learn from, not
                  whether the result gets marked. */}
              <span className="mt-2 block text-sm leading-snug"
                style={{ color: scoreable ? "var(--color-blue)" : "var(--color-ink-faint)" }}>
                {scoreable
                  ? "inside the train window — the analogs stop here"
                  : "held-out test window — scored whenever the outcome is already known"}
              </span>
            </label>

            <label className="block">
              <span className="label mb-2 block">What if…</span>
              <textarea
                value={text} rows={3}
                onChange={(e) => setText(e.target.value)}
                placeholder="Describe the event the market is about to be handed…"
                className="w-full resize-none px-3 py-3 text-base leading-relaxed"
              />
            </label>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="label mr-1">Try one</span>
            {PRESETS.map((p) => (
              <button
                key={p.key}
                onClick={() => { setTicker(p.ticker); setAsOf(p.as_of); setText(p.text); }}
                className="rounded-full border border-[var(--color-gray-400)] bg-white px-4 py-1.5 text-sm font-semibold text-[var(--color-ink-dim)] transition hover:border-[var(--color-blue)] hover:bg-[var(--color-blue-tint)] hover:text-[var(--color-blue)]"
              >
                {p.ticker} · {p.kind}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-end justify-between gap-5 border-t border-[var(--color-rule)] pt-6">
            <div className="flex flex-wrap items-center gap-6">
              <label className="flex items-center gap-3">
                <span className="label">Horizon</span>
                <select value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} className="px-3 py-2">
                  {[1, 3, 5, 10, 21].map((h) => <option key={h} value={h}>{h}d</option>)}
                </select>
              </label>
              <label className="flex items-center gap-3">
                <span className="label">Futures</span>
                <select value={nPaths} onChange={(e) => setNPaths(Number(e.target.value))} className="px-3 py-2">
                  {[500, 1000, 2000, 4000].map((n) => <option key={n} value={n}>{n.toLocaleString()}</option>)}
                </select>
              </label>
            </div>
            <button onClick={() => void run()} disabled={running || !text.trim()} className="btn-primary text-base">
              {running ? "Fanning out…" : "Branch from here"}
            </button>
          </div>

          {err && (
            <div className="rounded-lg border border-[var(--color-neg)] bg-[#FDF3F2] px-6 py-5">
              <div className="label" style={{ color: "var(--color-neg)" }}>backend error</div>
              <div className="num mt-2 text-sm text-[var(--color-ink-dim)]">{err}</div>
              <button
                onClick={async () => { setErr(null); void bakedAvailable(); }}
                className="btn-secondary mt-4 bg-white">
                Dismiss
              </button>
            </div>
          )}
        </div>
      </section>

      <div ref={resultRef} />

      {/* ---------------- the picture ---------------- */}
      <section className="panel min-w-0 overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-b border-[var(--color-rule)] px-5 py-4 sm:px-8">
          <h2 className="label-title">{ticker} · branching {asOf}</h2>
          <div className="flex flex-wrap items-center gap-4">
            <label className="flex cursor-pointer items-center gap-2 text-sm text-[var(--color-ink-dim)]">
              <input type="checkbox" checked={showTail} onChange={(e) => setShowTail(e.target.checked)}
                className="h-4 w-4 accent-[var(--color-blue)]" />
              show what came next
            </label>
            <label className="flex items-center gap-2">
              <span className="label">Fit</span>
              <select value={fit} onChange={(e) => setFit(e.target.value as "auto" | "all" | "futures")}
                className="px-2 py-1.5 text-sm">
                <option value="auto">auto</option>
                <option value="futures">the futures</option>
                <option value="all">all history</option>
              </select>
            </label>
            <SourceTag source="atlas" detail="price line" />
          </div>
        </div>

        <div className="overflow-x-auto">
          <div className="min-w-[760px] p-5 sm:p-8">
            {series.length ? (
              <BranchChart
                series={series}
                branchDate={asOf}
                horizonDays={ens?.horizon_days ?? horizon}
                ensemble={ens}
                actual={score?.actual_return ?? null}
                showTail={showTail}
                fit={fit}
              />
            ) : (
              <div className="flex min-h-[240px] items-center justify-center rounded-lg border border-dashed border-[var(--color-gray-400)] px-6 py-10 text-center">
                <p className="max-w-[52ch] text-[var(--color-ink-faint)]">
                  The bundled price record has no series for {ticker}, so there is no real line to
                  branch from. Nothing is drawn.
                </p>
              </div>
            )}
          </div>
        </div>

        {!ens && series.length > 0 && (
          <p className="border-t border-[var(--color-rule)] px-5 py-4 text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)] sm:px-8">
            {stale
              ? "Ticker or date changed since the last run — the previous fan was cleared rather than left drawn over a different company's price line. Branch again."
              : "The real line is drawn. Press Branch from here and the futures open out of the blue mark."}
          </p>
        )}

        {ens?.narrative && (
          <p className="border-t border-[var(--color-rule)] px-5 py-5 text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)] sm:px-8">
            {ens.narrative}
          </p>
        )}
      </section>

      {/* ---------------- three numbers ---------------- */}
      {ens && (
        <section className="panel min-w-0">
          <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-b border-[var(--color-rule)] px-5 py-4 sm:px-8">
            <h2 className="label-title">Read the result</h2>
            <SourceTag source={shownSource} />
          </div>
          <div className="p-5 sm:p-8">
            {fellBack && (
              <div className="callout-notice mb-7 px-6 py-5">
                <div className="label" style={{ color: "var(--color-notice)" }}>
                  This result is synthetic
                </div>
                <p className="mt-2 max-w-[76ch] text-[0.9375rem] leading-relaxed text-[var(--color-ink-dim)]">
                  The page is in <span className="num font-semibold">{mode}</span> mode, but nothing
                  precomputed matched {ticker} on {asOf}, so the fan above came from the in-browser
                  generator. It is a demonstration of the surface, not a measurement. Precomputed
                  runs exist for the four preset scenarios.
                </p>
              </div>
            )}
            <Verdict score={score} ensemble={ens} source={shownSource} />
            {!score && (
              <p className="mt-6 max-w-[80ch] text-[0.9375rem] leading-relaxed text-[var(--color-ink-faint)]">
                Branch inside the train window (on or before {TRAIN_END}) to get a verdict, or open{" "}
                <button onClick={onOpenEvidence} className="font-semibold text-[var(--color-blue)] underline underline-offset-4">
                  the evidence tab
                </button>{" "}
                where the same scoring runs across every test event at once.
              </p>
            )}
          </div>
        </section>
      )}

      {/* ---------------- show your work, folded ---------------- */}
      {ens && (
        <MethodDisclosure ensemble={ens} mode={shownSource as Mode} ticker={ticker} />
      )}

      {/* ---------------- one line, per contract §8 ---------------- */}
      {ens && <DisclosureLine />}

      {/* ---------------- 144 rules, folded ---------------- */}
      <section className="panel min-w-0">
        <button
          onClick={() => setShowRulial((v) => !v)}
          aria-expanded={showRulial}
          className="flex w-full flex-wrap items-center justify-between gap-x-6 gap-y-2 px-5 py-5 text-left sm:px-8"
        >
          <span className="min-w-0">
            <span className="label-title block">Branch the rules, not just the paths</span>
            <span className="mt-1 block max-w-[76ch] text-sm leading-relaxed text-[var(--color-ink-faint)]">
              The fan above assumes one way of building futures. There are 144 defensible ways. Run
              all of them and see which conclusions survive.
            </span>
          </span>
          <span className="btn-secondary shrink-0 bg-white">{showRulial ? "Hide" : "Open"}</span>
        </button>
        {showRulial && (
          <div className="border-t border-[var(--color-rule)] p-5 sm:p-8">
            <RulialPanel ticker={ticker} asOf={asOf} text={text} horizon={horizon} mode={mode} />
          </div>
        )}
      </section>
    </div>
  );
}
