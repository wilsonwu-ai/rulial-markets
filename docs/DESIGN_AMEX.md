# Design brief — American Express financial-institution direction

**Supersedes the dark "Data-Dense Dashboard" direction.** Wilson's call, 6 Sep: the product
should read like a financial institution's own tool, not a trading terminal.

## 1. Fonts — the licensing situation, read this first

American Express uses two proprietary typefaces, confirmed by reading their live CSS:

| Their font | Refs in amex.com | What it is | Can we use it |
|---|---|---|---|
| `BentonSans` | 54 | Font Bureau, descended from Morris Fuller Benton's News Gothic | **No.** Licensed, served from aexp-static.com |
| `Guardian` | 38 | Commercial Type, the Guardian's editorial family | **No.** Licensed |

We are not copying their font files or hotlinking their CDN. That is a licensing violation and
the CDN would fail for us anyway. Instead we use the closest legally-clear equivalents, chosen
on lineage rather than vibes:

```css
/* Benton Sans descends from News Gothic / Franklin Gothic.
   Public Sans is drawn from Libre Franklin, the same lineage. This is the
   honest analog, not an approximation of an approximation. */
@import url('https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,300..800;1,300..800&family=Source+Serif+4:opsz,wght@8..60,300..700&display=swap');

--font-sans:  'Public Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
--font-serif: 'Source Serif 4', Georgia, 'Times New Roman', serif;  /* Guardian analog, headlines only */
--font-mono:  ui-monospace, 'SF Mono', Menlo, monospace;            /* tickers, dates, raw values */
```

Numbers must use `font-variant-numeric: tabular-nums` everywhere. In a financial UI a column of
figures that shifts width as it animates reads as broken.

## 2. Colors — extracted from amex.com, not invented

```css
:root {
  /* brand */
  --amex-blue:        #006FCF;   /* primary. 210 references on their homepage */
  --amex-blue-hover:  #0066BE;
  --amex-blue-press:  #005DAE;
  --amex-blue-light:  #56A1E3;
  --amex-blue-pale:   #B5D7F4;
  --amex-blue-tint:   #EDF7FF;   /* pale wash for callout backgrounds */
  --amex-navy:        #00175A;   /* headings, deep chrome */

  /* neutrals */
  --gray-000: #FFFFFF;
  --gray-050: #FBFBFB;
  --gray-100: #F4F4F4;
  --gray-150: #F7F8F9;
  --gray-200: #E0E0E0;   /* borders, dividers */
  --gray-400: #BDBDBD;
  --gray-500: #8C8C8C;   /* NOT for body text, fails contrast on white */
  --gray-600: #737373;   /* smallest permissible secondary text on white */
  --gray-800: #3D3D3D;
  --gray-900: #1D2429;   /* body text */

  /* semantic, for returns. NEVER color alone: pair with sign and/or arrow glyph */
  --pos: #00733B;
  --neg: #B42318;
}
```

**Mode flips to LIGHT.** White and near-white surfaces, blue as the single accent, navy for
headings. This is the biggest change: the current UI is dark. Do not keep dark panels for
"contrast" — that reads as two designs stapled together.

## 3. What "feels like Amex" actually means

Not just blue. Four structural properties:

1. **Generous whitespace.** Amex is not dense. Sections breathe. Our density dial drops from
   8/10 to about 4/10. Fewer things per screen, each one larger.
2. **Card surfaces on a tinted ground.** White cards, `--gray-150` page background, 1px
   `--gray-200` border, `border-radius: 8px`, very soft shadow. No glass, no glow, no neon.
3. **One unmistakable primary action per view.** Solid `--amex-blue`, white text, generous
   padding, `border-radius: 999px` (Amex uses full-round buttons). Everything else is a
   text link or an outlined secondary.
4. **Restraint with color.** Blue for interactive and for our own data series. Green/red only
   for realized returns, and always with a sign character so color is never the only signal.

## 4. Type scale

```
display   44px / 1.1  / 700  navy   serif    hero only
h1        32px / 1.2  / 700  navy   sans
h2        24px / 1.3  / 600  navy   sans
h3        18px / 1.4  / 600  gray-900 sans
body      16px / 1.6  / 400  gray-900 sans
small     14px / 1.5  / 400  gray-600 sans
label     12px / 1.4  / 600  gray-600 sans   uppercase, 0.08em tracking
metric    36px / 1.0  / 700  navy   sans     tabular-nums
```

Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64. Nothing off-scale.

## 5. Charts, on a light ground

- Fan chart bands: tints of `--amex-blue` at increasing opacity toward the median. Median line
  solid `--amex-navy`, 2px.
- Realized-return overlay: `--neg` or `--pos` 2px, dashed, **labelled directly on the line**.
  Do not make the viewer hunt a legend for the single most important mark on screen.
- Histogram bars: `--amex-blue-light`, 1px white gap between bars.
- PIT histogram: same blue, with a dashed `--gray-500` line at the uniform expectation, labelled
  "flat = calibrated" so the meaning is legible without narration.
- Gridlines `--gray-200`, never darker. Axis labels `--gray-600`, 12px.
- Minimum stroke 2px. Hairlines vanish on a projector.

## 6. Non-negotiables carried over

- **The leakage disclosure panel stays**, per CONTRACT.md section 8. On a light ground it becomes
  a `--amex-blue-tint` callout with a `--amex-blue` left rule. Prominent, not fine print.
- **The MOCK/LIVE toggle stays** and stays honest about its state.
- Contrast: every text/background pair clears 4.5:1. `--gray-500` on white does NOT; use
  `--gray-600` or darker for anything a person has to read.
- Focus rings visible, 2px `--amex-blue`, offset 2px. Do not remove outlines.
- `prefers-reduced-motion` respected.
- No emoji as icons.

## 7. Do not touch

Component structure, prop contracts, API calls, data shapes, the mock fallback, `lib/`. This is
a visual and typographic reskin of a working application. Nothing about how it fetches or
computes changes.
