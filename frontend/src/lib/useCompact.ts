"use client";

import { useEffect, useState } from "react";

/**
 * True on phone-width viewports.
 *
 * Every chart in this app draws into a fixed-unit viewBox with `w-full`, so on
 * a 375px screen a 1000-unit-wide chart is scaled to 0.285 and a 13-unit label
 * renders at under 4 real pixels. The fix is not CSS: it is a narrower viewBox
 * and larger type units on mobile, which is what this flag selects. See the
 * `compact` branches in FanChart, TerminalHistogram, PitHistogram,
 * BacktestPanel and RulialFan.
 *
 * Starts false so the static export prerenders the desktop geometry and the
 * server and client agree on the first paint; the effect corrects it during
 * hydration. Charts render after a click in every panel but one, so the
 * correction is not visible in practice.
 */
export function useCompact(query = "(max-width: 700px)"): boolean {
  const [compact, setCompact] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia(query);
    const sync = () => setCompact(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, [query]);

  return compact;
}
