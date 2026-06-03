"""
Prétraitement des rapports d'incidents NASA ASRS.

Ce module gère :
  - le chargement robuste du CSV ASRS (double ligne d'en-tête caractéristique) ;
  - le repérage automatique des colonnes clés par mots-clés (le libellé exact
    varie selon les exports) ;
  - le parsing des dates au format ASRS (YYYYMM / YYYYMMDD) ;
  - le nettoyage des artefacts de désidentification (ZZZ, tokens masqués, etc.) ;
  - la tokenisation / suppression des stopwords / lemmatisation (NLTK).

Utilisé à la fois par le notebook d'analyse et par le dashboard Streamlit.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
#  Ressources NLTK
# --------------------------------------------------------------------------- #


def ensure_nltk() -> None:
    """Télécharge (si besoin) les ressources NLTK utilisées par le pipeline."""
    import nltk

    ressources = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
    ]
    for chemin, paquet in ressources:
        try:
            nltk.data.find(chemin)
        except LookupError:
            nltk.download(paquet, quiet=True)


# --------------------------------------------------------------------------- #
#  Stopwords métier aviation (à faible valeur discriminante)
# --------------------------------------------------------------------------- #
# Ces termes sont omniprésents dans les rapports ASRS et noient le signal
# thématique. Ils sont retirés EN PLUS des stopwords anglais standards.
AVIATION_STOPWORDS = {
    "aircraft", "flight", "plane", "airplane", "pilot", "crew", "captain",
    "first", "officer", "fo", "ca", "report", "reported", "reporter",
    "would", "could", "also", "due", "us", "got", "get", "around",
    "approximately", "about", "time", "back", "told", "said", "called",
    "ft", "feet", "kt", "kts", "knot", "knots", "nm",
}

# Tokens de désidentification ASRS à supprimer purement et simplement.
DEID_TOKENS = {
    "zzz", "zzzz", "zzzzz", "xxx", "xxxx", "abc", "xyz",
    "aaa", "bbb", "ccc", "ddd",
}

_RE_BRACKET = re.compile(r"\[[^\]]*\]")          # [masqué]
_RE_NONALPHA = re.compile(r"[^a-z\s]")           # tout sauf lettres/espaces
_RE_MULTISPACE = re.compile(r"\s+")
_RE_REPEAT_CAP = re.compile(r"\b[A-Z]{2,}\b")    # ZZZ, XXX en majuscules


# --------------------------------------------------------------------------- #
#  Chargement du CSV ASRS (double en-tête)
# --------------------------------------------------------------------------- #


def _flatten_columns(cols: pd.MultiIndex) -> list[str]:
    """Aplatit un MultiIndex de colonnes ASRS en noms lisibles.

    Les exports ASRS ont 2 lignes d'en-tête : une catégorie large (ex.
    "Aircraft 1") et un sous-champ (ex. "Flight Phase"). pandas remplit les
    cellules fusionnées par "Unnamed: x_level_0" qu'on ignore.
    """
    noms = []
    for niveau0, niveau1 in cols:
        parts = []
        for p in (niveau0, niveau1):
            p = str(p).strip()
            if p and not p.lower().startswith("unnamed"):
                parts.append(p)
        nom = " ".join(parts) if parts else "col"
        noms.append(nom)
    # Dédoublonnage (suffixe numérique si collision)
    vus: dict[str, int] = {}
    finals = []
    for n in noms:
        if n in vus:
            vus[n] += 1
            finals.append(f"{n} {vus[n]}")
        else:
            vus[n] = 0
            finals.append(n)
    return finals


def load_asrs_csv(path: str) -> pd.DataFrame:
    """Charge un export ASRS en gérant le double en-tête.

    Tente d'abord une lecture à double en-tête ; si une seule ligne d'en-tête
    est détectée (autre source / fichier déjà nettoyé), bascule en lecture
    simple.
    """
    # Tentative double en-tête
    try:
        df = pd.read_csv(path, header=[0, 1], dtype=str, encoding="utf-8",
                         on_bad_lines="skip", low_memory=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = _flatten_columns(df.columns)
        return df
    except Exception:
        pass
    # Repli : en-tête simple
    df = pd.read_csv(path, dtype=str, encoding="utf-8",
                     on_bad_lines="skip", low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def find_column(df: pd.DataFrame, *keywords: str) -> str | None:
    """Renvoie le 1er nom de colonne contenant TOUS les mots-clés (insensible
    à la casse). Permet d'adapter le pipeline aux variations de libellés."""
    kws = [k.lower() for k in keywords]
    for col in df.columns:
        cl = str(col).lower()
        if all(k in cl for k in kws):
            return col
    return None


# Mapping canonique -> liste de jeux de mots-clés (premier trouvé = retenu).
CANONICAL_FIELDS: dict[str, list[tuple[str, ...]]] = {
    "narrative_1": [("narrative",)],
    "narrative_2": [("narrative", "2"), ("report", "2", "narrative")],
    "synopsis": [("synopsis",)],
    "date": [("date",), ("time", "date")],
    "anomaly": [("anomaly",)],
    "flight_phase": [("flight", "phase"), ("phase",)],
    "aircraft": [("make", "model"), ("aircraft", "make")],
    "weather": [("flight", "conditions"), ("weather",)],
    "detector": [("detector",), ("detected",)],
    "contributing": [("contributing",)],
    "primary_problem": [("primary", "problem"),],
}


def map_canonical(df: pd.DataFrame) -> dict[str, str]:
    """Construit le dictionnaire {champ_canonique: nom_colonne_réel}."""
    mapping: dict[str, str] = {}
    for canon, jeux in CANONICAL_FIELDS.items():
        for kws in jeux:
            col = find_column(df, *kws)
            if col is not None:
                mapping[canon] = col
                break
    return mapping


# --------------------------------------------------------------------------- #
#  Dates
# --------------------------------------------------------------------------- #


def parse_asrs_date(series: pd.Series) -> pd.Series:
    """Parse la date ASRS (souvent 'YYYYMM' ou 'YYYYMMDD') -> datetime."""
    s = series.astype(str).str.replace(r"\D", "", regex=True)

    def _one(v: str):
        if not v or v == "nan":
            return pd.NaT
        if len(v) >= 8:
            return pd.to_datetime(v[:8], format="%Y%m%d", errors="coerce")
        if len(v) >= 6:
            return pd.to_datetime(v[:6] + "01", format="%Y%m%d", errors="coerce")
        if len(v) == 4:
            return pd.to_datetime(v + "0101", format="%Y%m%d", errors="coerce")
        return pd.NaT

    return s.map(_one)


# --------------------------------------------------------------------------- #
#  Nettoyage texte
# --------------------------------------------------------------------------- #


def clean_text(text: str) -> str:
    """Nettoyage 'léger' destiné à l'affichage et à la vectorisation TF-IDF.

    - retire les artefacts de désidentification ([..], ZZZ, XXX) ;
    - minuscule, ne garde que les lettres ;
    - supprime les tokens de désidentification connus.
    """
    if not isinstance(text, str) or not text.strip():
        return ""
    t = _RE_BRACKET.sub(" ", text)
    t = _RE_REPEAT_CAP.sub(" ", t)          # retire ZZZ/XXX en majuscules
    t = t.lower()
    t = _RE_NONALPHA.sub(" ", t)
    tokens = [w for w in t.split() if w not in DEID_TOKENS and len(w) > 2]
    return _RE_MULTISPACE.sub(" ", " ".join(tokens)).strip()


_RE_REPEAT_LOWER = re.compile(r"\b(?:zzz+|xxx+)\b", re.IGNORECASE)
_RE_MULTISPACE_PUNCT = re.compile(r"\s+([.,;:!?])")


def light_clean(text: str) -> str:
    """Nettoyage 'léger' préservant les phrases naturelles, pour les embeddings.

    Contrairement à ``clean_text`` (sac-de-mots pour TF-IDF/LDA), on garde la
    ponctuation, la casse et l'ordre des mots — ce qui convient mieux aux
    modèles de phrases (sentence-transformers). On retire seulement les
    artefacts de désidentification (ZZZ/XXX, [masqué]) qui n'apportent rien.
    """
    if not isinstance(text, str) or not text.strip():
        return ""
    t = _RE_BRACKET.sub(" ", text)
    t = _RE_REPEAT_CAP.sub(" ", t)
    t = _RE_REPEAT_LOWER.sub(" ", t)
    t = _RE_MULTISPACE.sub(" ", t)
    t = _RE_MULTISPACE_PUNCT.sub(r"\1", t)
    return t.strip()


@lru_cache(maxsize=1)
def _lemmatizer():
    from nltk.stem import WordNetLemmatizer
    return WordNetLemmatizer()


@lru_cache(maxsize=1)
def _stopwords() -> frozenset[str]:
    from nltk.corpus import stopwords
    return frozenset(stopwords.words("english")) | AVIATION_STOPWORDS | DEID_TOKENS


def tokenize_lemmatize(text: str, extra_stopwords: Iterable[str] | None = None) -> list[str]:
    """Tokenise, retire stopwords (anglais + métier) et lemmatise."""
    from nltk.tokenize import word_tokenize

    stop = _stopwords()
    if extra_stopwords:
        stop = stop | frozenset(extra_stopwords)
    lemm = _lemmatizer()
    cleaned = clean_text(text)
    tokens = word_tokenize(cleaned)
    return [lemm.lemmatize(tok) for tok in tokens if tok not in stop and len(tok) > 2]


def preprocess_corpus(texts: Iterable[str],
                      extra_stopwords: Iterable[str] | None = None,
                      progress: bool = True
                      ) -> tuple[list[str], list[list[str]]]:
    """Prétraite un corpus (tokenisation + stopwords + lemmatisation).

    Retourne (textes_nettoyés_joints, listes_de_tokens) — le premier sert à
    TF-IDF/LDA, le second à gensim (cohérence). Affiche une barre de progression
    (utile sur de gros corpus comme les 125k rapports ASRS).
    """
    ensure_nltk()
    texts = list(texts)
    it = texts
    if progress:
        try:
            from tqdm.auto import tqdm
            it = tqdm(texts, desc="Prétraitement NLP", unit="doc")
        except Exception:
            pass
    token_lists = [tokenize_lemmatize(t, extra_stopwords) for t in it]
    joined = [" ".join(toks) for toks in token_lists]
    return joined, token_lists


def build_unified_text(df: pd.DataFrame, mapping: dict[str, str]) -> pd.Series:
    """Concatène Narrative 1 + Narrative 2 (texte brut) pour chaque rapport."""
    parts = []
    for canon in ("narrative_1", "narrative_2"):
        col = mapping.get(canon)
        if col is not None:
            parts.append(df[col].fillna("").astype(str))
    if not parts:
        # repli sur le synopsis si aucune narrative
        col = mapping.get("synopsis")
        if col is not None:
            parts.append(df[col].fillna("").astype(str))
    if not parts:
        return pd.Series([""] * len(df), index=df.index)
    out = parts[0]
    for p in parts[1:]:
        out = out.str.cat(p, sep=" ")
    return out.str.strip()
