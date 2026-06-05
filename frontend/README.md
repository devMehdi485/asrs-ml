# AeroInsight AI — Dashboard React (NASA ASRS)

Dashboard web **React + TypeScript + Vite + Tailwind + Recharts** reproduisant la
maquette Figma Make *AeroInsight AI*. Thème sombre « aviation intelligence »,
6 pages, alimenté par un **export JSON statique** des résultats d'analyse ASRS
(aucun backend requis).

## Pages
1. **Executive Intelligence** — KPIs, top clusters, tendances, signaux, causes
2. **Operational Dashboard** — distributions (anomalies, phases), répartition des thèmes
3. **Cluster Explorer** — projection 2D interactive + inspecteur de thème (mots-clés, synthèse, exemples)
4. **Thematic Analysis** — causes récurrentes, classification supervisée, thèmes LDA + pyLDAvis embarqué
5. **Temporal Heatmap** — volume + pics, heatmap anomalie×année, thèmes dans le temps
6. **Weak Signals** — seuil interactif, distribution d'atypicité, rapports atypiques

## Lancer en développement
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

## Build de production
```bash
npm run build        # génère dist/
npm run preview      # sert dist/ en local
```

## Données
L'app charge `public/data/asrs.json` (+ `lda_vis.html`). Pour le **régénérer**
depuis les résultats de l'analyse (`data/processed/`) :

```bash
# depuis la racine du projet
python notebooks_assets/export_json.py
```

> Le JSON est versionné pour que l'app fonctionne immédiatement après un clone.
> Relance l'export après chaque nouvelle exécution du notebook.

## Déploiement
`dist/` est un site statique : déployable tel quel (GitHub Pages, Netlify, Vercel…).
`base: "./"` (vite.config.ts) permet un hébergement dans un sous-chemin.
