"""Dashboard Streamlit simplifie pour le projet ASRS.

Vues conservees :
- nuage de mots par cluster ;
- carte temporelle des incidents.

Lancement :
    streamlit run dashboard/app.py
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from wordcloud import WordCloud


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")

st.set_page_config(
    page_title="ASRS ML - Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def load_artifacts():
    reports_path = os.path.join(PROC, "reports_clean.parquet")
    artefacts_path = os.path.join(PROC, "artefacts.json")

    if not os.path.exists(reports_path) or not os.path.exists(artefacts_path):
        return None, None

    df = pd.read_parquet(reports_path)
    with open(artefacts_path, encoding="utf-8") as f:
        art = json.load(f)

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    else:
        df["datetime"] = pd.NaT

    if "cluster" in df.columns:
        df["cluster"] = df["cluster"].astype(int)

    return df, art


def get_terms(art: dict, cluster_id: int) -> list[str]:
    raw_terms = art.get("terms_par_cluster", {}).get(str(cluster_id), [])
    if isinstance(raw_terms, dict):
        return list(raw_terms.keys())
    return list(raw_terms)


def get_label(art: dict, cluster_id: int) -> str:
    labels = art.get("labels", {})
    label = labels.get(str(cluster_id), labels.get(cluster_id, {}))
    if isinstance(label, dict):
        return label.get("label_court", f"Cluster {cluster_id}")
    if isinstance(label, str):
        return label
    return f"Cluster {cluster_id}"


def make_wordcloud(terms: list[str]):
    if not terms:
        return None

    weights = {term: len(terms) - i for i, term in enumerate(terms)}
    wc = WordCloud(
        width=1100,
        height=520,
        background_color="white",
        colormap="viridis",
        prefer_horizontal=0.95,
    ).generate_from_frequencies(weights)

    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    return fig


df, ART = load_artifacts()

st.title("Projet Machine Learning - NASA ASRS")
st.caption("Dashboard Streamlit simplifie : nuage de mots par cluster et carte temporelle des incidents.")

if df is None or ART is None:
    st.error(
        "Artefacts introuvables dans `data/processed/`. "
        "Lance d'abord le notebook d'analyse ou `python notebooks_assets/quick_results.py`."
    )
    st.stop()

valid_clusters = sorted(c for c in df["cluster"].dropna().unique().astype(int) if c != -1)
cluster_sizes = df[df["cluster"] != -1]["cluster"].value_counts().sort_index()
cluster_options = {
    (
        f"#{c} - {get_label(ART, c)} "
        f"({int(cluster_sizes.get(c, 0)):,} rapports)".replace(",", " ")
    ): c
    for c in valid_clusters
}

st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Vue",
    ["Nuage de mots par cluster", "Carte temporelle des incidents"],
    label_visibility="collapsed",
)

st.sidebar.header("Corpus")
st.sidebar.metric("Rapports", f"{len(df):,}".replace(",", " "))
st.sidebar.metric("Clusters", len(valid_clusters))
if df["datetime"].notna().any():
    st.sidebar.caption(
        f"Periode : {df['datetime'].min():%Y-%m} -> {df['datetime'].max():%Y-%m}"
    )


if page == "Nuage de mots par cluster":
    st.header("Nuage de mots par cluster")
    st.write(
        "Selectionne un cluster pour afficher les termes les plus caracteristiques "
        "du theme extrait des rapports ASRS."
    )

    selected_label = st.selectbox(
        "Cluster",
        list(cluster_options.keys()),
    )
    selected_cluster = cluster_options[selected_label]

    terms = get_terms(ART, selected_cluster)
    col_left, col_right = st.columns([2, 1])

    with col_left:
        fig = make_wordcloud(terms)
        if fig is None:
            st.warning("Aucun terme disponible pour ce cluster.")
        else:
            st.pyplot(fig, clear_figure=True)

    with col_right:
        st.subheader(get_label(ART, selected_cluster))
        st.metric("Rapports du cluster", f"{int(cluster_sizes.get(selected_cluster, 0)):,}".replace(",", " "))
        st.write("Mots-cles principaux")
        st.write(", ".join(terms[:20]) if terms else "Non disponible")

        syntheses = ART.get("syntheses", {})
        synthese = syntheses.get(str(selected_cluster), syntheses.get(selected_cluster, ""))
        if synthese:
            st.write("Synthese")
            st.info(synthese)


if page == "Carte temporelle des incidents":
    st.header("Carte temporelle des incidents")
    st.write(
        "Cette vue montre l'evolution des rapports dans le temps et la repartition "
        "annuelle des principales anomalies."
    )

    d = df.dropna(subset=["datetime"]).copy()
    if d.empty:
        st.warning("Aucune date exploitable dans les artefacts.")
        st.stop()

    d["month"] = d["datetime"].dt.to_period("M").dt.to_timestamp()
    d["year"] = d["datetime"].dt.year

    monthly = d.groupby("month").size().reset_index(name="rapports")
    fig_volume = go.Figure()
    fig_volume.add_trace(
        go.Scatter(
            x=monthly["month"],
            y=monthly["rapports"],
            mode="lines",
            fill="tozeroy",
            name="Rapports",
            line=dict(width=2),
        )
    )
    fig_volume.update_layout(
        title="Volume mensuel des incidents",
        xaxis_title="Mois",
        yaxis_title="Nombre de rapports",
        height=360,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig_volume, use_container_width=True)

    top_anomalies = d["anomaly"].astype(str).value_counts().head(12).index
    heat_df = d[d["anomaly"].astype(str).isin(top_anomalies)].copy()
    heat_df["anomaly_short"] = heat_df["anomaly"].astype(str).str.slice(0, 55)
    heat_counts = (
        heat_df.groupby(["anomaly_short", "year"])
        .size()
        .reset_index(name="rapports")
    )

    pivot = heat_counts.pivot_table(
        index="anomaly_short",
        columns="year",
        values="rapports",
        aggfunc="sum",
        fill_value=0,
    )

    fig_heatmap = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Carte temporelle des principales anomalies",
        labels={
            "x": "Annee",
            "y": "Anomalie",
            "color": "Rapports",
        },
    )
    fig_heatmap.update_layout(height=560, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_heatmap, use_container_width=True)
