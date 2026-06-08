import { useMemo } from "react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip,
} from "recharts";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";
import { useData } from "../context";
import { Card, Section, PageHeader, Intro, Explain } from "../components/ui";
import { C, colorFor } from "../lib";

const tip = { background: "#111a2e", border: "1px solid #1f2c44", borderRadius: 10, color: "#F1F5FB", fontSize: 12 };

const HEAT = ["#2b4b7e", "#3B82F6", "#F59E0B", "#EA580C", "#EF4444"];
const LEGEND = [["Faible", HEAT[0]], ["Modéré", HEAT[1]], ["Élevé", HEAT[2]], ["Très élevé", HEAT[3]], ["Critique", HEAT[4]]];
const cellColor = (v: number, max: number) => {
  if (!v) return "transparent";
  const r = v / max;
  return r < 0.2 ? HEAT[0] : r < 0.45 ? HEAT[1] : r < 0.7 ? HEAT[2] : r < 0.9 ? HEAT[3] : HEAT[4];
};

function Callout({ icon, title, text, tone }: { icon: any; title: string; text: string; tone: string }) {
  const T: any = { warn: ["bg-warn/8 border-warn/40", "text-warn"], down: ["bg-down/8 border-down/40", "text-down"], up: ["bg-up/8 border-up/40", "text-up"] };
  const Icon = icon;
  return (
    <div className={"flex items-start gap-3 rounded-2xl border p-4 " + T[tone][0]}>
      <Icon size={20} className={T[tone][1] + " mt-0.5 shrink-0"} />
      <div><div className="font-bold">{title}</div><div className="mt-0.5 text-sm text-muted">{text}</div></div>
    </div>
  );
}

export default function TemporalMap() {
  const { data } = useData()!;
  const t = data!.temporal;

  const peakIdx = t.volume.indexOf(Math.max(...t.volume));
  const parsePct = (s: string) => { const m = s.match(/([+-][\d.]+)%/); return m ? parseFloat(m[1]) : 0; };
  const rising = [...data!.clusters].filter((c) => c.trend.includes("hausse"))
    .sort((a, b) => parsePct(b.trend) - parsePct(a.trend))[0];
  const falling = [...data!.clusters].filter((c) => c.trend.includes("baisse"))
    .sort((a, b) => parsePct(a.trend) - parsePct(b.trend))[0];

  const heat = useMemo(() => {
    const years = Array.from(new Set(t.heatmap.periods.map((p) => p.slice(0, 4))));
    const mat = t.heatmap.anomalies.map((_, ai) => {
      const row: Record<string, number> = {};
      t.heatmap.periods.forEach((p, pi) => { const y = p.slice(0, 4); row[y] = (row[y] || 0) + t.heatmap.matrix[ai][pi]; });
      return years.map((y) => row[y] || 0);
    });
    return { years, mat, max: Math.max(1, ...mat.flat()) };
  }, [data]);

  const totData = t.topics_over_time.periods.map((p, i) => {
    const o: any = { p }; t.topics_over_time.series.forEach((s) => (o[`c${s.id}`] = s.values[i])); return o;
  });

  return (
    <div>
      <PageHeader title="Temporal Map" subtitle="Évolution des incidents dans le temps par catégorie" />

      <Intro>
        Cette page répond à : <b className="text-ink">les incidents évoluent-ils dans le temps ?</b>
        Les encadrés ci-dessous résument les faits marquants (pic, thème en hausse, en baisse) ;
        les graphiques détaillent ensuite quand et quels types d'incidents surviennent.
      </Intro>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <Callout icon={Activity} tone="warn" title="Pic d'activité"
          text={`${t.periods[peakIdx]} : pic avec ${t.volume[peakIdx]} rapports`} />
        {rising && <Callout icon={TrendingUp} tone="down" title="Tendance émergente"
          text={`${rising.label.split(" · ")[0]} ${rising.trend.replace(/[↑↓→]/g, "").trim()}`} />}
        {falling && <Callout icon={TrendingDown} tone="up" title="Évolution positive"
          text={`${falling.label.split(" · ")[0]} ${falling.trend.replace(/[↑↓→]/g, "").trim()}`} />}
      </div>

      <Section>Volume mensuel d'incidents</Section>
      <Card>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={t.periods.map((p, i) => ({ p, nb: t.volume[i] }))}>
            <defs><linearGradient id="v" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={C.accent} stopOpacity={0.5} /><stop offset="100%" stopColor={C.accent} stopOpacity={0} />
            </linearGradient></defs>
            <XAxis dataKey="p" stroke={C.muted} fontSize={10} tickFormatter={(v) => v.slice(0, 4)} minTickGap={45} />
            <YAxis stroke={C.muted} fontSize={11} />
            <Tooltip contentStyle={tip} />
            <Area type="monotone" dataKey="nb" stroke={C.accent} strokeWidth={2} fill="url(#v)" />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      <Section>Heatmap : type d'anomalie × année</Section>
      <Card className="overflow-x-auto">
        <div className="mb-3 flex flex-wrap items-center gap-3 text-xs text-muted">
          {LEGEND.map(([l, c]) => (
            <span key={l} className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded" style={{ background: c }} />{l}</span>
          ))}
        </div>
        <table className="border-separate" style={{ borderSpacing: 2 }}>
          <thead><tr><th></th>{heat.years.map((y) => <th key={y} className="px-1 text-[9px] text-muted">{y.slice(2)}</th>)}</tr></thead>
          <tbody>
            {t.heatmap.anomalies.map((a, ai) => {
              const rowMax = Math.max(1, ...heat.mat[ai]);  // normalisation PAR LIGNE
              return (
                <tr key={a}>
                  <td className="truncate pr-2 text-right text-[10px] text-muted"
                    title={a} style={{ maxWidth: 180, width: 180 }}>{a}</td>
                  {heat.mat[ai].map((v, yi) => (
                    <td key={yi} title={`${a} · ${heat.years[yi]} : ${v}`}
                      style={{ width: 16, height: 16, borderRadius: 3, background: cellColor(v, rowMax) }} />
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
        <Explain>chaque ligne = un type d'anomalie, chaque colonne = une année. La couleur est
          relative à <b>chaque type</b> : une case <b>vive (rouge)</b> marque les années de pic
          pour ce type. Une ligne qui se réchauffe vers la droite = un type d'incident en
          progression.</Explain>
      </Card>

      <Section>Part de chaque thème dans le temps (top 8)</Section>
      <Card>
        <ResponsiveContainer width="100%" height={340}>
          <AreaChart data={totData}>
            <XAxis dataKey="p" stroke={C.muted} fontSize={10} tickFormatter={(v) => v.slice(0, 4)} minTickGap={45} />
            <YAxis stroke={C.muted} fontSize={11} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
            <Tooltip contentStyle={tip} />
            {t.topics_over_time.series.map((s) => (
              <Area key={s.id} type="monotone" dataKey={`c${s.id}`} name={s.label} stackId="1"
                stroke={colorFor(s.id)} fill={colorFor(s.id)} fillOpacity={0.55} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
        <Explain>chaque bande colorée = la part d'un thème parmi les 8 principaux, au fil
          du temps. Une bande qui s'épaissit = un thème qui prend de l'importance relative.</Explain>
      </Card>
    </div>
  );
}
