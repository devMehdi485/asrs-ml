"""
Clustering thématique des rapports ASRS : cohérence + interprétabilité.

Fournit :
  - réduction UMAP des embeddings (avec fallback PCA) ;
  - K-Means et HDBSCAN (fallback K-Means si hdbscan absent) ;
  - tableau de comparaison des deux modèles (silhouette, DB, CH, bruit, ARI…) ;
  - extraction de termes par cluster via c-TF-IDF ;
  - documents représentatifs par cluster ;
  - labellisation (semi-)automatique : label court + label langage naturel ;
  - synthèse métier par cluster (FR) à partir des métadonnées dominantes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from collections import Counter

from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.metrics import (
    silhouette_score, davies_bouldin_score, calinski_harabasz_score,
    adjusted_rand_score,
)
from sklearn.feature_extraction.text import CountVectorizer

# Au-delà de ce nombre de points, la silhouette (O(n²)) est calculée sur un
# échantillon, et le balayage du coude utilise MiniBatchKMeans.
LARGE_N = 20000
SIL_SAMPLE = 10000


# --------------------------------------------------------------------------- #
#  Réduction de dimension
# --------------------------------------------------------------------------- #


def reduce_dimensions(embeddings, n_components: int = 5, seed: int = 42,
                      n_neighbors: int = 15, min_dist: float = 0.0):
    """Réduit les embeddings via UMAP (fallback PCA). Retourne (X_réduit, méthode)."""
    try:
        import umap
        reducer = umap.UMAP(
            n_components=n_components, n_neighbors=n_neighbors,
            min_dist=min_dist, metric="cosine", random_state=seed,
        )
        return reducer.fit_transform(embeddings), reducer, "UMAP"
    except Exception as exc:  # pragma: no cover
        print(f"[clustering] UMAP indisponible ({exc}); repli sur PCA.")
        from sklearn.decomposition import PCA
        reducer = PCA(n_components=n_components, random_state=seed)
        return reducer.fit_transform(embeddings), reducer, "PCA"


def umap_2d(embeddings, seed: int = 42):
    """Projection 2D pour la visualisation du dashboard."""
    try:
        import umap
        reducer = umap.UMAP(n_components=2, metric="cosine", random_state=seed)
        return reducer.fit_transform(embeddings)
    except Exception:
        from sklearn.decomposition import PCA
        return PCA(n_components=2, random_state=seed).fit_transform(embeddings)


# --------------------------------------------------------------------------- #
#  Modèles de clustering
# --------------------------------------------------------------------------- #


def _silhouette(X, labels, seed: int = 42):
    """Silhouette, échantillonnée si le jeu est volumineux (O(n²) sinon)."""
    n = len(labels)
    if n > LARGE_N:
        return silhouette_score(X, labels, sample_size=SIL_SAMPLE, random_state=seed)
    return silhouette_score(X, labels)


def choose_k_elbow(X, k_range=range(2, 13), seed: int = 42):
    """Calcule inertie + silhouette pour une plage de k (méthode du coude).

    Sur un grand jeu, utilise MiniBatchKMeans (rapide) + silhouette échantillonnée.
    """
    big = len(X) > LARGE_N
    rows = []
    for k in k_range:
        if big:
            km = MiniBatchKMeans(n_clusters=k, random_state=seed, n_init=3,
                                 batch_size=2048)
        else:
            km = KMeans(n_clusters=k, random_state=seed, n_init=10)
        labels = km.fit_predict(X)
        rows.append({
            "k": k,
            "inertie": km.inertia_,
            "silhouette": _silhouette(X, labels, seed),
        })
    return pd.DataFrame(rows)


def cluster_kmeans(X, k: int, seed: int = 42):
    """K-Means final. MiniBatchKMeans au-delà de LARGE_N points (scalable)."""
    if len(X) > LARGE_N:
        km = MiniBatchKMeans(n_clusters=k, random_state=seed, n_init=5,
                             batch_size=2048)
    else:
        km = KMeans(n_clusters=k, random_state=seed, n_init=10)
    labels = km.fit_predict(X)
    return km, labels


def hdbscan_available() -> bool:
    try:
        import hdbscan  # noqa: F401
        return True
    except Exception:
        return False


def cluster_hdbscan(X, min_cluster_size: int = 30, min_samples: int | None = None):
    """HDBSCAN ; -1 = bruit. Lève ImportError si non installé."""
    import hdbscan
    model = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        prediction_data=True,
    )
    labels = model.fit_predict(X)
    return model, labels


# --------------------------------------------------------------------------- #
#  Évaluation & comparaison
# --------------------------------------------------------------------------- #


def _purity(labels, truth) -> float:
    """Pureté : moyenne pondérée de la classe majoritaire par cluster."""
    df = pd.DataFrame({"c": labels, "t": truth})
    df = df[df["c"] != -1]
    if df.empty:
        return float("nan")
    total = len(df)
    s = 0
    for _, grp in df.groupby("c"):
        s += grp["t"].value_counts().iloc[0]
    return s / total


def cluster_metrics(X, labels, truth=None) -> dict:
    """Métriques de cohérence pour un partitionnement donné.

    Les points de bruit (-1, HDBSCAN) sont exclus des métriques internes.
    """
    labels = np.asarray(labels)
    mask = labels != -1
    n_clusters = len(set(labels[mask]))
    bruit = float((~mask).mean())
    out = {
        "n_clusters": n_clusters,
        "taux_bruit": round(bruit, 3),
    }
    if n_clusters >= 2 and mask.sum() > n_clusters:
        Xm, lm = X[mask], labels[mask]
        out["silhouette"] = round(float(_silhouette(Xm, lm)), 4)
        out["davies_bouldin"] = round(float(davies_bouldin_score(Xm, lm)), 4)
        out["calinski_harabasz"] = round(float(calinski_harabasz_score(Xm, lm)), 1)
    else:
        out.update(silhouette=float("nan"), davies_bouldin=float("nan"),
                   calinski_harabasz=float("nan"))
    if truth is not None:
        truth = np.asarray(truth)
        out["ARI_vs_anomaly"] = round(float(adjusted_rand_score(truth[mask], labels[mask])), 4)
        out["purete_vs_anomaly"] = round(float(_purity(labels, truth)), 4)
    # équilibre : ratio plus grand / plus petit cluster
    tailles = pd.Series(labels[mask]).value_counts()
    if len(tailles) > 0:
        out["taille_min"] = int(tailles.min())
        out["taille_max"] = int(tailles.max())
        out["ratio_desequilibre"] = round(float(tailles.max() / max(tailles.min(), 1)), 1)
    return out


def compare_models(X, results: dict[str, np.ndarray], truth=None) -> pd.DataFrame:
    """Tableau comparatif {nom_modèle: labels} -> DataFrame de métriques."""
    rows = {name: cluster_metrics(X, labels, truth) for name, labels in results.items()}
    return pd.DataFrame(rows).T


def select_best_model(comparison: pd.DataFrame) -> tuple[str, str]:
    """Règle de décision explicite pour le choix du modèle final.

    Retourne (nom_modèle, justification_texte).
    Heuristique : on privilégie la silhouette ; HDBSCAN est retenu si sa
    silhouette est au moins aussi bonne ET que son taux de bruit reste
    exploitable (< 35 %) — car son bruit alimente la détection de signaux
    faibles. Sinon K-Means, plus équilibré.
    """
    if "silhouette" not in comparison.columns:
        best = comparison.index[0]
        return best, "Modèle unique disponible."

    sil = comparison["silhouette"]
    best_sil = sil.idxmax()

    if "HDBSCAN" in comparison.index and "KMeans" in comparison.index:
        sil_h = comparison.loc["HDBSCAN", "silhouette"]
        sil_k = comparison.loc["KMeans", "silhouette"]
        bruit_h = comparison.loc["HDBSCAN", "taux_bruit"]
        if sil_h >= sil_k - 0.02 and bruit_h < 0.35:
            return ("HDBSCAN",
                    f"HDBSCAN retenu : silhouette {sil_h:.3f} ≈/≥ K-Means "
                    f"({sil_k:.3f}) et taux de bruit exploitable "
                    f"({bruit_h:.0%}) réutilisé pour les signaux faibles.")
        return ("KMeans",
                f"K-Means retenu : silhouette {sil_k:.3f} vs HDBSCAN "
                f"{sil_h:.3f} (bruit {bruit_h:.0%}), clusters plus équilibrés "
                f"et plus simples à interpréter pour le métier.")
    return best_sil, f"Meilleure silhouette ({sil[best_sil]:.3f})."


# --------------------------------------------------------------------------- #
#  Interprétation : c-TF-IDF, exemples, labels, synthèses
# --------------------------------------------------------------------------- #


def c_tfidf_terms(texts, labels, top_n: int = 12,
                  max_docs_per_cluster: int = 4000, seed: int = 42) -> dict[int, list[str]]:
    """Termes saillants par cluster via c-TF-IDF (TF-IDF par classe).

    On concatène les documents d'un cluster en un 'méga-document', puis on
    compare la fréquence relative des termes entre clusters. Sur un gros corpus,
    on échantillonne ``max_docs_per_cluster`` documents par cluster (les termes
    saillants restent stables, et la mémoire/vitesse sont maîtrisées).
    """
    labels = np.asarray(labels)
    texts = np.asarray(texts, dtype=object)
    rng = np.random.default_rng(seed)
    clusters = sorted(c for c in set(labels) if c != -1)
    docs_par_cluster = []
    for c in clusters:
        idx = np.where(labels == c)[0]
        if len(idx) > max_docs_per_cluster:
            idx = rng.choice(idx, max_docs_per_cluster, replace=False)
        docs_par_cluster.append(" ".join(texts[idx]))
    cv = CountVectorizer(ngram_range=(1, 2), min_df=1, max_features=10000)
    counts = cv.fit_transform(docs_par_cluster).toarray().astype(float)
    vocab = np.array(cv.get_feature_names_out())

    # c-TF-IDF : tf (par cluster) * log(1 + N_moyen / fréquence du terme)
    tf = counts / counts.sum(axis=1, keepdims=True).clip(min=1)
    freq_terme = counts.sum(axis=0)
    idf = np.log(1 + counts.sum() / freq_terme.clip(min=1))
    ctfidf = tf * idf

    out: dict[int, list[str]] = {}
    for i, c in enumerate(clusters):
        top_idx = np.argsort(ctfidf[i])[::-1][:top_n]
        out[int(c)] = vocab[top_idx].tolist()
    return out


def representative_docs(embeddings, labels, raw_texts, n: int = 4,
                        model=None) -> dict[int, list[str]]:
    """Narratives les plus représentatives (proches du centroïde) par cluster."""
    embeddings = np.asarray(embeddings)
    labels = np.asarray(labels)
    raw_texts = np.asarray(raw_texts, dtype=object)
    out: dict[int, list[str]] = {}
    for c in sorted(set(labels)):
        if c == -1:
            continue
        idx = np.where(labels == c)[0]
        centroid = embeddings[idx].mean(axis=0)
        dist = np.linalg.norm(embeddings[idx] - centroid, axis=1)
        ordre = idx[np.argsort(dist)[:n]]
        out[int(c)] = [str(raw_texts[i])[:600] for i in ordre]
    return out


def auto_label(terms_par_cluster: dict[int, list[str]],
               reps: dict[int, list[str]] | None = None
               ) -> dict[int, dict[str, str]]:
    """Labellisation semi-automatique.

    - label_court : top termes c-TF-IDF joints par ' · '
    - label_nl    : phrase en langage naturel construite par template à partir
                    des termes saillants (heuristique, sans dépendance LLM).
    """
    out: dict[int, dict[str, str]] = {}
    for c, terms in terms_par_cluster.items():
        court = " · ".join(terms[:4])
        tete = ", ".join(terms[:3])
        label_nl = (f"Rapports centrés sur « {tete} » "
                    f"(mots-clés : {', '.join(terms[:6])}).")
        out[c] = {"label_court": court, "label_nl": label_nl}
    return out


def _mode_or_na(series: pd.Series) -> str:
    series = series.dropna().astype(str)
    series = series[series.str.strip() != ""]
    if series.empty:
        return "n/d"
    return series.value_counts().idxmax()


def business_summary(df: pd.DataFrame, labels, mapping: dict[str, str],
                     terms_par_cluster: dict[int, list[str]]
                     ) -> dict[int, str]:
    """Synthèse métier (FR) par cluster à partir des métadonnées dominantes."""
    labels = np.asarray(labels)
    df = df.copy()
    df["_cluster"] = labels
    total = (labels != -1).sum()
    out: dict[int, str] = {}
    for c in sorted(set(labels)):
        if c == -1:
            continue
        sub = df[df["_cluster"] == c]
        part = len(sub) / max(total, 1) * 100
        anomaly = (_mode_or_na(sub[mapping["anomaly"]])
                   if "anomaly" in mapping else "n/d")
        phase = (_mode_or_na(sub[mapping["flight_phase"]])
                 if "flight_phase" in mapping else "n/d")
        termes = ", ".join(terms_par_cluster.get(int(c), [])[:5])
        out[int(c)] = (
            f"Le cluster {c} regroupe {len(sub)} rapports ({part:.1f} % du corpus). "
            f"Anomalie dominante : « {anomaly} ». Phase de vol typique : « {phase} ». "
            f"Termes saillants : {termes}. "
            f"Ces rapports décrivent vraisemblablement des incidents liés à ces "
            f"facteurs récurrents."
        )
    return out


def recurring_causes_table(df: pd.DataFrame, labels, mapping: dict[str, str],
                           labels_dict: dict[int, dict[str, str]],
                           trends: dict[int, str] | None = None) -> pd.DataFrame:
    """Tableau final des principales causes récurrentes, trié par importance."""
    labels = np.asarray(labels)
    df = df.copy()
    df["_cluster"] = labels
    total = (labels != -1).sum()
    rows = []
    for c in sorted(set(labels)):
        if c == -1:
            continue
        sub = df[df["_cluster"] == c]
        rows.append({
            "cluster": int(c),
            "label": labels_dict.get(int(c), {}).get("label_court", ""),
            "nb_rapports": len(sub),
            "part_%": round(len(sub) / max(total, 1) * 100, 1),
            "anomalie_dominante": (_mode_or_na(sub[mapping["anomaly"]])
                                   if "anomaly" in mapping else "n/d"),
            "phase_dominante": (_mode_or_na(sub[mapping["flight_phase"]])
                                if "flight_phase" in mapping else "n/d"),
            "tendance": (trends or {}).get(int(c), "n/d"),
        })
    table = pd.DataFrame(rows).sort_values("nb_rapports", ascending=False)
    return table.reset_index(drop=True)
