import { ChevronRight } from "lucide-react";
import { useData } from "../context";
import { Kpi, Card, Section, PageHeader, Chip } from "../components/ui";
import { fmt, trendClass } from "../lib";

export default function ThematicAnalysis() {
  const { data } = useData()!;
  if (!data) return null;
  const clf = data.classification;
  const maxSize = Math.max(...data.clusters.map((c) => c.size));
  const themes = data.clusters.slice(0, 12);

  return (
    <div>
      <PageHeader title="Thematic Analysis"
        subtitle={`${data.meta.n_themes} thèmes dominants identifiés sur l'ensemble des rapports`} />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi label="Thèmes" value={data.meta.n_themes} icon="🗂️" />
        <Kpi label="Modèle" value={data.meta.model} icon="🧠" tint="accent" />
        <Kpi label="Cohérence LDA c_v" value={data.lda.coherence ?? "—"} icon="📐" tint="up" />
        <Kpi label="Plus gros thème" value={`${data.causes[0]?.["part_%"]}%`} icon="🥇" tint="warn" />
      </div>

      <Section>Thèmes dominants</Section>
      <div className="flex flex-col gap-3">
        {themes.map((c) => {
          const imp = Math.round((c.size / maxSize) * 100);
          return (
            <Card key={c.id} className="py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-baseline gap-3">
                  <span className="text-lg font-bold">{c.label.split(" · ").slice(0, 2).join(" · ")}</span>
                  <span className="text-sm text-muted">{fmt(c.size)} rapports</span>
                </div>
                <ChevronRight size={18} className="text-muted" />
              </div>
              <div className="mt-3 flex items-center gap-3">
                <span className="text-[0.7rem] font-semibold uppercase tracking-wider text-muted">Importance</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-line">
                  <div className="h-full rounded-full bg-gradient-to-r from-accent2 to-accent" style={{ width: `${imp}%` }} />
                </div>
                <span className="w-10 text-right text-sm font-bold">{imp}%</span>
                <span className={"w-44 text-right text-xs font-semibold " + trendClass(c.trend)}>{c.trend}</span>
              </div>
              <div className="mt-3 flex flex-wrap">
                {c.terms.slice(0, 6).map((t) => <Chip key={t}>{t}</Chip>)}
              </div>
            </Card>
          );
        })}
      </div>

      {clf?.models?.length > 0 && (
        <>
          <Section>Classification supervisée du type d'incident</Section>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {clf.models.map((mdl) => (
              <Card key={mdl.name}>
                <div className="font-semibold">{mdl.name}</div>
                <div className="mt-2 flex gap-8">
                  <div><div className="text-2xl font-extrabold text-accent">{mdl.f1_macro}</div>
                    <div className="text-xs text-muted">F1 macro</div></div>
                  <div><div className="text-2xl font-extrabold text-accent">{mdl.f1_weighted}</div>
                    <div className="text-xs text-muted">F1 pondéré</div></div>
                </div>
              </Card>
            ))}
          </div>
          {clf.report && (
            <Card className="mt-3 overflow-x-auto">
              <pre className="text-[11px] leading-5 text-muted">{clf.report}</pre>
            </Card>
          )}
        </>
      )}

      {data.lda_vis_html && (
        <>
          <Section>Visualisation interactive des thèmes LDA (pyLDAvis)</Section>
          <Card className="overflow-hidden p-0">
            <iframe src={`${import.meta.env.BASE_URL}data/lda_vis.html`} title="pyLDAvis"
              className="w-full" style={{ height: 820, border: 0, background: "#fff" }} />
          </Card>
        </>
      )}

      <Section>Toutes les causes récurrentes</Section>
      <Card className="overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-left text-muted">
              {["#", "Thème", "Rapports", "% corpus", "Anomalie dominante", "Phase", "Tendance"].map((h) => (
                <th key={h} className="px-4 py-3 font-semibold">{h}</th>))}
            </tr>
          </thead>
          <tbody>
            {data.causes.map((c) => (
              <tr key={c.cluster} className="border-b border-line/50 hover:bg-white/[.03]">
                <td className="px-4 py-2 text-muted">{c.cluster}</td>
                <td className="px-4 py-2 font-medium">{c.label}</td>
                <td className="px-4 py-2">{fmt(c.nb_rapports)}</td>
                <td className="px-4 py-2">{c["part_%"]}%</td>
                <td className="px-4 py-2 text-muted">{String(c.anomalie_dominante).slice(0, 38)}</td>
                <td className="px-4 py-2 text-muted">{c.phase_dominante}</td>
                <td className={"px-4 py-2 " + trendClass(c.tendance)}>{c.tendance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
