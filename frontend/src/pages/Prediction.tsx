import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { Card, Section, PageHeader, Intro, Explain } from "../components/ui";
import { loadModel, predict, ModelJSON } from "../predict";
import { C } from "../lib";

const EXEMPLES = [
  "While taxiing for departure we crossed the hold short line and entered the active runway without a clearance from the tower.",
  "During cruise we observed a rapid loss of oil pressure on the number two engine, ran the checklist and declared an emergency.",
  "On final approach a drone passed very close to the cockpit at about 1200 feet above ground.",
  "We encountered severe turbulence in convective weather and a flight attendant was injured during service.",
];

export default function Prediction() {
  const [model, setModel] = useState<ModelJSON | null>(null);
  const [text, setText] = useState(EXEMPLES[0]);
  const [res, setRes] = useState<ReturnType<typeof predict> | null>(null);

  useEffect(() => { loadModel().then(setModel); }, []);

  const run = () => { if (model && text.trim()) setRes(predict(text, model)); };
  useEffect(() => { if (model && !res) run(); }, [model]);

  return (
    <div>
      <PageHeader title="Prédiction d'incident"
        subtitle="Le modèle supervisé en direct : un récit → le type d'incident prédit" />

      <Intro>
        Colle (ou écris) un <b className="text-ink">récit d'incident en anglais</b> ; le modèle
        (TF-IDF + régression logistique, entraîné sur 125 763 rapports) prédit son
        <b className="text-ink"> type</b> parmi 8 catégories, avec une probabilité.
        Tout est calculé <b className="text-ink">dans le navigateur</b> — aucun serveur.
      </Intro>

      <div className="mb-3 flex flex-wrap gap-2">
        {EXEMPLES.map((e, i) => (
          <button key={i} onClick={() => setText(e)}
            className="rounded-full border border-line bg-surface px-3 py-1.5 text-xs text-muted hover:text-ink hover:border-accent/40">
            Exemple {i + 1}
          </button>
        ))}
      </div>

      <Card>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={5}
          className="w-full resize-y rounded-lg border border-line bg-surface2 p-3 text-sm text-ink outline-none focus:border-accent/60"
          placeholder="Ex. During climb the autopilot disconnected and we received a stall warning…" />
        <div className="mt-3 flex items-center gap-3">
          <button onClick={run} disabled={!model}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-accent2 to-accent px-4 py-2.5 text-sm font-semibold text-white shadow-glow disabled:opacity-50">
            <Sparkles size={16} /> {model ? "Prédire le type" : "Chargement du modèle…"}
          </button>
          {res && <span className="text-xs text-muted">{res.matched} termes reconnus</span>}
        </div>
      </Card>

      {res && (
        <>
          <Section>Résultat</Section>
          <Card>
            <div className="mb-1 text-sm text-muted">Type d'incident prédit</div>
            <div className="text-2xl font-extrabold text-accent">{res.ranked[0].cls}</div>
            <div className="mt-1 text-sm text-muted">confiance {(res.ranked[0].p * 100).toFixed(0)} %</div>

            <div className="mt-5 space-y-2">
              {res.ranked.slice(0, 5).map((r) => (
                <div key={r.cls} className="flex items-center gap-3">
                  <div className="w-64 shrink-0 truncate text-sm" title={r.cls}>{r.cls}</div>
                  <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-line">
                    <div className="h-full rounded-full" style={{ width: `${r.p * 100}%`, background: C.accent }} />
                  </div>
                  <div className="w-12 text-right text-sm font-semibold">{(r.p * 100).toFixed(0)}%</div>
                </div>
              ))}
            </div>
          </Card>
          <Explain>le modèle compare le texte aux mots-clés appris pour chaque type d'incident.
            Plus la barre est longue, plus il est sûr. S'il reconnaît peu de termes (ex. récit
            très court ou hors-domaine), la confiance baisse — c'est normal.</Explain>
        </>
      )}
    </div>
  );
}
