import { useState } from "react";
import { ChevronRight } from "lucide-react";
import { useData } from "../context";
import { Kpi, Card, Section, PageHeader, Chip, Intro, Explain } from "../components/ui";
import { fmt, trendClass } from "../lib";

export default function ThematicAnalysis() {
  const { data } = useData()!;
  const [showLda, setShowLda] = useState(false);
  if (!data) return null;
  const clf = data.classification;
  const maxSize = Math.max(...data.clusters.map((c) => c.size));
  const themes = data.clusters.slice(0, 12);

  return (
    <div>
      <PageHeader title="Thematic Analysis"
        subtitle={`${data.meta.n_themes} thèmes dominants identifiés sur l'ensemble des rapports`} />

      <Intro>
        Un <b className="text-ink">thème</b> = un groupe de récits qui parlent de la même chose
        (ex. « train d'atterrissage »), découvert automatiquement. Plus bas, la
        <b className="text-ink"> classification</b> est un modèle qui devine le type d'un incident
        à partir de son texte ; le <b className="text-ink">LDA</b> est une 2ᵉ méthode de thèmes.
      </Intro>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi label="Thèmes" value={data.meta.n_themes} icon="🗂️" />
        <Kpi label="Modèle" value={data.meta.model} icon="🧠" tint="accent" />
        <Kpi label="Cohérence LDA c_v" value={data.lda.coherence ?? "—"} icon="📐" tint="up" />
        <Kpi label="Plus gros thème" value={`${data.causes[0]?.["part_%"]}%`} icon="🥇" tint="warn" />
      </div>

      <Section>Thèmes dominants</Section>
      <Explain>la barre <b>« importance »</b> = la taille du thème (sa part dans le total).
        La mention colorée indique s'il est en <span className="text-up">hausse</span> ou en
        <span className="text-down"> baisse</span> récente. Les puces bleues sont ses mots-clés.</Explain>
      <div className="mt-3 flex flex-col gap-3">
        {themes.map((c) => {
          const imp = Math.round((c.size / maxSize) * 100);
          return (
            <Card key={c.id} className="py-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-baseline gap-3">
                    <span className="text-lg font-bold">{c.name}</span>
                    <span className="text-sm text-muted">{fmt(c.size)} rapports · {c.part}%</span>
                  </div>
                  <div className="mt-0.5 flex items-center gap-2">
                    <span className="chip">{c.category}</span>
                    <span className="text-sm text-muted">{c.desc}</span>
                  </div>
                </div>
                <ChevronRight size={18} className="mt-1 shrink-0 text-muted" />
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
          <Explain>un modèle apprend à <b>deviner le type d'incident</b> à partir du texte.
            Le <b>F1</b> est une note de précision entre 0 et 1 (1 = parfait) ; ici jusqu'à
            <b> 0,61</b>, ce qui est correct pour 8 catégories et des récits libres.</Explain>
          <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
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
            <Card className="mt-3">
              <div className="mb-2 text-sm font-semibold">Détail par classe — régression logistique</div>
              <div className="overflow-x-auto">
                <pre className="text-[11px] leading-5 text-muted">{clf.report}</pre>
              </div>
            </Card>
          )}
        </>
      )}

      {data.lda_vis_html && (
        <>
          <Section>Visualisation interactive des thèmes LDA (pyLDAvis)</Section>
          {showLda ? (
            <Card className="overflow-hidden p-0">
              <iframe src={`${import.meta.env.BASE_URL}data/lda_vis.html`} title="pyLDAvis"
                className="w-full" style={{ height: 820, border: 0, background: "#fff" }} />
            </Card>
          ) : (
            <Card className="flex items-center justify-between">
              <span className="text-sm text-muted">Visualisation interactive (D3) — chargement à la demande.</span>
              <button onClick={() => setShowLda(true)}
                className="rounded-lg bg-gradient-to-r from-accent2 to-accent px-4 py-2 text-sm font-semibold text-white shadow-glow">
                Charger la visualisation
              </button>
            </Card>
          )}
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
                <td className="px-4 py-2 font-medium">{(c as any).name || c.label}</td>
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
