import { useMemo, useState } from "react";
import { Filter, ZoomIn } from "lucide-react";
import { useData } from "../context";
import { Card, Section, PageHeader, Trend, Chip, Intro, Explain } from "../components/ui";
import ScatterCanvas from "../components/ScatterCanvas";
import { colorFor, fmt } from "../lib";

const btn = "flex items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2 text-sm text-muted hover:text-ink hover:border-accent/40 transition";

export default function ClusterExplorer() {
  const { data } = useData()!;
  const cats = data!.categories;
  const catName = useMemo(() => cats.map((c) => c.category), [data]);
  const [active, setActive] = useState<string | null>(null);   // catégorie filtrée
  const [sel, setSel] = useState<number>(data!.clusters[0].id);

  const activeIdx = active ? catName.indexOf(active) : -1;

  // centres de chaque catégorie -> étiquettes sur la carte
  const labels = useMemo(() => {
    const agg: Record<number, { sx: number; sy: number; n: number }> = {};
    for (const p of data!.scatter) {
      const a = (agg[p.cat] ||= { sx: 0, sy: 0, n: 0 });
      a.sx += p.x; a.sy += p.y; a.n++;
    }
    return Object.entries(agg)
      .sort((x, y) => y[1].n - x[1].n).slice(0, 8)
      .map(([ci, a]) => ({ text: catName[+ci] || "", x: a.sx / a.n, y: a.sy / a.n }));
  }, [data, catName]);
  const themes = active ? data!.clusters.filter((c) => c.category === active) : data!.clusters.slice(0, 12);
  const cluster = data!.clusters.find((c) => c.id === sel)!;

  return (
    <div>
      <PageHeader title="Cluster Explorer"
        subtitle={`Projection UMAP de ${fmt(data!.meta.n_reports)} rapports — ${data!.meta.n_themes} thèmes en ${cats.length} catégories`}
        right={
          <div className="flex gap-2">
            <button className={btn}><ZoomIn size={16} /> Zoom</button>
            <button className={btn}><Filter size={16} /> Filter</button>
          </div>
        } />

      <Intro>
        <b className="text-ink">Cette carte = une « photo » de tous les récits.</b> Chaque
        point est un rapport d'incident. Deux points <b className="text-ink">proches</b> =
        deux récits qui <b className="text-ink">parlent de la même chose</b>. La
        <b className="text-ink"> couleur</b> indique la catégorie. On voit ainsi se former des
        « îlots » de thèmes. Clique une catégorie ci-dessous pour l'isoler, ou un thème plus bas
        pour lire son détail.
      </Intro>

      {/* Filtres par catégorie */}
      <div className="mb-4 flex flex-wrap gap-2">
        <button onClick={() => setActive(null)}
          className={"rounded-full border px-3 py-1.5 text-xs font-semibold transition " +
            (!active ? "border-accent bg-accent/15 text-accent" : "border-line text-muted hover:text-ink")}>
          Toutes
        </button>
        {cats.map((c, i) => (
          <button key={c.category} onClick={() => setActive(c.category)}
            className={"flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition " +
              (active === c.category ? "border-accent bg-accent/15 text-ink" : "border-line text-muted hover:text-ink")}>
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: colorFor(i) }} />
            {c.category} <span className="opacity-60">{c.part}%</span>
          </button>
        ))}
      </div>

      <Card>
        <ScatterCanvas points={data!.scatter} activeIdx={activeIdx} color={colorFor} labels={labels} height={460} />
        <Explain>les axes n'ont pas d'unité (c'est une projection mathématique) — seules
          comptent la <b>proximité</b> des points et leur <b>couleur</b>. Des groupes de même
          couleur bien séparés = des thèmes distincts et cohérents.</Explain>
      </Card>

      <Section>{active ? `Thèmes — ${active}` : "Thèmes principaux"}</Section>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {themes.map((c) => (
          <button key={c.id} onClick={() => setSel(c.id)}
            className={"flex items-center justify-between rounded-xl border bg-surface px-4 py-3 text-left transition " +
              (c.id === sel ? "border-accent/60 shadow-glow" : "border-line hover:border-accent/30")}>
            <span className="flex items-center gap-2.5 truncate">
              <span className="h-3 w-3 shrink-0 rounded-full" style={{ background: colorFor(catName.indexOf(c.category)) }} />
              <span className="truncate text-sm font-semibold">{c.name}</span>
            </span>
            <span className="ml-2 shrink-0 text-sm text-muted">{fmt(c.size)}</span>
          </button>
        ))}
      </div>

      <Section>Détail du thème</Section>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card>
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <span className="h-3 w-3 rounded-full" style={{ background: colorFor(catName.indexOf(cluster.category)) }} />
            <span className="font-bold">{cluster.name}</span>
            <span className="chip ml-1">{cluster.category}</span>
          </div>
          <p className="mb-3 text-sm text-muted">{cluster.desc}</p>
          <div className="flex flex-wrap">
            {cluster.terms.map((t, i) => (
              <span key={t} className="mr-2 mb-2 rounded-full border border-accent/30 bg-accent/10 px-3 py-1 font-semibold text-accent"
                style={{ fontSize: `${1.1 - i * 0.045}rem` }}>{t}</span>
            ))}
          </div>
        </Card>
        <Card>
          <div className="text-sm font-semibold">Synthèse métier</div>
          <p className="mt-1 text-sm text-muted">{cluster.synthese}</p>
          <div className="mt-3 flex items-center gap-3">
            <Chip>{fmt(cluster.size)} rapports · {cluster.part}%</Chip><Trend t={cluster.trend} />
          </div>
        </Card>
      </div>

      <Section>Narratives représentatives</Section>
      <div className="grid grid-cols-1 gap-3">
        {cluster.reps.map((r, i) => (
          <Card key={i} className="py-4"><Chip>{i + 1}</Chip><span className="text-sm text-muted">{r}…</span></Card>
        ))}
      </div>
    </div>
  );
}
