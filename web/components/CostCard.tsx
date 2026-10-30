"use client";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import raw from "@/public/cost.json";
import { COLORS } from "@/lib/data";

// cost.json is written by scripts/cost_and_forward.py from the committed Runs.
type Row = { config: string; shots: number; canary_circuits: number; qpu_seconds: number; auc: number; correct: number; jobs: number };
const C = raw as unknown as { cost: Row[]; forward: { auc: number; correct: number; jobs: number; worst_genuine: number } };

export function CostCard() {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useInView(ref, { once: true, margin: "-10% 0px" });
  const rows = [...C.cost].sort((a, b) => b.qpu_seconds - a.qpu_seconds);
  const full = rows[0];
  const perfect = rows.filter((r) => r.correct === r.jobs);
  const best = perfect[perfect.length - 1];
  const max = full.qpu_seconds;
  return (
    <div className="grid2" style={{ marginTop: 28, alignItems: "stretch" }}>
      <div className="card" ref={ref}>
        <h3>What verification costs</h3>
        <p className="cap">
          Canary QPU time per job versus how many of the {full.jobs} jobs are still called correctly, each scored without its own calibration cycle.
          Fewer shots uses the first shots of each recorded job.
        </p>
        <div style={{ display: "grid", gap: 10 }}>
          {rows.map((r, i) => {
            const ok = r.correct === r.jobs;
            return (
              <div key={`${r.config}${r.shots}`} style={{ display: "grid", gridTemplateColumns: "minmax(140px, 1.2fr) 2fr 64px", gap: 10, alignItems: "center", fontSize: 13 }}>
                <span style={{ color: r === best ? "var(--frost)" : "#c2d6ea" }}>{r.config.replace(" (today)", "")} · {r.shots}</span>
                <div style={{ height: 10, background: "#10263f", borderRadius: 5, overflow: "hidden" }}>
                  <motion.div initial={{ width: 0 }} animate={{ width: seen ? `${(r.qpu_seconds / max) * 100}%` : 0 }} transition={{ duration: 0.9, delay: i * 0.05 }}
                    style={{ height: "100%", borderRadius: 5, background: ok ? "var(--gold)" : COLORS.forged, opacity: r === best ? 1 : 0.6 }} />
                </div>
                <span className="mono" style={{ textAlign: "right", color: ok ? "var(--frost)" : COLORS.forged }}>{r.correct}/{r.jobs}</span>
              </div>
            );
          })}
        </div>
        <div className="legend" style={{ marginTop: 12 }}>
          <span><i style={{ background: "var(--gold)" }} />every job correct</span>
          <span><i style={{ background: COLORS.forged }} />misses some</span>
          <span>bar = QPU seconds of Canaries</span>
        </div>
      </div>
      <div className="card" style={{ display: "grid", gap: 22, alignContent: "start" }}>
        <div>
          <div className="unit">cheapest setting that catches every job</div>
          <div className="big">{best.qpu_seconds}s</div>
          <div style={{ color: "var(--mute)", fontSize: 14 }}>
            {best.config}, {best.canary_circuits} circuits × {best.shots} shots, against {full.qpu_seconds}s today
            ({Math.round((1 - best.qpu_seconds / full.qpu_seconds) * 100)}% less). No single family manages it alone.
          </div>
        </div>
        <div style={{ borderTop: "1px solid var(--line)", paddingTop: 18 }}>
          <div className="unit">forward in time: trained only on earlier days</div>
          <div className="big">{C.forward.correct}/{C.forward.jobs}</div>
          <div style={{ color: "var(--mute)", fontSize: 14 }}>
            AUC {C.forward.auc.toFixed(2)}. Each calibration cycle scored by a Detector that had only seen the cycles before it, the way a
            customer would actually use it. Worst real job {C.forward.worst_genuine.toFixed(2)}.
          </div>
        </div>
      </div>
    </div>
  );
}
