"""
Génère le notebook d'analyse `asrs_nlp_analysis.ipynb` via nbformat.

Construire le notebook par programme garantit un JSON valide et reproductible.
Relancer ce script régénère le notebook (cellules non exécutées).
"""
import os
import nbformat as nbf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "asrs_nlp_analysis.ipynb")

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip("\n")))


# ----------------------------------------------------------------------------- #
md(r"""
# Analyse NLP des rapports d'incidents de sécurité aérienne — NASA ASRS

**NLP · Classification de texte · Clustering thématique · Détection de signaux faibles · Analyse temporelle**

Ce notebook met en œuvre un pipeline complet d'analyse des narratives textuelles
désidentifiées de la base **Aviation Safety Reporting System (ASRS)** de la NASA :

1. Chargement & prétraitement NLP des rapports
2. Analyse exploratoire (EDA)
3. Vectorisation hybride (TF-IDF + embeddings de phrases)
4. Clustering thématique **cohérent et interprétable** (K-Means vs HDBSCAN)
5. Interprétation : c-TF-IDF, labellisation automatique, synthèses métier
6. Classification supervisée (Logistic Regression, SVM)
7. Analyse temporelle de l'évolution des incidents
8. Détection de signaux faibles (rapports atypiques précurseurs)
9. Synthèse & tableau des causes récurrentes

> Les modèles et artefacts entraînés ici sont **sérialisés dans `data/processed/`**
> et rechargés par le dashboard Streamlit (`dashboard/app.py`).
""")

md(r"""
## 0. Configuration & dépendances

Les bibliothèques sont listées dans `requirements.txt`. Le pipeline est **hybride**
et **robuste** : si une dépendance moderne (sentence-transformers, hdbscan, gensim)
n'est pas installable, un repli est utilisé automatiquement (voir messages affichés).
""")

code(r"""
import os, sys, warnings, json
warnings.filterwarnings("ignore")

# Rendre le package src/ importable
sys.path.insert(0, os.path.abspath("."))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 5)

from src import preprocessing as P
from src import vectorize as V
from src import clustering as C
from src import temporal as T
from src import anomalies as A

RANDOM_STATE = 42
PROC_DIR = "data/processed"
MODEL_DIR = os.path.join(PROC_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Sélection automatique du dataset (par ordre de préférence) :
#   1. dataset complet Kaggle (2002-2025, ~125k)  2. export officiel  3. synthétique
CANDIDATS = ["data/ASRS_FULL_DATASET.csv", "data/ASRS_DBOnline.csv", "data/ASRS_export.csv"]
DATA_CSV = next((p for p in CANDIDATS if os.path.exists(p)), "data/ASRS_export.csv")

# Nb max de points projetés en 2D pour la visualisation (le scatter de 125k
# points serait illisible et lent ; on échantillonne pour l'affichage).
N_VIZ = 25000

# Granularité du clustering (réglable) :
#  - N_CLUSTERS    : nb de thèmes pour K-Means (granularité métier visée)
#  - MIN_CLUSTER_SIZE : taille mini d'un cluster HDBSCAN (~0.1 % du corpus).
# IMPORTANT : ne PAS faire dépendre min_cluster_size de len(df)//50, sinon sur
# 125k il vaut ~2500 et HDBSCAN s'effondre en 2 clusters.
N_CLUSTERS = 15
MIN_CLUSTER_SIZE = 150

# GPU si disponible (accélère fortement les embeddings)
print("Device embeddings :", V.detect_device().upper())
print("Dataset sélectionné :", DATA_CSV)
print("Environnement prêt.")
""")

md(r"""
## 1. Chargement des données

Les exports ASRS possèdent une **double ligne d'en-tête** (catégorie + sous-champ).
La fonction `load_asrs_csv` la gère et aplatit les noms de colonnes ; `map_canonical`
repère ensuite les champs clés par mots-clés (les libellés exacts varient selon
les exports).

> **Pas encore de données ?** Si `data/ASRS_export.csv` est absent, on génère un
> jeu **synthétique** au format ASRS pour développer/valider le pipeline. Remplacez
> ce fichier par l'export réel (voir `README.md`) puis ré-exécutez le notebook.
""")

code(r"""
if not os.path.exists(DATA_CSV):
    print("Aucun CSV ASRS trouvé -> génération d'un jeu synthétique de démonstration.")
    from src import synthetic
    synthetic.generate(DATA_CSV)

print("Chargement de", DATA_CSV, "...")
df = P.load_asrs_csv(DATA_CSV)
mapping = P.map_canonical(df)
print("Dimensions :", df.shape)
print("\nColonnes détectées :"); print(list(df.columns))
print("\nMapping canonique :");
for k, v in mapping.items(): print(f"  {k:16s} -> {v}")
df.head(3)
""")

md(r"""
### Inspection : valeurs manquantes & aperçu des narratives
""")

code(r"""
taux_na = (df.isna().mean() * 100).round(1).sort_values(ascending=False)
print("Taux de valeurs manquantes (%):\n", taux_na.to_string())
print("\nExemple de narrative :\n", df[mapping["narrative_1"]].dropna().iloc[0][:500])
""")

md(r"""
## 2. Prétraitement NLP

- Construction d'un **texte unifié** = Narrative 1 + Narrative 2.
- Parsing de la **date** ASRS (format `YYYYMM`/`YYYYMMDD`) → base de l'analyse temporelle.
- Nettoyage des **artefacts de désidentification** (`ZZZ`, `[masqué]`, `XXX`…).
- Tokenisation, suppression des **stopwords** (anglais + métier aviation), **lemmatisation**.
""")

code(r"""
PRE_CACHE = os.path.join(PROC_DIR, "reports_pre.parquet")
CANON = ["text_raw", "text_light", "text_clean", "datetime", "annee",
         "anomaly", "flight_phase", "aircraft"]

if os.path.exists(PRE_CACHE):
    df = pd.read_parquet(PRE_CACHE)
    print("Prétraitement rechargé du cache :", df.shape)
else:
    df["text_raw"] = P.build_unified_text(df, mapping)
    df["datetime"] = P.parse_asrs_date(df[mapping["date"]])
    df["annee"] = df["datetime"].dt.year
    # Renommer les métadonnées en noms CANONIQUES (stables pour la suite)
    ren = {mapping["anomaly"]: "anomaly"}
    if "flight_phase" in mapping: ren[mapping["flight_phase"]] = "flight_phase"
    if "aircraft" in mapping:     ren[mapping["aircraft"]] = "aircraft"
    df = df.rename(columns=ren)
    df = df[df["text_raw"].str.len() > 20].reset_index(drop=True)

    # Deux versions du texte :
    #  - text_light : phrases naturelles nettoyées (désid.) -> EMBEDDINGS
    #  - text_clean : sac-de-mots lemmatisé sans stopwords  -> TF-IDF / LDA
    df["text_light"] = df["text_raw"].map(P.light_clean)
    texts_clean, _ = P.preprocess_corpus(df["text_raw"])
    df["text_clean"] = texts_clean
    df["text_raw"] = df["text_raw"].str.slice(0, 2000)   # borne la taille du cache
    df = df[[c for c in CANON if c in df.columns]]
    df.to_parquet(PRE_CACHE)
    print("Prétraitement calculé & mis en cache :", df.shape)

# À partir d'ici, le mapping est l'IDENTITÉ sur les noms canoniques.
mapping = {"anomaly": "anomaly"}
for c in ("flight_phase", "aircraft"):
    if c in df.columns: mapping[c] = c
# token_lists reconstruits depuis text_clean (déjà lemmatisé, espace-séparé)
token_lists = [t.split() for t in df["text_clean"]]
print("Rapports retenus :", len(df))
print("Light :", str(df['text_light'].iloc[0])[:150])
print("Clean :", str(df['text_clean'].iloc[0])[:150])
""")

md(r"""
## 3. Analyse exploratoire (EDA)

Distribution des anomalies / phases de vol, longueur des narratives, et nuage de
mots global.
""")

code(r"""
fig, axes = plt.subplots(1, 2, figsize=(16, 5))
df[mapping["anomaly"]].value_counts().head(12).plot.barh(ax=axes[0], color="steelblue")
axes[0].set_title("Top 12 des anomalies déclarées"); axes[0].invert_yaxis()
if "flight_phase" in mapping:
    df[mapping["flight_phase"]].value_counts().head(10).plot.barh(ax=axes[1], color="indianred")
    axes[1].set_title("Phases de vol"); axes[1].invert_yaxis()
plt.tight_layout(); plt.show()
""")

code(r"""
from wordcloud import WordCloud
wc = WordCloud(width=1000, height=400, background_color="white", colormap="viridis")
wc.generate(" ".join(df["text_clean"]))
plt.figure(figsize=(14, 5)); plt.imshow(wc); plt.axis("off")
plt.title("Nuage de mots global (narratives nettoyées)"); plt.show()
""")

md(r"""
## 4. Vectorisation hybride

- **TF-IDF** (uni + bigrammes) → interprétabilité + classification supervisée.
- **Embeddings de phrases** (`all-MiniLM-L6-v2`) → représentation sémantique pour
  le clustering. Fallback automatique vers LSA si indisponible.
""")

code(r"""
tfidf_vec, X_tfidf = V.build_tfidf(df["text_clean"], min_df=5)
print("Matrice TF-IDF :", X_tfidf.shape)

# Embeddings calculés sur le texte NATUREL (text_light) -> meilleure sémantique.
# Sur GPU, ~1-2 min pour 125k ; sur CPU, beaucoup plus long (cache .npy ensuite).
embeddings, methode_emb = V.get_document_embeddings(
    df["text_light"].tolist(), X_tfidf,
    cache_path=os.path.join(PROC_DIR, "embeddings.npy"))
print("Embeddings :", embeddings.shape, "| méthode :", methode_emb)
""")

md(r"""
## 5. Clustering thématique : cohérence & interprétabilité

### 5.1 Réduction de dimension + entraînement K-Means et HDBSCAN

On réduit les embeddings (UMAP, fallback PCA) puis on entraîne **les deux** modèles
sur les **mêmes données** pour une comparaison équitable.
""")

code(r"""
# Réduction UMAP mise en cache (coûteuse sur 125k) : rechargée si la taille colle.
RED_CACHE = os.path.join(PROC_DIR, "reduced.npy")
if os.path.exists(RED_CACHE) and np.load(RED_CACHE, mmap_mode="r").shape[0] == len(df):
    X_red = np.load(RED_CACHE); methode_red = "UMAP (cache)"
else:
    X_red, reducer, methode_red = C.reduce_dimensions(embeddings, n_components=5,
                                                      seed=RANDOM_STATE)
    np.save(RED_CACHE, X_red)
print("Réduction :", methode_red, X_red.shape)

# Méthode du coude + silhouette (transparence). NB : sur des embeddings
# sémantiques, la silhouette favorise mécaniquement très peu de clusters ; pour
# une analyse THÉMATIQUE on vise une granularité métier (N_CLUSTERS), choix
# documenté plutôt que l'argmax silhouette (qui donnerait k≈2-3).
elbow = C.choose_k_elbow(X_red, k_range=range(2, 25), seed=RANDOM_STATE)
fig, ax = plt.subplots(1, 2, figsize=(14, 4))
ax[0].plot(elbow["k"], elbow["inertie"], "o-"); ax[0].set_title("Méthode du coude (inertie)")
ax[1].plot(elbow["k"], elbow["silhouette"], "o-", color="green"); ax[1].set_title("Silhouette vs k")
for a in ax: a.set_xlabel("k"); a.axvline(N_CLUSTERS, ls="--", c="red", alpha=.5)
plt.tight_layout(); plt.show()

best_k = N_CLUSTERS
print(f"k retenu pour K-Means : {best_k} (granularité thématique visée). "
      f"Silhouette à ce k : {float(elbow.loc[elbow['k']==best_k,'silhouette'].iloc[0]):.3f}")
""")

code(r"""
km_model, labels_km = C.cluster_kmeans(X_red, best_k, seed=RANDOM_STATE)

if C.hdbscan_available():
    hdb_model, labels_hdb = C.cluster_hdbscan(X_red, min_cluster_size=MIN_CLUSTER_SIZE,
                                              min_samples=10)
    resultats = {"KMeans": labels_km, "HDBSCAN": labels_hdb}
else:
    print("hdbscan indisponible -> K-Means uniquement.")
    hdb_model, labels_hdb = None, None
    resultats = {"KMeans": labels_km}
""")

md(r"""
### 5.2 Comparaison explicite K-Means vs HDBSCAN

Tableau de métriques de cohérence sur les **mêmes données réduites**, plus le
recoupement avec le champ métier `Anomaly` (ARI, pureté). Une **règle de décision
explicite** sélectionne le modèle final.
""")

code(r"""
truth = df[mapping["anomaly"]].astype(str).values
comparaison = C.compare_models(X_red, resultats, truth=truth)
display(comparaison)

best_name, justification = C.select_best_model(comparaison)
print("\n>>> Modèle retenu :", best_name)
print(">>> Justification :", justification)

labels = resultats[best_name]
df["cluster"] = labels
""")

md(r"""
**Lecture du tableau** — critères d'évaluation :

- **Silhouette** (↑ meilleur), **Davies-Bouldin** (↓ meilleur), **Calinski-Harabasz**
  (↑ meilleur) mesurent la *cohérence géométrique* des clusters.
- **ARI / pureté vs anomalie** mesurent l'*alignement métier* avec les catégories
  d'anomalies codées par les analystes ASRS.
- **Taux de bruit** (HDBSCAN) : les points non assignés alimentent la détection de
  signaux faibles (§8).

La règle de décision privilégie la silhouette, en retenant HDBSCAN lorsque son bruit
reste exploitable, sinon K-Means pour des clusters plus équilibrés et lisibles.
""")

md(r"""
### 5.3 Interprétation : c-TF-IDF, labels automatiques, exemples & synthèses métier

Pour chaque cluster : termes saillants (**c-TF-IDF**), **label** court + en langage
naturel, **narratives représentatives** (analyse qualitative, pas seulement des
métriques) et **synthèse métier**.
""")

code(r"""
terms_par_cluster = C.c_tfidf_terms(df["text_clean"].values, labels, top_n=12)
labels_dict = C.auto_label(terms_par_cluster)
reps = C.representative_docs(embeddings, labels, df["text_raw"].values, n=3)
syntheses = C.business_summary(df, labels, mapping, terms_par_cluster)

for c in sorted(terms_par_cluster):
    print("="*90)
    print(f"CLUSTER {c}  |  {labels_dict[c]['label_court']}")
    print("Synthèse métier :", syntheses[c])
    print("Exemple représentatif :", reps[c][0][:240], "...")
""")

md(r"""
### 5.4 Visualisation 2D des clusters + nuages de mots par cluster
""")

code(r"""
# Projection 2D sur un ÉCHANTILLON (un scatter de 125k points serait illisible
# et lent ; UMAP 2D est aussi coûteux). On stocke x,y pour l'échantillon, NaN sinon.
rng = np.random.default_rng(RANDOM_STATE)
viz_idx = (np.sort(rng.choice(len(df), N_VIZ, replace=False))
           if len(df) > N_VIZ else np.arange(len(df)))
coords = C.umap_2d(embeddings[viz_idx], seed=RANDOM_STATE)
df["x"] = np.nan; df["y"] = np.nan
df.iloc[viz_idx, df.columns.get_loc("x")] = coords[:, 0]
df.iloc[viz_idx, df.columns.get_loc("y")] = coords[:, 1]
print(f"Projection 2D calculée sur {len(viz_idx)} points (sur {len(df)}).")

dv = df.iloc[viz_idx]
lv = np.asarray(labels)[viz_idx]
plt.figure(figsize=(11, 8))
mask = lv != -1
sns.scatterplot(x=dv["x"][mask], y=dv["y"][mask], hue=lv[mask],
                palette="tab20", s=8, legend="brief")
if (~mask).any():
    plt.scatter(dv["x"][~mask], dv["y"][~mask], c="lightgray", s=5, label="bruit")
plt.title("Projection 2D des rapports colorés par cluster (échantillon)")
plt.legend(bbox_to_anchor=(1.02, 1), fontsize=7, ncol=2)
plt.tight_layout(); plt.show()
""")

code(r"""
from wordcloud import WordCloud
clusters = sorted(terms_par_cluster)
n = len(clusters); cols = 3; rows = (n + cols - 1)//cols
fig, axes = plt.subplots(rows, cols, figsize=(16, 4*rows))
for ax, c in zip(np.array(axes).ravel(), clusters):
    freq = {t: (len(terms_par_cluster[c]) - i) for i, t in enumerate(terms_par_cluster[c])}
    wc = WordCloud(width=400, height=250, background_color="white").generate_from_frequencies(freq)
    ax.imshow(wc); ax.axis("off"); ax.set_title(f"Cluster {c}")
for ax in np.array(axes).ravel()[n:]: ax.axis("off")
plt.suptitle("Nuages de mots par cluster (termes c-TF-IDF)"); plt.tight_layout(); plt.show()
""")

md(r"""
### 5.5 LDA & cohérence thématique (vue probabiliste complémentaire)

LDA fournit une vue thème→termes probabiliste. On mesure la **cohérence c_v**
(gensim) pour évaluer l'interprétabilité des thèmes.
""")

code(r"""
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

cv = CountVectorizer(max_features=3000, min_df=5, max_df=0.5, ngram_range=(1,1))
X_counts = cv.fit_transform(df["text_clean"])
vocab = cv.get_feature_names_out()

n_topics = best_k
lda = LatentDirichletAllocation(n_components=n_topics, random_state=RANDOM_STATE,
                                learning_method="batch", max_iter=20)
lda.fit(X_counts)

def top_words(model, feat, n=10):
    return [[feat[i] for i in topic.argsort()[::-1][:n]] for topic in model.components_]

topics_words = top_words(lda, vocab, 10)
for i, w in enumerate(topics_words):
    print(f"Thème LDA {i}: {', '.join(w)}")
""")

code(r"""
# Cohérence c_v via gensim (fallback : message si indisponible)
try:
    from gensim.corpora import Dictionary
    from gensim.models import CoherenceModel
    dic = Dictionary(token_lists)
    cm = CoherenceModel(topics=topics_words, texts=token_lists,
                        dictionary=dic, coherence="c_v")
    print(f"Cohérence c_v moyenne du modèle LDA : {cm.get_coherence():.4f}")
except Exception as e:
    print("Cohérence gensim indisponible :", e)
""")

code(r"""
# Visualisation pyLDAvis (sauvegardée en HTML). Sur un échantillon de documents
# pour rester rapide/léger en mémoire à grande échelle (le modèle LDA est inchangé).
try:
    import pyLDAvis, pyLDAvis.lda_model
    n_vis = min(20000, X_counts.shape[0])
    sub = rng.choice(X_counts.shape[0], n_vis, replace=False) if X_counts.shape[0] > n_vis else slice(None)
    vis = pyLDAvis.lda_model.prepare(lda, X_counts[sub], cv, mds="tsne")
    pyLDAvis.save_html(vis, os.path.join(PROC_DIR, "lda_vis.html"))
    print(f"Visualisation LDA sauvegardée (sur {n_vis} docs) : data/processed/lda_vis.html")
except Exception as e:
    print("pyLDAvis indisponible :", e)
""")

md(r"""
## 6. Classification supervisée des types d'incidents

**Cible** : le champ `Anomaly` (multi-valué, séparé par `;`). On le simplifie en
gardant la **catégorie principale** et en se restreignant aux **top-K classes** les
plus fréquentes pour un problème mono-label exploitable. On compare **Logistic
Regression** et **SVM linéaire** sur TF-IDF.
""")

code(r"""
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, confusion_matrix, f1_score

# Catégorie d'anomalie principale (avant le premier ';') puis top-K
anomaly_primary = df[mapping["anomaly"]].astype(str).str.split(";").str[0].str.strip()
topK = anomaly_primary.value_counts().head(8).index
mask_sup = anomaly_primary.isin(topK)
y = anomaly_primary[mask_sup]
X_sup = X_tfidf[mask_sup.values]
print("Échantillon supervisé :", X_sup.shape, "| classes :", y.nunique())
print(y.value_counts())

X_tr, X_te, y_tr, y_te = train_test_split(X_sup, y, test_size=0.25,
                                          stratify=y, random_state=RANDOM_STATE)
""")

code(r"""
modeles = {
    "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
    "SVM linéaire": LinearSVC(class_weight="balanced"),
}
for nom, clf in modeles.items():
    clf.fit(X_tr, y_tr)
    pred = clf.predict(X_te)
    print("="*70); print(nom)
    print(f"F1 macro = {f1_score(y_te, pred, average='macro'):.3f} | "
          f"F1 pondéré = {f1_score(y_te, pred, average='weighted'):.3f}")
    print(classification_report(y_te, pred, zero_division=0))
""")

code(r"""
# Matrice de confusion du meilleur modèle (Logistic Regression par défaut)
clf = modeles["Logistic Regression"]
pred = clf.predict(X_te)
cm = confusion_matrix(y_te, pred, labels=clf.classes_)
plt.figure(figsize=(9, 7))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=[c[:18] for c in clf.classes_],
            yticklabels=[c[:18] for c in clf.classes_])
plt.title("Matrice de confusion — Logistic Regression")
plt.ylabel("Vérité"); plt.xlabel("Prédiction"); plt.xticks(rotation=45, ha="right")
plt.tight_layout(); plt.show()
""")

md(r"""
## 7. Analyse temporelle de l'évolution des incidents

Volume mensuel, heatmap anomalie × temps, et **topics-over-time** pour repérer les
thèmes émergents. Détection des pics par z-score.
""")

code(r"""
vol = T.monthly_volume(df)
plt.figure(figsize=(13, 4))
plt.plot(vol["periode_ts"], vol["nb"], marker="o", ms=3)
peaks = T.detect_peaks(vol.set_index("periode_ts")["nb"])
pk = peaks[peaks["pic"]]
plt.scatter(pk.index, pk["valeur"], color="red", zorder=5, label="pic (z≥2)")
plt.title("Volume mensuel d'incidents"); plt.legend(); plt.tight_layout(); plt.show()
""")

code(r"""
heat = T.category_time_heatmap(df, mapping["anomaly"], top=10)
plt.figure(figsize=(14, 6))
sns.heatmap(heat.T, cmap="rocket_r", cbar_kws={"label": "nb rapports"})
plt.title("Heatmap : type d'anomalie × temps"); plt.xlabel("période"); plt.tight_layout(); plt.show()
""")

code(r"""
tot = T.topics_over_time(df, "cluster", normalize=True)
tot.columns = [f"Cluster {c}" for c in tot.columns]
plt.figure(figsize=(13, 5))
for col in tot.columns:
    plt.plot(tot.index, tot[col], label=col)
plt.title("Part de chaque cluster dans le temps (topics-over-time)")
plt.legend(bbox_to_anchor=(1.02, 1), fontsize=8); plt.tight_layout(); plt.show()

trends = T.cluster_trends(df, "cluster", "datetime")
print("Tendances par cluster :")
for c, t in sorted(trends.items()): print(f"  Cluster {c}: {t}")
""")

md(r"""
## 8. Détection de signaux faibles (rapports atypiques)

Combinaison de l'**Isolation Forest** (atypicité globale), du **bruit HDBSCAN** et
de la **distance au centroïde**. Croisement avec les **thèmes rares mais émergents**.
""")

code(r"""
iso_model, iso_scores = A.isolation_forest_scores(X_red, contamination=0.05,
                                                  seed=RANDOM_STATE)
cdist = A.centroid_distance(X_red, labels)
weak = A.weak_signals_table(df, iso_scores, cdist, labels, "text_raw",
                            top=20, trends=trends)
emergents = A.emerging_rare_themes(df, "cluster", trends)
print("Thèmes rares ET émergents (signaux faibles thématiques) :", emergents)
weak.head(10)[["score_atypicite", "bruit_hdbscan", "cluster", "narrative"]]
""")

md(r"""
## 9. Synthèse : tableau des principales causes récurrentes

Tableau récapitulatif trié par importance (taille du cluster), avec label, anomalie
et phase dominantes, et tendance temporelle. Sérialisé pour le dashboard.
""")

code(r"""
table_causes = C.recurring_causes_table(df, labels, mapping, labels_dict, trends)
display(table_causes)
""")

md(r"""
## 10. Sérialisation des artefacts pour le dashboard

On sauvegarde le DataFrame enrichi, les coordonnées 2D, les labels/termes/synthèses,
le tableau des causes et les modèles, pour un chargement instantané dans Streamlit.
""")

code(r"""
import joblib

# DataFrame enrichi (colonnes utiles au dashboard)
cols_keep = ["text_raw", "datetime", "annee", "cluster", "x", "y",
             mapping["anomaly"]]
if "flight_phase" in mapping: cols_keep.append(mapping["flight_phase"])
if "aircraft" in mapping: cols_keep.append(mapping["aircraft"])
df_out = df[cols_keep].rename(columns={
    mapping["anomaly"]: "anomaly",
    mapping.get("flight_phase", "flight_phase"): "flight_phase",
    mapping.get("aircraft", "aircraft"): "aircraft",
}).copy()
# Tronquer les narratives stockées (le dashboard n'affiche que des extraits) :
# évite un parquet de plusieurs centaines de Mo à 125k rapports.
df_out["text_raw"] = df_out["text_raw"].astype(str).str.slice(0, 1500)
df_out.to_parquet(os.path.join(PROC_DIR, "reports_clean.parquet"))

# Scores d'atypicité par rapport (aligné sur df)
np.save(os.path.join(PROC_DIR, "iso_scores.npy"), iso_scores)

# Artefacts d'interprétation (JSON)
artefacts = {
    "methode_embeddings": methode_emb,
    "methode_reduction": methode_red,
    "modele_clustering": best_name,
    "justification": justification,
    "terms_par_cluster": {str(k): v for k, v in terms_par_cluster.items()},
    "labels": {str(k): v for k, v in labels_dict.items()},
    "syntheses": {str(k): v for k, v in syntheses.items()},
    "reps": {str(k): v for k, v in reps.items()},
    "trends": {str(k): v for k, v in trends.items()},
    "emergents": emergents,
    "comparaison": comparaison.reset_index().to_dict(orient="records"),
}
with open(os.path.join(PROC_DIR, "artefacts.json"), "w", encoding="utf-8") as f:
    json.dump(artefacts, f, ensure_ascii=False, indent=2, default=str)

table_causes.to_csv(os.path.join(PROC_DIR, "causes_recurrentes.csv"), index=False)
joblib.dump({"tfidf": tfidf_vec, "lda": lda, "count_vec": cv,
             "clf": modeles["Logistic Regression"]},
            os.path.join(MODEL_DIR, "models.joblib"))
print("Artefacts sauvegardés dans", PROC_DIR)
""")

md(r"""
## 11. Conclusion — lecture face aux critères d'évaluation

**Cohérence des clusters.** Comparaison explicite K-Means vs HDBSCAN (silhouette,
Davies-Bouldin, Calinski-Harabasz, ARI/pureté), choix du modèle justifié par une
règle de décision, et validation **qualitative** via les narratives représentatives.

**Interprétabilité thématique.** Termes c-TF-IDF + labels (court & langage naturel),
synthèses métier par cluster, vue LDA probabiliste avec **cohérence c_v** et pyLDAvis,
et **tableau des causes récurrentes**.

**Dimension temporelle.** Volume mensuel + détection de pics, heatmap anomalie×temps,
topics-over-time révélant les thèmes en hausse/baisse.

**Signaux faibles.** Isolation Forest + bruit HDBSCAN + distance au centroïde, croisés
avec les thèmes rares mais émergents.

**Qualité du dashboard.** Tous les artefacts ci-dessus alimentent le dashboard
Streamlit (`streamlit run dashboard/app.py`), dont la page *Executive Summary*.

**Limites.** Désidentification (perte d'information), déséquilibre des classes
d'anomalies, biais de déclaration volontaire. **Pistes.** Embeddings de domaine
aéronautique, classification multi-label, modélisation de séquences temporelles.
""")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
with open(OUT, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print("Notebook généré :", OUT, "| cellules :", len(cells))
