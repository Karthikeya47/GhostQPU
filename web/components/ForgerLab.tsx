"use client";
import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import { COLORS, D, genuineRuns, jobLabel, twinOf } from "@/lib/data";

const FAMILIES = [
  { key: "coh_", name: "Coherent over-rotation", cost: "fit every qubit's pulse error from real hardware runs" },
  { key: "spec_", name: "Neighbor crosstalk (ZZ)", cost: "measure every coupler's static ZZ on hardware" },
  { key: "ro_", name: "Readout in context", cost: "learn neighbor-dependent readout for every pair" },
  { key: "drift_", name: "Drift over time", cost: "reproduce how the device wanders during a job" },
] as const;

/** Exactly the frozen Detector: standardize, weight, sigmoid per chunk, then average over the 8 chunks. */
function score(chunks: Record<string, number>[]) {
  const F = D.frozen;
  const p = chunks.map((c) => {
    const z = F.features.reduce((s, f, i) => s + ((c[f] - F.mean[i]) / F.scale[i]) * F.coef[i], F.intercept);
    return 1 / (1 + Math.exp(-z));
  });
  return p.reduce((a, b) => a + b, 0) / p.length;
}

/** Move each family of the Twin's Signature part of the way toward what the hardware showed, chunk by chunk. */
function blend(genuine: Record<string, number>[], forged: Record<string, number>[], mix: number[]) {
  return forged.map((c, k) => {
    const out: Record<string, number> = { ...c };
    D.frozen.features.forEach((f) => {
      const fam = FAMILIES.findIndex((x) => f.startsWith(x.key));
      out[f] = c[f] + mix[fam] * (genuine[k][f] - c[f]);
    });
    return out;
  });
}

export function ForgerLab() {
  const pairs = genuineRuns.filter((g) => twinOf(g.id));
  const sig = (id: string) => D.signatures.filter((s) => s.run_id === id).sort((a, b) => a.chunk - b.chunk);
  // Open on the job where no single faked family is enough, so the reader has to combine them.
  const [gid, setGid] = useState(() => {
    const hardest = (id: string) => Math.min(...FAMILIES.map((_, i) => score(blend(sig(id), sig(`${id}_forged`), FAMILIES.map((__, j) => +(i === j))))));
    const winnable = pairs.filter((g) => score(sig(g.id)) <= 0.35);
    return winnable.reduce((b, g) => (hardest(g.id) > hardest(b.id) ? g : b)).id;
  });
  const [mix, setMix] = useState<number[]>([0, 0, 0, 0]);
  const genuine = useMemo(() => sig(gid), [gid]);
  const forged = useMemo(() => sig(`${gid}_forged`), [gid]);

  const edited = blend(genuine, forged, mix);
  const s = score(edited);
  const label = s >= 0.65 ? "FORGED" : s <= 0.35 ? "GENUINE" : "INCONCLUSIVE";
  const color = label === "FORGED" ? COLORS.forged : label === "GENUINE" ? "var(--good)" : "var(--mute)";
  const fooled = s < 0.5;

  return (
    <div className="grid2" style={{ alignItems: "start" }}>
      <div className="card">
        <h3>Your forged job</h3>
        <p className="cap">Start from the stock Forger&apos;s Twin. Each slider copies part of one Canary family from the real hardware run into your forgery.</p>
        <div className="tabs" role="group" aria-label="Job to forge" style={{ margin: "8px 0 18px" }}>
          {pairs.map((g) => (
            <button key={g.id} className="tab" aria-pressed={g.id === gid} onClick={() => { setGid(g.id); setMix([0, 0, 0, 0]); }}>
              {jobLabel(g.id).replace(" · new cycle", "")}
            </button>
          ))}
        </div>
        <div style={{ display: "grid", gap: 18 }}>
          {FAMILIES.map((f, i) => (
            <label key={f.key} style={{ display: "grid", gap: 6 }}>
              <span style={{ display: "flex", justifyContent: "space-between", fontSize: 14 }}>
                <span>{f.name}</span>
                <span className="mono" style={{ color: mix[i] ? COLORS.forged : "var(--mute)" }}>{Math.round(mix[i] * 100)}% faked</span>
              </span>
              <input className="slider" type="range" min={0} max={1} step={0.01} value={mix[i]}
                onChange={(e) => setMix((m) => m.map((v, j) => (j === i ? +e.target.value : v)))} />
              <span style={{ fontSize: 12, color: "var(--mute)" }}>A real Forger would have to {f.cost}.</span>
            </label>
          ))}
        </div>
        <button className="tab" style={{ marginTop: 18 }} onClick={() => setMix([0, 0, 0, 0])}>Reset</button>
      </div>

      <div className="card" style={{ position: "sticky", top: 24 }}>
        <div className="unit">frozen Detector says</div>
        <div className="display" style={{ fontSize: "clamp(40px, 6vw, 76px)", fontWeight: 900, lineHeight: 0.95, color, textShadow: `0 0 40px ${color}55` }}>
          |{label}⟩
        </div>
        <div className="mono" style={{ marginTop: 8, color: "var(--mute)" }}>
          forged score <span style={{ color: "var(--frost)", fontSize: 22 }}>{s.toFixed(3)}</span>
        </div>
        <div style={{ position: "relative", height: 14, background: "#1a2130", borderRadius: 7, marginTop: 18, overflow: "hidden" }}>
          <motion.div animate={{ width: `${s * 100}%` }} transition={{ type: "spring", stiffness: 140, damping: 20 }}
            style={{ height: "100%", background: `linear-gradient(90deg, var(--good), ${COLORS.forged})`, borderRadius: 7 }} />
          {[0.35, 0.5, 0.65].map((t) => (
            <div key={t} style={{ position: "absolute", top: 0, bottom: 0, left: `${t * 100}%`, borderLeft: `1px ${t === 0.5 ? "solid" : "dashed"} var(--gold)` }} />
          ))}
        </div>
        <div className="mono" style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--mute)", marginTop: 4 }}>
          <span>0 genuine</span><span>0.5</span><span>forged 1</span>
        </div>
        <p style={{ marginTop: 18, fontSize: 15, color: fooled ? "var(--frost)" : "var(--mute)" }}>
          {fooled
            ? `You fooled it, by faking ${FAMILIES.filter((_, i) => mix[i] > 0).map((f) => f.name.toLowerCase()).join(", ")}. Each of those is physics the public calibration does not contain.`
            : "Still caught. Find out how much of the hardware's physics you have to copy before the Detector lets you through. On most of our jobs one family carries the evidence, and which one changes by machine and day; try the other jobs."}
        </p>
        <p className="cap" style={{ marginTop: 10 }}>
          This runs the frozen Detector&apos;s exact weights in your browser on the job&apos;s real 8-chunk Signatures. The sliders edit
          features directly; a real Forger would have to produce them by simulating that physics.
        </p>
      </div>
    </div>
  );
}
