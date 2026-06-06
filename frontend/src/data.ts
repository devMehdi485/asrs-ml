import { useEffect, useState } from "react";

export interface Cluster {
  id: number; name: string; category: string; desc: string;
  label: string; label_nl: string; size: number; part: number;
  terms: string[]; synthese: string; trend: string; reps: string[];
}
export interface Category { category: string; size: number; n_themes: number; part: number; }
export interface Cause {
  cluster: number; label: string; nb_rapports: number; part_: number;
  anomalie_dominante: string; phase_dominante: string; tendance: string;
  [k: string]: any;
}
export interface AsrsData {
  meta: {
    n_reports: number; n_themes: number; period: [string, string] | null;
    model: string; justification: string; embeddings: string; reduction: string;
    n_weak: number; n_up: number;
  };
  comparison: any[];
  distributions: { anomaly: { name: string; count: number }[]; phase: { name: string; count: number }[] };
  categories: Category[];
  causes: Cause[];
  clusters: Cluster[];
  scatter: { x: number; y: number; c: number; cat: number }[];
  temporal: {
    periods: string[]; volume: number[]; peaks: boolean[];
    heatmap: { anomalies: string[]; periods: string[]; matrix: number[][] };
    topics_over_time: { periods: string[]; series: { id: number; label: string; values: number[] }[] };
  };
  weak_signals: { score: number; cluster: number; anomaly: string; date: string; text: string }[];
  atyp_hist: { centers: number[]; counts: number[] };
  lda_vis_html: boolean;
  emergents: number[];
  lda: { coherence: number | null; topics: string[] };
  classification: { models: { name: string; f1_macro: number; f1_weighted: number }[]; report: string };
}

export function useAsrsData() {
  const [data, setData] = useState<AsrsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/asrs.json?t=${Date.now()}`, { cache: "no-store" })
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);
  return { data, error };
}
