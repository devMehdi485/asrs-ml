"""Démo concrète du MODÈLE supervisé : un récit d'incident -> type prédit."""
import os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import joblib
from src import preprocessing as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = joblib.load(os.path.join(ROOT, "data", "processed", "models", "models.joblib"))
tfidf, clf = m["tfidf"], m["clf"]
P.ensure_nltk()

EXEMPLES = [
    "While taxiing for departure we crossed the hold short line and entered the "
    "active runway without a clearance from the tower.",
    "During cruise we observed a rapid loss of oil pressure on the number two "
    "engine, ran the checklist, shut it down and declared an emergency.",
    "The autopilot did not capture our assigned altitude and we overshot by 400 "
    "feet before correcting; ATC issued a traffic alert.",
    "We encountered severe turbulence in convective weather; two flight "
    "attendants were injured during the cabin service.",
    "On final approach a drone passed very close to the cockpit at about 1200 feet.",
]

print("=" * 78)
print("MODÈLE SUPERVISÉ — prédiction du type d'incident à partir du texte")
print("Classes connues :", ", ".join(clf.classes_))
print("=" * 78)
for txt in EXEMPLES:
    clean = " ".join(P.tokenize_lemmatize(txt))
    X = tfidf.transform([clean])
    pred = clf.predict(X)[0]
    proba = clf.predict_proba(X)[0]
    top = sorted(zip(clf.classes_, proba), key=lambda t: -t[1])[:3]
    print("\n📝", txt[:90], "…")
    print("  →  PRÉDICTION :", pred)
    print("     top-3 :", " | ".join(f"{c} {p:.0%}" for c, p in top))
