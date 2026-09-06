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
import { ScenarioPanel } from "./ScenarioPanel";
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

  /**
   * Ledger + backtest are ONE keyed result rather than three independent
   * pieces of state. Keying on `mode|ticker` means "is this stale?" is derived
   * at render time instead of being reset by a setState at the top of an
   * effect, which both removes a cascading render and makes an out-of-order
   * response physically unable to paint under the wrong ticker.
   */
  const [ledger, setLedger] = useState<
    { key: string; events: EventRec[]; bt: Backtest | null } | null
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
    if (!decided.current) {
      decided.current = true;
      setMode(ok ? "live" : "mock");
    }
  }, []);

  /** Re-probe on demand. Only ever called from a user event, so flipping the
   *  spinner on synchronously here is safe — unlike inside an effect body. */
  const recheck = useCallback(async () => {
    setChecking(true);
    const ok = await probeHealth();
    applyProbe(ok);
    return ok;
  }, [applyProbe]);

  // Mount probe. `checking` already starts true, so this sets no state until
  // the promise resolves and never triggers a cascading render.
  useEffect(() => {
    let dead = false;
    void probeHealth().then((ok) => { if (!dead) applyProbe(ok); });
    return () => { dead = true; };
  }, [applyProbe]);

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
      api.events(mode, ticker).catch(() => [] as EventRec[]),
      api.backtest(mode, ticker).catch(() => null),
    ]).then(([e, b]) => {
      if (!dead) setLedger({ key, events: e, bt: b });
    });
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
        // prefers-reduced-motion is a CSS media query and cannot reach a
        // JS-initiated scroll. A several-hundred-pixel smooth scroll is
        // exactly the vestibular trigger the preference exists for, so we
        // read it here by hand.
        const reduce =
          typeof window !== "undefined" &&
          window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        document.getElementById("ensemble")?.scrollIntoView({
          behavior: reduce ? "auto" : "smooth",
          block: "start",
        });
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
    <main className="mx-auto max-w-[1440px] px-6 pb-28 pt-10 lg:px-10">
      <Masthead
        mode={mode} setMode={setMode} healthy={healthy} checking={checking}
        onRecheck={() => void recheck()}
      />

      {mode === "mock" && (
        <div className="callout-notice rise mb-8 flex flex-wrap items-center gap-x-6 gap-y-3 px-6 py-5">
          <span className="label-title" style={{ color: "var(--color-notice)" }}>Mock mode</span>
          <span className="max-w-[86ch] text-sm leading-relaxed text-[var(--color-ink-dim)]">{MOCK_NOTICE}</span>
          <button
            onClick={async () => { const ok = await recheck(); if (ok) setMode("live"); }}
            className="btn-secondary ml-auto bg-white"
            style={{ color: "var(--color-notice)", borderColor: "var(--color-notice)" }}
          >
            Try live backend
          </button>
        </div>
      )}

      <div className="grid gap-10">
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
            <div className="mt-6 rounded-lg border border-[var(--color-neg)] bg-[#FDF3F2] px-6 py-5">
              <div className="label" style={{ color: "var(--color-neg)" }}>backend error</div>
              <div className="num mt-2 text-sm text-[var(--color-ink-dim)]">{err}</div>
              <button onClick={() => { setMode("mock"); setErr(null); }}
                className="btn-secondary mt-4 bg-white">
                Fall back to mock
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

              <div className="mt-10 border-t border-[var(--color-rule)] pt-8">
                <div className="label mb-4">Terminal return distribution</div>
                <TerminalHistogram ensemble={ens} actual={actual} />
              </div>

              {ens.narrative && (
                <p className="mt-8 max-w-[92ch] border-l-[3px] border-[var(--color-blue)] pl-5 text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)]">
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
                <div className="flex min-h-[110px] items-center justify-center rounded-lg border border-dashed border-[var(--color-gray-400)] px-6 py-8 text-center">
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
            <div className="flex min-h-[260px] flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-[var(--color-gray-400)] px-6 py-12 text-center">
              <div className="label-title"
                style={{ fontSize: "1.5rem", color: "var(--color-ink-faint)" }}>
                pick a scenario, then sample
              </div>
              <p className="max-w-[54ch] text-base leading-relaxed text-[var(--color-ink-faint)]">
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

        <Panel
          title="Inverse — what event would produce this probability?"
          index="05" delay={120}
          right={<span className="label">many events give the same probability · candidates, not an answer</span>}
        >
          <ScenarioPanel ticker={ticker} asOf={asOf} horizon={horizon} mode={mode} />
        </Panel>

        <Panel title={`Walk-forward — ${ticker} on the 2020+ test window`} index="06" delay={140}
          right={<span className="label">flat PIT is the win condition</span>}>
          <BacktestPanel bt={bt} ticker={ticker} />
        </Panel>

        <Panel title={`Seed ledger — ${ticker} train events (≤ ${TRAIN_END})`} index="07" delay={160}
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

      <footer className="mt-16 flex flex-wrap items-end justify-between gap-8 border-t border-[var(--color-rule)] pt-8">
        <div>
          <div className="display text-3xl">rulial-markets</div>
          <p className="mt-3 max-w-[64ch] text-sm leading-relaxed text-[var(--color-ink-faint)]">
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
      <span className="num font-semibold text-[var(--color-navy)]">{value}</span>
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
      <div className="flex flex-wrap items-start justify-between gap-8 border-b border-[var(--color-rule)] pb-8">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <span className="block h-2.5 w-2.5 rounded-full pulse-dot" style={{ background: "var(--color-blue)" }} />
            <span className="label label-bright">rulial-markets · sundai 139 · wolfram research</span>
          </div>
          <h1 className="display mt-5 text-[clamp(2.25rem,5vw,3.5rem)]">
            The ensemble of
            <span className="italic" style={{ color: "var(--color-blue)" }}> reachable futures</span>
          </h1>
          <p className="mt-5 max-w-[70ch] text-[1.125rem] leading-relaxed text-[var(--color-ink-dim)]">
            Describe an event. Get back a distribution of forward return paths, not a number.
            We score how well the distribution was <em className="not-italic font-semibold text-[var(--color-navy)]">calibrated</em>,
            against a null we are forbidden to remove — because &ldquo;we called the crash&rdquo; is a story,
            and a flat PIT histogram is a result.
          </p>
        </div>
        <ModeToggle mode={mode} setMode={setMode} healthy={healthy} checking={checking} onRecheck={onRecheck} />
      </div>
    </header>
  );
}
