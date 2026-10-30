"use client";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { ShotRaster } from "@/components/ShotRaster";
import { COLORS, D, runById } from "@/lib/data";

type Phase = "idle" | "running" | "done";
const MACHINES = [...new Set(D.by_cycle.runs.map((r) => r.backend))].sort();
const verdictOf = (s: number) => (s >= 0.65 ? "FORGED" : s <= 0.35 ? "GENUINE" : "INCONCLUSIVE");

/** Replays a real recorded job end to end: build, transpile, queue, shots, Signatures, chunk scores, Verdict. */
export function JobConsole() {
  const [machine, setMachine] = useState(MACHINES.includes("ibm_kingston") ? "ibm_kingston" : MACHINES[0]);
  const [phase, setPhase] = useState<Phase>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [lines, setLines] = useState<string[]>([]);
  const [shots, setShots] = useState(0);
  const [chunks, setChunks] = useState<number[]>([]);
  const [guess, setGuess] = useState<"GENUINE" | "FORGED" | null>(null);
  const timers = useRef<number[]>([]);
  const last = useRef<string | null>(null);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const submit = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    const pool = D.by_cycle.runs.filter((r) => r.backend === machine && r.run_id !== last.current);
    const pick = pool[Math.floor(Math.random() * pool.length)];
    last.current = pick.run_id;
    const run = runById(pick.run_id);
    const scores = D.by_cycle.chunks.filter((c) => c.run_id === pick.run_id).sort((a, b) => a.chunk - b.chunk).map((c) => c.forged_score);
    const canaries = run.circuits.filter((c) => c.role === "canary").length;
    const total = run.circuits.length * run.info.shots;
    setJobId(pick.run_id);
    setPhase("running");
    setGuess(null);
    setLines([]);
    setShots(0);
    setChunks([]);
    const fast = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0.15 : 1;
    const at = (ms: number, f: () => void) => timers.current.push(window.setTimeout(f, ms * fast));
    const log = (ms: number, text: string) => at(ms, () => setLines((l) => [...l, text]));
    log(0, `Building Batch: ${canaries} Canaries hidden among ${run.circuits.length - canaries} Workload circuits, shuffled`);
    log(700, `Transpiling to native gates (rz, sx, x, cz) on ${run.placements.length * 2} physical qubits, Canaries at optimization level 0`);
    log(1400, `Queued on ${machine} · calibration cycle ${run.cycle.slice(0, 16).replace("T", " ")}`);
    log(2100, `Executing ${run.circuits.length} circuits × ${run.info.shots} shots`);
    for (let k = 1; k <= 20; k++) at(2100 + k * 110, () => setShots(Math.round((total * k) / 20)));
    log(4600, "Extracting Signatures: 12 features × 8 time-ordered chunks");
    scores.forEach((s, k) => at(5100 + k * 320, () => setChunks((c) => [...c, s])));
    at(5100 + scores.length * 320 + 300, () => setPhase("done"));
  };

  const run = jobId ? runById(jobId) : null;
  const score = chunks.length ? chunks.reduce((a, b) => a + b, 0) / chunks.length : 0;
  const verdict = verdictOf(score);
  const truth = run?.origin === "genuine" ? "GENUINE" : "FORGED";
  const vColor = verdict === "FORGED" ? COLORS.forged : verdict === "GENUINE" ? "var(--good)" : "var(--mute)";

  return (
    <div className="console">
      <div className="console-bar">
        <span className="mono">ghostqpu · job console</span>
        <span className="mono" style={{ color: "var(--mute)" }}>{phase === "running" ? "● running" : phase === "done" ? "● complete" : "○ ready"}</span>
      </div>
      <div className="console-body">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <span className="mono" style={{ color: "var(--mute)", fontSize: 13 }}>backend</span>
          {MACHINES.map((m) => (
            <button key={m} className="tab" aria-pressed={m === machine} disabled={phase === "running"} onClick={() => setMachine(m)}>{m}</button>
          ))}
          <button className="run-btn" onClick={submit} disabled={phase === "running"}>
            {phase === "idle" ? "▶ Submit job" : phase === "running" ? "Running…" : "▶ Submit another"}
          </button>
        </div>

        {phase === "idle" && (
          <p className="mono" style={{ color: "var(--mute)", fontSize: 13, marginTop: 22, lineHeight: 1.8 }}>
            $ Pick a backend and submit. A provider returns a job. Somewhere in it are 30 hidden Canaries.<br />
            $ Was it run on a quantum computer, or forged from public calibration data?
          </p>
        )}

        <div className="mono console-log" aria-live="polite">
          <AnimatePresence>
            {lines.map((l, i) => (
              <motion.div key={`${jobId}${i}`} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}>
                <span style={{ color: "var(--gold)" }}>▸</span> {l}
                {i === 3 && <span style={{ color: "var(--frost)" }}> · {shots.toLocaleString()} shots read</span>}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {run && lines.length >= 4 && (
          <div style={{ marginTop: 10 }}>
            <div className="mono" style={{ fontSize: 11, color: "var(--mute)", marginBottom: 6 }}>
              shot record, N={run.raster_circuit.n} X-gate Canary · each column one shot · lit = 1
            </div>
            <ShotRaster key={jobId} bits={run.raster} color="#e4eaf0" label="Shot record streaming in" />
          </div>
        )}

        {chunks.length > 0 && (
          <div style={{ marginTop: 18 }}>
            <div className="mono" style={{ fontSize: 11, color: "var(--mute)", marginBottom: 8 }}>
              forged score per chunk · Detector never saw this job&apos;s calibration cycle
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(8, 1fr)", gap: 6, alignItems: "end", height: 90, position: "relative" }}>
              <div style={{ position: "absolute", left: 0, right: 0, bottom: 45, borderTop: "1px dashed var(--gold-dim)" }} />
              {chunks.map((s, i) => (
                <motion.div key={i} initial={{ height: 0 }} animate={{ height: `${Math.max(s * 100, 2)}%` }} transition={{ type: "spring", stiffness: 120 }}
                  style={{ background: s > 0.5 ? COLORS.forged : "var(--good)", borderRadius: 3, opacity: 0.9 }} title={s.toFixed(2)} />
              ))}
            </div>
          </div>
        )}

        {phase === "running" && (
          <div style={{ marginTop: 18, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <span className="mono" style={{ fontSize: 13, color: "var(--mute)" }}>Your call before the Detector answers:</span>
            {(["GENUINE", "FORGED"] as const).map((g) => (
              <button key={g} className="tab" aria-pressed={guess === g} onClick={() => setGuess(g)}>|{g.toLowerCase()}⟩</button>
            ))}
          </div>
        )}

        <AnimatePresence>
          {phase === "done" && run && (
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} style={{ marginTop: 22, display: "grid", gap: 10 }}>
              <div className="display" style={{ fontSize: "clamp(44px, 7vw, 84px)", fontWeight: 900, lineHeight: 0.9, color: vColor, textShadow: `0 0 40px ${vColor}55` }}>
                |{verdict}⟩
              </div>
              <div className="mono" style={{ color: "var(--mute)", fontSize: 14 }}>
                mean forged score <span style={{ color: "var(--frost)" }}>{score.toFixed(3)}</span> · 0.35 to 0.65 is inconclusive
              </div>
              <div className="mono" style={{ fontSize: 14, borderTop: "1px solid var(--line)", paddingTop: 12 }}>
                Truth: <b style={{ color: truth === "GENUINE" ? COLORS.genuine : COLORS.forged }}>
                  {truth === "GENUINE" ? `executed on IBM ${run.info.backend}` : "forged by the calibration-matched simulator"}
                </b>
                {truth === "GENUINE" && run.info.job_id && <span style={{ color: "var(--mute)" }}> · IBM job {run.info.job_id}</span>}
                <br />
                <span style={{ color: "var(--mute)" }}>
                  Detector {verdict === truth ? "correct" : verdict === "INCONCLUSIVE" ? "abstained" : "wrong"}
                  {guess && ` · you ${guess === truth ? "were right" : "were wrong"}`}
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
