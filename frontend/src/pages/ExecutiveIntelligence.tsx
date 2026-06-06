import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from "recharts";
import { useData } from "../context";
import { Kpi, Card, Section, PageHeader, Trend, Chip } from "../components/ui";
import { C, colorFor, fmt, trendClass } from "../lib";

export default function ExecutiveIntelligence() {
  const { data } = useData()!;
  if (!data) return null;
  const m = data.meta;
  const topCauses = data.causes.slice(0, 6).map((c) => ({
    label: c.label.length > 34 ? c.label.slice(0, 34) + "…" : c.label,
    nb: c.nb_rapports, cluster: c.cluster,
  }));
  const up = data.clusters.filter((c) => c.trend.includes("hausse")).slice(0, 4);
  const down = data.clusters.filter((c) => c.trend.includes("baisse")).slice(0, 2);
  const topWeak = [...data.weak_signals].slice(0, 3);

  return (
    <div>
      <PageHeader title="Executive Intelligence"
        subtitle="Synthèse stratégique auto-générée des risques de sécurité aérienne"
        right={
          <div className="flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-xs text-muted">
            <span className="h-2 w-2 animate-pulse rounded-full bg-up" />
            {m.model} · {m.period ? `${m.period[0].slice(0, 4)}–${m.period[1].slice(0, 4)}` : ""}
          </div>
        } />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <Kpi label="Rapports analysés" value={fmt(m.n_reports)} icon="🛩️" accent />
        <Kpi label="Thèmes d'incidents" value={m.n_themes} icon="🧩" accent />
        <Kpi label="Période" value={m.period ? `${m.period[0].slice(0, 4)}–${m.period[1].slice(0, 4)}` : "—"} icon="🗓️" />
        <Kpi label="Signaux faibles" value={m.n_weak} icon="⚠️" />
        <Kpi label="Thèmes en hausse" value={m.n_up} icon="📈" />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <Section>Clusters les plus importants</Section>
          <Card>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topCauses} layout="vertical" margin={{ left: 10, right: 20 }}>
                <XAxis type="number" stroke={C.muted} fontSize={11} />
                <YAxis type="category" dataKey="label" width={170} stroke={C.muted} fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,.04)" }} />
                <Bar dataKey="nb" radius={[0, 6, 6, 0]}>
                  {topCauses.map((d) => <Cell key={d.cluster} fill={colorFor(d.cluster)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Section>Tendances marquantes</Section>
          {[...up, ...down].map((c) => (
            <Card key={c.id} className="mb-3 py-3">
              <div className="flex items-center justify-between">
                <div><Chip>#{c.id}</Chip><span className="font-semibold">{c.label}</span></div>
              </div>
              <div className="mt-1"><Trend t={c.trend} /></div>
            </Card>
          ))}
        </div>
      </div>

      <Section>Signaux faibles les plus notables</Section>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {topWeak.map((w, i) => (
          <Card key={i} className="py-4">
            <Chip>atypicité {w.score.toFixed(2)}</Chip>
            <p className="mt-1 text-sm text-muted">{w.text.slice(0, 180)}…</p>
          </Card>
        ))}
      </div>

      <Section>Principales causes récurrentes</Section>
      <Card className="overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-left text-muted">
              {["#", "Thème", "Rapports", "% corpus", "Anomalie dominante", "Tendance"].map((h) => (
                <th key={h} className="px-4 py-3 font-semibold">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.causes.slice(0, 15).map((c) => (
              <tr key={c.cluster} className="border-b border-line/50 hover:bg-white/[.03]">
                <td className="px-4 py-2.5 text-muted">{c.cluster}</td>
                <td className="px-4 py-2.5 font-medium">{c.label}</td>
                <td className="px-4 py-2.5">{fmt(c.nb_rapports)}</td>
                <td className="px-4 py-2.5">{c["part_%"]}%</td>
                <td className="px-4 py-2.5 text-muted">{String(c.anomalie_dominante).slice(0, 40)}</td>
                <td className={"px-4 py-2.5 " + trendClass(c.tendance)}>{c.tendance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

const tooltipStyle = {
  background: "#0F1B2E", border: "1px solid #22344c", borderRadius: 10,
  color: "#E6EDF6", fontSize: 12,
};
