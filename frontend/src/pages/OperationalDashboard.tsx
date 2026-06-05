import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from "recharts";
import { useData } from "../context";
import { Kpi, Card, Section, PageHeader } from "../components/ui";
import { C, colorFor, fmt } from "../lib";

const tip = { background: "#0F1B2E", border: "1px solid #22344c", borderRadius: 10, color: "#E6EDF6", fontSize: 12 };

export default function OperationalDashboard() {
  const { data } = useData()!;
  if (!data) return null;
  const anom = data.distributions.anomaly.map((d) => ({
    name: d.name.length > 30 ? d.name.slice(0, 30) + "…" : d.name, count: d.count,
  }));
  const phase = data.distributions.phase.map((d) => ({ name: d.name, count: d.count }));
  const clusters = [...data.clusters].slice(0, 25)
    .map((c) => ({ label: c.label.split(" · ")[0], nb: c.size, id: c.id }));

  return (
    <div>
      <PageHeader title="Operational Dashboard"
        subtitle="Vue d'ensemble opérationnelle des incidents" />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi label="Rapports" value={fmt(data.meta.n_reports)} icon="🛩️" accent />
        <Kpi label="Anomalies (top)" value={anom.length} icon="🏷️" />
        <Kpi label="Phases de vol" value={phase.length} icon="🧭" />
        <Kpi label="Thèmes" value={data.meta.n_themes} icon="🧩" />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div>
          <Section>Top anomalies déclarées</Section>
          <Card>
            <ResponsiveContainer width="100%" height={420}>
              <BarChart data={anom} layout="vertical" margin={{ left: 10, right: 20 }}>
                <XAxis type="number" stroke={C.muted} fontSize={11} />
                <YAxis type="category" dataKey="name" width={180} stroke={C.muted} fontSize={10} />
                <Tooltip contentStyle={tip} cursor={{ fill: "rgba(255,255,255,.04)" }} />
                <Bar dataKey="count" radius={[0, 6, 6, 0]} fill={C.accent} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
        <div>
          <Section>Phases de vol</Section>
          <Card>
            <ResponsiveContainer width="100%" height={420}>
              <BarChart data={phase} layout="vertical" margin={{ left: 10, right: 20 }}>
                <XAxis type="number" stroke={C.muted} fontSize={11} />
                <YAxis type="category" dataKey="name" width={120} stroke={C.muted} fontSize={11} />
                <Tooltip contentStyle={tip} cursor={{ fill: "rgba(255,255,255,.04)" }} />
                <Bar dataKey="count" radius={[0, 6, 6, 0]} fill={C.accent2} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      </div>

      <Section>Répartition par thème (top 25)</Section>
      <Card>
        <ResponsiveContainer width="100%" height={360}>
          <BarChart data={clusters} margin={{ left: 0, right: 10, bottom: 60 }}>
            <XAxis dataKey="label" angle={-40} textAnchor="end" interval={0}
              height={70} stroke={C.muted} fontSize={10} />
            <YAxis stroke={C.muted} fontSize={11} />
            <Tooltip contentStyle={tip} cursor={{ fill: "rgba(255,255,255,.04)" }} />
            <Bar dataKey="nb" radius={[6, 6, 0, 0]}>
              {clusters.map((d) => <Cell key={d.id} fill={colorFor(d.id)} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
