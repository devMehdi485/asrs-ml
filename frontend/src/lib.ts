// Palette catégorielle (clusters) lisible sur fond sombre
export const PALETTE = [
  "#22D3EE", "#3B82F6", "#A78BFA", "#F472B6", "#34D399", "#FBBF24",
  "#FB7185", "#60A5FA", "#2DD4BF", "#F59E0B", "#C084FC", "#4ADE80",
  "#38BDF8", "#FCA5A5", "#818CF8", "#5EEAD4", "#FDBA74", "#E879F9",
  "#93C5FD", "#86EFAC",
];

export const C = {
  accent: "#22D3EE",
  accent2: "#3B82F6",
  up: "#34D399",
  down: "#FB7185",
  warn: "#FBBF24",
  ink: "#E6EDF6",
  muted: "#8aa0b8",
  line: "#22344c",
  surface: "#0F1B2E",
};

export const colorFor = (id: number) =>
  PALETTE[((id % PALETTE.length) + PALETTE.length) % PALETTE.length];

export const trendClass = (t: string) =>
  t?.includes("hausse") ? "text-up" : t?.includes("baisse") ? "text-down" : "text-muted";

export const fmt = (n: number) => n.toLocaleString("fr-FR").replace(/,/g, " ");
