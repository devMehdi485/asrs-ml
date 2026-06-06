import { useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, Cell,
} from "recharts";
import { ShieldAlert, Sparkles, Gauge } from "lucide-react";
import { useData } from "../context";
import { Kpi, Card, Section, PageHeader, Chip, Intro, Explain } from "../components/ui";
import { C, colorFor } from "../lib";

const tip = { background: "#111a2e", border: "1px solid #1f2c44", borderRadius: 10, color: "#F1F5FB", fontSize: 12 };

export default function WeakSignals() {
  const { data } = useData()!;
  const [seuil, setSeuil] = useState(0.6);
  const hist = data!.atyp_hist.centers.map((c, i) => ({ c, n: data!.atyp_hist.counts[i] }));
  const rows = data!.weak_signals.filter((w) => w.score >= seuil);
  const labelOf = (id: number) => data!.clusters.find((c) => c.id === id)?.name ?? `#${id}`;

  const critical = data!.weak_signals.filter((w) => w.score >= 0.85).length;
  const avgConf = rows.length ? Math.round(100 * rows.reduce((a, w) => a + w.score, 0) / rows.length) : 0;
  const badge = (s: number) => s >= 0.85 ? ["Critique", "bg-down/15 text-down border-down/40"]
    : s >= 0.72 ? ["Événement rare", "bg-warn/15 text-warn border-warn/40"]
    : ["Condition atypique", "bg-accent/15 text-accent border-accent/40"];

  return (
    <div>
      <PageHeader title="Weak Signals Detection"
        subtitle={`${rows.length} incidents atypiques nécessitant attention`} />

      <Intro>
        Un <b className="text-ink">signal faible</b> = un rapport qui <b className="text-ink">ne
        ressemble à aucun autre</b> (vocabulaire ou situation rares). Ces cas isolés peuvent
        être les <b className="text-ink">précurseurs</b> de problèmes nouveaux (ex. drones, GPS
        brouillé). L'IA leur attribue un <b className="text-ink">score d'atypicité</b> ; le
        curseur ci-dessous fixe le seuil au-delà duquel on les examine.
      </Intro>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Kpi label="Risque critique" value={critical} icon={<ShieldAlert size={18} />} tint="down" />
        <Kpi label="Motifs émergents" value={data!.emergents.length} icon={<Sparkles size={18} />} tint="warn" />
        <Kpi label="Confiance moyenne" value={`${avgConf}%`} icon={<Gauge size={18} />} tint="accent" />
      </div>

      <div className="mt-5 max-w-md">
        <label className="text-sm text-muted">Seuil d'atypicité : <b className="text-ink">{seuil.toFixed(2)}</b></label>
        <input type="range" min={0} max={1} step={0.05} value={seuil}
          onChange={(e) => setSeuil(Number(e.target.value))}
          className="mt-2 w-full accent-[#3B82F6]" />
      </div>

      <Section>Distribution des scores d'atypicité</Section>
      <Card>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={hist}>
            <XAxis dataKey="c" stroke={C.muted} fontSize={11} tickFormatter={(v) => v.toFixed(1)} minTickGap={20} />
            <YAxis stroke={C.muted} fontSize={11} />
            <Tooltip contentStyle={tip} cursor={{ fill: "rgba(255,255,255,.04)" }} />
            <ReferenceLine x={hist.reduce((a, b) => Math.abs(b.c - seuil) < Math.abs(a.c - seuil) ? b : a).c}
              stroke={C.down} strokeDasharray="4 4" />
            <Bar dataKey="n" radius={[4, 4, 0, 0]}>
              {hist.map((d, i) => <Cell key={i} fill={d.c >= seuil ? C.down : C.accent} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <Explain>la plupart des rapports sont « normaux » (gros pic à gauche). Les rares
          rapports à <b>droite</b> du trait rouge sont les plus atypiques — ceux à examiner.</Explain>
      </Card>

      <Section>Rapports les plus atypiques ({rows.length})</Section>
      <div className="flex flex-col gap-3">
        {rows.slice(0, 40).map((w, i) => {
          const [bl, bc] = badge(w.score);
          return (
            <Card key={i} className="py-4">
              <div className="flex items-start gap-4">
                <div className="shrink-0 text-3xl font-extrabold" style={{ color: colorFor(w.cluster) }}>
                  {Math.round(w.score * 100)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold">WS-{String(i + 1).padStart(3, "0")}</span>
                    <span className={"rounded-md border px-2 py-0.5 text-xs font-semibold " + bc}>{bl}</span>
                    <span className="ml-auto text-xs text-muted">Confiance {Math.round(w.score * 100)}%</span>
                  </div>
                  <div className="mt-0.5 text-xs text-muted">{w.date} · #{w.cluster} {labelOf(w.cluster).split(" · ")[0]} · {w.anomaly}</div>
                  <p className="mt-2 text-sm text-muted">{w.text}…</p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
