"use client";

import { useState } from "react";
import type { Ensemble, EventRec, Mode } from "@/lib/types";

/**
 * "What did we use to produce this branch?"
 *
 * Every field here is read off the response that produced the fan on screen.
 * Nothing is described in the abstract: the analogs listed ARE the windows that
 * were resampled, and the counts ARE the counts. If a value is absent from the
 * response it is omitted rather than guessed.
 */
export function MethodDisclosure({
  ensemble, mode, ticker, seedCount,
}: {
  ensemble: Ensemble;
  mode: Mode;
  ticker: string;
  seedCount?: number;
}) {
  const [open, setOpen] = useState(false);

  const analogs: EventRec[] = (ensemble.analogs ?? []) as EventRec[];
  const nPaths = ensemble.paths?.length ?? 0;
  // The generator states its rule count in the narrative; parse rather than assume.
  const ruleMatch = /mixture of (\d+) generator rules/.exec(ensemble.narrative ?? "");
  const nRules = ruleMatch ? Number(ruleMatch[1]) : undefined;

  const sourceLabel =
    mode === "live" ? "live backend" : mode === "baked" ? "precomputed, real" : "in-browser synthetic";

  return (
    <div className="rounded-lg border border-[var(--color-axis)] bg-white">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition hover:bg-[var(--color-blue-tint)]"
      >
        <span className="label-title" style={{ color: "var(--color-navy)" }}>
          How this branch was made
        </span>
        <span className="flex items-center gap-3">
          <span className="num text-xs text-[var(--color-ink-faint)]">
            {nPaths.toLocaleString()} paths · {analogs.length} analogs
            {nRules ? ` · ${nRules} rules` : ""}
          </span>
          <span aria-hidden className="text-[var(--color-blue)]">{open ? "−" : "+"}</span>
        </span>
      </button>

      {open && (
        <div className="grid gap-6 border-t border-[var(--color-axis)] px-5 py-6">
          <ol className="grid gap-4">
            <Step n={1} title="Retrieve real precedents">
              Searched the event ledger for the {analogs.length} closest historical situations to
              the text you typed. <b>Every one closed on or before {ensemble.as_of_date}</b> — the
              guard that stops the model seeing its own answer.
            </Step>
            <Step n={2} title="Weight them">
              A language model read your event text and returned scenario weights
              {nRules ? ` across ${nRules} generator rules` : ""} — regime and dispersion
              adjustments only. <b>It never emits a probability or a return.</b>
            </Step>
            <Step n={3} title="Resample, don't simulate">
              Block bootstrap over those precedents&apos; <i>realized</i> forward windows.
              Each of the {nPaths.toLocaleString()} lines on the chart is a real{" "}
              {ensemble.horizon_days}-day stretch of {ticker} history, replayed from your branch
              point. Nothing is drawn from a fitted curve.
            </Step>
            <Step n={4} title="Coarse-grain">
              Collapse {nPaths.toLocaleString()} paths to the quantile bands you see. This is the
              bounded-observer step: we cannot hold every path, so we summarise the ensemble.
            </Step>
          </ol>

          {analogs.length > 0 && (
            <div>
              <div className="label mb-3" style={{ color: "var(--color-ink-dim)" }}>
                The precedents actually used ({analogs.length})
              </div>
              <div className="max-h-56 overflow-y-auto rounded border border-[var(--color-axis)]">
                <table className="w-full border-collapse text-left">
                  <tbody>
                    {analogs.map((a, i) => (
                      <tr key={`${a.ticker}-${a.date}-${i}`}
                          className="border-b border-[var(--color-axis)] last:border-0">
                        <td className="num px-3 py-2 text-xs font-semibold text-[var(--color-navy)]">{a.ticker}</td>
                        <td className="num px-3 py-2 text-xs text-[var(--color-ink-dim)]">{a.date}</td>
                        <td className="num px-3 py-2 text-right text-xs font-semibold"
                            style={{ color: a.move_pct < 0 ? "var(--color-neg)" : "var(--color-pos)" }}>
                          {a.move_pct >= 0 ? "+" : ""}{(a.move_pct * 100).toFixed(1)}%
                        </td>
                        <td className="px-3 py-2 text-xs text-[var(--color-ink-faint)]">
                          {a.headline || <span className="italic">no researched cause on file</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
            <Fact k="Ticker" v={ensemble.ticker || ticker} />
            <Fact k="Branch point" v={ensemble.as_of_date} />
            <Fact k="Horizon" v={`${ensemble.horizon_days} trading days`} />
            <Fact k="Paths sampled" v={nPaths.toLocaleString()} />
            <Fact k="Precedents used" v={String(analogs.length)} />
            {nRules !== undefined && <Fact k="Generator rules" v={String(nRules)} />}
            {seedCount !== undefined && <Fact k="Ledger size" v={`${seedCount} events`} />}
            <Fact k="Computed by" v={sourceLabel} />
          </dl>

          <p className="text-xs leading-relaxed text-[var(--color-ink-faint)]">
            Reproduce it: <span className="num">POST /api/forecast</span> with this ticker, text,
            as-of date and horizon. The endpoint is deterministic for a given request, so the same
            inputs return the same paths. Source in{" "}
            <span className="num">backend/rulial/generator.py</span>.
          </p>
        </div>
      )}
    </div>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <li className="flex gap-4">
      <span className="num flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--color-blue-tint)] text-xs font-semibold text-[var(--color-blue)]">
        {n}
      </span>
      <span className="text-sm leading-relaxed text-[var(--color-ink-dim)]">
        <b className="text-[var(--color-navy)]">{title}.</b> {children}
      </span>
    </li>
  );
}

function Fact({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-dashed border-[var(--color-axis)] pb-2">
      <dt className="label" style={{ color: "var(--color-ink-faint)" }}>{k}</dt>
      <dd className="num text-sm font-semibold text-[var(--color-navy)]">{v}</dd>
    </div>
  );
}
