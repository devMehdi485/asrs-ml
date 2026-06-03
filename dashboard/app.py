"""
Dashboard interactif — Analyse NLP des rapports d'incidents NASA ASRS.

Lancement :  streamlit run dashboard/app.py

Le dashboard NE réentraîne RIEN : il charge les artefacts produits par le notebook
`asrs_nlp_analysis.ipynb` dans `data/processed/`. Exécutez d'abord le notebook.

Pages :
  1. Executive Summary  — synthèse auto-générée (thèmes, clusters, tendances, signaux)
  2. Vue d'ensemble      — KPIs + filtres
  3. Clusters & thèmes   — projection 2D, nuage de mots par cluster, exemples
  4. Temporel            — volume, heatmap anomalie×temps, topics-over-time
  5. Signaux faibles     — rapports atypiques triés
"""
from __future__ import annotations

import os
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")

st.set_page_config(page_title="ASRS — Analyse NLP des incidents",
                   page_icon="✈️", layout="wide")


# --------------------------------------------------------------------------- #
#  Chargement des artefacts (mis en cache)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def load_artifacts():
    df = pd.read_parquet(os.path.join(PROC, "reports_clean.parquet"))
    with open(os.path.join(PROC, "artefacts.json"), encoding="utf-8") as f:
        art = json.load(f)
    iso = np.load(os.path.join(PROC, "iso_scores.npy"))
    causes = pd.read_csv(os.path.join(PROC, "causes_recurrentes.csv"))
    df["iso_score"] = iso
    # normalisation pour lisibilité
    df["score_atypicite"] = (iso - iso.min()) / (np.ptp(iso) + 1e-9)
    df["cluster"] = df["cluster"].astype(int)
    return df, art, causes


def artifacts_present() -> bool:
    return os.path.exists(os.path.join(PROC, "artefacts.json"))


if not artifacts_present():
    st.error("Artefacts introuvables dans `data/processed/`.\n\n"
             "Exécutez d'abord le notebook **asrs_nlp_analysis.ipynb** "
             "(il génère les fichiers nécessaires au dashboard).")
    st.stop()

df, ART, CAUSES = load_artifacts()
CLUSTERS = sorted(df["cluster"].unique())
TERMS = {int(k): v for k, v in ART["terms_par_cluster"].items()}
LABELS = {int(k): v for k, v in ART["labels"].items()}
SYNTH = {int(k): v for k, v in ART["syntheses"].items()}
REPS = {int(k): v for k, v in ART.get("reps", {}).items()}
TRENDS = {int(k): v for k, v in ART.get("trends", {}).items()}


def cluster_name(c: int) -> str:
    return LABELS.get(c, {}).get("label_court", f"Cluster {c}")


def make_wordcloud_fig(terms: list[str]):
    freq = {t: (len(terms) - i) for i, t in enumerate(terms)}
    wc = WordCloud(width=640, height=320, background_color="white",
                   colormap="viridis").generate_from_frequencies(freq)
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ax.imshow(wc); ax.axis("off")
    return fig


# --------------------------------------------------------------------------- #
#  Navigation
# --------------------------------------------------------------------------- #
st.sidebar.title("✈️ ASRS NLP")
st.sidebar.caption("Analyse des rapports d'incidents de sécurité aérienne")
page = st.sidebar.radio(
    "Navigation",
    ["📌 Executive Summary", "📊 Vue d'ensemble", "🧩 Clusters & thèmes",
     "📈 Temporel", "⚠️ Signaux faibles"],
)
st.sidebar.markdown("---")
st.sidebar.caption(
    f"Embeddings : {ART.get('methode_embeddings','?')}\n\n"
    f"Réduction : {ART.get('methode_reduction','?')}\n\n"
    f"Clustering : **{ART.get('modele_clustering','?')}**")


# =========================================================================== #
#  PAGE 1 — EXECUTIVE SUMMARY (auto-généré)
# =========================================================================== #
if page.startswith("📌"):
    st.title("📌 Executive Summary")
    st.caption("Synthèse générée automatiquement à partir des analyses du notebook.")

    periode = ""
    if df["datetime"].notna().any():
        periode = (f"{df['datetime'].min():%Y-%m} → {df['datetime'].max():%Y-%m}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rapports analysés", f"{len(df):,}".replace(",", " "))
    c2.metric("Thèmes / clusters", len([c for c in CLUSTERS if c != -1]))
    c3.metric("Période couverte", periode or "n/d")
    n_signaux = int((df["score_atypicite"] > 0.6).sum())
    c4.metric("Signaux faibles", n_signaux)

    st.markdown("---")

    colA, colB = st.columns(2)

    with colA:
        st.subheader("🏆 Clusters les plus importants")
        top_causes = CAUSES.head(5)
        for _, r in top_causes.iterrows():
            st.markdown(
                f"**Cluster {int(r['cluster'])} — {r['label']}**  \n"
                f"{r['part_%']} % du corpus · anomalie : *{r['anomalie_dominante']}* · "
                f"phase : *{r['phase_dominante']}* · {r['tendance']}")

    with colB:
        st.subheader("🔑 Principaux thèmes détectés")
        for c in CLUSTERS:
            if c == -1:
                continue
            st.markdown(f"**{cluster_name(c)}** — {LABELS.get(c, {}).get('label_nl','')}")

    st.markdown("---")
    colC, colD = st.columns(2)

    with colC:
        st.subheader("📈 Tendances temporelles marquantes")
        hausse = [c for c, t in TRENDS.items() if "hausse" in t]
        baisse = [c for c, t in TRENDS.items() if "baisse" in t]
        if hausse:
            st.markdown("**En hausse :**")
            for c in hausse:
                st.markdown(f"- Cluster {c} ({cluster_name(c)}) — {TRENDS[c]}")
        if baisse:
            st.markdown("**En baisse :**")
            for c in baisse:
                st.markdown(f"- Cluster {c} ({cluster_name(c)}) — {TRENDS[c]}")
        if not hausse and not baisse:
            st.info("Pas de tendance marquée sur la période.")

    with colD:
        st.subheader("⚠️ Signaux faibles les plus intéressants")
        emergents = ART.get("emergents", [])
        if emergents:
            st.markdown("**Thèmes rares mais émergents :** "
                        + ", ".join(f"Cluster {c}" for c in emergents))
        top_signaux = df.sort_values("score_atypicite", ascending=False).head(3)
        for _, r in top_signaux.iterrows():
            st.markdown(f"> *(score {r['score_atypicite']:.2f})* "
                        f"{str(r['text_raw'])[:200]}…")

    st.markdown("---")
    st.subheader("📋 Tableau des principales causes récurrentes")
    st.dataframe(CAUSES, width="stretch", hide_index=True)


# =========================================================================== #
#  PAGE 2 — VUE D'ENSEMBLE
# =========================================================================== #
elif page.startswith("📊"):
    st.title("📊 Vue d'ensemble")

    # Filtres
    with st.sidebar:
        st.markdown("### Filtres")
        anomalies = ["(toutes)"] + sorted(df["anomaly"].dropna().astype(str).unique())
        sel_anom = st.selectbox("Anomalie", anomalies)
        if "flight_phase" in df.columns:
            phases = ["(toutes)"] + sorted(df["flight_phase"].dropna().astype(str).unique())
            sel_phase = st.selectbox("Phase de vol", phases)
        else:
            sel_phase = "(toutes)"

    d = df.copy()
    if sel_anom != "(toutes)":
        d = d[d["anomaly"].astype(str) == sel_anom]
    if sel_phase != "(toutes)" and "flight_phase" in d.columns:
        d = d[d["flight_phase"].astype(str) == sel_phase]

    c1, c2, c3 = st.columns(3)
    c1.metric("Rapports (filtrés)", f"{len(d):,}".replace(",", " "))
    c2.metric("Anomalies distinctes", d["anomaly"].nunique())
    c3.metric("Clusters représentés", d["cluster"].nunique())

    col1, col2 = st.columns(2)
    with col1:
        top_anom = d["anomaly"].astype(str).value_counts().head(12).reset_index()
        top_anom.columns = ["anomaly", "nb"]
        fig = px.bar(top_anom, x="nb", y="anomaly", orientation="h",
                     title="Top anomalies", color="nb", color_continuous_scale="Blues")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        st.plotly_chart(fig, width="stretch")
    with col2:
        if "flight_phase" in d.columns:
            top_phase = d["flight_phase"].astype(str).value_counts().head(10).reset_index()
            top_phase.columns = ["phase", "nb"]
            fig = px.bar(top_phase, x="nb", y="phase", orientation="h",
                         title="Phases de vol", color="nb", color_continuous_scale="Reds")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
            st.plotly_chart(fig, width="stretch")

    st.subheader("Répartition par cluster")
    rep = d["cluster"].value_counts().sort_index().reset_index()
    rep.columns = ["cluster", "nb"]
    rep["label"] = rep["cluster"].map(cluster_name)
    fig = px.bar(rep, x="cluster", y="nb", hover_data=["label"],
                 title="Nombre de rapports par cluster", color="nb",
                 color_continuous_scale="Viridis")
    st.plotly_chart(fig, width="stretch")


# =========================================================================== #
#  PAGE 3 — CLUSTERS & THÈMES
# =========================================================================== #
elif page.startswith("🧩"):
    st.title("🧩 Exploration des clusters & thèmes")

    # Projection 2D (uniquement les points projetés ; échantillon sur gros corpus)
    d = df[(df["cluster"] != -1) & df["x"].notna()].copy()
    d["label"] = d["cluster"].map(cluster_name)
    if len(d) > 30000:                      # bride d'affichage Plotly
        d = d.sample(30000, random_state=42)
    fig = px.scatter(
        d, x="x", y="y", color=d["cluster"].astype(str),
        hover_data={"x": False, "y": False, "anomaly": True, "label": True},
        title="Projection 2D des rapports (couleur = cluster)", opacity=0.7)
    fig.update_traces(marker=dict(size=6))
    fig.update_layout(height=550, legend_title="Cluster")
    st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    sel = st.selectbox("Choisir un cluster à explorer",
                       [c for c in CLUSTERS if c != -1],
                       format_func=lambda c: f"Cluster {c} — {cluster_name(c)}")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Nuage de mots (c-TF-IDF)")
        st.pyplot(make_wordcloud_fig(TERMS[sel]))
    with col2:
        st.subheader("Synthèse métier")
        st.info(SYNTH.get(sel, ""))
        st.markdown(f"**Label (langage naturel)** : {LABELS.get(sel, {}).get('label_nl','')}")
        st.markdown(f"**Tendance temporelle** : {TRENDS.get(sel, 'n/d')}")
        st.markdown("**Termes saillants** : " + ", ".join(TERMS[sel]))

    st.subheader("Narratives représentatives")
    for i, txt in enumerate(REPS.get(sel, []), 1):
        st.markdown(f"**{i}.** {txt}…")


# =========================================================================== #
#  PAGE 4 — TEMPOREL
# =========================================================================== #
elif page.startswith("📈"):
    st.title("📈 Évolution temporelle des incidents")

    if df["datetime"].isna().all():
        st.warning("Aucune date exploitable dans le jeu de données.")
        st.stop()

    d = df.dropna(subset=["datetime"]).copy()
    d["periode"] = d["datetime"].dt.to_period("M").dt.to_timestamp()

    # Volume mensuel + pics
    vol = d.groupby("periode").size().reset_index(name="nb")
    mu, sigma = vol["nb"].mean(), vol["nb"].std(ddof=0)
    vol["pic"] = (vol["nb"] - mu) / (sigma + 1e-9) >= 2
    fig = px.line(vol, x="periode", y="nb", title="Volume mensuel d'incidents",
                  markers=True)
    pk = vol[vol["pic"]]
    if not pk.empty:
        fig.add_scatter(x=pk["periode"], y=pk["nb"], mode="markers",
                        marker=dict(color="red", size=10), name="pic (z≥2)")
    st.plotly_chart(fig, width="stretch")

    # Heatmap anomalie × temps
    st.subheader("Heatmap : type d'anomalie × temps")
    top_anom = d["anomaly"].astype(str).value_counts().head(10).index
    dh = d[d["anomaly"].astype(str).isin(top_anom)]
    pivot = (dh.groupby([dh["periode"], dh["anomaly"].astype(str)])
             .size().unstack(fill_value=0))
    fig = px.imshow(pivot.T, aspect="auto", color_continuous_scale="Reds",
                    labels=dict(x="période", y="anomalie", color="nb"))
    fig.update_layout(height=450)
    st.plotly_chart(fig, width="stretch")

    # Topics over time
    st.subheader("Part de chaque cluster dans le temps")
    dt = d[d["cluster"] != -1]
    tot = (dt.groupby([dt["periode"], dt["cluster"]]).size()
           .unstack(fill_value=0))
    tot = tot.div(tot.sum(axis=1).clip(lower=1), axis=0)
    tot.columns = [f"Cluster {c}" for c in tot.columns]
    fig = px.area(tot, title="Topics-over-time (proportions)")
    fig.update_layout(height=450, legend_title="")
    st.plotly_chart(fig, width="stretch")


# =========================================================================== #
#  PAGE 5 — SIGNAUX FAIBLES
# =========================================================================== #
elif page.startswith("⚠️"):
    st.title("⚠️ Signaux faibles — rapports atypiques")
    st.caption("Rapports les plus éloignés des comportements typiques "
               "(Isolation Forest + distance aux clusters). Candidats précurseurs.")

    seuil = st.slider("Seuil de score d'atypicité", 0.0, 1.0, 0.6, 0.05)
    atyp = df[df["score_atypicite"] >= seuil].sort_values(
        "score_atypicite", ascending=False)

    c1, c2 = st.columns(2)
    c1.metric("Rapports au-dessus du seuil", len(atyp))
    emergents = ART.get("emergents", [])
    c2.metric("Thèmes rares & émergents", len(emergents))
    if emergents:
        st.info("Thèmes rares mais en croissance (signaux faibles thématiques) : "
                + ", ".join(f"Cluster {c} ({cluster_name(c)})" for c in emergents))

    # Distribution des scores
    fig = px.histogram(df, x="score_atypicite", nbins=40,
                       title="Distribution des scores d'atypicité")
    fig.add_vline(x=seuil, line_dash="dash", line_color="red")
    st.plotly_chart(fig, width="stretch")

    st.subheader(f"Top rapports atypiques (n={len(atyp)})")
    show = atyp[["score_atypicite", "cluster", "anomaly", "datetime", "text_raw"]].head(40).copy()
    show["text_raw"] = show["text_raw"].astype(str).str.slice(0, 300)
    st.dataframe(show, width="stretch", hide_index=True,
                 column_config={"score_atypicite": st.column_config.ProgressColumn(
                     "atypicité", min_value=0, max_value=1)})

    with st.expander("🔍 Lire un rapport atypique en entier"):
        if len(atyp):
            idx = st.number_input("Index (0 = plus atypique)", 0, len(atyp)-1, 0)
            row = atyp.iloc[int(idx)]
            st.markdown(f"**Score** {row['score_atypicite']:.3f} · "
                        f"**Cluster** {row['cluster']} · **Anomalie** {row['anomaly']}")
            st.write(str(row["text_raw"]))
