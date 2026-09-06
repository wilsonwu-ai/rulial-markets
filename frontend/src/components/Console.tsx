"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, probeHealth } from "@/lib/api";
import { MOCK_NOTICE, mockTickers } from "@/lib/mock";
import type {
  Backtest, EventRec, ForecastResponse, Mode, TickerInfo,
} from "@/lib/types";
import { TRAIN_END } from "@/lib/types";
import { pct } from "@/lib/quant";
import { Panel } from "./Panel";
import { ControlPanel } from "./ControlPanel";
import { FanChart } from "./FanChart";
import { TerminalHistogram } from "./TerminalHistogram";
import { Scorecard } from "./Scorecard";
import { LeakagePanel } from "./LeakagePanel";
import { BacktestPanel } from "./BacktestPanel";
import { EventLedger } from "./EventLedger";
import { ModeToggle } from "./ModeToggle";
import { PRESETS } from "./presets";

export function Console() {
  const [mode, setMode] = useState<Mode>("mock");
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(true);
  const decided = useRef(false);

  const [tickers, setTickers] = useState<TickerInfo[]>(mockTickers());
  const [ticker, setTicker] = useState(PRESETS[1].ticker);
  const [asOf, setAsOf] = useState(PRESETS[1].as_of);
  const [text, setText] = useState(PRESETS[1].text);
  const [horizon, setHorizon] = useState(5);
  const [nPaths, setNPaths] = useState(2000);

  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ForecastResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [events, setEvents] = useState<EventRec[]>([]);
  const [eventsLoading, setEventsLoading] = useState(true);
  const [bt, setBt] = useState<Backtest | null>(null);

  /* ---- health probe decides the initial mode, once ---- */
  const recheck = useCallback(async () => {
    setChecking(true);
    const ok = await probeHealth();
    setHealthy(ok);
    setChecking(false);
    if (!decided.current) {
      decided.current = true;
      setMode(ok ? "live" : "mock");
    }
    return ok;
  }, []);

  useEffect(() => { void recheck(); }, [recheck]);

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
    setEventsLoading(true);
    setEvents([]);
    setBt(null);
    api.events(mode, ticker)
      .then((e) => { if (!dead) setEvents(e); })
      .catch(() => { if (!dead) setEvents([]); })
      .finally(() => { if (!dead) setEventsLoading(false); });
    api.backtest(mode, ticker)
      .then((b) => { if (!dead) setBt(b); })
      .catch(() => { if (!dead) setBt(null); });
    return () => { dead = true; };
  }, [mode, ticker]);

  /* ---- run a forecast ---- */
  const run = useCallback(async () => {
    setRunning(true);
    setErr(null);
    try {
      const res = await api.forecast(mode, {
        ticker, event_text: text, as_of_date: asOf,
        horizon_days: horizon, n_paths: nPaths,
      });
      setResult(res);
      requestAnimationFrame(() => {
        document.getElementById("ensemble")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }, [mode, ticker, text, asOf, horizon, nPaths]);

  const ens = result?.ensemble ?? null;
  const score = result?.score ?? null;
  const actual = score?.actual_return ?? null;

  return (
    <main className="mx-auto max-w-[1440px] px-6 pb-28 pt-8 lg:px-10">
      <Masthead
        mode={mode} setMode={setMode} healthy={healthy} checking={checking}
        onRecheck={() => void recheck()}
      />

      {mode === "mock" && (
        <div className="rise mb-8 border border-[rgba(255,207,74,0.4)]">
          <div className="hazard h-[8px] w-full" />
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 bg-[rgba(255,207,74,0.06)] px-5 py-4">
            <span className="num text-lg" style={{ color: "var(--color-hazard)" }}>MOCK MODE</span>
            <span className="text-sm text-[var(--color-ink-dim)]">{MOCK_NOTICE}</span>
            <button
              onClick={async () => { const ok = await recheck(); if (ok) setMode("live"); }}
              className="label ml-auto border border-[rgba(255,207,74,0.5)] px-3 py-1.5 transition hover:bg-[rgba(255,207,74,0.12)]"
              style={{ color: "var(--color-hazard)" }}
            >
              try live backend
            </button>
          </div>
        </div>
      )}

      <div className="grid gap-8">
        <Panel title="Control — condition the ensemble" index="01" delay={40}
          right={<span className="label">as-of ≤ {TRAIN_END} gets scored</span>}>
          <ControlPanel
            tickers={tickers}
            ticker={ticker} setTicker={setTicker}
            asOf={asOf} setAsOf={setAsOf}
            text={text} setText={setText}
            horizon={horizon} setHorizon={setHorizon}
            nPaths={nPaths} setNPaths={setNPaths}
            onRun={() => void run()} running={running}
          />
          {err && (
            <div className="mt-5 border border-[var(--color-down)] bg-[rgba(255,95,86,0.07)] px-4 py-3">
              <div className="label" style={{ color: "var(--color-down)" }}>backend error</div>
              <div className="num mt-1 text-sm text-[var(--color-ink-dim)]">{err}</div>
              <button onClick={() => { setMode("mock"); setErr(null); }}
                className="label mt-3 border border-[var(--color-rule-bright)] px-3 py-1.5 hover:text-[var(--color-hazard)]">
                fall back to mock
              </button>
            </div>
          )}
        </Panel>

        <div id="ensemble" />

        {ens ? (
          <>
            <Panel
              title={`Ensemble — ${ens.ticker} · ${ens.horizon_days}d forward from ${ens.as_of_date}`}
              index="02" delay={60}
              right={
                <div className="flex flex-wrap items-center gap-5">
                  <Readout label="paths" value={String(Array.isArray(ens.paths) ? ens.paths.length : 0)} />
                  <Readout label="mean" value={pct(ens.mean, 2)} />
                  <Readout label="σ" value={`${(ens.std * 100).toFixed(2)}%`} />
                </div>
              }
            >
              <FanChart ensemble={ens} actual={actual} />

              <div className="mt-8 border-t border-[var(--color-rule)] pt-7">
                <div className="label mb-4">Terminal return distribution</div>
                <TerminalHistogram ensemble={ens} actual={actual} />
              </div>

              {ens.narrative && (
                <p className="mt-7 max-w-[92ch] border-l-2 border-[var(--color-phosphor)] pl-5 text-[1.05rem] leading-relaxed text-[var(--color-ink-dim)]">
                  {ens.narrative}
                </p>
              )}
            </Panel>

            {score ? (
              <Panel title="Scorecard — CRPS against the frozen null" index="03" delay={80}
                right={<span className="label">directional hit-rate withheld by contract §7</span>}>
                <Scorecard score={score} />
              </Panel>
            ) : (
              <Panel title="Scorecard" index="03" delay={80}>
                <div className="flex min-h-[110px] items-center justify-center border border-dashed border-[var(--color-rule)] px-6 text-center">
                  <p className="max-w-[58ch] text-[var(--color-ink-faint)]">
                    No score for this request — the as-of date is not historical, so the realized
                    return does not exist yet. The ensemble stands on its own; nothing is invented
                    to fill the gap.
                  </p>
                </div>
              </Panel>
            )}
          </>
        ) : (
          <Panel title="Ensemble" index="02" delay={60}>
            <div className="flex min-h-[280px] flex-col items-center justify-center gap-4 border border-dashed border-[var(--color-rule)] text-center">
              <div className="display text-[clamp(1.5rem,3vw,2.4rem)] text-[var(--color-ink-faint)]">
                pick a scenario, then sample
              </div>
              <p className="max-w-[52ch] text-sm leading-relaxed text-[var(--color-ink-faint)]">
                Four one-click scenarios sit above. The fan chart, the terminal distribution and the
                scorecard all render from a single call to <span className="num">POST /api/forecast</span>.
              </p>
            </div>
          </Panel>
        )}

        <LeakagePanel
          famous={bt?.n_famous}
          obscure={bt?.n_obscure}
          liftFamous={bt?.mean_crps_lift_famous}
          liftObscure={bt?.mean_crps_lift_obscure}
        />

        <Panel title={`Walk-forward — ${ticker} on the 2020+ test window`} index="05" delay={120}
          right={<span className="label">flat PIT is the win condition</span>}>
          <BacktestPanel bt={bt} ticker={ticker} />
        </Panel>

        <Panel title={`Seed ledger — ${ticker} train events (≤ ${TRAIN_END})`} index="06" delay={140}
          right={<span className="label">|Δ| ≥ 15% over 5 sessions · major tier ≥ 25% · frozen</span>}>
          <EventLedger
            events={events} ticker={ticker} loading={eventsLoading}
            onPick={(e) => {
              setAsOf(e.date);
              if (e.headline) setText(e.headline);
            }}
          />
        </Panel>
      </div>

      <footer className="mt-16 flex flex-wrap items-end justify-between gap-6 border-t border-[var(--color-rule)] pt-8">
        <div>
          <div className="display text-3xl text-[var(--color-ink-dim)]">rulial-markets</div>
          <p className="mt-2 max-w-[62ch] text-sm leading-relaxed text-[var(--color-ink-faint)]">
            Built at Sundai Hack 139 with Wolfram Research. The framing is Wolfram&rsquo;s: inside a
            computationally irreducible process you cannot predict the trajectory, but there are
            pockets where the statistics are reducible. We measured ours — forward direction has no
            out-of-sample signal, forward dispersion does. That gap is the entire product.
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

function Readout({ label, value }: { label: string; value: string }) {
  return (
    <span className="flex items-baseline gap-2">
      <span className="label">{label}</span>
      <span className="num text-[var(--color-ink)]">{value}</span>
    </span>
  );
}

function Masthead({
  mode, setMode, healthy, checking, onRecheck,
}: {
  mode: Mode; setMode: (m: Mode) => void;
  healthy: boolean | null; checking: boolean; onRecheck: () => void;
}) {
  return (
    <header className="rise mb-8">
      <div className="flex flex-wrap items-start justify-between gap-6 border-b border-[var(--color-rule)] pb-7">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <span className="block h-2.5 w-2.5 pulse-dot" style={{ background: "var(--color-phosphor)" }} />
            <span className="label label-bright">rulial-markets · sundai 139 · wolfram research</span>
          </div>
          <h1 className="display mt-5 text-[clamp(2.6rem,7vw,6rem)] text-[var(--color-ink)]">
            The ensemble of
            <span className="italic text-[var(--color-phosphor)]"> reachable futures</span>
          </h1>
          <p className="mt-5 max-w-[70ch] text-[1.12rem] leading-relaxed text-[var(--color-ink-dim)]">
            Describe an event. Get back a distribution of forward return paths, not a number.
            We score how well the distribution was <em className="not-italic text-[var(--color-ink)]">calibrated</em>,
            against a null we are forbidden to remove — because &ldquo;we called the crash&rdquo; is a story,
            and a flat PIT histogram is a result.
          </p>
        </div>
        <ModeToggle mode={mode} setMode={setMode} healthy={healthy} checking={checking} onRecheck={onRecheck} />
      </div>
    </header>
  );
}
