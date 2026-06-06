// Prédiction 100% navigateur : réplique TF-IDF + régression logistique
// à partir de model.json exporté depuis le modèle Python (scikit-learn).

export interface ModelJSON {
  classes: string[];
  vocab: Record<string, number>;
  idf: number[];
  coef: number[][];
  intercept: number[];
  sublinear: boolean;
  ngram_max: number;
}

let MODEL: ModelJSON | null = null;

export async function loadModel(): Promise<ModelJSON> {
  if (MODEL) return MODEL;
  const r = await fetch(`${import.meta.env.BASE_URL}data/model.json?t=${Date.now()}`, { cache: "no-store" });
  MODEL = await r.json();
  return MODEL!;
}

function tokens(text: string): string[] {
  return text.toLowerCase().replace(/[^a-z\s]/g, " ").split(/\s+/).filter((w) => w.length > 2);
}

export function predict(text: string, model: ModelJSON) {
  const toks = tokens(text);
  // n-grammes (1..ngram_max) présents dans le vocabulaire
  const counts: Record<number, number> = {};
  const add = (term: string) => {
    const idx = model.vocab[term];
    if (idx !== undefined) counts[idx] = (counts[idx] || 0) + 1;
  };
  for (let i = 0; i < toks.length; i++) {
    add(toks[i]);
    if (model.ngram_max >= 2 && i + 1 < toks.length) add(toks[i] + " " + toks[i + 1]);
  }
  // vecteur TF-IDF (tf sublinéaire) + normalisation L2
  const feat: Record<number, number> = {};
  let norm = 0;
  for (const k in counts) {
    const idx = +k;
    const tf = model.sublinear ? 1 + Math.log(counts[idx]) : counts[idx];
    const w = tf * model.idf[idx];
    feat[idx] = w; norm += w * w;
  }
  norm = Math.sqrt(norm) || 1;
  const nFeat = Object.keys(feat).length;

  // scores = coef · x + intercept
  const scores = model.classes.map((_, c) => {
    let s = model.intercept[c];
    for (const k in feat) s += (feat[+k] / norm) * model.coef[c][+k];
    return s;
  });
  // softmax
  const mx = Math.max(...scores);
  const exp = scores.map((s) => Math.exp(s - mx));
  const sum = exp.reduce((a, b) => a + b, 0);
  const probs = exp.map((e) => e / sum);

  const ranked = model.classes
    .map((cls, i) => ({ cls, p: probs[i] }))
    .sort((a, b) => b.p - a.p);
  return { ranked, matched: nFeat };
}
