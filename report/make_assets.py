"""
Génère les figures + le mot2vec de démonstration pour le rapport et la présentation.
Sorties : report/figures/*.png  et  report/word2vec.json
"""
import os, json, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wordcloud import WordCloud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
FIG = os.path.join(ROOT, "report", "figures")
os.makedirs(FIG, exist_ok=True)

art = json.load(open(os.path.join(PROC, "artefacts.json"), encoding="utf-8"))
causes = pd.read_csv(os.path.join(PROC, "causes_recurrentes.csv"))
data = json.load(open(os.path.join(ROOT, "frontend", "public", "data", "asrs.json"), encoding="utf-8"))

PALETTE = ["#2563EB", "#16A34A", "#D97706", "#DC2626", "#9333EA", "#0D9488",
           "#3B82F6", "#EA580C", "#059669", "#DB2777", "#6366F1", "#0891B2"]
plt.rcParams.update({"font.size": 11, "axes.edgecolor": "#cccccc",
                     "axes.grid": True, "grid.color": "#eeeeee", "figure.dpi": 140})


def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(FIG, name), bbox_inches="tight"); plt.close(fig)
    print("  fig:", name)


# 1. Répartition par catégorie
cats = data["categories"]
fig, ax = plt.subplots(figsize=(8, 4.2))
y = [c["category"] for c in cats][::-1]; v = [c["part"] for c in cats][::-1]
ax.barh(y, v, color=[PALETTE[i % len(PALETTE)] for i in range(len(y))])
ax.set_xlabel("% du corpus"); ax.set_title("Répartition des incidents par catégorie")
for i, val in enumerate(v): ax.text(val + 0.3, i, f"{val}%", va="center", fontsize=9)
save(fig, "categories.png")

# 2. Top thèmes
top = data["causes"][:12][::-1]
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh([c["name"][:38] for c in top], [c["nb_rapports"] for c in top],
        color="#2563EB")
ax.set_xlabel("nombre de rapports"); ax.set_title("Top 12 des thèmes d'incidents")
save(fig, "top_themes.png")

# 3. Volume temporel
t = data["temporal"]
fig, ax = plt.subplots(figsize=(9, 3.6))
xs = pd.to_datetime(t["periods"])
ax.fill_between(xs, t["volume"], color="#2563EB", alpha=0.25)
ax.plot(xs, t["volume"], color="#2563EB", lw=1.5)
ax.set_title("Volume mensuel d'incidents"); ax.set_ylabel("rapports")
save(fig, "temporal_volume.png")

# 4. Heatmap anomalie x temps (par année)
hm = t["heatmap"]
mat = np.array(hm["matrix"], dtype=float)
years = sorted(set(p[:4] for p in hm["periods"]))
agg = np.zeros((len(hm["anomalies"]), len(years)))
for j, p in enumerate(hm["periods"]):
    yi = years.index(p[:4])
    agg[:, yi] += mat[:, j]
fig, ax = plt.subplots(figsize=(9, 4.5))
im = ax.imshow(agg, aspect="auto", cmap="rocket_r" if "rocket_r" in plt.colormaps() else "magma")
ax.set_yticks(range(len(hm["anomalies"]))); ax.set_yticklabels([a[:38] for a in hm["anomalies"]], fontsize=7)
ax.set_xticks(range(0, len(years), 2)); ax.set_xticklabels(years[::2], fontsize=8)
ax.set_title("Heatmap : type d'anomalie × année"); fig.colorbar(im, label="rapports")
save(fig, "heatmap.png")

# 5. Scatter UMAP coloré par catégorie
sc = data["scatter"]
fig, ax = plt.subplots(figsize=(7.5, 5.5))
xs = [p["x"] for p in sc]; ys = [p["y"] for p in sc]; cs = [PALETTE[p["cat"] % len(PALETTE)] for p in sc]
ax.scatter(xs, ys, c=cs, s=5, alpha=0.6, linewidths=0)
ax.set_title("Projection UMAP des rapports (couleur = catégorie)")
ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
# légende
import matplotlib.patches as mp
handles = [mp.Patch(color=PALETTE[i % len(PALETTE)], label=c["category"]) for i, c in enumerate(cats)]
ax.legend(handles=handles, fontsize=7, loc="center left", bbox_to_anchor=(1, 0.5))
save(fig, "scatter.png")

# 6. Nuages de mots par cluster (top 4)
terms = {int(k): v for k, v in art["terms_par_cluster"].items()}
top_ids = [c["cluster"] for c in data["causes"][:4]]
names = {c["cluster"]: c["name"] for c in data["causes"]}
fig, axes = plt.subplots(2, 2, figsize=(10, 6))
for ax, cid in zip(axes.ravel(), top_ids):
    freq = {t_: (len(terms[cid]) - i) for i, t_ in enumerate(terms[cid])}
    wc = WordCloud(width=420, height=240, background_color="white", colormap="viridis")
    ax.imshow(wc.generate_from_frequencies(freq)); ax.axis("off")
    ax.set_title(names.get(cid, f"#{cid}")[:40], fontsize=10)
save(fig, "wordclouds.png")

# 7. word2vec (gensim) — démonstration d'embeddings de mots (brief)
w2v_out = {}
try:
    from gensim.models import Word2Vec
    pre = os.path.join(PROC, "reports_pre.parquet")
    if os.path.exists(pre):
        toks = [str(t).split() for t in pd.read_parquet(pre, columns=["text_clean"])["text_clean"]]
        print(f"  word2vec : entraînement sur {len(toks)} documents…")
        m = Word2Vec(sentences=toks, vector_size=100, window=5, min_count=20,
                     workers=4, epochs=5, seed=42)
        for seed in ["runway", "engine", "fuel", "weather", "altitude", "gear"]:
            if seed in m.wv:
                w2v_out[seed] = [(w, round(float(s), 3)) for w, s in m.wv.most_similar(seed, topn=6)]
        print("  word2vec OK :", list(w2v_out))
    else:
        print("  reports_pre absent -> word2vec sauté")
except Exception as e:
    print("  word2vec indisponible :", e)
json.dump(w2v_out, open(os.path.join(ROOT, "report", "word2vec.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print("Assets générés dans report/figures/")
