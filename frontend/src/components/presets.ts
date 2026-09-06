/**
 * One-click stage presets. Four buttons so nobody has to type in front of a
 * room. Each as-of date sits inside the train window (<= 2019-12-31), so the
 * generator is never handed a date past the frozen boundary.
 */
export interface Preset {
  key: string;
  kind: string;
  ticker: string;
  as_of: string;
  text: string;
  tone: "down" | "up" | "shock" | "grind";
}

export const PRESETS: Preset[] = [
  {
    key: "swan",
    kind: "Black swan · bearish",
    ticker: "BA",
    as_of: "2019-03-08",
    tone: "down",
    text:
      "A second 737 MAX crashes days after the first investigation opens. Regulators in three " +
      "continents ground the fleet indefinitely, deliveries halt, and two flag carriers publicly " +
      "reopen their order books to Airbus.",
  },
  {
    key: "boom",
    kind: "Bullish surprise",
    ticker: "NVDA",
    as_of: "2019-11-14",
    tone: "up",
    text:
      "NVDA announces datacenter revenue up 200% year over year, says next-generation capacity is " +
      "sold out through the following fiscal year, and raises guidance well beyond consensus.",
  },
  {
    key: "geo",
    kind: "Geopolitical shock",
    ticker: "XOM",
    as_of: "2019-09-13",
    tone: "shock",
    text:
      "Strikes disable a major Gulf crude processing facility overnight. Iran is blamed, the Strait " +
      "of Hormuz is effectively closed to tanker traffic, and Brent gaps higher at the open with no " +
      "clear timeline for restored supply.",
  },
  {
    key: "cuts",
    kind: "Layoffs · guidance cut",
    ticker: "META",
    as_of: "2019-10-30",
    tone: "grind",
    text:
      "Meta announces 11,000 layoffs and an indefinite hiring freeze, cuts ad revenue guidance, and " +
      "concedes that reported engagement growth was overstated by a measurement error.",
  },
];
