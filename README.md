# Analyse NLP des rapports d'incidents de sécurité aérienne — NASA ASRS

Pipeline complet de **traitement du langage naturel** appliqué aux narratives
textuelles désidentifiées de la base **Aviation Safety Reporting System (ASRS)**
de la NASA. Objectifs : extraire les **causes récurrentes** d'incidents, **classifier**
les types d'incidents, faire émerger des **thématiques** par clustering cohérent et
interprétable, repérer des **signaux faibles** (rapports atypiques précurseurs), et
analyser l'**évolution temporelle** des incidents — le tout exposé dans un
**dashboard interactif**.

---

## 🗂️ Structure du projet

```
ASRS ML/
├── data/
│   ├── ASRS_export.csv          # données brutes (à télécharger — voir ci-dessous)
│   └── processed/               # artefacts générés par le notebook
├── asrs_nlp_analysis.ipynb      # LIVRABLE 1 : analyse & modélisation (FR, pédagogique)
├── dashboard/app.py             # LIVRABLE 2 : dashboard Streamlit (5 pages)
├── src/                         # modules réutilisés par le notebook ET le dashboard
│   ├── preprocessing.py         #   chargement CSV ASRS, nettoyage, tokenisation
│   ├── vectorize.py             #   TF-IDF + embeddings de phrases (fallback LSA)
│   ├── clustering.py            #   K-Means/HDBSCAN, c-TF-IDF, labels, synthèses
│   ├── temporal.py              #   volume, heatmap, topics-over-time, tendances
│   ├── anomalies.py             #   signaux faibles (Isolation Forest, bruit, distance)
│   └── synthetic.py             #   générateur de données de démonstration
├── notebooks_assets/build_notebook.py   # (re)génère le notebook via nbformat
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

```bash
pip install -r requirements.txt
```

> **Python 3.13 / numpy 2.x.** Le pipeline est **robuste** : si `sentence-transformers`,
> `hdbscan` ou `gensim` ne s'installent pas, des replis automatiques prennent le relais
> (LSA à la place des embeddings, K-Means à la place de HDBSCAN). Les messages affichés
> indiquent la méthode réellement utilisée.

L'exécution du notebook nécessite aussi un kernel : `pip install ipykernel`.

---

## 📥 Obtenir le dataset ASRS

La base ASRS n'expose **pas d'API** : l'export se fait manuellement via l'outil de
recherche en ligne. Placez le fichier obtenu dans `data/ASRS_export.csv`.

1. Ouvrir **https://asrs.arc.nasa.gov/search/database.html** → bouton **« Start Search »**.
2. Définir une requête bornée (ex. une plage de dates) pour rester **≤ 10 000 rapports**
   par export (limite NASA).
3. Afficher au minimum les champs : **Narrative (Reporter 1 & 2)**, **Synopsis**,
   **Date**, **Anomaly**, **Flight Phase**, **Aircraft Make/Model**,
   **Flight Conditions/Weather**, **Detector**, **Primary Problem**.
4. Exporter au format **CSV** et enregistrer sous `data/ASRS_export.csv`.

> **Particularité :** les exports ASRS ont une **double ligne d'en-tête**
> (catégorie + sous-champ). Le module `src/preprocessing.py` la gère automatiquement
> et repère les colonnes par mots-clés (les libellés exacts varient selon les exports).

> **Sans données réelles ?** Le notebook génère automatiquement un **jeu synthétique**
> au format ASRS (`src/synthetic.py`) pour développer/valider le pipeline.

### Sélection automatique du dataset

Le notebook choisit le CSV à utiliser dans cet ordre de préférence :

1. `data/ASRS_FULL_DATASET.csv` — dataset complet (ex. Kaggle, ~125 000 rapports, 2002-2025)
2. `data/ASRS_DBOnline.csv` — export officiel via l'outil ASRS
3. `data/ASRS_export.csv` — jeu synthétique de secours

Le premier fichier trouvé est utilisé (variable `DATA_CSV` dans la cellule de configuration).

### ⚡ Performance & GPU (gros dataset)

- Les **embeddings** (`sentence-transformers`) utilisent **automatiquement le GPU**
  (CUDA) s'il est disponible — fortement recommandé pour ~125k rapports
  (quelques minutes sur GPU contre 15-20 min sur CPU). Le résultat est mis en
  **cache** (`data/processed/embeddings.npy`) : les exécutions suivantes sont instantanées.
  Le cache est **invalidé automatiquement** si la taille du corpus change.
- À grande échelle, le pipeline adapte ses calculs : **silhouette échantillonnée**
  (O(n²) sinon), **MiniBatchKMeans** pour le balayage du coude, **projection 2D et
  pyLDAvis sur échantillon** (`N_VIZ`, par défaut 25 000) pour la lisibilité/vitesse.
- Étape la plus longue hors embeddings : **UMAP** (CPU). Compter ~20-40 min au total
  pour un run complet sur 125k (hors cache), bien moins avec le cache d'embeddings.

---

## 🚀 Utilisation

**1. Analyse (notebook)** — entraîne les modèles et sérialise les artefacts dans
`data/processed/` :

```bash
jupyter notebook asrs_nlp_analysis.ipynb        # exécuter toutes les cellules
# ou, en ligne de commande :
jupyter nbconvert --to notebook --execute --inplace asrs_nlp_analysis.ipynb
```

**2. Dashboard** — recharge les artefacts (aucun réentraînement) :

```bash
streamlit run dashboard/app.py
```

Le dashboard comporte **5 pages** : *Executive Summary* (synthèse auto-générée),
*Vue d'ensemble*, *Clusters & thèmes* (projection 2D + nuage de mots par cluster),
*Temporel* (volume, heatmap, topics-over-time), *Signaux faibles*.

---

## 🧪 Méthodologie & critères d'évaluation

| Critère | Mise en œuvre | Métriques |
|---|---|---|
| **Cohérence des clusters** | Comparaison explicite **K-Means vs HDBSCAN** sur embeddings réduits (UMAP) ; règle de décision justifiée ; analyse **qualitative** (narratives représentatives) | silhouette, Davies-Bouldin, Calinski-Harabasz, ARI / pureté vs `Anomaly`, taux de bruit |
| **Interprétabilité thématique** | Termes **c-TF-IDF** par cluster, **labellisation** (court + langage naturel), **synthèses métier**, vue **LDA** + pyLDAvis, **tableau des causes récurrentes** | cohérence **c_v** (gensim), c-TF-IDF |
| **Dimension temporelle** | Volume mensuel, **heatmap** anomalie×temps, **topics-over-time** | détection de pics (z-score), pente de tendance |
| **Signaux faibles** | **Isolation Forest** + bruit HDBSCAN + distance au centroïde ; thèmes rares **émergents** | score d'atypicité, contamination |
| **Classification supervisée** | **Logistic Regression** & **SVM linéaire** sur TF-IDF (cible : anomalie principale, top-K classes) | accuracy, **F1 macro/pondéré**, matrice de confusion |
| **Qualité du dashboard** | Streamlit + Plotly, 5 pages, filtres croisés, page *Executive Summary* auto-générée, artefacts pré-calculés | — |

### Approche NLP hybride

- **TF-IDF** (uni + bigrammes) : interprétable, base de la classification et du c-TF-IDF.
- **Embeddings de phrases** (`all-MiniLM-L6-v2`) : représentation sémantique pour un
  clustering plus cohérent que le sac-de-mots.

---

## ⚠️ Limites

Désidentification (perte d'information contextuelle), déséquilibre des classes
d'anomalies, biais de déclaration volontaire (sous-déclaration de certains incidents).
**Pistes** : embeddings de domaine aéronautique, classification multi-label, modèles
de séquences temporelles.

---

*Données : NASA Aviation Safety Reporting System — https://asrs.arc.nasa.gov/. Rapports
désidentifiés, accès libre.*
