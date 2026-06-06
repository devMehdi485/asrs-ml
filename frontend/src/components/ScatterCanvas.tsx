import { useEffect, useRef, useState } from "react";

type Pt = { x: number; y: number; cat: number };

export default function ScatterCanvas({ points, activeIdx, color, height = 460 }: {
  points: Pt[]; activeIdx: number; color: (i: number) => string; height?: number;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const [w, setW] = useState(800);

  useEffect(() => {
    if (!wrap.current) return;
    const ro = new ResizeObserver((e) => setW(e[0].contentRect.width));
    ro.observe(wrap.current);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const cv = canvas.current;
    if (!cv || !points.length) return;
    const dpr = window.devicePixelRatio || 1;
    const H = height;
    cv.width = w * dpr; cv.height = H * dpr;
    cv.style.width = w + "px"; cv.style.height = H + "px";
    const ctx = cv.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, H);

    const xs = points.map((p) => p.x), ys = points.map((p) => p.y);
    const med = (a: number[]) => { const s = [...a].sort((p, q) => p - q); return s[s.length >> 1]; };
    // domaine SYMÉTRIQUE centré sur la médiane -> masse dense au centre du canvas
    const mx = med(xs), my = med(ys);
    const hwx = Math.max(mx - Math.min(...xs), Math.max(...xs) - mx) || 1;
    const hwy = Math.max(my - Math.min(...ys), Math.max(...ys) - my) || 1;
    const pad = 20;
    const sx = (x: number) => pad + ((x - (mx - hwx)) / (2 * hwx)) * (w - 2 * pad);
    const sy = (y: number) => H - pad - ((y - (my - hwy)) / (2 * hwy)) * (H - 2 * pad);

    const draw = (p: Pt, dim: boolean) => {
      ctx.beginPath();
      ctx.globalAlpha = dim ? 0.05 : 0.75;
      ctx.fillStyle = color(p.cat);
      ctx.arc(sx(p.x), sy(p.y), dim ? 2 : 2.7, 0, 7);
      ctx.fill();
    };
    // points atténués d'abord, actifs ensuite (au-dessus)
    if (activeIdx >= 0) {
      points.forEach((p) => p.cat !== activeIdx && draw(p, true));
      points.forEach((p) => p.cat === activeIdx && draw(p, false));
    } else {
      points.forEach((p) => draw(p, false));
    }
    ctx.globalAlpha = 1;
  }, [points, activeIdx, w, height, color]);

  return (
    <div ref={wrap} style={{ width: "100%" }}>
      <canvas ref={canvas} />
    </div>
  );
}
