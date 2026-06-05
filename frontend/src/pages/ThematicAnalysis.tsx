import { useData } from "../context";
import { Kpi, Card, Section, PageHeader, Chip } from "../components/ui";
import { fmt, trendClass } from "../lib";

export default function ThematicAnalysis() {
  const { data } = useData()!;
  if (!data) return null;
  const clf = data.classification;

  return (
    <div>
      <PageHeader title="Thematic Analysis"
        subtitle="Cartographie thématique, modélisation LDA et causes récurrentes" />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi label="Thèmes" value={data.meta.n_themes} icon="🗂️" accent />
        <Kpi label="Modèle" value={data.meta.model} icon="🧠" />
        <Kpi label="Cohérence LDA c_v" value={data.lda.coherence ?? "—"} icon="📐" accent />
        <Kpi label="Plus gros thème" value={`${data.causes[0]?.["part_%"]}%`} icon="🥇" />
      </div>

      <Card className="mt-5">
        <div className="text-sm font-semibold">Justification du modèle retenu</div>
        <p className="mt-1 text-sm text-muted">{data.meta.justification}</p>
      </Card>

      {clf?.models?.length > 0 && (
        <>
          <Section>Classification supervisée du type d'incident</Section>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {clf.models.map((mdl) => (
              <Card key={mdl.name}>
                <div className="font-semibold">{mdl.name}</div>
                <div className="mt-2 flex gap-6">
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

      <Section>Mots-clés saillants par thème (top 16)</Section>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {data.clusters.slice(0, 16).map((c) => (
          <Card key={c.id} className="py-4">
            <div className="mb-2"><Chip>#{c.id}</Chip>
              <span className="text-sm font-semibold">{fmt(c.size)} rapports</span></div>
            <div className="flex flex-wrap">{c.terms.slice(0, 7).map((t) => <Chip key={t}>{t}</Chip>)}</div>
          </Card>
        ))}
      </div>

      {data.lda.topics?.length > 0 && (
        <>
          <Section>Thèmes LDA (top mots)</Section>
          <Card className="space-y-1.5">
            {data.lda.topics.map((t, i) => (
              <div key={i} className="text-sm">
                <span className="text-accent font-semibold">Thème {i}</span>
                <span className="text-muted"> — {t}</span>
              </div>
            ))}
          </Card>
        </>
      )}

      {data.lda_vis_html && (
        <>
          <Section>Visualisation interactive (pyLDAvis)</Section>
          <Card className="p-0 overflow-hidden">
            <iframe src={`${import.meta.env.BASE_URL}data/lda_vis.html`}
              title="pyLDAvis" className="w-full" style={{ height: 820, border: 0, background: "#fff" }} />
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
