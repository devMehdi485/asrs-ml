"""
Exporte les résultats ASRS (artefacts) en un JSON statique consommé par l'app
React (frontend/). Aucune dépendance serveur : le dashboard React charge ce
fichier directement.

Sortie : frontend/public/data/asrs.json
"""
import os, json, re
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
OUT_DIR = os.path.join(ROOT, "frontend", "public", "data")
os.makedirs(OUT_DIR, exist_ok=True)

SCATTER_N = 6000
WEAK_N = 60

df = pd.read_parquet(os.path.join(PROC, "reports_clean.parquet"))
art = json.load(open(os.path.join(PROC, "artefacts.json"), encoding="utf-8"))
iso = np.load(os.path.join(PROC, "iso_scores.npy"))
causes = pd.read_csv(os.path.join(PROC, "causes_recurrentes.csv"))
df["iso"] = iso
df["atyp"] = (iso - iso.min()) / (np.ptp(iso) + 1e-9)
df["cluster"] = df["cluster"].astype(int)

TERMS = {int(k): v for k, v in art["terms_par_cluster"].items()}
LABELS = {int(k): v for k, v in art["labels"].items()}
SYN = {int(k): v for k, v in art["syntheses"].items()}
REPS = {int(k): v for k, v in art.get("reps", {}).items()}
TRENDS = {int(k): v for k, v in art.get("trends", {}).items()}
sizes = df[df["cluster"] != -1]["cluster"].value_counts()
total = int((df["cluster"] != -1).sum())


def clabel(c): return LABELS.get(c, {}).get("label_court", f"Cluster {c}")


# ---- clusters ----
clusters = []
for c in sizes.index:
    clusters.append({
        "id": int(c), "label": clabel(c),
        "label_nl": LABELS.get(c, {}).get("label_nl", ""),
        "size": int(sizes[c]), "part": round(100 * sizes[c] / total, 2),
        "terms": TERMS.get(c, [])[:12], "synthese": SYN.get(c, ""),
        "trend": TRENDS.get(c, "n/d"), "reps": REPS.get(c, [])[:3],
    })

# ---- scatter (échantillon) ----
dv = df[(df["cluster"] != -1) & df["x"].notna()]
if len(dv) > SCATTER_N:
    dv = dv.sample(SCATTER_N, random_state=42)
scatter = [{"x": round(float(r.x), 3), "y": round(float(r.y), 3), "c": int(r.cluster)}
           for r in dv.itertuples()]

# ---- temporel ----
dt = df.dropna(subset=["datetime"]).copy()
dt["m"] = dt["datetime"].dt.to_period("M").dt.to_timestamp()
vol = dt.groupby("m").size()
months = [d.strftime("%Y-%m") for d in vol.index]
volume = [int(v) for v in vol.values]
mu, sd = float(np.mean(volume)), float(np.std(volume))
peaks = [bool((v - mu) / (sd + 1e-9) >= 2) for v in volume]

top_anoms = dt["anomaly"].astype(str).value_counts().head(12).index.tolist()
da = dt[dt["anomaly"].astype(str).isin(top_anoms)]
heat = (da.groupby([da["m"], da["anomaly"].astype(str)]).size()
        .unstack(fill_value=0).reindex(columns=top_anoms, fill_value=0))
heat_periods = [d.strftime("%Y-%m") for d in heat.index]
heatmap = {"anomalies": [a[:45] for a in top_anoms],
           "periods": heat_periods,
           "matrix": [[int(x) for x in row] for row in heat.T.values.tolist()]}

big = sizes.head(8).index.tolist()
dtt = dt[dt["cluster"].isin(big)]
tot = dtt.groupby([dtt["m"], dtt["cluster"]]).size().unstack(fill_value=0).reindex(columns=big, fill_value=0)
tot = tot.div(tot.sum(axis=1).clip(lower=1), axis=0)
topics_over_time = {"periods": [d.strftime("%Y-%m") for d in tot.index],
                    "series": [{"id": int(c), "label": clabel(c),
                                "values": [round(float(x), 4) for x in tot[c].values]}
                               for c in big]}

# ---- signaux faibles ----
ws = df.sort_values("atyp", ascending=False).head(WEAK_N)
weak = [{"score": round(float(r.atyp), 3), "cluster": int(r.cluster),
         "anomaly": str(r.anomaly)[:60],
         "date": (r.datetime.strftime("%Y-%m") if pd.notna(r.datetime) else ""),
         "text": str(r.text_raw)[:400]} for r in ws.itertuples()]

# ---- histogramme des scores d'atypicité (page Weak Signals) ----
counts_h, edges_h = np.histogram(df["atyp"].values, bins=40, range=(0, 1))
atyp_hist = {"centers": [round(float((edges_h[i] + edges_h[i + 1]) / 2), 3) for i in range(len(counts_h))],
             "counts": [int(x) for x in counts_h]}

# ---- copie de la visualisation pyLDAvis pour l'embarquer dans l'app ----
import shutil
lda_src = os.path.join(PROC, "lda_vis.html")
if os.path.exists(lda_src):
    shutil.copy(lda_src, os.path.join(OUT_DIR, "lda_vis.html"))

# ---- LDA + classification : extraits du notebook exécuté ----
lda = {"coherence": None, "topics": []}
classification = {"models": [], "report": ""}
nb_path = os.path.join(ROOT, "asrs_nlp_analysis.ipynb")
if os.path.exists(nb_path):
    nb = json.load(open(nb_path, encoding="utf-8"))
    out_txt = []
    for cell in nb["cells"]:
        for o in cell.get("outputs", []):
            if "text" in o: out_txt.append("".join(o["text"]))
            d = o.get("data", {})
            if "text/plain" in d: out_txt.append("".join(d["text/plain"]))
    full = "\n".join(out_txt)
    m = re.search(r"Coh[ée]rence c_v[^:]*:\s*([0-9.]+)", full)
    if m: lda["coherence"] = float(m.group(1))
    lda["topics"] = [re.sub(r"^Th[èe]me LDA \d+:\s*", "", l).strip()
                     for l in full.splitlines() if re.match(r"Th[èe]me LDA \d+:", l)][:20]
    for name, mm in zip(["Logistic Regression", "SVM linéaire"],
                        re.findall(r"F1 macro = ([0-9.]+) \| F1 pond[ée]r[ée] = ([0-9.]+)", full)):
        classification["models"].append({"name": name, "f1_macro": float(mm[0]),
                                          "f1_weighted": float(mm[1])})
    idx = full.find("precision    recall")
    if idx > 0:
        classification["report"] = full[idx:idx + 1400]

# ---- distributions (page Operational) ----
def dist(col, n):
    vc = df[col].dropna().astype(str).value_counts().head(n)
    return [{"name": k[:55], "count": int(v)} for k, v in vc.items()]

distributions = {"anomaly": dist("anomaly", 15),
                 "phase": dist("flight_phase", 12) if "flight_phase" in df.columns else []}

period = ([df["datetime"].min().strftime("%Y-%m"),
           df["datetime"].max().strftime("%Y-%m")] if df["datetime"].notna().any() else None)

payload = {
    "meta": {
        "n_reports": int(len(df)), "n_themes": int(len(clusters)),
        "period": period, "model": art.get("modele_clustering"),
        "justification": art.get("justification"),
        "embeddings": art.get("methode_embeddings"),
        "reduction": art.get("methode_reduction"),
        "n_weak": int((df["atyp"] > 0.6).sum()),
        "n_up": sum(1 for t in TRENDS.values() if "hausse" in t),
    },
    "comparison": art.get("comparaison", []),
    "distributions": distributions,
    "causes": causes.to_dict(orient="records"),
    "clusters": clusters,
    "scatter": scatter,
    "temporal": {"periods": months, "volume": volume, "peaks": peaks,
                 "heatmap": heatmap, "topics_over_time": topics_over_time},
    "weak_signals": weak,
    "atyp_hist": atyp_hist,
    "lda_vis_html": os.path.exists(lda_src),
    "emergents": art.get("emergents", []),
    "lda": lda,
    "classification": classification,
}

out = os.path.join(OUT_DIR, "asrs.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, separators=(",", ":"), default=str)
print("Export JSON ->", out)
print(f"  {len(clusters)} clusters | {len(scatter)} pts scatter | "
      f"{len(months)} mois | {len(weak)} signaux | "
      f"LDA c_v={lda['coherence']} | {len(classification['models'])} modèles classif")
print(f"  taille: {os.path.getsize(out)/1024:.0f} Ko")
