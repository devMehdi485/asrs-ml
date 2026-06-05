"""
AeroInsight AI — Dashboard d'analyse des incidents de sécurité aérienne (NASA ASRS).

Design "AeroInsight AI" (thème sombre aviation-intelligence) reproduit dans Streamlit,
inspiré de la maquette Figma Make du même nom : thème slate/navy, accents cyan,
police Inter, cartes KPI, 6 pages.

Lancement :  streamlit run dashboard/app.py
Le dashboard recharge les artefacts produits par le notebook / quick_results
(data/processed/). Exécutez d'abord l'analyse.
"""
from __future__ import annotations

import os
import json
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from wordcloud import WordCloud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")

st.set_page_config(page_title="AeroInsight AI — ASRS", page_icon="✈️",
                   layout="wide", initial_sidebar_state="expanded")

# --------------------------------------------------------------------------- #
#  Design system "AeroInsight AI"
# --------------------------------------------------------------------------- #
BG = "#0B1120"; SURFACE = "#0F1B2E"; SURFACE2 = "#16243B"; BORDER = "#22344c"
TEXT = "#E6EDF6"; MUTED = "#8aa0b8"; ACCENT = "#22D3EE"; ACCENT2 = "#3B82F6"
UP = "#34D399"; DOWN = "#FB7185"; WARN = "#FBBF24"
# palette catégorielle (clusters) lisible sur fond sombre
PALETTE = (px.colors.qualitative.Bold + px.colors.qualitative.Vivid +
           px.colors.qualitative.Pastel + px.colors.qualitative.Set3)

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; }}
.stApp {{
  background:
    radial-gradient(900px 500px at 85% -5%, rgba(34,211,238,.10), transparent 60%),
    radial-gradient(800px 500px at 0% 0%, rgba(59,130,246,.10), transparent 55%),
    {BG};
  color: {TEXT};
}}
#MainMenu, footer, header [data-testid="stToolbar"] {{ visibility: hidden; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1500px; }}

/* Sidebar */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #081020 0%, #0a1730 100%);
  border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] * {{ color: {TEXT}; }}
.brand {{ display:flex; align-items:center; gap:.6rem; padding:.4rem .2rem 1rem; }}
.brand .logo {{
  width:38px; height:38px; border-radius:11px; display:grid; place-items:center;
  font-size:20px; background:linear-gradient(135deg,{ACCENT},{ACCENT2});
  box-shadow:0 6px 18px rgba(34,211,238,.35);
}}
.brand .name {{ font-weight:800; font-size:1.15rem; letter-spacing:.2px; }}
.brand .sub {{ font-size:.7rem; color:{MUTED}; margin-top:-2px; }}

/* Titres de section */
h1, h2, h3 {{ color:{TEXT}; font-weight:700; letter-spacing:.2px; }}
.page-title {{ font-size:1.7rem; font-weight:800; margin:.2rem 0 .1rem; }}
.page-sub {{ color:{MUTED}; margin-bottom:1.2rem; font-size:.95rem; }}
.sec {{ font-size:1.05rem; font-weight:700; margin:1.4rem 0 .6rem;
        padding-left:.6rem; border-left:3px solid {ACCENT}; }}

/* Cartes KPI */
.kpi {{
  background: linear-gradient(160deg, {SURFACE2}, {SURFACE});
  border:1px solid {BORDER}; border-radius:16px; padding:1.05rem 1.2rem;
  box-shadow:0 8px 24px rgba(0,0,0,.25); height:100%;
}}
.kpi .ico {{ font-size:1.1rem; opacity:.9; }}
.kpi .lab {{ color:{MUTED}; font-size:.78rem; text-transform:uppercase;
            letter-spacing:.6px; margin-top:.3rem; }}
.kpi .val {{ font-size:1.8rem; font-weight:800; margin-top:.1rem;
            background:linear-gradient(135deg,{TEXT},{ACCENT});
            -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.kpi .dl {{ font-size:.8rem; margin-top:.25rem; font-weight:600; }}

/* Cartes génériques / thèmes */
.card {{
  background:{SURFACE}; border:1px solid {BORDER}; border-radius:14px;
  padding:1rem 1.1rem; margin-bottom:.8rem;
}}
.card .t {{ font-weight:700; color:{TEXT}; }}
.card .m {{ color:{MUTED}; font-size:.85rem; margin-top:.2rem; }}
.chip {{ display:inline-block; padding:.12rem .55rem; border-radius:999px;
         font-size:.72rem; font-weight:600; background:rgba(34,211,238,.14);
         color:{ACCENT}; border:1px solid rgba(34,211,238,.3); margin-right:.3rem;}}
.up {{ color:{UP}; }} .down {{ color:{DOWN}; }} .flat {{ color:{MUTED}; }}

/* Widgets */
[data-testid="stMetric"] {{ background:{SURFACE}; border:1px solid {BORDER};
  border-radius:14px; padding:.8rem 1rem; }}
[data-baseweb="select"] > div {{ background:{SURFACE2}; border-color:{BORDER}; }}
.stDataFrame {{ border:1px solid {BORDER}; border-radius:12px; }}
div.stButton > button {{ background:{SURFACE2}; color:{TEXT}; border:1px solid {BORDER};
  border-radius:10px; }}
hr {{ border-color:{BORDER}; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def plotly_dark(fig, height=None, legend=True):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="Inter", size=12),
        margin=dict(l=10, r=10, t=40, b=10),
        colorway=PALETTE,
        title_font=dict(size=15, color=TEXT),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    )
    fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER)
    fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER)
    if height:
        fig.update_layout(height=height)
    if not legend:
        fig.update_layout(showlegend=False)
    return fig


def kpi_card(label, value, icon="", delta=None, delta_cls="flat"):
    dl = f'<div class="dl {delta_cls}">{delta}</div>' if delta else ""
    return (f'<div class="kpi"><div class="ico">{icon}</div>'
            f'<div class="lab">{label}</div><div class="val">{value}</div>{dl}</div>')


# --------------------------------------------------------------------------- #
#  Chargement des artefacts
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def load_artifacts():
    df = pd.read_parquet(os.path.join(PROC, "reports_clean.parquet"))
    with open(os.path.join(PROC, "artefacts.json"), encoding="utf-8") as f:
        art = json.load(f)
    iso = np.load(os.path.join(PROC, "iso_scores.npy"))
    causes = pd.read_csv(os.path.join(PROC, "causes_recurrentes.csv"))
    df["iso_score"] = iso
    df["score_atypicite"] = (iso - iso.min()) / (np.ptp(iso) + 1e-9)
    df["cluster"] = df["cluster"].astype(int)
    return df, art, causes


if not os.path.exists(os.path.join(PROC, "artefacts.json")):
    st.markdown(CSS, unsafe_allow_html=True)
    st.error("Artefacts introuvables dans `data/processed/`.\n\n"
             "Lance d'abord l'analyse (notebook `asrs_nlp_analysis.ipynb` ou "
             "`python notebooks_assets/quick_results.py`).")
    st.stop()

df, ART, CAUSES = load_artifacts()
CLUSTERS = sorted(df["cluster"].unique())
SIZES = df[df["cluster"] != -1]["cluster"].value_counts()
TERMS = {int(k): v for k, v in ART["terms_par_cluster"].items()}
LABELS = {int(k): v for k, v in ART["labels"].items()}
SYNTH = {int(k): v for k, v in ART["syntheses"].items()}
REPS = {int(k): v for k, v in ART.get("reps", {}).items()}
TRENDS = {int(k): v for k, v in ART.get("trends", {}).items()}
N_THEMES = len([c for c in CLUSTERS if c != -1])


def cluster_name(c):
    return LABELS.get(c, {}).get("label_court", f"Cluster {c}")


def trend_cls(t):
    return "up" if "hausse" in t else "down" if "baisse" in t else "flat"


def make_wordcloud_fig(terms):
    freq = {t: (len(terms) - i) for i, t in enumerate(terms)}
    wc = WordCloud(width=700, height=340, background_color=SURFACE,
                   colormap="cool", prefer_horizontal=0.95).generate_from_frequencies(freq)
    fig, ax = plt.subplots(figsize=(7, 3.4)); fig.patch.set_facecolor(SURFACE)
    ax.imshow(wc); ax.axis("off")
    return fig


# --------------------------------------------------------------------------- #
#  Sidebar / navigation
# --------------------------------------------------------------------------- #
st.sidebar.markdown(
    '<div class="brand"><div class="logo">✈</div>'
    '<div><div class="name">AeroInsight AI</div>'
    '<div class="sub">NASA ASRS · Safety Intelligence</div></div></div>',
    unsafe_allow_html=True)

PAGES = ["Executive Intelligence", "Operational Dashboard", "Cluster Explorer",
         "Thematic Analysis", "Temporal Heatmap", "Weak Signals"]
ICONS = ["📊", "🧭", "🧩", "🗂️", "🔥", "⚠️"]
page = st.sidebar.radio("Navigation",
                        [f"{i}  {p}" for i, p in zip(ICONS, PAGES)],
                        label_visibility="collapsed")
page = page[3:].strip()

st.sidebar.markdown("---")
st.sidebar.markdown(
    f'<div style="font-size:.78rem;color:{MUTED};line-height:1.7">'
    f'<b style="color:{TEXT}">{len(df):,}</b> rapports analysés<br>'
    f'<b style="color:{TEXT}">{N_THEMES}</b> thèmes détectés<br>'
    f'Modèle : <b style="color:{ACCENT}">{ART.get("modele_clustering","?")}</b><br>'
    f'Embeddings : {ART.get("methode_embeddings","?").split("/")[-1]}</div>'.replace(",", " "),
    unsafe_allow_html=True)


def page_header(title, subtitle):
    st.markdown(f'<div class="page-title">{title}</div>'
                f'<div class="page-sub">{subtitle}</div>', unsafe_allow_html=True)


def kpi_row(cards):
    cols = st.columns(len(cards))
    for col, c in zip(cols, cards):
        col.markdown(kpi_card(**c), unsafe_allow_html=True)


# =========================================================================== #
#  1. EXECUTIVE INTELLIGENCE
# =========================================================================== #
if page == "Executive Intelligence":
    page_header("Executive Intelligence",
                "Synthèse stratégique auto-générée des risques de sécurité aérienne")

    periode = (f"{df['datetime'].min():%Y} – {df['datetime'].max():%Y}"
               if df["datetime"].notna().any() else "n/d")
    n_signaux = int((df["score_atypicite"] > 0.6).sum())
    hausse = [c for c, t in TRENDS.items() if "hausse" in t]
    kpi_row([
        dict(label="Rapports analysés", value=f"{len(df):,}".replace(",", " "), icon="🛩️"),
        dict(label="Thèmes d'incidents", value=N_THEMES, icon="🧩"),
        dict(label="Période couverte", value=periode, icon="🗓️"),
        dict(label="Signaux faibles", value=n_signaux, icon="⚠️", delta_cls="down"),
        dict(label="Thèmes en hausse", value=len(hausse), icon="📈", delta_cls="up"),
    ])

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown('<div class="sec">Clusters les plus importants</div>', unsafe_allow_html=True)
        top = CAUSES.head(6)
        fig = px.bar(top[::-1], x="nb_rapports", y="label", orientation="h",
                     color="nb_rapports", color_continuous_scale=["#1e3a5f", ACCENT],
                     text="part_%")
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="rapports")
        st.plotly_chart(plotly_dark(fig, height=330, legend=False), width="stretch")
    with c2:
        st.markdown('<div class="sec">Tendances marquantes</div>', unsafe_allow_html=True)
        baisse = [c for c, t in TRENDS.items() if "baisse" in t]
        for c in (hausse[:4] + baisse[:2]):
            t = TRENDS[c]
            st.markdown(f'<div class="card"><span class="chip">#{c}</span>'
                        f'<span class="t">{cluster_name(c)}</span>'
                        f'<div class="m {trend_cls(t)}">{t}</div></div>',
                        unsafe_allow_html=True)

    st.markdown('<div class="sec">Signaux faibles les plus notables</div>', unsafe_allow_html=True)
    for _, r in df.sort_values("score_atypicite", ascending=False).head(3).iterrows():
        st.markdown(f'<div class="card"><span class="chip">atypicité '
                    f'{r["score_atypicite"]:.2f}</span> '
                    f'<span class="m">{str(r["text_raw"])[:240]}…</span></div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="sec">Principales causes récurrentes</div>', unsafe_allow_html=True)
    st.dataframe(CAUSES, width="stretch", hide_index=True)


# =========================================================================== #
#  2. OPERATIONAL DASHBOARD
# =========================================================================== #
elif page == "Operational Dashboard":
    page_header("Operational Dashboard", "Vue d'ensemble opérationnelle et filtres")

    with st.sidebar:
        st.markdown("### Filtres")
        anoms = ["(toutes)"] + sorted(df["anomaly"].dropna().astype(str).unique())
        sa = st.selectbox("Anomalie", anoms)
        if "flight_phase" in df.columns:
            phs = ["(toutes)"] + sorted(df["flight_phase"].dropna().astype(str).unique())
            sp = st.selectbox("Phase de vol", phs)
        else:
            sp = "(toutes)"
    d = df.copy()
    if sa != "(toutes)": d = d[d["anomaly"].astype(str) == sa]
    if sp != "(toutes)" and "flight_phase" in d.columns:
        d = d[d["flight_phase"].astype(str) == sp]

    kpi_row([
        dict(label="Rapports (filtrés)", value=f"{len(d):,}".replace(",", " "), icon="🛩️"),
        dict(label="Anomalies distinctes", value=int(d["anomaly"].nunique()), icon="🏷️"),
        dict(label="Clusters représentés", value=int(d["cluster"].nunique()), icon="🧩"),
        dict(label="% du corpus", value=f"{100*len(d)/len(df):.1f}%", icon="📦"),
    ])

    c1, c2 = st.columns(2)
    with c1:
        ta = d["anomaly"].astype(str).value_counts().head(12).reset_index()
        ta.columns = ["anomaly", "nb"]
        fig = px.bar(ta[::-1], x="nb", y="anomaly", orientation="h",
                     color="nb", color_continuous_scale=["#1e3a5f", ACCENT])
        fig.update_layout(coloraxis_showscale=False, yaxis_title="", title="Top anomalies")
        st.plotly_chart(plotly_dark(fig, height=420, legend=False), width="stretch")
    with c2:
        if "flight_phase" in d.columns:
            tp = d["flight_phase"].astype(str).value_counts().head(10).reset_index()
            tp.columns = ["phase", "nb"]
            fig = px.bar(tp[::-1], x="nb", y="phase", orientation="h",
                         color="nb", color_continuous_scale=["#3a1e5f", ACCENT2])
            fig.update_layout(coloraxis_showscale=False, yaxis_title="", title="Phases de vol")
            st.plotly_chart(plotly_dark(fig, height=420, legend=False), width="stretch")

    st.markdown('<div class="sec">Répartition par thème (top 25)</div>', unsafe_allow_html=True)
    rep = d[d["cluster"] != -1]["cluster"].value_counts().head(25).reset_index()
    rep.columns = ["cluster", "nb"]; rep["label"] = rep["cluster"].map(cluster_name)
    fig = px.bar(rep, x="label", y="nb", color="nb",
                 color_continuous_scale=["#1e3a5f", ACCENT])
    fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="rapports")
    st.plotly_chart(plotly_dark(fig, height=380, legend=False), width="stretch")


# =========================================================================== #
#  3. CLUSTER EXPLORER
# =========================================================================== #
elif page == "Cluster Explorer":
    page_header("Cluster Explorer", "Exploration interactive des thèmes d'incidents")

    d = df[(df["cluster"] != -1) & df["x"].notna()].copy()
    d["label"] = d["cluster"].map(cluster_name)
    if len(d) > 25000:
        d = d.sample(25000, random_state=42)
    # n'afficher que les plus gros clusters dans la légende pour la lisibilité
    big = SIZES.head(20).index
    d["grp"] = np.where(d["cluster"].isin(big), d["cluster"].astype(str), "autres")
    fig = px.scatter(d, x="x", y="y", color="grp", hover_data=["anomaly", "label"],
                     opacity=0.7)
    fig.update_traces(marker=dict(size=5))
    st.plotly_chart(plotly_dark(fig, height=520), width="stretch")

    st.markdown('<div class="sec">Inspecter un thème</div>', unsafe_allow_html=True)
    order = list(SIZES.index)
    sel = st.selectbox("Thème", order,
                       format_func=lambda c: f"#{c} · {cluster_name(c)} ({SIZES.get(c,0)} rapports)")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.pyplot(make_wordcloud_fig(TERMS[sel]))
    with c2:
        st.markdown(f'<div class="card"><div class="t">Synthèse métier</div>'
                    f'<div class="m">{SYNTH.get(sel,"")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card"><div class="t">Tendance</div>'
                    f'<div class="m {trend_cls(TRENDS.get(sel,""))}">{TRENDS.get(sel,"n/d")}</div></div>',
                    unsafe_allow_html=True)
        st.markdown('<div>' + ''.join(f'<span class="chip">{t}</span>'
                    for t in TERMS[sel][:8]) + '</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec">Narratives représentatives</div>', unsafe_allow_html=True)
    for i, txt in enumerate(REPS.get(sel, []), 1):
        st.markdown(f'<div class="card"><span class="chip">{i}</span>'
                    f'<span class="m">{txt}…</span></div>', unsafe_allow_html=True)


# =========================================================================== #
#  4. THEMATIC ANALYSIS
# =========================================================================== #
elif page == "Thematic Analysis":
    page_header("Thematic Analysis", "Cartographie thématique et causes récurrentes")

    kpi_row([
        dict(label="Thèmes", value=N_THEMES, icon="🗂️"),
        dict(label="Modèle retenu", value=ART.get("modele_clustering", "?"), icon="🧠"),
        dict(label="Plus gros thème",
             value=f"{CAUSES.iloc[0]['part_%']}%", icon="🥇"),
    ])
    st.markdown(f'<div class="card"><div class="t">Justification du modèle</div>'
                f'<div class="m">{ART.get("justification","")}</div></div>',
                unsafe_allow_html=True)

    st.markdown('<div class="sec">Toutes les causes récurrentes</div>', unsafe_allow_html=True)
    st.dataframe(CAUSES, width="stretch", hide_index=True, height=420)

    st.markdown('<div class="sec">Mots-clés saillants par thème (top 16)</div>',
                unsafe_allow_html=True)
    cols = st.columns(2)
    for i, c in enumerate(list(SIZES.head(16).index)):
        with cols[i % 2]:
            st.markdown(f'<div class="card"><span class="chip">#{c}</span>'
                        f'<span class="t">{SIZES.get(c,0)} rapports</span><div style="margin-top:.4rem">'
                        + ''.join(f'<span class="chip">{t}</span>' for t in TERMS[c][:7])
                        + '</div></div>', unsafe_allow_html=True)

    lda_path = os.path.join(PROC, "lda_vis.html")
    if os.path.exists(lda_path):
        st.markdown('<div class="sec">Visualisation LDA (pyLDAvis)</div>', unsafe_allow_html=True)
        with open(lda_path, encoding="utf-8") as f:
            components.html(f.read(), height=820, scrolling=True)


# =========================================================================== #
#  5. TEMPORAL HEATMAP
# =========================================================================== #
elif page == "Temporal Heatmap":
    page_header("Temporal Heatmap", "Évolution des incidents dans le temps")
    if df["datetime"].isna().all():
        st.warning("Aucune date exploitable."); st.stop()
    d = df.dropna(subset=["datetime"]).copy()
    d["periode"] = d["datetime"].dt.to_period("M").dt.to_timestamp()

    vol = d.groupby("periode").size().reset_index(name="nb")
    mu, sd = vol["nb"].mean(), vol["nb"].std(ddof=0)
    vol["pic"] = (vol["nb"] - mu) / (sd + 1e-9) >= 2
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=vol["periode"], y=vol["nb"], mode="lines",
                  line=dict(color=ACCENT, width=2), fill="tozeroy",
                  fillcolor="rgba(34,211,238,.12)", name="volume"))
    pk = vol[vol["pic"]]
    fig.add_trace(go.Scatter(x=pk["periode"], y=pk["nb"], mode="markers",
                  marker=dict(color=DOWN, size=9), name="pic (z≥2)"))
    fig.update_layout(title="Volume mensuel d'incidents")
    st.plotly_chart(plotly_dark(fig, height=320), width="stretch")

    st.markdown('<div class="sec">Heatmap : anomalie × temps</div>', unsafe_allow_html=True)
    top_a = d["anomaly"].astype(str).value_counts().head(12).index
    dh = d[d["anomaly"].astype(str).isin(top_a)]
    piv = (dh.assign(an=dh["anomaly"].astype(str).str.slice(0, 40))
           .groupby([dh["periode"], "an"]).size().unstack(fill_value=0))
    fig = px.imshow(piv.T, aspect="auto",
                    color_continuous_scale=["#0B1120", ACCENT2, ACCENT],
                    labels=dict(x="période", y="", color="nb"))
    st.plotly_chart(plotly_dark(fig, height=460), width="stretch")

    st.markdown('<div class="sec">Thèmes dans le temps (top 8)</div>', unsafe_allow_html=True)
    big = SIZES.head(8).index
    dt = d[d["cluster"].isin(big)]
    tot = (dt.groupby([dt["periode"], "cluster"]).size().unstack(fill_value=0))
    tot = tot.div(tot.sum(axis=1).clip(lower=1), axis=0)
    tot.columns = [cluster_name(c) for c in tot.columns]
    fig = px.area(tot)
    fig.update_layout(yaxis_title="part", xaxis_title="")
    st.plotly_chart(plotly_dark(fig, height=380), width="stretch")


# =========================================================================== #
#  6. WEAK SIGNALS
# =========================================================================== #
elif page == "Weak Signals":
    page_header("Weak Signals", "Rapports atypiques — précurseurs potentiels")
    seuil = st.slider("Seuil de score d'atypicité", 0.0, 1.0, 0.6, 0.05)
    atyp = df[df["score_atypicite"] >= seuil].sort_values("score_atypicite", ascending=False)
    emergents = ART.get("emergents", [])
    kpi_row([
        dict(label="Au-dessus du seuil", value=len(atyp), icon="⚠️"),
        dict(label="Score max", value=f"{df['score_atypicite'].max():.2f}", icon="🚩"),
        dict(label="Thèmes rares émergents", value=len(emergents), icon="🌱"),
    ])
    if emergents:
        st.markdown('<div>' + ''.join(
            f'<span class="chip">#{c} {cluster_name(c)}</span>' for c in emergents)
            + '</div>', unsafe_allow_html=True)

    fig = px.histogram(df, x="score_atypicite", nbins=40)
    fig.update_traces(marker_color=ACCENT2)
    fig.add_vline(x=seuil, line_dash="dash", line_color=DOWN)
    fig.update_layout(title="Distribution des scores d'atypicité", yaxis_title="rapports")
    st.plotly_chart(plotly_dark(fig, height=300, legend=False), width="stretch")

    st.markdown('<div class="sec">Rapports les plus atypiques</div>', unsafe_allow_html=True)
    show = atyp[["score_atypicite", "cluster", "anomaly", "datetime", "text_raw"]].head(40).copy()
    show["text_raw"] = show["text_raw"].astype(str).str.slice(0, 320)
    st.dataframe(show, width="stretch", hide_index=True,
                 column_config={"score_atypicite": st.column_config.ProgressColumn(
                     "atypicité", min_value=0.0, max_value=1.0)})
