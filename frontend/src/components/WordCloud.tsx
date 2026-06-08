import { useEffect, useRef, useState } from "react";

// Vrai nuage de mots sur <canvas> : les termes sont dimensionnés selon leur
// importance (rang) et placés en spirale sans se chevaucher.
const COLORS = ["#3B82F6", "#22D3EE", "#60A5FA", "#34D399", "#A78BFA", "#F59E0B",
                "#F472B6", "#2DD4BF", "#93C5FD", "#FBBF24", "#C084FC", "#5EEAD4"];

export default function WordCloud({ terms, seed = 0, height = 230 }: {
  terms: string[]; seed?: number; height?: number;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const [w, setW] = useState(560);

  useEffect(() => {
    if (!wrap.current) return;
    const ro = new ResizeObserver((e) => setW(e[0].contentRect.width));
    ro.observe(wrap.current);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const cv = canvas.current;
    if (!cv || !terms.length) return;
    const dpr = window.devicePixelRatio || 1;
    const H = height;
    cv.width = w * dpr; cv.height = H * dpr;
    cv.style.width = w + "px"; cv.style.height = H + "px";
    const ctx = cv.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, H);
    ctx.textAlign = "center"; ctx.textBaseline = "middle";

    const n = terms.length;
    const placed: { x: number; y: number; w: number; h: number }[] = [];
    const cx = w / 2, cy = H / 2;

    terms.forEach((t, i) => {
      const weight = (n - i) / n;                  // 1 (plus important) -> ~0
      const fs = Math.round(13 + weight * 23);     // 13..36 px
      ctx.font = `700 ${fs}px Inter, sans-serif`;
      const tw = ctx.measureText(t).width, th = fs;
      // recherche en spirale d'un emplacement libre
      let placedOk = false;
      for (let s = 0; s < 900 && !placedOk; s++) {
        const r = 4 * Math.sqrt(s);
        const a = s * 0.5 + (seed % 7);
        const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a) * 0.62;
        const box = { x: x - tw / 2 - 3, y: y - th / 2 - 2, w: tw + 6, h: th + 4 };
        if (box.x < 2 || box.y < 2 || box.x + box.w > w - 2 || box.y + box.h > H - 2) continue;
        const hit = placed.some((p) =>
          !(box.x > p.x + p.w || box.x + box.w < p.x || box.y > p.y + p.h || box.y + box.h < p.y));
        if (hit) continue;
        placed.push(box);
        ctx.fillStyle = COLORS[i % COLORS.length];
        ctx.globalAlpha = 0.55 + weight * 0.45;
        ctx.fillText(t, x, y);
        placedOk = true;
      }
    });
    ctx.globalAlpha = 1;
  }, [terms, seed, w, height]);

  return (
    <div ref={wrap} style={{ width: "100%" }}>
      <canvas ref={canvas} />
    </div>
  );
}
