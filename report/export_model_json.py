"""Exporte le classifieur linéaire (TF-IDF + LogReg) en JSON pour une prédiction
100% navigateur (aucun backend). -> frontend/public/data/model.json"""
import os, json, warnings
warnings.filterwarnings("ignore")
import numpy as np, joblib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = joblib.load(os.path.join(ROOT, "data", "processed", "models", "models.joblib"))
tfidf, clf = m["tfidf"], m["clf"]

vocab = {t: int(i) for t, i in tfidf.vocabulary_.items()}
idf = [round(float(x), 5) for x in tfidf.idf_]
coef = [[round(float(x), 4) for x in row] for row in clf.coef_]
out = {
    "classes": list(clf.classes_),
    "vocab": vocab,
    "idf": idf,
    "coef": coef,
    "intercept": [round(float(x), 4) for x in clf.intercept_],
    "sublinear": bool(getattr(tfidf, "sublinear_tf", False)),
    "ngram_max": tfidf.ngram_range[1],
}
path = os.path.join(ROOT, "frontend", "public", "data", "model.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("model.json :", round(os.path.getsize(path) / 1024), "Ko |",
      len(vocab), "termes |", len(out["classes"]), "classes")
