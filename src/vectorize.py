"""
Vectorisation hybride des narratives ASRS.

  - TF-IDF (uni + bigrammes) : représentation creuse, interprétable, utilisée
    pour la classification supervisée et la labellisation c-TF-IDF des clusters.
  - Embeddings de phrases (sentence-transformers, all-MiniLM-L6-v2) :
    représentation sémantique dense utilisée pour le clustering.
    Fallback automatique vers LSA (TruncatedSVD sur TF-IDF) si
    sentence-transformers / torch ne sont pas installables.
"""
from __future__ import annotations

import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

DEFAULT_MODEL = "all-MiniLM-L6-v2"


# --------------------------------------------------------------------------- #
#  TF-IDF
# --------------------------------------------------------------------------- #


def build_tfidf(texts, max_features: int = 5000, ngram=(1, 2),
                min_df: int = 5, max_df: float = 0.6):
    """Construit la matrice TF-IDF. Retourne (vectorizer, matrice creuse)."""
    vec = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram,
        min_df=min_df,
        max_df=max_df,
        sublinear_tf=True,
    )
    X = vec.fit_transform(texts)
    return vec, X


# --------------------------------------------------------------------------- #
#  Embeddings de phrases (avec fallback)
# --------------------------------------------------------------------------- #


def embeddings_available() -> bool:
    """Indique si sentence-transformers est utilisable."""
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


def detect_device() -> str:
    """Renvoie 'cuda' si un GPU est disponible, sinon 'cpu'."""
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def build_sentence_embeddings(texts, model_name: str = DEFAULT_MODEL,
                              batch_size: int | None = None,
                              cache_path: str | None = None,
                              device: str | None = None):
    """Calcule des embeddings de phrases ; met en cache (.npy) si demandé.

    - Utilise automatiquement le **GPU** (CUDA) s'il est disponible.
    - Le cache n'est réutilisé que si sa taille correspond au corpus courant
      (sinon il est recalculé) — évite d'utiliser un cache périmé.

    Lève ImportError si sentence-transformers est absent — l'appelant doit
    alors basculer sur ``build_lsa_embeddings``.
    """
    texts = list(texts)
    # Cache valide uniquement si le nombre de lignes correspond
    if cache_path and os.path.exists(cache_path):
        cached = np.load(cache_path)
        if cached.shape[0] == len(texts):
            print(f"[vectorize] Embeddings rechargés du cache ({cached.shape}).")
            return cached
        print(f"[vectorize] Cache périmé ({cached.shape[0]} ≠ {len(texts)}) -> recalcul.")

    from sentence_transformers import SentenceTransformer

    dev = device or detect_device()
    if batch_size is None:
        batch_size = 256 if dev == "cuda" else 64
    print(f"[vectorize] Encodage de {len(texts)} textes sur {dev.upper()} "
          f"(batch={batch_size})…")
    model = SentenceTransformer(model_name, device=dev)
    emb = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")
    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        np.save(cache_path, emb)
    return emb


def build_lsa_embeddings(tfidf_matrix, n_components: int = 100, seed: int = 42):
    """Fallback 'classique' : embeddings denses via LSA (TruncatedSVD)."""
    n_components = min(n_components, tfidf_matrix.shape[1] - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=seed)
    reduced = svd.fit_transform(tfidf_matrix)
    return normalize(reduced)


def get_document_embeddings(texts, tfidf_matrix, cache_path: str | None = None,
                            model_name: str = DEFAULT_MODEL):
    """Stratégie hybride : embeddings de phrases si possible, sinon LSA.

    Retourne (embeddings, méthode_str).
    """
    if embeddings_available():
        try:
            emb = build_sentence_embeddings(texts, model_name=model_name,
                                            cache_path=cache_path)
            return emb, f"sentence-transformers/{model_name}"
        except Exception as exc:  # pragma: no cover - dépend de l'install
            print(f"[vectorize] sentence-transformers a échoué ({exc}); "
                  f"repli sur LSA.")
    emb = build_lsa_embeddings(tfidf_matrix)
    return emb, "LSA (TruncatedSVD)"
