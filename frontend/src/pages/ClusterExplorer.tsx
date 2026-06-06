import { useMemo, useState } from "react";
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip,
} from "recharts";
import { Filter, ZoomIn } from "lucide-react";
import { useData } from "../context";
import { Card, Section, PageHeader, Trend, Chip } from "../components/ui";
import { C, colorFor, fmt } from "../lib";

const tip = { background: "#111a2e", border: "1px solid #1f2c44", borderRadius: 10, color: "#F1F5FB", fontSize: 12 };
const btn = "flex items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2 text-sm text-muted hover:text-ink hover:border-accent/40 transition";

export default function ClusterExplorer() {
  const { data } = useData()!;
  const ordered = data!.clusters;
  const [sel, setSel] = useState<number>(ordered[0].id);

  const groups = useMemo(() => {
    const top = new Set(ordered.slice(0, 20).map((c) => c.id));
    const byId: Record<string, { x: number; y: number }[]> = {};
    for (const p of data!.scatter) {
      const key = top.has(p.c) ? String(p.c) : "autres";
      (byId[key] ||= []).push({ x: p.x, y: p.y });
    }
    return byId;
  }, [data]);

  const cluster = ordered.find((c) => c.id === sel)!;

  return (
    <div>
      <PageHeader title="Cluster Explorer"
        subtitle={`Projection UMAP de ${fmt(data!.meta.n_reports)} rapports d'incidents`}
        right={
          <div className="flex gap-2">
            <button className={btn}><ZoomIn size={16} /> Zoom</button>
            <button className={btn}><Filter size={16} /> Filter</button>
          </div>
        } />

      <Card>
        <ResponsiveContainer width="100%" height={460}>
          <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
            <XAxis type="number" dataKey="x" hide />
            <YAxis type="number" dataKey="y" hide />
            <ZAxis range={[16, 16]} />
            <Tooltip contentStyle={tip} cursor={{ strokeDasharray: "3 3" }} />
            {Object.entries(groups).map(([key, pts]) => (
              <Scatter key={key} data={pts}
                fill={key === "autres" ? "#33415570" : colorFor(Number(key))}
                fillOpacity={key === String(sel) ? 1 : 0.6} />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </Card>

      <Section>Thèmes principaux</Section>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {ordered.slice(0, 12).map((c) => (
          <button key={c.id} onClick={() => setSel(c.id)}
            className={"flex items-center justify-between rounded-xl border bg-surface px-4 py-3 text-left transition " +
              (c.id === sel ? "border-accent/60 shadow-glow" : "border-line hover:border-accent/30")}>
            <span className="flex items-center gap-2.5 truncate">
              <span className="h-3 w-3 shrink-0 rounded-full" style={{ background: colorFor(c.id) }} />
              <span className="truncate text-sm font-semibold">{c.name}</span>
            </span>
            <span className="ml-2 shrink-0 text-sm text-muted">({fmt(c.size)})</span>
          </button>
        ))}
      </div>

      <Section>Détail du thème</Section>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card>
          <div className="mb-1 flex items-center gap-2">
            <span className="h-3 w-3 rounded-full" style={{ background: colorFor(sel) }} />
            <span className="font-bold">{cluster.name}</span>
            <span className="chip ml-1">{cluster.category}</span>
          </div>
          <p className="mb-3 text-sm text-muted">{cluster.desc}</p>
          <div className="flex flex-wrap">
            {cluster.terms.map((t, i) => (
              <span key={t} className="mr-2 mb-2 rounded-full border border-accent/30 bg-accent/10 px-3 py-1 font-semibold text-accent"
                style={{ fontSize: `${1.1 - i * 0.045}rem` }}>{t}</span>
            ))}
          </div>
        </Card>
        <Card>
          <div className="text-sm font-semibold">Synthèse métier</div>
          <p className="mt-1 text-sm text-muted">{cluster.synthese}</p>
          <div className="mt-3 flex items-center gap-3">
            <Chip>{fmt(cluster.size)} rapports · {cluster.part}%</Chip><Trend t={cluster.trend} />
          </div>
        </Card>
      </div>

      <Section>Narratives représentatives</Section>
      <div className="grid grid-cols-1 gap-3">
        {cluster.reps.map((r, i) => (
          <Card key={i} className="py-4"><Chip>{i + 1}</Chip><span className="text-sm text-muted">{r}…</span></Card>
        ))}
      </div>
    </div>
  );
}
