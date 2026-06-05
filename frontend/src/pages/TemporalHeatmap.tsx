import { useMemo } from "react";
import {
  ResponsiveContainer, ComposedChart, Area, Scatter, XAxis, YAxis, Tooltip,
  AreaChart,
} from "recharts";
import { useData } from "../context";
import { Card, Section, PageHeader } from "../components/ui";
import { C, colorFor } from "../lib";

const tip = { background: "#0F1B2E", border: "1px solid #22344c", borderRadius: 10, color: "#E6EDF6", fontSize: 12 };

export default function TemporalHeatmap() {
  const { data } = useData()!;
  const t = data!.temporal;

  const volume = t.periods.map((p, i) => ({
    period: p, nb: t.volume[i], peak: t.peaks[i] ? t.volume[i] : null,
  }));

  // Heatmap agrégée par année (lisibilité)
  const heat = useMemo(() => {
    const years = Array.from(new Set(t.heatmap.periods.map((p) => p.slice(0, 4))));
    const mat = t.heatmap.anomalies.map((_, ai) => {
      const row: Record<string, number> = {};
      t.heatmap.periods.forEach((p, pi) => {
        const y = p.slice(0, 4);
        row[y] = (row[y] || 0) + t.heatmap.matrix[ai][pi];
      });
      return years.map((y) => row[y] || 0);
    });
    const max = Math.max(1, ...mat.flat());
    return { years, mat, max };
  }, [data]);

  const tot = t.topics_over_time;
  const totData = tot.periods.map((p, i) => {
    const o: any = { period: p };
    tot.series.forEach((s) => (o[`c${s.id}`] = s.values[i]));
    return o;
  });

  return (
    <div>
      <PageHeader title="Temporal Heatmap"
        subtitle="Évolution des incidents dans le temps" />

      <Section>Volume mensuel d'incidents (pics en rouge)</Section>
      <Card>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={volume}>
            <defs>
              <linearGradient id="vol" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={C.accent} stopOpacity={0.5} />
                <stop offset="100%" stopColor={C.accent} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="period" stroke={C.muted} fontSize={10}
              tickFormatter={(v) => v.slice(0, 4)} minTickGap={40} />
            <YAxis stroke={C.muted} fontSize={11} />
            <Tooltip contentStyle={tip} />
            <Area type="monotone" dataKey="nb" stroke={C.accent} fill="url(#vol)" strokeWidth={2} />
            <Scatter dataKey="peak" fill={C.down} />
          </ComposedChart>
        </ResponsiveContainer>
      </Card>

      <Section>Heatmap : type d'anomalie × année</Section>
      <Card className="overflow-x-auto">
        <table className="border-separate" style={{ borderSpacing: 2 }}>
          <thead>
            <tr>
              <th></th>
              {heat.years.map((y) => (
                <th key={y} className="px-1 text-[9px] text-muted">{y.slice(2)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {t.heatmap.anomalies.map((a, ai) => (
              <tr key={a}>
                <td className="pr-2 text-right text-[10px] text-muted whitespace-nowrap"
                  style={{ maxWidth: 200 }}>{a}</td>
                {heat.mat[ai].map((v, yi) => (
                  <td key={yi} title={`${a} · ${heat.years[yi]} : ${v}`}
                    style={{
                      width: 16, height: 16, borderRadius: 3,
                      background: `rgba(34,211,238,${Math.min(1, v / heat.max) * 0.95 + (v ? 0.05 : 0)})`,
                    }} />
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Section>Part de chaque thème dans le temps (top 8)</Section>
      <Card>
        <ResponsiveContainer width="100%" height={360}>
          <AreaChart data={totData}>
            <XAxis dataKey="period" stroke={C.muted} fontSize={10}
              tickFormatter={(v) => v.slice(0, 4)} minTickGap={40} />
            <YAxis stroke={C.muted} fontSize={11} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
            <Tooltip contentStyle={tip} />
            {tot.series.map((s) => (
              <Area key={s.id} type="monotone" dataKey={`c${s.id}`} name={s.label}
                stackId="1" stroke={colorFor(s.id)} fill={colorFor(s.id)} fillOpacity={0.55} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
