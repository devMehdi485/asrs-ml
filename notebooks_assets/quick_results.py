"""Résultats rapides depuis le cache (saute le LDA lent).
Produit tous les artefacts dont le DASHBOARD a besoin, en ~5 min.
"""
import os, json, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from src import clustering as C, temporal as T, anomalies as A

RS = 42; N_VIZ = 25000; N_CLUSTERS = 15; MIN_CLUSTER_SIZE = 150
PROC = "data/processed"; os.makedirs(os.path.join(PROC, "models"), exist_ok=True)

print(">> chargement des caches…")
df = pd.read_parquet(os.path.join(PROC, "reports_pre.parquet"))
embeddings = np.load(os.path.join(PROC, "embeddings.npy"))
X_red = np.load(os.path.join(PROC, "reduced.npy"))
assert len(df) == len(embeddings) == len(X_red), "tailles incohérentes"
mapping = {"anomaly": "anomaly"}
for c in ("flight_phase", "aircraft"):
    if c in df.columns: mapping[c] = c
print(f"   {len(df)} rapports | embeddings {embeddings.shape} | reduced {X_red.shape}")

print(">> clustering K-Means + HDBSCAN…")
km, labels_km = C.cluster_kmeans(X_red, N_CLUSTERS, seed=RS)
hdb, labels_hdb = C.cluster_hdbscan(X_red, min_cluster_size=MIN_CLUSTER_SIZE, min_samples=10)
truth = df[mapping["anomaly"]].astype(str).values
comparaison = C.compare_models(X_red, {"KMeans": labels_km, "HDBSCAN": labels_hdb}, truth=truth)
best_name, justification = C.select_best_model(comparaison)
labels = labels_km if best_name == "KMeans" else labels_hdb
df["cluster"] = labels
print(comparaison[["n_clusters", "silhouette", "taux_bruit", "ARI_vs_anomaly"]].to_string())
print("   MODÈLE RETENU :", best_name, "->", justification)

print(">> interprétation (c-TF-IDF, labels, résumés)…")
terms = C.c_tfidf_terms(df["text_clean"].values, labels, top_n=12)
labels_dict = C.auto_label(terms)
reps = C.representative_docs(embeddings, labels, df["text_raw"].values, n=3)
syntheses = C.business_summary(df, labels, mapping, terms)
trends = T.cluster_trends(df, "cluster", "datetime")
table_causes = C.recurring_causes_table(df, labels, mapping, labels_dict, trends)

print(">> signaux faibles (Isolation Forest)…")
iso_model, iso_scores = A.isolation_forest_scores(X_red, contamination=0.05, seed=RS)
emergents = A.emerging_rare_themes(df, "cluster", trends)

print(">> projection 2D (échantillon)…")
rng = np.random.default_rng(RS)
viz_idx = (np.sort(rng.choice(len(df), N_VIZ, replace=False)) if len(df) > N_VIZ
           else np.arange(len(df)))
coords = C.umap_2d(embeddings[viz_idx], seed=RS)
df["x"] = np.nan; df["y"] = np.nan
df.iloc[viz_idx, df.columns.get_loc("x")] = coords[:, 0]
df.iloc[viz_idx, df.columns.get_loc("y")] = coords[:, 1]

print(">> sérialisation des artefacts…")
cols = ["text_raw", "datetime", "annee", "cluster", "x", "y", "anomaly"]
for c in ("flight_phase", "aircraft"):
    if c in df.columns: cols.append(c)
df_out = df[cols].copy()
df_out["text_raw"] = df_out["text_raw"].astype(str).str.slice(0, 1500)
df_out.to_parquet(os.path.join(PROC, "reports_clean.parquet"))
np.save(os.path.join(PROC, "iso_scores.npy"), iso_scores)
table_causes.to_csv(os.path.join(PROC, "causes_recurrentes.csv"), index=False)
artefacts = {
    "methode_embeddings": "sentence-transformers/all-MiniLM-L6-v2",
    "methode_reduction": "UMAP", "modele_clustering": best_name,
    "justification": justification,
    "terms_par_cluster": {str(k): v for k, v in terms.items()},
    "labels": {str(k): v for k, v in labels_dict.items()},
    "syntheses": {str(k): v for k, v in syntheses.items()},
    "reps": {str(k): v for k, v in reps.items()},
    "trends": {str(k): v for k, v in trends.items()},
    "emergents": emergents,
    "comparaison": comparaison.reset_index().to_dict(orient="records"),
}
with open(os.path.join(PROC, "artefacts.json"), "w", encoding="utf-8") as f:
    json.dump(artefacts, f, ensure_ascii=False, indent=2, default=str)

print("\n================ RÉSULTATS ================")
print(f"Nb de thèmes/clusters : {len([c for c in set(labels) if c != -1])}")
print("\nTABLEAU DES CAUSES RÉCURRENTES :")
print(table_causes[["cluster", "label", "nb_rapports", "part_%",
                    "anomalie_dominante", "tendance"]].to_string(index=False))
print("\nSignaux faibles (thèmes rares émergents) :", emergents)
print("\nARTEFACTS ÉCRITS -> dashboard prêt. ALL OK")
