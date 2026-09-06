import type { Metadata } from "next";
import { Public_Sans, Source_Serif_4 } from "next/font/google";
import "./globals.css";

/**
 * Two faces plus the system mono, per docs/DESIGN_AMEX.md §1.
 *
 * American Express sets its site in BentonSans (54 refs in their live CSS) and
 * Guardian (38 refs). Both are licensed and served from aexp-static.com; we do
 * not copy their font files and we do not hotlink their CDN. So each face is
 * replaced by the closest legally-clear equivalent chosen on LINEAGE, not vibes:
 *
 *  - Public Sans  — drawn from Libre Franklin, which descends from Franklin
 *                   Gothic / News Gothic. Benton Sans descends from the same
 *                   Morris Fuller Benton originals. Honest analog, not an
 *                   approximation of an approximation. Carries all UI prose.
 *  - Source Serif 4 — the Guardian analog. Kept on a short leash: the masthead
 *                   and the leakage-disclosure headline. Two call sites.
 *  - system mono  — tickers, dates and inline raw values only. Every figure
 *                   also carries `font-variant-numeric: tabular-nums` via
 *                   `.num` / `.figure`, which is what protects the fallback.
 *
 * No component names a font. Families are swappable from this file plus the
 * three `--font-*` lines in globals.css.
 */
const display = Source_Serif_4({
  weight: ["400", "600", "700"],
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--font-source-serif",
  display: "swap",
});

const sans = Public_Sans({
  weight: ["300", "400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-public-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "rulial-markets — the ensemble of reachable futures",
  description:
    "Conditional event descriptions in, calibrated ensembles of forward return paths out. Scored by CRPS against a null, not by whether we called the crash.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable}`}>
      <body>
        <div id="shell">{children}</div>
      </body>
    </html>
  );
}
