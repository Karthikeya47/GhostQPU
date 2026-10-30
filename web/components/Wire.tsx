"use client";
import { motion, useInView } from "framer-motion";
import { useRef, type ReactNode } from "react";

/** Section header drawn as one qubit wire: |0⟩ ── gate ── measure, with a pulse travelling along it. */
export function Wire({ gate, children }: { gate: string; children: ReactNode }) {
  const ref = useRef<SVGSVGElement>(null);
  const seen = useInView(ref, { once: true, margin: "-10% 0px" });
  const meter = gate === "M";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 22, flexWrap: "wrap" }}>
      <svg ref={ref} width="236" height="40" viewBox="0 0 236 40" aria-hidden style={{ flex: "none", overflow: "visible" }}>
        <text x="0" y="25" fontSize="15" fill="var(--gold)" fontFamily="var(--f-mono)">|0⟩</text>
        <motion.line x1="34" x2="230" y1="20" y2="20" stroke="var(--gold-dim)" strokeWidth="1.5"
          initial={{ pathLength: 0 }} animate={{ pathLength: seen ? 1 : 0 }} transition={{ duration: 1, ease: "easeInOut" }} />
        <motion.g initial={{ opacity: 0, scale: 0.6 }} animate={seen ? { opacity: 1, scale: 1 } : {}} transition={{ delay: 0.45, type: "spring", stiffness: 260 }}
          style={{ transformOrigin: "110px 20px" }}>
          <rect x="88" y="6" width="44" height="28" rx="4" fill="var(--ink)" stroke="var(--gold)" strokeWidth="1.5" />
          <text x="110" y="25" textAnchor="middle" fontSize="13" fill="var(--gold)" fontFamily="var(--f-mono)">{meter ? "" : gate}</text>
          {meter && (
            <g stroke="var(--gold)" strokeWidth="1.5" fill="none">
              <path d="M98 27 A12 12 0 0 1 122 27" />
              <line x1="110" y1="27" x2="118" y2="13" />
            </g>
          )}
        </motion.g>
        <motion.g initial={{ opacity: 0 }} animate={seen ? { opacity: 1 } : {}} transition={{ delay: 0.75 }}>
          <rect x="176" y="6" width="34" height="28" rx="4" fill="var(--ink)" stroke="var(--gold-dim)" strokeWidth="1.2" />
          <path d="M183 26 A10 10 0 0 1 203 26" stroke="var(--gold-dim)" strokeWidth="1.2" fill="none" />
          <line x1="193" y1="26" x2="199" y2="15" stroke="var(--gold-dim)" strokeWidth="1.2" />
        </motion.g>
        {seen && <circle r="3" cy="20" fill="var(--gold)" className="wire-pulse" />}
      </svg>
      <span className="stage-label">{children}</span>
    </div>
  );
}
