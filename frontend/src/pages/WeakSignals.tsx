import { useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, Cell,
} from "recharts";
import { useData } from "../context";
import { Kpi, Card, Section, PageHeader, Chip } from "../components/ui";
import { C } from "../lib";

const tip = { background: "#0F1B2E", border: "1px solid #22344c", borderRadius: 10, color: "#E6EDF6", fontSize: 12 };

export default function WeakSignals() {
  const { data } = useData()!;
  const [seuil, setSeuil] = useState(0.6);
  const hist = data!.atyp_hist.centers.map((c, i) => ({ c, n: data!.atyp_hist.counts[i] }));
  const rows = data!.weak_signals.filter((w) => w.score >= seuil);
  const labelOf = (id: number) =>
    data!.clusters.find((c) => c.id === id)?.label ?? `#${id}`;

  return (
    <div>
      <PageHeader title="Weak Signals"
        subtitle="Rapports atypiques — précurseurs potentiels d'accidents" />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        <Kpi label="Au-dessus du seuil" value={rows.length} icon="⚠️" accent />
        <Kpi label="Seuil d'atypicité" value={seuil.toFixed(2)} icon="🎚️" />
        <Kpi label="Thèmes rares émergents" value={data!.emergents.length} icon="🌱" />
      </div>

      <div className="mt-5">
        <label className="text-sm text-muted">Seuil de score d'atypicité : <b className="text-ink">{seuil.toFixed(2)}</b></label>
        <input type="range" min={0} max={1} step={0.05} value={seuil}
          onChange={(e) => setSeuil(Number(e.target.value))}
          className="mt-2 w-full max-w-md accent-[#22D3EE]" />
      </div>

      {data!.emergents.length > 0 && (
        <div className="mt-3">
          {data!.emergents.map((c) => <Chip key={c}>#{c} {labelOf(c)}</Chip>)}
        </div>
      )}

      <Section>Distribution des scores d'atypicité</Section>
      <Card>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={hist}>
            <XAxis dataKey="c" stroke={C.muted} fontSize={11}
              tickFormatter={(v) => v.toFixed(1)} minTickGap={20} />
            <YAxis stroke={C.muted} fontSize={11} />
            <Tooltip contentStyle={tip} cursor={{ fill: "rgba(255,255,255,.04)" }} />
            <ReferenceLine x={hist.reduce((a, b) => Math.abs(b.c - seuil) < Math.abs(a.c - seuil) ? b : a).c}
              stroke={C.down} strokeDasharray="4 4" />
            <Bar dataKey="n" radius={[4, 4, 0, 0]}>
              {hist.map((d, i) => <Cell key={i} fill={d.c >= seuil ? C.down : C.accent2} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Section>Rapports les plus atypiques ({rows.length})</Section>
      <div className="grid grid-cols-1 gap-3">
        {rows.slice(0, 40).map((w, i) => (
          <Card key={i} className="py-4">
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <Chip>atypicité {w.score.toFixed(2)}</Chip>
              <span className="text-xs text-muted">#{w.cluster} · {labelOf(w.cluster)}</span>
              {w.date && <span className="text-xs text-muted">· {w.date}</span>}
              <span className="text-xs text-muted">· {w.anomaly}</span>
            </div>
            <p className="text-sm text-muted">{w.text}…</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
