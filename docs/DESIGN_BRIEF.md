# DESIGN_BRIEF.md — polish and coherence pass

**Lane:** DESIGN-CONSULT. **Scope:** `frontend/src/**` only.
**Method:** source-read audit of all 13 components + `globals.css` + `layout.tsx`, with every
contrast ratio in this document computed from the actual hex values in `globals.css` (WCAG 2.1
relative-luminance formula). No screenshot was taken; two items below are flagged
`VERIFY VISUALLY` because they cannot be settled from source.

**This is a polish pass, not a redesign.** Nothing in the current UI is proposed for deletion.
Every item names a file and a specific change.

---

## 0. STOP — unresolved direction conflict, parent must reconcile

Three specifications for this frontend currently exist and they do not agree. Per CONTRACT.md §9
(*"if a lane believes the contract is wrong, it reports the problem in its return value and codes
to the contract anyway"*), this brief is written to the direction I was handed. The parent decides.

| Source | Mode | Type | Density | Status |
|---|---|---|---|---|
| **Shipped code** (`frontend/src`, mtime 13:48) | dark "Observatory" | Instrument Serif + IBM Plex Sans + IBM Plex Mono | ~8/10 | deployed, working |
| **This lane's instruction** | dark "Data-Dense Dashboard" | Fira Code + Fira Sans | 8/10 | what this brief follows |
| **`docs/DESIGN_AMEX.md`** (mtime 13:52 — the newest artifact in the repo) | **light** | Public Sans + Source Serif 4 | **4/10** | written, **not implemented anywhere** |

`docs/DESIGN_AMEX.md` opens with: *"**Supersedes the dark 'Data-Dense Dashboard' direction.**
Wilson's call, 6 Sep."* It is timestamped four minutes after the frontend was last written, and
`grep` finds no reference to `amex`, `#006FCF`, or `Public Sans` anywhere in `frontend/src`.

**Read that as: my instruction may be stale.** I did not act on my own judgement about which wins.

To make this brief useful either way, every item below is tagged:

- **`[REPAINT-PROOF]`** — survives a light-mode Amex reskin unchanged. Type scale, spacing,
  stroke widths, focus behaviour, keyboard access, the CSS-specificity bug. Roughly two-thirds
  of the work. Implement these now regardless of which direction wins.
- **`[DARK-ONLY]`** — a specific hex or alpha value that a light reskin would discard.

Where `DESIGN_AMEX.md` §5–6 already agrees with a finding here (minimum 2px strokes, 4.5:1 text,
visible focus rings, direct-label the realized return, no emoji), the item is marked
**`↔ AMEX-ALIGNED`**. Those are settled under either direction.

---

## 1. Audit — what the current UI already does well

Do not "improve" these. They are the reason the app reads as an instrument.

**`Panel.tsx`** — the single strongest structural idea in the build. A bordered section with an
index chip (`01`…`06`), a left title, and a right-hand slot for a standing caveat. The right slot
is doing real work: `Console.tsx` uses it to keep *"directional hit-rate withheld by contract §7"*
and *"flat PIT is the win condition"* permanently on screen next to the numbers they qualify.
That is contract-as-chrome, and it is exactly right for a judged demo.

**`.panel::before` / `::after` corner ticks** (`globals.css`) — 9px L-brackets on opposite
corners. Cheap, non-decorative, and they read as measurement equipment rather than as a card.
This is the design language's best gesture.

**`FanChart.tsx`** — the terminal-density strip welded to the right edge of the fan is genuinely
good information design: the fan and `TerminalHistogram` become one object seen from two angles,
and the viewer gets that without narration. The honesty footer that states whether the envelope
is real per-step path data or a √t expansion of terminal quantiles is the kind of thing that wins
a judge over. Keep both.

**`FanChart.tsx` lines 129–142** — the code comment documenting that `className="label"` beats an
SVG `fontSize` presentation attribute, with an inline-style fix. Correct diagnosis, and it is the
only place in the build that got it right (see item **P0-6**).

**`PitHistogram.tsx`** — refuses to render a verdict below n=30 and says why, in plain English,
on screen. `Scorecard.tsx` labels its own headline *"Read this as n = 1"* and ships the demeaned
twin beside the raw lift. `BacktestPanel.tsx` prints `n_tests = 0` as a designed state rather
than an error. `EventLedger.tsx` treats an empty ledger as a first-class screen. This is the
product's actual differentiator rendered as UI, and it is well done.

**`LeakagePanel.tsx`** — CONTRACT §8 demanded the disclosure be stated "out loud, in the
product," and this is a full-width hazard-striped panel with a serif headline, not a footnote.
The three numbered guards and the collapsible prior-art section are the right shape.

**`ModeToggle.tsx`** — honest about mock vs live, with a health-probe dot and a re-probe button.
The mock banner in `Console.tsx` is impossible to miss. Do not soften either.

**`Console.tsx` lines 40–57** — the keyed `{key, events, bt}` ledger state. Staleness is derived
at render time, so an out-of-order response is *physically unable* to paint under the wrong
ticker. Structural, not cosmetic. Untouchable.

---

## 2. The typography conflict, resolved — do not re-decide

Locked system: **Fira Code** (headings/labels), **Fira Sans** (body), tabular figures on all
numbers. Shipped: IBM Plex Mono + IBM Plex Sans + Instrument Serif.

**Decision — swap the two locked faces, keep the serif on a short leash.**

The swap is mechanical and touches **zero components**, because every component references only
`.num`, `.label`, or `var(--font-mono)` — never a font name.

**`frontend/src/app/layout.tsx`** `[REPAINT-PROOF]`

```ts
import { Instrument_Serif, Fira_Code, Fira_Sans } from "next/font/google";

const sans = Fira_Sans({
  weight: ["300", "400", "500", "600"],
  subsets: ["latin"],
  variable: "--font-fira-sans",
  display: "swap",
});

const mono = Fira_Code({
  weight: ["400", "500", "600"],
  subsets: ["latin"],
  variable: "--font-fira-code",
  display: "swap",
});
// `display` (Instrument_Serif) stays exactly as written.
```

**`frontend/src/app/globals.css`** `@theme` block:

```css
--font-sans: var(--font-fira-sans), ui-sans-serif, system-ui, sans-serif;
--font-mono: var(--font-fira-code), ui-monospace, "SF Mono", monospace;
```

**Fira Code is monospaced, so every figure is tabular by construction** — the lock's
"tabular figures for all numbers" requirement is satisfied for anything carrying `.num`. Keep
`font-variant-numeric: tabular-nums` on `.num` anyway; it costs nothing and it is what protects
the Fira Sans fallback path.

**Instrument Serif survives in exactly two places** — `Console.tsx:302` (masthead `<h1>`) and
`LeakagePanel.tsx:31` (`<h3>`). Those are the product's one editorial gesture and they are
working. It is removed from the other three call sites, where it is either wrong or invisible:

| File:line | Current | Change | Why |
|---|---|---|---|
| `Scorecard.tsx:30` | `className="display num …"` | `className="num …"` | **The headline CRPS-lift number is currently rendering in a serif display face with proportional figures.** See P0-6. |
| `Console.tsx:225` | `className="display …"` empty state | `className="label-title"`, size `1.5rem` | An empty state should not carry the hero face. |
| `Console.tsx:262` | `className="display text-3xl"` footer wordmark | `className="num"`, `letter-spacing: 0.12em` | The wordmark is `rulial-markets` — a lowercase mono lockup reads more like the product than a serif does. |

*If the owner wants strict two-face purity:* drop `Instrument_Serif` from `layout.tsx` and set
`--font-display: var(--font-fira-code)`. Both `<h1>` and `<h3>` then need explicit
`font-weight: 500` and `letter-spacing: -0.01em`. **Do not do this without being asked** — it is
a redesign, and this lane was told not to propose one.

---

## 3. Prioritized polish items

### P0 — projection legibility. Without these the demo is harder to read from the back of the room.

---

**P0-1 · `globals.css` — the `.label` class is 10.88px and it is on everything.**
`[REPAINT-PROOF]` `↔ AMEX-ALIGNED` (their label spec is 12px/0.08em)

`.label` is `font-size: 0.68rem` (10.88px) with `letter-spacing: 0.22em`. It carries every panel
title (via `Panel.tsx`), every field label, every chart legend, every stat caption — roughly 50
call sites. At 10.88px with 2.4px of letter-spacing, word shapes dissolve at projection distance;
the tracking actively hurts because the eye loses the word as a unit before it loses the letters.

Replace with a two-tier system:

```css
.label {
  font-family: var(--font-mono);
  font-size: 0.75rem;        /* 12px — the DOM floor */
  line-height: 1.35;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-ink-faint);
}
.label-bright { color: var(--color-ink-dim); }

/* NEW — panel titles only. They are section headings, not captions. */
.label-title {
  font-family: var(--font-mono);
  font-size: 0.8125rem;      /* 13px */
  line-height: 1.3;
  letter-spacing: 0.11em;
  text-transform: uppercase;
  font-weight: 500;
  color: var(--color-ink-dim);
}
```

**`Panel.tsx`**, the `<h2>`: `className="label label-bright truncate"` → `className="label-title truncate"`.

**`ModeToggle.tsx`**, both toggle buttons and the health-probe label: `className="label"` →
`className="label-title"`. Mock-vs-live is an honesty signal; it should not be the smallest text
on screen.

> Watch the `Panel` `right` slots when this lands. The longest is
> `"|Δ| ≥ 15% over 5 sessions · major tier ≥ 25% · frozen"` (`Console.tsx`, seed-ledger panel).
> At 12px it should still fit on one line at ≥1280px, but **`VERIFY VISUALLY`**. If it wraps,
> shorten the string — do not shrink the type back down.

---

**P0-2 · `globals.css` — `--color-ink-faint` fails WCAG AA and it is carrying body copy.**
`[DARK-ONLY]` `↔ AMEX-ALIGNED` (their §6 requires 4.5:1 on every text pair)

`#5d6879` measures **3.37:1** on `--color-panel` `#0d1017` and **3.59:1** on `--color-void`.
AA for normal text is 4.5:1. It is not decorative — it is the default `.label` colour, every
chart axis label, the `Guard` card body copy in `LeakagePanel`, both empty-state paragraphs, the
footer, and every `note` line in `Scorecard`/`BacktestPanel`.

```css
--color-ink-faint: #7d8b9e;   /* was #5d6879 */
```

Measured: **5.49:1** on panel, **5.84:1** on void. The three-step ink ramp stays properly ordered
and still reads as a hierarchy:

| Token | Hex | vs `--color-panel` | vs `--color-void` |
|---|---|---|---|
| `--color-ink` | `#eef1f6` | 16.81:1 | 17.89:1 |
| `--color-ink-dim` | `#9aa6b8` | 7.72:1 | 8.22:1 |
| `--color-ink-faint` | **`#7d8b9e`** | **5.49:1** | **5.84:1** |

---

**P0-3 · `globals.css` — the rule ramp is invisible under projector lights.**
`[DARK-ONLY]`

`--color-rule` `#1e2532` measures **1.24:1** on panel; `--color-rule-bright` `#2f3a4d` measures
**1.66:1**. Every panel border, every divider, every chart gridline and the corner ticks are drawn
in these. In a room with the lights up, a 1.24:1 edge is not there. This also collides with the
locked anti-pattern *"hairline strokes."*

Shift the whole ramp up one step and add a dedicated axis token:

```css
--color-rule:        #2f3a4d;   /* was #1e2532 → 1.66:1 on panel */
--color-rule-bright: #46546d;   /* was #2f3a4d → 2.49:1 on panel */
--color-axis:        #54637e;   /* NEW → 3.14:1 on panel, 3.34:1 on void */
```

`--color-axis` clears the 3:1 that WCAG 1.4.11 requires of graphical objects that carry meaning.
Use it for: chart baselines, the PIT uniform-reference line's companion axis, the zero line in
`PerEventStrip`, and — critically — **form-control borders**, which currently sit at 1.24:1 (see
P0-7). This shift also fixes the `.panel::before/::after` corner ticks for free: they move from
1.66:1 to 2.49:1.

---

**P0-4 · `FanChart.tsx` — the 90% band, the whole point of the chart, starts at 5% opacity.**
`[DARK-ONLY]`

```
#fanOuter  phosphor 0.05 → 0.17    composited: 1.08:1 → 1.43:1 against panel
#fanInner  phosphor 0.13 → 0.36    composited: 1.29:1 → 2.46:1
```

A 1.08:1 fill is not visible on a projector, on a laptop in a bright room, or in a photo of the
screen. The p5–p95 envelope *is* the product's argument — it must read as a shape from ten metres.

```jsx
<linearGradient id="fanOuter" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%"   stopColor="var(--color-phosphor)" stopOpacity="0.18" />
  <stop offset="100%" stopColor="var(--color-phosphor)" stopOpacity="0.28" />
</linearGradient>
<linearGradient id="fanInner" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%"   stopColor="var(--color-phosphor)" stopOpacity="0.32" />
  <stop offset="100%" stopColor="var(--color-phosphor)" stopOpacity="0.46" />
</linearGradient>
```

Measured composites against `--color-panel`: outer **1.47:1 → 1.97:1**, inner **2.20:1 → 3.36:1**.
The two bands stay separable (outer tops out below where inner starts) and the p5/p95 boundary
strokes at `opacity 0.45` still give each band an edge — raise those to `0.6` and
`strokeWidth={1.5}` while you are in the file.

**The legend swatches have the same disease.** `Legend swatch="rgba(55,230,207,0.14)"` for p5–p95
renders a 24×12px block at **1.32:1** — a blank rectangle. Update both swatch values to match the
new band midpoints and give every swatch an edge:

```jsx
<Legend swatch="rgba(55,230,207,0.39)" label="p25–p75" />
<Legend swatch="rgba(55,230,207,0.23)" label="p5–p95" />
```

and in the `Legend` component, add to the non-`line` swatch:
`boxShadow: "inset 0 0 0 1px rgba(55,230,207,0.55)"`.

---

**P0-5 · `globals.css` — the full-viewport grain overlay sits on top of every chart.**
`[DARK-ONLY]` `VERIFY VISUALLY`

`body::after` is a fractal-noise SVG at `opacity: 0.22` with `mix-blend-mode: overlay`, fixed over
the entire viewport including the SVGs. Film grain costs effective contrast everywhere, and on a
projector (or a screen-share, or a photo a judge takes) fine noise moirés against the pixel grid.
`body::before` adds a 1px dot lattice at `rgba(120,145,180,0.16)` on a 34px pitch, which composites
to **1.19:1** against the void — enough to texture the ground *and* enough to compete with a
gridline behind a chart.

Keep the atmosphere, halve the cost:

```css
body::after  { opacity: 0.10; }                              /* was 0.22 */
/* in body::before, third background-image layer: */
radial-gradient(rgba(120, 145, 180, 0.09) 1px, transparent 1px);   /* was 0.16 → 1.10:1 */
```

The two soft field glows (`0.09` teal, `0.055` amber) are fine — leave them.

---

**P0-6 · `Scorecard.tsx:30` + `globals.css` — the single most important number on the screen is
set in the one face that has no tabular figures.** `[REPAINT-PROOF]`

`<div className="display num text-[clamp(3rem,7vw,5.6rem)]">` applies both `.display`
(`font-family: var(--font-display)` → Instrument Serif) and `.num`
(`font-family: var(--font-mono)`). Equal specificity — one class each — so **source order decides,
and `.num` is declared before `.display` in `globals.css`.** `.display` wins. The headline
CRPS-lift percentage, at up to 5.6rem, renders in a serif display face with proportional figures.
This violates the locked "tabular figures for all numbers" rule at the exact place it matters most,
and it makes the number visibly jitter in width as it changes between runs.

Two fixes, apply both:

1. **`Scorecard.tsx:30`** — drop `display` from the className. Fixes the instance and documents intent.
2. **`globals.css`** — move the `.num` declaration *below* `.display` so `.num` wins any future
   collision. A number is a number regardless of what else it is tagged.

---

**P0-7 · `globals.css` — form-control borders sit at 1.24:1.** `[DARK-ONLY]` `↔ AMEX-ALIGNED`

`select, input, textarea { border: 1px solid var(--color-rule); }`. WCAG 1.4.11 requires 3:1 for
the boundary of an interactive control. After the P0-3 ramp shift `--color-rule` reaches only
1.66:1 — not enough. Point controls at the new axis token and thicken the stroke:

```css
select, input, textarea {
  background: var(--color-panel-2);
  border: 1px solid var(--color-axis);   /* 3.14:1 */
  color: var(--color-ink);
  font-family: var(--font-mono);
  font-size: 1rem;                        /* explicit — UA default is ~13.33px */
  border-radius: 0;                       /* explicit — Safari rounds selects */
}
```

---

### P1 — coherence. The build is consistent within components and drifts between them.

---

**P1-1 · `Panel.tsx` — panel padding disagrees with `LeakagePanel.tsx`.** `[REPAINT-PROOF]`

`Panel` uses `p-5` (20px) body and `px-5 py-3` header. `LeakagePanel` — the one panel that does
not use the `Panel` component — uses `px-6 py-6` (24px). Side by side down a single scroll column,
that 4px is visible as a wobble in the left edge of the content.

`Panel.tsx`: body `p-5` → `p-6`; header `px-5 py-3` → `px-6 py-3.5`. 24px becomes the single
gutter value for every panel in the app. `LeakagePanel` then needs no change.

---

**P1-2 · Four components render sub-12px text.** `[REPAINT-PROOF]`

12px is the DOM floor for this build. Current offenders, all to `text-[0.75rem]`:

| File | Current | Where |
|---|---|---|
| `Scorecard.tsx` | `text-[0.72rem]` | `Cell` note line |
| `Scorecard.tsx` | `text-[0.7rem]` | `ZRuler` σ tick labels |
| `BacktestPanel.tsx` | `text-[0.72rem]` | `Stat` note line |
| `ControlPanel.tsx` | `text-[0.7rem]` | preset card index `0{i+1}` |
| `ControlPanel.tsx` | `text-[0.82rem]` | preset card body → `text-sm` (0.875rem) |

`text-xs` (0.75rem) elsewhere is already at the floor — leave those.

---

**P1-3 · Signed-percentage formatting is reimplemented three times.** `[REPAINT-PROOF]`

`Scorecard.tsx` (twice), `BacktestPanel.tsx` (twice), and `LeakagePanel.tsx` (`Split`) each write
`` `${v >= 0 ? "+" : "−"}${(Math.abs(v) * 100).toFixed(1)}%` `` inline. Same logic, five copies,
and nothing enforces that they stay identical. Add one helper beside `pct` in `lib/quant.ts` —
it is LANE-UI's file, and this is a formatting concern, not a numeric one:

```ts
/** Signed percentage with an explicit + and a real U+2212 minus. Lift figures only. */
export const signedPct = (x: number, d = 1) =>
  `${x >= 0 ? "+" : "−"}${(Math.abs(x) * 100).toFixed(d)}%`;
```

**House rules for figures, apply everywhere:** percentages 1 decimal; CRPS 5 decimals (already
correct via `fixed(…, 5)`); PIT 3 decimals; σ 2 decimals; the minus glyph is always U+2212 `−`,
never a hyphen — a hyphen is narrower than a plus and breaks column alignment even in a
monospaced face.

---

**P1-4 · `Console.tsx` — the container caps at 1440px on a 1920px projector.** `[REPAINT-PROOF]`
`VERIFY VISUALLY`

`main` is `max-w-[1440px] px-6 lg:px-10`. On a 1920-wide projection that leaves ~240px of dead
ground on each side while the fan chart — the thing everyone is looking at — is squeezed. Raise to
`max-w-[1600px]`. Prose is already protected by per-block caps (`max-w-[70ch]`, `[74ch]`, `[92ch]`,
`[52ch]`), so nothing runs to an unreadable measure. This widens the effective chart scale factor
from ~1.32 to ~1.48, which is a free legibility gain on every SVG in the app.

---

**P1-5 · `LeakagePanel.tsx:28` — a dead Tailwind class fights an inline style.** `[REPAINT-PROOF]`

```jsx
<section className="panel rise border-[var(--color-hazard)]/40"
         style={{ borderColor: "rgba(255,207,74,0.34)" }}>
```

The `/40` opacity modifier does not apply to an arbitrary `var()` value; the class is inert and
the inline style is what paints. Delete the class, keep the style. Cosmetic, but the next person
to read it will assume the class works and will edit the wrong one.

---

**P1-6 · `globals.css` — the `sweep` keyframe is unused.** `[REPAINT-PROOF]`

`@keyframes sweep` (and its `--len` custom property) has no consumer in any component. Harmless.
Leave it if a stroke-draw animation is planned; delete it if not. Flagged for completeness only —
this is the only dead CSS in the file.

---

### P2 — finish.

**P2-1 · `PitHistogram.tsx` — the FanChart bug, uncorrected.** `[REPAINT-PROOF]`
The "PIT BUCKET" caption is `<text className="label" fontSize="10">`. `.label` sets
`font-size: 0.68rem`, which beats the presentation attribute — exactly the trap `FanChart.tsx`
documents in its own comment. Replace with the same inline-style pattern used there, at the size
mandated in §5.

**P2-2 · `TerminalHistogram.tsx` — stagger cost.** `[REPAINT-PROOF]`
56 bars at `120 + i * 5`ms means the last bar lands at 400ms. Fine. But `PitHistogram` uses
`i * 45` over 10 bars (405ms) and `PerEventStrip` uses `i * 28`. Three different stagger rates for
the same gesture. Standardise on **total stagger ≤ 350ms per chart**, computed as
`delay = i * (350 / n)`. Motion is locked at 4/10; a chart that is still assembling when the
presenter starts talking about it is a liability.

**P2-3 · `FanChart.tsx` — reduce the glow filter.** `[DARK-ONLY]`
`<filter id="glow"><feGaussianBlur stdDeviation="3">` on the median line and the actual marker.
At `stdDeviation="3"` in a 1000-unit viewBox this reads as instrument phosphor and it is doing
useful work — it keeps the median visible where it crosses the band boundary. Reduce to `2` and
stop there. **Do not add glow anywhere else**; the locked anti-pattern list says
"crypto-dashboard neon," and a second glow is where that starts.

**P2-4 · `EventLedger.tsx` — the sticky header needs an opaque backstop.** `[REPAINT-PROOF]`
`<thead className="sticky top-0 bg-[var(--color-panel)]">` sits over rows scrolling beneath it in a
`max-h-[340px]` container. `bg-panel` matches the panel behind it so it is opaque — correct — but
after the P0-3 ramp shift, add `border-b border-[var(--color-axis)]` to the header row so the
boundary between frozen header and scrolling body is unambiguous at distance.

---

## 4. Tokens — literal values to apply

Add to the `@theme` block in `frontend/src/app/globals.css`. Tailwind v4 exposes `@theme` custom
properties as utilities automatically; arbitrary-value classes (`text-[0.75rem]`) keep working, so
this is additive and breaks nothing.

### 4.1 Typographic scale

Root stays 16px. The scale is a 1.125–1.25 hybrid: tight in the label range where density matters,
opening up at the display end where the room has to read it.

```css
/* --- type scale ------------------------------------------------ */
--fs-label:      0.75rem;    /* 12px  DOM FLOOR. captions, legends, field labels   */
--fs-label-lg:   0.8125rem;  /* 13px  panel titles, mode toggle                    */
--fs-body-sm:    0.875rem;   /* 14px  secondary prose, table cells, notes          */
--fs-body:       1rem;       /* 16px  default body                                 */
--fs-body-lg:    1.0625rem;  /* 17px  narrative paragraph, plain-English readouts  */
--fs-lede:       1.125rem;   /* 18px  masthead sub-paragraph                       */
--fs-stat-sm:    1.375rem;   /* 22px  inline readouts, ledger emphasis             */
--fs-stat:       1.75rem;    /* 28px  Scorecard Cell values                        */
--fs-stat-lg:    2rem;       /* 32px  BacktestPanel Stat values                    */
--fs-metric:     2.5rem;     /* 40px  LeakagePanel Split figures                   */
--fs-hero:       clamp(2.6rem, 7vw, 6rem);      /* masthead h1 — unchanged         */
--fs-hero-2:     clamp(1.75rem, 3.4vw, 2.8rem); /* leakage h3  — unchanged         */
--fs-headline:   clamp(3rem, 7vw, 5.6rem);      /* CRPS lift   — unchanged         */

/* --- line heights ---------------------------------------------- */
--lh-tight:   1.1;    /* display, hero, big metrics                  */
--lh-snug:    1.3;    /* headings, stat values, table rows           */
--lh-normal:  1.5;    /* UI prose                                    */
--lh-relaxed: 1.65;   /* the narrative + disclosure paragraphs       */

/* --- tracking --------------------------------------------------- */
--tr-label:   0.14em;   /* .label, uppercase mono at 12px            */
--tr-title:   0.11em;   /* .label-title at 13px                      */
--tr-button:  0.16em;   /* SAMPLE THE ENSEMBLE (was 0.18em)          */
--tr-num:     0.01em;   /* large mono figures, opens them up slightly */
--tr-display: -0.015em; /* serif hero — unchanged                    */
```

Existing sizes that are already on-scale and need no edit: `text-lg` (18px) on the ticker/date
controls, `text-sm` (14px), `text-xs` (12px), and the three `clamp()` values above.

### 4.2 Spacing

Strict 4px base. Nothing off-scale — if a value is not on this list it is a bug.

```css
--sp-1:  0.25rem;  /*  4px  icon gaps, tick offsets                     */
--sp-2:  0.5rem;   /*  8px  label→value, inline chip padding            */
--sp-3:  0.75rem;  /* 12px  legend item gaps, table cell padding-y      */
--sp-4:  1rem;     /* 16px  intra-group stacking                        */
--sp-5:  1.25rem;  /* 20px  control-row gaps                            */
--sp-6:  1.5rem;   /* 24px  PANEL GUTTER — body and header, all panels  */
--sp-7:  1.75rem;  /* 28px  inter-block inside a panel                  */
--sp-8:  2rem;     /* 32px  panel→panel in the main grid                */
--sp-10: 2.5rem;   /* 40px  masthead→first panel                        */
--sp-16: 4rem;     /* 64px  footer separation                           */
```

Applied values, so nothing is left to judgement:

| Where | File | Value |
|---|---|---|
| Panel body padding | `Panel.tsx` | `--sp-6` (`p-6`) |
| Panel header padding | `Panel.tsx` | `--sp-6` × `0.875rem` (`px-6 py-3.5`) |
| Panel → panel | `Console.tsx` grid | `--sp-8` (`gap-8`, unchanged) |
| Masthead → first panel | `Console.tsx` | `--sp-8` (`mb-8`, unchanged) |
| Chart → its footer rule | `FanChart.tsx` | `--sp-3` above, `--sp-3` below (`mt-3 pt-3`, unchanged) |
| Grid hairline gaps (`gap-[1px]`) | `Scorecard`, `BacktestPanel`, `LeakagePanel`, `ControlPanel` | keep at `1px` — this is a border technique, not spacing |
| Page horizontal | `Console.tsx` | `px-6 lg:px-10`, unchanged |
| Page bottom | `Console.tsx` | `pb-28`, unchanged |

**Border radius: 0 everywhere.** The build is already fully square except UA defaults on
`<select>` in Safari — P0-7 pins that. Do not introduce a radius.

---

## 5. Chart legibility rules at projection distance

These are arithmetic, not taste. Every chart is an SVG with a `viewBox` scaled to its container,
so an SVG `font-size` of *N* renders at *N × scale* CSS pixels. The scale factors, computed from
the current layout at a 1440px viewport (`max-w-[1440px]`, `lg:px-10`, panel border + `p-5`):

| Chart | viewBox width | Container | **Scale** | at `max-w-[1600px]` |
|---|---|---|---|---|
| `FanChart` | 1000 | ~1318px | **1.32×** | 1.48× |
| `TerminalHistogram` | 1000 | ~1318px | **1.32×** | 1.48× |
| `PerEventStrip` (`BacktestPanel`) | 1000 | ~1318px | **1.32×** | 1.48× |
| `PitHistogram` | 620 | ~755px (1.4fr of a 2.4fr grid) | **1.22×** | 1.36× |

### Rule 1 — minimum rendered text is 16px CSS. No exceptions inside a chart.

Divide 16 by the scale factor and round up:

| Chart | Minimum SVG `fontSize` | Current values | Action |
|---|---|---|---|
| `FanChart` | **13** | 13 (y-axis ✓), 12 (x-axis ✗), 11 (density caption ✗), 14–15 (actual ✓) | x-axis 12 → **13**; density caption 11 → **13** |
| `TerminalHistogram` | **13** | 12 (quantile keys ✗), 12 (quantile values ✗), 15 (realized ✓) | both 12 → **13** |
| `PerEventStrip` | **13** | 11 (all three axis labels ✗) | 11 → **13** |
| `PitHistogram` | **14** | 11 (bucket labels ✗), 12 (count labels ✗), `.label` caption ✗ | buckets 11 → **14**; counts 12 → **15**; caption → inline style at **14** |

Never set an SVG text size with a CSS class. `.label` and `.num` both carry `font-size` in `rem`,
which resolves in *user-space units* and silently overrides the `fontSize` attribute — this is the
bug `FanChart.tsx` already documents at lines 129–142. `className="num"` alone is safe (it sets
only family and `tabular-nums`); `className="label"` on an SVG `<text>` is not.

### Rule 2 — minimum stroke is 2px rendered. `↔ AMEX-ALIGNED` (their §5: "Minimum stroke 2px. Hairlines vanish on a projector.")

At 1.32× a `strokeWidth={1}` renders at 1.32px. Locked anti-patterns forbid hairlines.

| Element | File | Current | Set to |
|---|---|---|---|
| Gridlines | `FanChart` | 1 | **1.5** (→2.0px), stroke `--color-rule-bright` |
| Zero line (the `t≈0` gridline) | `FanChart` | 1 @ opacity 0.9 | **2**, stroke `--color-axis`, opacity 1, solid |
| p5 / p95 boundary | `FanChart` | 1 @ 0.45 | **1.5** @ **0.6** |
| Median (p50) | `FanChart` | 2.5 | **3** |
| Realized-return line | `FanChart` | 2 dashed | **3**, dash `10 5` |
| Baseline | `TerminalHistogram` | 1 | **2**, stroke `--color-axis` |
| Zero line | `TerminalHistogram` | 1 dashed `3 4` | **1.5**, dash `4 6` |
| Quantile ticks | `TerminalHistogram` | 1 / 2 (p50) | **1.5** / **2.5** |
| Realized-return line | `TerminalHistogram` | 2.5 | **3** |
| Zero line | `PerEventStrip` | 1 | **2**, stroke `--color-axis` |
| Uniform reference | `PitHistogram` | 2 dashed `8 5` | **2.5**, dash `10 6` |
| Baseline | `PitHistogram` | 1 (default) | **2**, stroke `--color-axis` |

Dash patterns scale too: `strokeDasharray="2 5"` on the `FanChart` gridlines renders as a 2.6px
dash with a 6.6px gap, which reads as noise rather than as a dashed line. Use **`"3 6"`**.

### Rule 3 — the realized return is labelled on the mark, never in the legend only.
`↔ AMEX-ALIGNED` (their §5: *"Do not make the viewer hunt a legend for the single most important mark on screen."*)

Already correct in both charts (`ACTUAL −31.2%` on the line in `FanChart`, `REALIZED …` at the top
of the vertical rule in `TerminalHistogram`). **Protect this.** Two additions:

- `FanChart` — the `ACTUAL` label is placed at `x={M.l + 8}`, i.e. hard against the left axis. If
  the realized value lands within ~8% of a gridline it collides with that gridline's `%` label.
  Add a 3px-radius rounded backing rect in `--color-panel` at 0.85 alpha behind the text.
- Both charts — the label's `fontSize` should be **the largest text in the chart** (currently 14
  and 15 respectively). Keep them at least 2 units above every other label in their SVG.

### Rule 4 — colour is never the only channel.

`FanChart` already pairs the band colour with a written verdict
(*"actual landed inside / OUTSIDE the 90% band"*) — keep it, and keep the word `OUTSIDE`
capitalised; that is the only all-caps word in the footer and it is doing the work.
`PitHistogram` colours over-tall bars in `--color-hazard` — good, and it is already backed by the
prose readout. `EventLedger` colours `move_pct` up/down — the sign character is already present
via `pct()`, so this passes. `BacktestPanel`'s `PerEventStrip` encodes sign as colour *and* as
direction from the zero line — passes.

The one gap: `Scorecard`'s `Cell` components distinguish "CRPS (ours)" from "CRPS (null)" by
colour alone (`--color-phosphor` vs `--color-null`). The label text disambiguates, so this passes
in isolation — but **`--color-null` `#7b8db0` measures 5.69:1** and reads as merely dimmer rather
than as a different series. Leave the hue; add `note="the baseline we must beat"` weight by
setting the null `Cell`'s value to `font-weight: 400` against the phosphor cell's `500`.

### Rule 5 — the PIT histogram must be readable as "flat or not flat" with zero narration.

This is the contract's stated win condition (§7) and it is the chart most likely to be
misunderstood. Current state is good; three finishing moves:

1. The uniform-reference line is `--color-actual` dashed. Add a label at the right end of the
   line, inside the plot: `flat = calibrated`, `--color-actual`, `fontSize` **14**, `text-anchor:
   end`, at `x=600`. Do not rely on the legend below the chart. `↔ AMEX-ALIGNED` (their §5 asks for
   exactly this string).
2. Bar `opacity` is 0.6 / 0.75. Raise to **0.85** for both states — at 0.6 the phosphor fill sits
   at roughly half its stated contrast and the bar tops get soft.
3. Empty buckets render `{c || ""}` — nothing. At n≈12 across 10 buckets, several buckets are
   legitimately zero, and a *visible* zero is evidence. Render `0` in `--color-ink-faint` rather
   than an empty string.

### Rule 6 — every chart keeps its `role="img"` and `aria-label`.

All four already have one, and each label is a real sentence rather than "chart". Keep that
standard for anything new. Where a chart carries a numeric conclusion, restate it in the DOM as
text — `FanChart`'s inside/outside verdict and `PitHistogram`'s plain-English readout already do
this, which is what makes the SVGs non-essential for a screen-reader user.

---

## 6. Accessibility must-fixes

### 6.1 Contrast pairs — every text/background combination in the build

Measured against `--color-panel` `#0d1017` (the surface almost all text sits on). AA normal text
is 4.5:1; AA large text (≥18.66px bold or ≥24px) is 3:1.

| Foreground | Hex | Ratio | Verdict |
|---|---|---|---|
| `--color-ink` | `#eef1f6` | 16.81:1 | ✅ AAA |
| `--color-ink-dim` | `#9aa6b8` | 7.72:1 | ✅ AAA |
| `--color-ink-faint` | `#5d6879` | **3.37:1** | ❌ **FAIL — fix per P0-2 → `#7d8b9e`, 5.49:1** |
| `--color-phosphor` | `#37e6cf` | 12.13:1 | ✅ AAA |
| `--color-actual` | `#ffb020` | 10.41:1 | ✅ AAA |
| `--color-hazard` | `#ffcf4a` | 12.94:1 | ✅ AAA |
| `--color-up` | `#52e07a` | 11.15:1 | ✅ AAA |
| `--color-down` | `#ff5f56` | 6.36:1 | ✅ AA |
| `--color-null` | `#7b8db0` | 5.69:1 | ✅ AA |
| `--color-rule` (as a boundary) | `#1e2532` | **1.24:1** | ❌ **FAIL — P0-3 / P0-7** |
| `--color-rule-bright` (as a boundary) | `#2f3a4d` | **1.66:1** | ❌ **FAIL — P0-3** |

After P0-2 and P0-3 land, every text pair in the app clears AA and every informative boundary
clears 1.4.11's 3:1 via `--color-axis` (3.14:1).

Two combinations to check that are *not* text-on-panel:

- **Hazard on hazard-tint.** `LeakagePanel` puts `--color-hazard` `#ffcf4a` text on
  `rgba(255,207,74,0.05)` over panel. The tint is 5% — the effective background is within a
  rounding error of `--color-panel`, so the 12.94:1 figure holds. ✅
- **Mock banner.** `Console.tsx` puts `--color-hazard` on `rgba(255,207,74,0.06)` over
  `--color-void`. Same reasoning, 13.77:1. ✅

### 6.2 Focus states — currently unspecified for every button in the app

`globals.css` sets `outline: none` on `:focus` for `select, input, textarea` and replaces it with
a phosphor border plus a 1px ring. Buttons get nothing — they fall through to the UA focus ring,
which is inconsistent across browsers and is the first thing a `outline: none` reset will eat.
There are **eleven** interactive buttons (mode toggle ×2, health re-probe, "try live backend",
"fall back to mock", 4 preset cards, "SAMPLE THE ENSEMBLE", "read the full disclosure") plus every
`EventLedger` row.

Add to `globals.css`: `[REPAINT-PROOF]` `↔ AMEX-ALIGNED` (their §6: *"Focus rings visible, 2px, offset 2px. Do not remove outlines."*)

```css
/* One focus treatment for the whole app. Keyboard-only — never fires on mouse. */
:where(button, a, [role="button"], summary, tr[tabindex]):focus-visible {
  outline: 2px solid var(--color-phosphor);
  outline-offset: 2px;
}
/* Inputs keep their in-border treatment, but must also carry a real outline. */
select:focus-visible, input:focus-visible, textarea:focus-visible {
  outline: 2px solid var(--color-phosphor);
  outline-offset: 1px;
}
/* Never remove a focus ring on a non-:focus-visible basis. */
```

Note `--color-phosphor` is 12.13:1 against panel, so the ring clears 1.4.11's 3:1 for a focus
indicator with room to spare. On the phosphor-bordered "SAMPLE THE ENSEMBLE" button the ring would
sit on a phosphor border — give that one button `outline-color: var(--color-ink)` (16.81:1) so the
focus state is distinguishable from the resting state.

### 6.3 `EventLedger.tsx` — clickable rows are unreachable by keyboard. `[REPAINT-PROOF]`

```jsx
<tr onClick={() => onPick(e)} className="cursor-pointer …">
```

A `<tr>` with a click handler and no `tabIndex`, no `role`, and no key handler is invisible to
keyboard and screen-reader users, and clicking it silently rewrites the as-of date and the event
text in the control panel — a state change with no accessible trigger. Minimal fix, no structural
change:

```jsx
<tr
  onClick={() => onPick(e)}
  onKeyDown={(k) => {
    if (k.key === "Enter" || k.key === " ") { k.preventDefault(); onPick(e); }
  }}
  tabIndex={0}
  role="button"
  aria-label={`Load ${e.ticker} ${e.date}, ${pct(e.move_pct, 1)} into the control panel`}
  className="cursor-pointer …"
>
```

Also add a hover/focus affordance beyond the background change — a 2px `--color-phosphor` left
border on `:hover, :focus-visible` so the row announces that it is a control.

### 6.4 `prefers-reduced-motion` — one real gap. `[REPAINT-PROOF]` `↔ AMEX-ALIGNED`

The CSS block is good: it kills `.rise`, `.bloom`, `.pulse-dot` and clamps all transition
durations. Two things it cannot reach:

1. **`Console.tsx`, the `run()` callback** — `scrollIntoView({ behavior: "smooth" })` is
   JavaScript and ignores the media query entirely. A smooth scroll of several hundred pixels is
   exactly the vestibular trigger the preference exists for. Fix:

   ```ts
   const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
   document.getElementById("ensemble")?.scrollIntoView({
     behavior: reduce ? "auto" : "smooth",
     block: "start",
   });
   ```

2. **The `* { transition-duration: 0.01ms }` rule does not clamp `animation-duration`** for any
   animation added later. Broaden the reset so future work inherits it:

   ```css
   @media (prefers-reduced-motion: reduce) {
     *, *::before, *::after {
       animation-duration: 0.01ms !important;
       animation-iteration-count: 1 !important;
       transition-duration: 0.01ms !important;
       scroll-behavior: auto !important;
     }
   }
   ```

   Keep the explicit `.rise, .bloom, .pulse-dot { animation: none !important }` line as well — the
   `both` fill-mode on `.rise` means a 0.01ms animation still lands on its end state, but `none`
   is unambiguous.

### 6.5 Smaller items

- **`ControlPanel.tsx`, the as-of-date hint.** The in/out-of-window message changes colour between
  `--color-phosphor` and `--color-hazard` — but the *text* also changes, so colour is not the only
  channel. ✅ No change. Do bump it from `text-xs` to `text-sm`; it is the sentence that explains
  why a score does or does not appear.
- **`ControlPanel.tsx`, the run button.** `disabled:opacity-35` on the phosphor text yields roughly
  4.2:1 — below AA, but WCAG explicitly exempts disabled controls. Acceptable. Consider `40` so
  the disabled reason is still readable at distance.
- **`aria-pressed` on the mode toggle** is already correct. The `role="group"` with
  `aria-label="data source"` is correct. Leave both.
- **No emoji as icons anywhere in the build.** ✅ Confirmed by grep. Keep it that way.
- **`lang="en"` is set** on `<html>` in `layout.tsx`. ✅

---

## 7. DO NOT TOUCH

Breaking any of these costs working behaviour, a contract guarantee, or the product's
defensibility. This list is not advisory.

### Frozen by CONTRACT.md — a lane may not change these at all
- `CONTRACT.md`, `backend/rulial/config.py`, `backend/rulial/types.py`.
- `frontend/src/lib/types.ts` — the TS mirror of the frozen dataclasses. Its own header says
  "do not improve these here." The constants `TRAIN_END`, `TIER_MAJOR`, `TIER_SIGNIFICANT`,
  `WINDOW_DAYS` are frozen values, not defaults.
- **The `crps_null` column in `Scorecard.tsx`.** CONTRACT §7: the null may not be removed,
  "however good it makes us look to drop it." It may not be visually demoted either — no
  collapsing it into a tooltip, no moving it below the fold.
- **The absence of directional hit-rate.** CONTRACT §7 forbids it as a headline. `Scorecard.tsx`
  does not even compute it, deliberately. Do not add it. Do not remove the standing caveat
  *"directional hit-rate withheld by contract §7"* from the panel header.
- **`LeakagePanel.tsx` in its entirety, as a full-width panel.** CONTRACT §8 requires the
  disclosure to appear in the UI. Restyling its colours is in scope; shrinking it, collapsing it
  behind a disclosure triangle by default, or moving it below the walk-forward panel is not.

### Copy owned by other lanes — restyle, never rewrite
- **The three prior-art citations in `LeakagePanel.tsx`** (Lopez-Lira/Tang/Zhu arXiv:2504.14765;
  Gao/Jiang/Yan arXiv:2512.23847; Gneiting/Balabdaoui/Raftery 2007) and every figure quoted around
  them — 0.61% / 16.87% MAPE, 80.6% → 45.7%, 1.78×, +14.8% → −4.5%, +2.0%, 30 up-jumps to 3.
  **This lane did not verify any of them and has no basis to edit them.** Changing a digit while
  "tidying" a paragraph is the single worst thing that could happen to this project.
- **`PitHistogram.tsx`'s power thresholds** — `UNDIAGNOSTIC_BELOW = 30`, `CONCLUSIVE_AT = 60`, and
  the ~30%-at-n=12 / ~92%-at-n=60 figures. Measured numbers with a stated provenance
  ("Phase-1 recon"). Not design parameters.
- **`Scorecard.tsx`'s "Read this as n = 1" paragraph** and the +10.4% median / −6.8% mean figures.
- **`presets.ts`** — the four scenarios, their dates, and their text. Every `as_of` sits inside the
  train window by construction; changing one silently pushes the generator past the frozen
  boundary. Tone colours and card layout are fair game; the data is not.
- The empty-state paragraphs in `EventLedger.tsx` and `BacktestPanel.tsx`. They explain *why* a
  ticker legitimately has zero events. Typographic changes only.

### Working machinery — visual pass only
- **`Console.tsx` lines 40–57**, the keyed ledger state and the `fresh`/`ledgerKey` derivation, and
  the `decided` ref that makes the health probe decide the initial mode exactly once. Both carry
  comments explaining the race they prevent.
- **All of `lib/`** — `api.ts`, `mock.ts`, `quant.ts`, `types.ts`. The one permitted edit is
  adding `signedPct` to `quant.ts` per P1-3. Do not touch the CRPS estimators, the mulberry32 RNG,
  `buildFan`, or `terminalReturns`.
- **The dual-shape `PathsPayload` handling** — `isPathMatrix`, and the on-screen line that says
  whether the envelope is real path data or a √t expansion. That sentence is a live honesty
  disclosure, not a debug string.
- **The mock fallback path and `MOCK_NOTICE`.** The banner stays loud and yellow.
- **`ModeToggle.tsx`'s health-probe semantics.** Restyle freely; do not change what the dot means
  or default it to "live" when the probe has not returned.
- Every component's props interface. This is a visual and typographic pass — data flow, fetches
  and computed values do not change. (`DESIGN_AMEX.md` §7 states the identical boundary.)

### Design decisions that are already right
- Square corners, zero border-radius, everywhere.
- The `Panel` index chips `01`–`06` and the right-hand caveat slot.
- The `.panel::before/::after` corner ticks.
- The terminal-density strip on the right edge of `FanChart`.
- Direct labelling of the realized return on both charts.
- `role="img"` + a full-sentence `aria-label` on all four SVGs.

---

## 8. Implementation order and verification

Sequence, because P0-3 changes token values that later items reference:

1. `globals.css` — tokens: fonts (§2), `--color-ink-faint` (P0-2), rule ramp + `--color-axis`
   (P0-3), type scale + spacing (§4), `.label` / `.label-title` (P0-1), `.num` moved below
   `.display` (P0-6), form controls (P0-7), focus block (§6.2), reduced-motion block (§6.4),
   grain and lattice (P0-5).
2. `layout.tsx` — font swap (§2).
3. `Panel.tsx` — `label-title` on the `<h2>`, `p-6` / `px-6 py-3.5` (P0-1, P1-1).
4. `Console.tsx` — `max-w-[1600px]` (P1-4), reduced-motion scroll (§6.4), the two `display`
   removals (§2).
5. `Scorecard.tsx`, `BacktestPanel.tsx`, `LeakagePanel.tsx`, `ControlPanel.tsx` — `signedPct`
   (P1-3), sub-12px sizes (P1-2), the dead class (P1-5).
6. `FanChart.tsx`, `TerminalHistogram.tsx`, `PitHistogram.tsx` — §5 in full (P0-4, P2-1, P2-3).
7. `EventLedger.tsx` — keyboard access (§6.3), sticky-header border (P2-4).
8. `ModeToggle.tsx` — `label-title` (P0-1).

Then verify, in this order:

- [ ] `npm run build` is clean. No new dependency was added — Fira Code and Fira Sans both ship
      via `next/font/google`, which is already in use.
- [ ] Zoom the browser to **50%** and read the page from two metres. That approximates a judge at
      the back of the room. Every label must still be a word, not a texture.
- [ ] Tab through the entire page with the mouse untouched. Eleven buttons, every form control,
      and every ledger row must show a visible ring, in order, with nothing skipped.
- [ ] Toggle OS "Reduce motion" and re-run a forecast. Nothing animates; the jump to `#ensemble`
      is instant.
- [ ] Run `BA` (which has events) and a ticker with none. Both empty states must still be
      first-class screens, not error states.
- [ ] Screenshot the fan chart and open it at 25%. The p5–p95 band must still read as a shape.
- [ ] `VERIFY VISUALLY` — the `Panel` right-slot caveat strings at 12px (P0-1) and the
      `max-w-[1600px]` change (P1-4) on the actual projector or a 1920px window.
- [ ] Nothing on the §7 list changed. Diff it before handing back.
