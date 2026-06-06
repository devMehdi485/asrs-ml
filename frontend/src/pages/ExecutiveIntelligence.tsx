import { Download } from "lucide-react";
import { useData } from "../context";
import { Card, Section, PageHeader } from "../components/ui";
import { fmt, trendClass } from "../lib";

export default function ExecutiveIntelligence() {
  const { data } = useData()!;
  if (!data) return null;
  const m = data.meta;
  const top = data.causes[0];
  const rising = data.clusters.filter((c) => c.trend.includes("hausse"));
  const f1 = data.classification.models?.[0];
  const period = m.period ? `${m.period[0]} – ${m.period[1]}` : "—";

  return (
    <div>
      <PageHeader title="Executive Intelligence Report"
        subtitle={`Analyse stratégique de sécurité · Période : ${period}`}
        right={
          <button onClick={() => window.print()}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-accent2 to-accent px-4 py-2.5 text-sm font-semibold text-white shadow-glow">
            <Download size={16} /> Exporter le rapport
          </button>
        } />

      <Card>
        <h2 className="text-xl font-bold">Synthèse exécutive</h2>
        <div className="mt-3 space-y-4 text-[0.95rem] leading-relaxed text-muted">
          <p>
            L'analyse de <b className="text-ink">{fmt(m.n_reports)}</b> rapports d'incidents NASA ASRS
            ({period}) met en évidence les tendances clés des risques de sécurité aérienne. Le pipeline
            NLP (embeddings sémantiques + {m.model}) a identifié <b className="text-ink">{m.n_themes}</b> thèmes
            d'incidents distincts.
          </p>
          <p>
            Le thème prédominant est <b className="text-ink">« {top?.label} »</b> ({top?.["part_%"]}% du corpus,
            anomalie dominante : {String(top?.anomalie_dominante).slice(0, 50)}).
            {rising.length > 0 && <> <b className="text-ink">{rising.length}</b> thèmes sont en croissance récente,
              au premier rang desquels <b className="text-ink">« {rising[0].label.split(" · ")[0]} »</b> ({rising[0].trend.replace(/[↑↓→]/g, "").trim()}).</>}
          </p>
          <p>
            Le système de détection de signaux faibles a relevé <b className="text-ink">{m.n_weak}</b> rapports
            atypiques nécessitant une investigation prioritaire.
            {f1 && <> La classification supervisée des types d'incidents atteint un
              <b className="text-ink"> F1 pondéré de {f1.f1_weighted}</b> ({f1.name}).</>}
          </p>
        </div>
      </Card>

      <Section>Axes stratégiques prioritaires</Section>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {(rising.length ? rising : data.clusters).slice(0, 4).map((c, i) => (
          <Card key={c.id} className="py-4">
            <div className="flex items-center gap-3">
              <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-accent/15 font-bold text-accent">{i + 1}</div>
              <div className="font-semibold">{c.label.split(" · ").slice(0, 2).join(" · ")}</div>
            </div>
            <div className={"mt-2 text-sm font-semibold " + trendClass(c.trend)}>{c.trend}</div>
            <div className="mt-1 text-sm text-muted">{c.synthese.slice(0, 150)}…</div>
          </Card>
        ))}
      </div>

      <Section>Tableau de synthèse — causes récurrentes</Section>
      <Card className="overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-left text-muted">
              {["#", "Thème", "Rapports", "% corpus", "Anomalie dominante", "Tendance"].map((h) => (
                <th key={h} className="px-4 py-3 font-semibold">{h}</th>))}
            </tr>
          </thead>
          <tbody>
            {data.causes.slice(0, 15).map((c) => (
              <tr key={c.cluster} className="border-b border-line/50">
                <td className="px-4 py-2 text-muted">{c.cluster}</td>
                <td className="px-4 py-2 font-medium">{c.label}</td>
                <td className="px-4 py-2">{fmt(c.nb_rapports)}</td>
                <td className="px-4 py-2">{c["part_%"]}%</td>
                <td className="px-4 py-2 text-muted">{String(c.anomalie_dominante).slice(0, 40)}</td>
                <td className={"px-4 py-2 " + trendClass(c.tendance)}>{c.tendance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
