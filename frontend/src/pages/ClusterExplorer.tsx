import { useMemo, useState } from "react";
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip,
} from "recharts";
import { useData } from "../context";
import { Card, Section, PageHeader, Trend, Chip } from "../components/ui";
import { C, colorFor, fmt } from "../lib";

const tip = { background: "#0F1B2E", border: "1px solid #22344c", borderRadius: 10, color: "#E6EDF6", fontSize: 12 };

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
        subtitle="Exploration interactive des thèmes d'incidents (projection sémantique 2D)" />

      <Card>
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
            <XAxis type="number" dataKey="x" hide />
            <YAxis type="number" dataKey="y" hide />
            <ZAxis range={[14, 14]} />
            <Tooltip contentStyle={tip} cursor={{ strokeDasharray: "3 3" }} />
            {Object.entries(groups).map(([key, pts]) => (
              <Scatter key={key} name={key === "autres" ? "autres" : `#${key}`}
                data={pts} fill={key === "autres" ? "#33415580" : colorFor(Number(key))}
                fillOpacity={0.65} />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </Card>

      <Section>Inspecter un thème</Section>
      <select
        value={sel}
        onChange={(e) => setSel(Number(e.target.value))}
        className="mb-4 w-full max-w-xl rounded-xl border border-line bg-surface2 px-3 py-2.5 text-sm text-ink"
      >
        {ordered.map((c) => (
          <option key={c.id} value={c.id}>
            #{c.id} · {c.label} ({fmt(c.size)} rapports)
          </option>
        ))}
      </select>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card>
          <div className="mb-2 text-sm font-semibold text-muted">Mots-clés (c-TF-IDF)</div>
          <div className="flex flex-wrap">
            {cluster.terms.map((t, i) => (
              <span key={t}
                className="mr-2 mb-2 rounded-full border border-accent/30 bg-accent/10 px-3 py-1 font-semibold text-accent"
                style={{ fontSize: `${1.15 - i * 0.05}rem` }}>
                {t}
              </span>
            ))}
          </div>
        </Card>
        <Card>
          <div className="text-sm font-semibold">Synthèse métier</div>
          <p className="mt-1 text-sm text-muted">{cluster.synthese}</p>
          <div className="mt-3 flex items-center gap-2">
            <Chip>#{cluster.id}</Chip><span className="text-sm">{fmt(cluster.size)} rapports · {cluster.part}%</span>
          </div>
          <div className="mt-2"><Trend t={cluster.trend} /></div>
        </Card>
      </div>

      <Section>Narratives représentatives</Section>
      <div className="grid grid-cols-1 gap-3">
        {cluster.reps.map((r, i) => (
          <Card key={i} className="py-4"><Chip>{i + 1}</Chip>
            <span className="text-sm text-muted">{r}…</span></Card>
        ))}
      </div>
    </div>
  );
}
