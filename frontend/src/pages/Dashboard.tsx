import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from "recharts";
import { FileText, Network, Tags, AlertTriangle } from "lucide-react";
import { useData } from "../context";
import { Kpi, Card, Section, PageHeader } from "../components/ui";
import { C, colorFor, fmt } from "../lib";

const tip = { background: "#111a2e", border: "1px solid #1f2c44", borderRadius: 10, color: "#F1F5FB", fontSize: 12 };

export default function Dashboard() {
  const { data } = useData()!;
  if (!data) return null;
  const m = data.meta;
  const timeline = data.temporal.periods.map((p, i) => ({ p, nb: data.temporal.volume[i] }));
  const topClusters = data.causes.slice(0, 8).map((c: any) => ({
    label: c.name.length > 34 ? c.name.slice(0, 34) + "…" : c.name, nb: c.nb_rapports, id: c.cluster,
  }));
  const cats = data.categories.map((c, i) => ({ name: c.category, nb: c.size, i }));

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Aviation Safety Intelligence Overview"
        right={
          <div className="flex items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2 text-sm text-muted">
            <span className="h-2 w-2 animate-pulse rounded-full bg-up" />
            Période : {m.period ? `${m.period[0]} → ${m.period[1]}` : "—"}
          </div>
        } />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi label="Rapports analysés" value={fmt(m.n_reports)} icon={<FileText size={18} />} />
        <Kpi label="Clusters détectés" value={m.n_themes} icon={<Network size={18} />} tint="up" />
        <Kpi label="Thèmes LDA" value={data.lda.topics.length || "—"} icon={<Tags size={18} />} tint="accent" />
        <Kpi label="Signaux faibles" value={m.n_weak} icon={<AlertTriangle size={18} />} tint="down" />
      </div>

      <Section>Évolution temporelle des incidents</Section>
      <Card>
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={timeline}>
            <defs>
              <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={C.accent} stopOpacity={0.5} />
                <stop offset="100%" stopColor={C.accent} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="p" stroke={C.muted} fontSize={10}
              tickFormatter={(v) => v.slice(0, 4)} minTickGap={45} />
            <YAxis stroke={C.muted} fontSize={11} />
            <Tooltip contentStyle={tip} />
            <Area type="monotone" dataKey="nb" stroke={C.accent} strokeWidth={2} fill="url(#g)" name="rapports" />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      <Section>Répartition par catégorie d'incident</Section>
      <Card>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={cats} layout="vertical" margin={{ left: 10, right: 20 }}>
            <XAxis type="number" stroke={C.muted} fontSize={11} />
            <YAxis type="category" dataKey="name" width={180} stroke={C.muted} fontSize={11} />
            <Tooltip contentStyle={tip} cursor={{ fill: "rgba(255,255,255,.04)" }} />
            <Bar dataKey="nb" radius={[0, 6, 6, 0]}>
              {cats.map((d) => <Cell key={d.i} fill={colorFor(d.i)} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Section>Principaux thèmes d'incidents</Section>
      <Card>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={topClusters} layout="vertical" margin={{ left: 10, right: 20 }}>
            <XAxis type="number" stroke={C.muted} fontSize={11} />
            <YAxis type="category" dataKey="label" width={180} stroke={C.muted} fontSize={11} />
            <Tooltip contentStyle={tip} cursor={{ fill: "rgba(255,255,255,.04)" }} />
            <Bar dataKey="nb" radius={[0, 6, 6, 0]}>
              {topClusters.map((d) => <Cell key={d.id} fill={colorFor(d.id)} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
