"use client";
import { motion } from "framer-motion";

const VX = 800;
const VY = 330;
const RIBS = Array.from({ length: 20 }, (_, i) => (i + 1) * 78);
const RINGS = Array.from({ length: 7 }, (_, i) => i);

/** The ribbed glass vault: curved ribs converging on a dark core, with light running along a few of them. */
export function Vault({ strength }: { strength: number }) {
  const rib = (s: number, side: 1 | -1) => `M${VX + side * s} 960 Q${VX + side * s * 1.08} ${VY - 10} ${VX + side * s * 0.05} ${VY}`;
  return (
    <motion.svg aria-hidden className="vault" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice"
      animate={{ opacity: strength }} transition={{ duration: 1.2, ease: "easeInOut" }}>
      <defs>
        <linearGradient id="rib" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0" stopColor="#cfeaff" stopOpacity="0.55" />
          <stop offset="0.7" stopColor="#6fb6ff" stopOpacity="0.18" />
          <stop offset="1" stopColor="#0a2a4c" stopOpacity="0" />
        </linearGradient>
        <radialGradient id="core" cx="50%" cy="37%" r="40%">
          <stop offset="0" stopColor="#010610" stopOpacity="0.95" />
          <stop offset="1" stopColor="#010610" stopOpacity="0" />
        </radialGradient>
      </defs>
      {RINGS.map((k) => (
        <ellipse key={k} cx={VX} cy={VY + 40} rx={260 + k * 190} ry={70 + k * 52} fill="none" stroke="#8fd3ff"
          strokeOpacity={0.05 + k * 0.012} strokeWidth={k === 3 ? 10 : 1.2} />
      ))}
      {RIBS.flatMap((s, i) => [1, -1].map((side) => (
        <path key={`${i}${side}`} d={rib(s, side as 1 | -1)} fill="none" stroke="url(#rib)" strokeWidth={1 + i * 0.12} />
      )))}
      {[3, 8, 14].flatMap((i) => [1, -1].map((side) => (
        <path key={`l${i}${side}`} d={rib(RIBS[i], side as 1 | -1)} fill="none" stroke="#eaf6ff" strokeWidth={2}
          className="vault-light" style={{ animationDelay: `${i * 0.37 + (side > 0 ? 0 : 1.1)}s` }} />
      )))}
      <ellipse cx={VX} cy={VY} rx={420} ry={260} fill="url(#core)" />
    </motion.svg>
  );
}
