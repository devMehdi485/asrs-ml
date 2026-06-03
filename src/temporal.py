"""
Analyse de la dimension temporelle des incidents ASRS.

  - volume d'incidents par mois ;
  - heatmap (anomalie ou cluster) × période ;
  - proportion de chaque thème/cluster dans le temps (topics-over-time) ;
  - détection de pics (z-score) et tendance (pente de régression).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_period(df: pd.DataFrame, date_col: str = "datetime",
               freq: str = "M") -> pd.DataFrame:
    """Ajoute une colonne 'periode' (Period) et 'periode_ts' (Timestamp)."""
    df = df.copy()
    df["periode"] = df[date_col].dt.to_period(freq)
    df["periode_ts"] = df["periode"].dt.to_timestamp()
    return df


def monthly_volume(df: pd.DataFrame, date_col: str = "datetime") -> pd.DataFrame:
    """Volume d'incidents par mois -> DataFrame (periode_ts, nb)."""
    s = df.dropna(subset=[date_col]).copy()
    s["periode_ts"] = s[date_col].dt.to_period("M").dt.to_timestamp()
    out = s.groupby("periode_ts").size().reset_index(name="nb")
    return out.sort_values("periode_ts")


def category_time_heatmap(df: pd.DataFrame, cat_col: str,
                          date_col: str = "datetime", top: int = 12) -> pd.DataFrame:
    """Matrice période × catégorie (counts) pour heatmap.

    Limite aux ``top`` catégories les plus fréquentes pour la lisibilité.
    """
    s = df.dropna(subset=[date_col]).copy()
    s["periode_ts"] = s[date_col].dt.to_period("M").dt.to_timestamp()
    cats = s[cat_col].astype(str).value_counts().head(top).index
    s = s[s[cat_col].astype(str).isin(cats)]
    pivot = (s.groupby(["periode_ts", cat_col]).size()
             .unstack(fill_value=0).sort_index())
    return pivot


def topics_over_time(df: pd.DataFrame, cluster_col: str = "cluster",
                     date_col: str = "datetime", normalize: bool = True) -> pd.DataFrame:
    """Proportion (ou volume) de chaque cluster par mois."""
    s = df.dropna(subset=[date_col]).copy()
    s = s[s[cluster_col] != -1]
    s["periode_ts"] = s[date_col].dt.to_period("M").dt.to_timestamp()
    pivot = (s.groupby(["periode_ts", cluster_col]).size()
             .unstack(fill_value=0).sort_index())
    if normalize:
        pivot = pivot.div(pivot.sum(axis=1).clip(lower=1), axis=0)
    return pivot


def detect_peaks(series: pd.Series, z_threshold: float = 2.0) -> pd.DataFrame:
    """Détecte les pics d'une série temporelle via z-score."""
    vals = series.astype(float)
    mu, sigma = vals.mean(), vals.std(ddof=0)
    if sigma == 0:
        z = pd.Series(0.0, index=vals.index)
    else:
        z = (vals - mu) / sigma
    out = pd.DataFrame({"valeur": vals, "zscore": z})
    out["pic"] = out["zscore"] >= z_threshold
    return out


def trend_slope(series: pd.Series) -> float:
    """Pente de la régression linéaire (tendance) d'une série temporelle."""
    y = series.astype(float).values
    if len(y) < 2:
        return 0.0
    x = np.arange(len(y))
    return float(np.polyfit(x, y, 1)[0])


def cluster_trends(df: pd.DataFrame, cluster_col: str = "cluster",
                   date_col: str = "datetime", recent_frac: float = 0.33
                   ) -> dict[int, str]:
    """Qualifie la tendance de chaque cluster (croissance / déclin / stable).

    Compare la part du cluster sur la période récente vs le reste.
    """
    pivot = topics_over_time(df, cluster_col, date_col, normalize=True)
    if pivot.empty:
        return {}
    n = len(pivot)
    cut = max(1, int(n * (1 - recent_frac)))
    ancienne = pivot.iloc[:cut].mean()
    recente = pivot.iloc[cut:].mean()
    out: dict[int, str] = {}
    for c in pivot.columns:
        diff = recente.get(c, 0) - ancienne.get(c, 0)
        pente = trend_slope(pivot[c])
        if diff > 0.02 and pente > 0:
            etat = "↑ en hausse"
        elif diff < -0.02 and pente < 0:
            etat = "↓ en baisse"
        else:
            etat = "→ stable"
        out[int(c)] = f"{etat} ({diff:+.1%} récent)"
    return out
