"use client";
import { useInView } from "framer-motion";
import { useEffect, useRef } from "react";

/** Shot record as a stream: each row is one shot, each column a clbit. Lit cells are 1s. */
export function ShotRaster({ bits, color, label }: { bits: number[][]; color: string; label: string }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const seen = useInView(ref, { once: true, margin: "-10% 0px" });

  useEffect(() => {
    const c = ref.current;
    if (!c || !seen) return;
    const ctx = c.getContext("2d")!;
    const cols = bits[0].length;
    const rows = bits.length;
    const dpr = window.devicePixelRatio || 1;
    const w = c.clientWidth;
    const cell = w / rows;
    const h = cell * cols * 2.2;
    c.width = w * dpr;
    c.height = h * dpr;
    c.style.height = `${h}px`;
    ctx.scale(dpr, dpr);
    const ch = h / cols;
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let shown = still ? rows : 0;
    let raf = 0;
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      for (let s = 0; s < shown; s++) {
        for (let b = 0; b < cols; b++) {
          const on = bits[s][b] === 1;
          // Even clbits are the canary targets (ideal 0), odd ones the neighbors.
          ctx.fillStyle = on ? color : b % 2 === 0 ? "#10263f" : "#0b1d33";
          ctx.fillRect(s * cell + 0.5, b * ch + 1, Math.max(cell - 1, 1), ch - 2);
        }
      }
      if (shown < rows) {
        shown = Math.min(rows, shown + 3);
        raf = requestAnimationFrame(draw);
      }
    };
    draw();
    return () => cancelAnimationFrame(raf);
  }, [seen, bits, color]);

  return <canvas ref={ref} style={{ width: "100%", display: "block" }} role="img" aria-label={label} />;
}
