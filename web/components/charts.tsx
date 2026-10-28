"use client";
import { motion, useInView } from "framer-motion";
import { useRef, useState } from "react";

const W = 560;
const H = 320;
const P = { l: 52, r: 16, t: 16, b: 44 };
const iw = W - P.l - P.r;
const ih = H - P.t - P.b;
const GRID = "#232b3a";
const MUTE = "#8791a3";

const nice = (max: number, n = 4) => {
  const step = Math.pow(10, Math.floor(Math.log10(max / n)));
  const s = [1, 2, 2.5, 5, 10].map((k) => k * step).find((k) => max / k <= n) ?? step * 10;
  return Array.from({ length: Math.ceil(max / s) + 1 }, (_, i) => +(i * s).toFixed(6));
};
const fmt = (v: number) => (Math.abs(v) >= 10 ? v.toFixed(0) : +v.toFixed(3) + "");

function useDraw() {
  const ref = useRef<SVGSVGElement>(null);
  const seen = useInView(ref, { once: true, margin: "-15% 0px" });
  return { ref, seen };
}

function Axes({ xs, ys, sx, sy, xLabel, yLabel, xFmt = fmt }: {
  xs: number[]; ys: number[]; sx: (v: number) => number; sy: (v: number) => number; xLabel: string; yLabel: string; xFmt?: (v: number) => string;
}) {
  return (
    <g fontSize={11} fill={MUTE}>
      {ys.map((v) => (
        <g key={`y${v}`}>
          <line x1={P.l} x2={W - P.r} y1={sy(v)} y2={sy(v)} stroke={GRID} />
          <text x={P.l - 8} y={sy(v) + 4} textAnchor="end">{fmt(v)}</text>
        </g>
      ))}
      {xs.map((v) => (
        <text key={`x${v}`} x={sx(v)} y={H - P.b + 18} textAnchor="middle">{xFmt(v)}</text>
      ))}
      <text x={P.l + iw / 2} y={H - 6} textAnchor="middle">{xLabel}</text>
      <text transform={`translate(12 ${P.t + ih / 2}) rotate(-90)`} textAnchor="middle">{yLabel}</text>
    </g>
  );
}

export type Series = { name: string; color: string; pts: [number, number][]; dashed?: boolean };

export function LineChart({ series, xLabel, yLabel, xTicks, yMax, label }: {
  series: Series[]; xLabel: string; yLabel: string; xTicks: number[]; yMax?: number; label: string;
}) {
  const { ref, seen } = useDraw();
  const [hover, setHover] = useState<{ x: number; y: number; s: string; c: string; px: number; py: number } | null>(null);
  const xMax = Math.max(...xTicks);
  const ys = nice(yMax ?? Math.max(...series.flatMap((s) => s.pts.map((p) => p[1]))) * 1.08);
  const top = ys[ys.length - 1];
  const sx = (v: number) => P.l + (v / xMax) * iw;
  const sy = (v: number) => P.t + ih - (v / top) * ih;
  return (
    <svg ref={ref} viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxHeight: 440 }} role="img" aria-label={label} onMouseLeave={() => setHover(null)}>
      <Axes xs={xTicks} ys={ys} sx={sx} sy={sy} xLabel={xLabel} yLabel={yLabel} />
      {series.map((s, si) => {
        const d = s.pts.map((p, i) => `${i ? "L" : "M"}${sx(p[0])},${sy(p[1])}`).join("");
        return (
          <g key={s.name}>
            <motion.path d={d} fill="none" stroke={s.color} strokeWidth={2.5} strokeDasharray={s.dashed ? "6 5" : undefined}
              strokeLinecap="round" strokeLinejoin="round"
              initial={{ pathLength: 0 }} animate={{ pathLength: seen ? 1 : 0 }} transition={{ duration: 1.6, delay: si * 0.35, ease: "easeInOut" }}
              style={{ filter: `drop-shadow(0 0 6px ${s.color}66)` }} />
            {s.pts.map((p, i) => (
              <motion.circle key={i} cx={sx(p[0])} cy={sy(p[1])} r={4.5} fill={s.color} stroke="#0b0e14" strokeWidth={1.5}
                initial={{ scale: 0 }} animate={{ scale: seen ? 1 : 0 }} transition={{ delay: si * 0.35 + 0.2 + (i / s.pts.length) * 1.4 }}
                onMouseEnter={() => setHover({ x: p[0], y: p[1], s: s.name, c: s.color, px: sx(p[0]), py: sy(p[1]) })}
                style={{ cursor: "crosshair" }} />
            ))}
          </g>
        );
      })}
      {hover && <Tip {...hover} text={`${hover.s}: ${fmt(hover.x)} → ${hover.y.toFixed(4)}`} />}
    </svg>
  );
}

function Tip({ px, py, c, text }: { px: number; py: number; c: string; text: string }) {
  const w = text.length * 6.8 + 16;
  const x = Math.min(Math.max(px - w / 2, 4), W - w - 4);
  const y = py < 50 ? py + 14 : py - 36;
  return (
    <g pointerEvents="none">
      <rect x={x} y={y} width={w} height={24} rx={6} fill="#0b0e14" stroke={c} />
      <text x={x + 8} y={y + 16} fontSize={11} fill="#e4eaf0">{text}</text>
    </g>
  );
}

export function GroupedBars({ groups, series, yLabel, label }: {
  groups: string[]; series: { name: string; color: string; values: number[] }[]; yLabel: string; label: string;
}) {
  const { ref, seen } = useDraw();
  const [hover, setHover] = useState<{ px: number; py: number; c: string; text: string } | null>(null);
  const ys = nice(Math.max(...series.flatMap((s) => s.values)) * 1.1);
  const top = ys[ys.length - 1];
  const sy = (v: number) => P.t + ih - (v / top) * ih;
  const gw = iw / groups.length;
  const bw = Math.min(28, (gw * 0.7) / series.length);
  return (
    <svg ref={ref} viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxHeight: 440 }} role="img" aria-label={label} onMouseLeave={() => setHover(null)}>
      <Axes xs={[]} ys={ys} sx={() => 0} sy={sy} xLabel="" yLabel={yLabel} />
      {groups.map((g, gi) => {
        const cx = P.l + gw * gi + gw / 2;
        return (
          <g key={g}>
            <text x={cx} y={H - P.b + 18} textAnchor="middle" fontSize={11} fill={MUTE}>{g}</text>
            {series.map((s, si) => {
              const x = cx - (bw * series.length) / 2 + si * bw + 2;
              const v = s.values[gi];
              return (
                <motion.rect key={s.name} x={x} width={bw - 4} rx={3} fill={s.color}
                  initial={{ y: sy(0), height: 0 }} animate={seen ? { y: sy(v), height: sy(0) - sy(v) } : {}}
                  transition={{ duration: 0.9, delay: gi * 0.12 + si * 0.08, ease: [0.2, 0.8, 0.2, 1] }}
                  onMouseEnter={() => setHover({ px: x + bw / 2, py: sy(v), c: s.color, text: `${s.name}: ${v.toFixed(4)}` })} />
              );
            })}
          </g>
        );
      })}
      {hover && <Tip {...hover} />}
    </svg>
  );
}

export function ScoreBars({ scores, label, color }: { scores: number[]; label: string; color: string }) {
  const { ref, seen } = useDraw();
  const h = 220;
  const ih2 = h - P.t - 36;
  const sy = (v: number) => P.t + ih2 - v * ih2;
  const gw = iw / scores.length;
  return (
    <svg ref={ref} viewBox={`0 0 ${W} ${h}`} width="100%" role="img" aria-label={label}>
      {[0, 0.5, 1].map((v) => (
        <g key={v} fontSize={11} fill={MUTE}>
          <line x1={P.l} x2={W - P.r} y1={sy(v)} y2={sy(v)} stroke={v === 0.5 ? "#c9a24a" : GRID} strokeDasharray={v === 0.5 ? "4 4" : undefined} />
          <text x={P.l - 8} y={sy(v) + 4} textAnchor="end">{v}</text>
        </g>
      ))}
      <text x={W - P.r} y={sy(0.5) - 6} textAnchor="end" fontSize={10} fill="#c9a24a">threshold</text>
      {scores.map((s, i) => (
        <g key={i}>
          <motion.rect x={P.l + gw * i + gw * 0.18} width={gw * 0.64} rx={4} fill={color}
            initial={{ y: sy(0), height: 0 }} animate={seen ? { y: sy(s), height: sy(0) - sy(s) } : {}}
            transition={{ duration: 0.8, delay: i * 0.07, ease: [0.2, 0.8, 0.2, 1] }} />
          <text x={P.l + gw * i + gw / 2} y={h - 16} textAnchor="middle" fontSize={11} fill={MUTE}>{i + 1}</text>
        </g>
      ))}
      <text x={P.l + iw / 2} y={h - 1} textAnchor="middle" fontSize={11} fill={MUTE}>time-ordered chunk of the job</text>
    </svg>
  );
}

export function WeightBars({ weights, labels }: { weights: [string, number][]; labels: Record<string, string> }) {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useInView(ref, { once: true, margin: "-10% 0px" });
  const max = Math.max(...weights.map((w) => Math.abs(w[1])));
  return (
    <div ref={ref} style={{ display: "grid", gap: 8 }}>
      {weights.map(([k, v], i) => (
        <div key={k} style={{ display: "grid", gridTemplateColumns: "minmax(120px, 230px) 1fr 56px", gap: 12, alignItems: "center", fontSize: 13 }}>
          <span style={{ color: "#c4ccd8" }}>{labels[k] ?? k}</span>
          <div style={{ height: 12, background: "#1a2130", borderRadius: 6, overflow: "hidden" }}>
            <motion.div style={{ height: "100%", borderRadius: 6, background: v < 0 ? "#2a78d6" : "#eb6834", boxShadow: `0 0 12px ${v < 0 ? "#2a78d6" : "#eb6834"}88` }}
              initial={{ width: 0 }} animate={{ width: seen ? `${(Math.abs(v) / max) * 100}%` : 0 }} transition={{ duration: 1, delay: i * 0.06 }} />
          </div>
          <span className="mono" style={{ color: "#8791a3", textAlign: "right" }}>{v > 0 ? "+" : ""}{v.toFixed(2)}</span>
        </div>
      ))}
    </div>
  );
}
