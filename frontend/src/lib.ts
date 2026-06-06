// Palette catégorielle (clusters) — alignée sur la maquette AeroInsight
export const PALETTE = [
  "#3B82F6", "#22C55E", "#F59E0B", "#EF4444", "#A855F7", "#14B8A6",
  "#60A5FA", "#FB923C", "#34D399", "#F472B6", "#818CF8", "#2DD4BF",
  "#FBBF24", "#F87171", "#C084FC", "#4ADE80", "#38BDF8", "#FCD34D",
  "#A3E635", "#E879F9",
];

export const C = {
  accent: "#3B82F6",
  accent2: "#2563EB",
  up: "#22C55E",
  down: "#EF4444",
  warn: "#F59E0B",
  ink: "#F1F5FB",
  muted: "#8b9bb4",
  line: "#1f2c44",
  surface: "#111a2e",
};

export const colorFor = (id: number) =>
  PALETTE[((id % PALETTE.length) + PALETTE.length) % PALETTE.length];

export const trendClass = (t: string) =>
  t?.includes("hausse") ? "text-up" : t?.includes("baisse") ? "text-down" : "text-muted";

export const fmt = (n: number) => n.toLocaleString("fr-FR").replace(/,/g, " ");
