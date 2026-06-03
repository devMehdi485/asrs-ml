"""
Détection de signaux faibles / rapports atypiques.

Combine trois signaux :
  - Isolation Forest sur les embeddings réduits (score d'atypicité global) ;
  - bruit HDBSCAN (label -1) lorsqu'il est disponible ;
  - distance au centroïde du cluster d'appartenance (atypicité locale).

Un rapport est un "signal faible" s'il est atypique ET/OU appartient à un
thème rare mais en croissance récente.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def isolation_forest_scores(X, contamination: float = 0.05, seed: int = 42):
    """Score d'anomalie (plus élevé = plus atypique) via Isolation Forest."""
    iso = IsolationForest(contamination=contamination, random_state=seed,
                          n_estimators=200)
    iso.fit(X)
    # score_samples : plus bas = plus anormal -> on inverse pour lisibilité
    raw = -iso.score_samples(X)
    return iso, raw


def centroid_distance(X, labels):
    """Distance de chaque point au centroïde de son cluster (atypicité locale)."""
    X = np.asarray(X)
    labels = np.asarray(labels)
    dist = np.full(len(X), np.nan)
    for c in set(labels):
        if c == -1:
            continue
        idx = np.where(labels == c)[0]
        centroid = X[idx].mean(axis=0)
        dist[idx] = np.linalg.norm(X[idx] - centroid, axis=1)
    return dist


def weak_signals_table(df: pd.DataFrame, iso_scores, centroid_dist,
                       labels, raw_text_col: str, top: int = 30,
                       trends: dict[int, str] | None = None) -> pd.DataFrame:
    """Construit la table des signaux faibles, triée par atypicité.

    Combine le score Isolation Forest (normalisé) et le statut de bruit
    HDBSCAN ; annote la tendance du cluster d'origine.
    """
    labels = np.asarray(labels)
    s = pd.DataFrame(index=df.index)
    s["score_isolation"] = (iso_scores - iso_scores.min()) / (
        np.ptp(iso_scores) + 1e-9)
    s["distance_centroide"] = centroid_dist
    s["bruit_hdbscan"] = labels == -1
    s["cluster"] = labels
    s["score_atypicite"] = s["score_isolation"] + 0.3 * s["bruit_hdbscan"].astype(float)
    if trends is not None:
        s["tendance_cluster"] = [trends.get(int(c), "n/d") for c in labels]
    s["narrative"] = df[raw_text_col].astype(str).str.slice(0, 400).values
    return s.sort_values("score_atypicite", ascending=False).head(top).reset_index(drop=True)


def emerging_rare_themes(df: pd.DataFrame, cluster_col: str,
                         trends: dict[int, str], rare_quantile: float = 0.25
                         ) -> list[int]:
    """Identifie les thèmes rares (petite taille) ET en hausse = signaux faibles
    thématiques."""
    tailles = df[df[cluster_col] != -1][cluster_col].value_counts()
    if tailles.empty:
        return []
    seuil = tailles.quantile(rare_quantile)
    rares = set(tailles[tailles <= seuil].index)
    emergents = [int(c) for c in rares
                 if "hausse" in trends.get(int(c), "")]
    return emergents
