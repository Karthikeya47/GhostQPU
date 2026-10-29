"use client";
import { AnimatePresence, motion, MotionConfig } from "framer-motion";
import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { GroupedBars, LineChart, ScoreBars, WeightBars } from "@/components/charts";
import { ShotRaster } from "@/components/ShotRaster";
import { COLORS, D, FEATURE_LABELS, genuineRuns, jobLabel, mean, runById, scoreOf, twinOf } from "@/lib/data";
import { CNOT_N, CNOT_SIM, IDEAL_TVD, J1, NULL_TEST_AUC, STRONGER_FORGER, WORKLOAD_TVD } from "@/lib/research";

const Scene = dynamic(() => import("@/components/three").then((m) => m.Scene), { ssr: false });
const ChipScene = dynamic(() => import("@/components/three").then((m) => m.ChipScene), { ssr: false });
const CoherentScene = dynamic(() => import("@/components/three").then((m) => m.CoherentScene), { ssr: false });
const SignatureScene = dynamic(() => import("@/components/three").then((m) => m.SignatureScene), { ssr: false });

const fresh = runById(D.fresh_ids.find((id) => !id.endsWith("_forged"))!);
const J1_ID = "ibm_marrakesh_20261027T050804_77679";
const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;

const rise = { initial: { opacity: 0, y: 40 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-10%" }, transition: { duration: 0.8, ease: [0.2, 0.8, 0.2, 1] as const } };

export default function Page() {
  const [runId, setRunId] = useState(genuineRuns[genuineRuns.length - 1].id);
  return (
    <MotionConfig reducedMotion="user">
      <Hero />
      <Threat />
      <BatchSection />
      <Evidence runId={runId} setRunId={setRunId} />
      <Coherent3D runId={runId} setRunId={setRunId} />
      <Shots runId={runId} />
      <Verdict />
      <SignatureSpace />
      <StressTest />
      <Footer />
    </MotionConfig>
  );
}

function Hero() {
  const canaries = fresh.circuits.filter((c) => c.role === "canary").length;
  return (
    <header style={{ position: "relative", minHeight: "100svh", display: "flex", alignItems: "flex-end", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0 }}>
        <Scene camera={[0, 7.5, 9.5]} className="hero3d" label="3D model of the 156-qubit ibm_marrakesh chip with its forged copy floating above">
          <ChipScene chip={D.chips.fresh} placements={fresh.placements} />
        </Scene>
      </div>
      <div style={{ position: "absolute", inset: 0, pointerEvents: "none", background: "linear-gradient(180deg, rgba(11,14,20,0.6) 0%, transparent 25%, transparent 50%, var(--ink) 96%)" }} />
      <div className="wrap" style={{ position: "relative", width: "100%", padding: "0 var(--gutter) 64px", pointerEvents: "none" }}>
        <motion.div className="stage" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
          GhostQPU · ibm_marrakesh · 156 qubits
        </motion.div>
        <h1 className="display" style={{ fontWeight: 900, fontSize: "clamp(52px, 8.4vw, 132px)", lineHeight: 0.86, maxWidth: "11ch", textShadow: "0 4px 40px #0b0e14" }}>
          {"Did your job ever touch a quantum computer?".split(" ").map((w, i) => (
            <motion.span key={i} style={{ display: "inline-block", marginRight: "0.22em", color: w === "touch" ? "var(--gold)" : undefined }}
              initial={{ opacity: 0, y: 60, filter: "blur(12px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ delay: 0.4 + i * 0.08, duration: 0.9, ease: [0.2, 0.8, 0.2, 1] }}>{w}</motion.span>
          ))}
        </h1>
        <motion.p className="lede" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.3 }}>
          The gold lattice is the real chip, drawn from its published coupling map. The orange copy floating above it is the <b>Forger</b>: a
          simulator built from the same public calibration. GhostQPU hides {canaries} <b>Canaries</b> in your Batch to tell them apart.
        </motion.p>
        <motion.div className="mono" style={{ marginTop: 28, fontSize: 12, color: "var(--mute)", display: "flex", gap: 24, flexWrap: "wrap" }}
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.6 }}>
          <span><span style={{ color: "var(--gold)" }}>●</span> canary placements</span>
          <span>brightness = T1</span>
          <span>hover a qubit for its calibration</span>
        </motion.div>
      </div>
    </header>
  );
}

function Threat() {
  const shots = fresh.info.shots;
  const stats = [
    [fresh.circuits.length, "circuits per Batch"],
    [fresh.circuits.filter((c) => c.role === "canary").length, "hidden Canaries"],
    [shots, "shots each"],
    [fresh.info.qpu_seconds ?? 11, "QPU seconds billed"],
  ] as const;
  return (
    <section className="section">
      <div className="wrap">
        <motion.div {...rise}>
          <div className="stage">The threat</div>
          <h2 className="title">Quantum time is resold. Nobody checks it ran.</h2>
          <p className="lede">
            A reseller takes your circuits, runs them through Qiskit Aer with the noise model IBM publishes for the backend, and bills you for
            QPU time. The output has the right shape and roughly the right error rates. We built that <b>Forger</b> ourselves, using the exact
            calibration that was live when each real job executed, so it is the strongest fair attacker.
          </p>
        </motion.div>
        <div className="grid4" style={{ marginTop: 56 }}>
          {stats.map(([v, l], i) => (
            <motion.div key={l} {...rise} transition={{ ...rise.transition, delay: i * 0.1 }} style={{ borderTop: "1px solid var(--gold-dim)", paddingTop: 16 }}>
              <div className="big">{v}</div>
              <div className="unit">{l}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

const FAMILY_COLOR: Record<string, string> = { coherent: "#c9a24a", spectator: "#5aa0f2", readout: "#b48cf0" };

function BatchSection() {
  const [reveal, setReveal] = useState(false);
  return (
    <section className="section" style={{ background: "linear-gradient(180deg, transparent, #0e121a 30%, #0e121a 70%, transparent)" }}>
      <div className="wrap">
        <motion.div {...rise}>
          <div className="stage">Inside one Batch · {jobLabel(fresh.id)}</div>
          <h2 className="title">The Canaries hide in plain sight.</h2>
          <p className="lede">
            Every circuit is compiled to native gates on physical qubits, then shuffled. To the provider all {fresh.circuits.length} look alike.
            Only 4 are the customer&apos;s Workload. The rest have a known ideal answer and probe effects a calibration-based simulator leaves out.
          </p>
        </motion.div>
        <div className="tabs">
          <button className="tab" aria-pressed={reveal} onClick={() => setReveal((r) => !r)}>{reveal ? "Hide the Canaries" : "Reveal the Canaries"}</button>
          {reveal && (
            <div className="legend" style={{ alignItems: "center" }}>
              {Object.entries(FAMILY_COLOR).map(([k, c]) => <span key={k}><i style={{ background: c }} />{k}</span>)}
              <span><i style={{ background: "#e4eaf0" }} />workload</span>
            </div>
          )}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(118px, 1fr))", gap: 10 }}>
          {fresh.circuits.map((c, i) => {
            const color = c.role === "workload" ? "#e4eaf0" : FAMILY_COLOR[c.family];
            const params = Object.entries(c.params).map(([k, v]) => `${k}=${v}`).join(" ");
            return (
              <motion.div key={i} layout className="mono"
                initial={{ opacity: 0, scale: 0.8 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}
                transition={{ delay: (i % 12) * 0.03 }}
                style={{
                  border: `1px solid ${reveal ? color : "var(--line)"}`, borderRadius: 10, padding: "10px 12px", fontSize: 11,
                  background: reveal ? `${color}14` : "var(--panel)", boxShadow: reveal ? `0 0 18px ${color}33` : "none",
                  transition: "all 0.5s", transitionDelay: `${i * 18}ms`, minHeight: 86,
                }}>
                <div style={{ color: "var(--mute)" }}>circuit {String(i + 1).padStart(2, "0")}</div>
                <AnimatePresence mode="wait">
                  {reveal ? (
                    <motion.div key="r" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                      <div style={{ color, fontWeight: 500, marginTop: 4 }}>{c.family}</div>
                      <div style={{ color: "var(--mute)", wordBreak: "break-word" }}>{params || "customer circuit"}</div>
                    </motion.div>
                  ) : (
                    <motion.div key="h" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={{ marginTop: 4, color: "#c4ccd8" }}>
                      depth {c.depth}<br /><span style={{ color: "var(--mute)" }}>{Object.values(c.ops).reduce((a, b) => a + b, 0)} ops</span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function RunTabs({ runId, setRunId }: { runId: string; setRunId: (id: string) => void }) {
  return (
    <div className="tabs" role="group" aria-label="Genuine run">
      {genuineRuns.map((r) => (
        <button key={r.id} className="tab" aria-pressed={r.id === runId} onClick={() => setRunId(r.id)}>
          {jobLabel(r.id)}{D.fresh_ids.includes(r.id) ? " · new cycle" : ""}
        </button>
      ))}
    </div>
  );
}

function Legend() {
  return (
    <div className="legend">
      <span><i style={{ background: COLORS.genuine }} />Genuine (IBM hardware)</span>
      <span><i style={{ background: COLORS.forged }} />Forged Twin</span>
    </div>
  );
}

function Evidence({ runId, setRunId }: { runId: string; setRunId: (id: string) => void }) {
  const [variant, setVariant] = useState<"plain" | "sx sandwich">("plain");
  const g = runById(runId);
  const t = twinOf(runId);
  const coh = (r: typeof g) => r.curves.coherent.filter((c) => c.variant === variant).sort((a, b) => a.n - b.n).map((c) => [c.n, c.p1] as [number, number]);
  const spec = (r: typeof g) => r.curves.spectator.map((c) => [c.delay_us, c.shift] as [number, number]);
  const ro = (r: typeof g) => [[0, 0], [0, 1], [1, 0], [1, 1]].map(([tg, nb]) => r.curves.readout.find((c) => c.target === tg && c.neighbor === nb)!.error);
  const end = (pts: [number, number][]) => pts[pts.length - 1][1];
  const gc = coh(g);
  const tc = t ? coh(t) : [];
  return (
    <section className="section" id="evidence">
      <div className="wrap">
        <motion.div {...rise}>
          <div className="stage">Evidence</div>
          <h2 className="title">Same circuits. Same calibration. Different physics.</h2>
          <p className="lede">
            Each Genuine Run has a Twin: the Forger&apos;s output for the identical Batch under the calibration live at execution. After 128 X gates
            the real qubit reads wrong <b style={{ color: COLORS.genuine }}>{pct(end(gc))}</b> of the time. The Forger predicts{" "}
            <b style={{ color: COLORS.forged }}>{tc.length ? pct(end(tc)) : "n/a"}</b>.
          </p>
        </motion.div>
        <RunTabs runId={runId} setRunId={setRunId} />
        <div className="grid2">
          <motion.div className="card" {...rise} style={{ gridColumn: "1 / -1" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", alignItems: "start" }}>
              <div>
                <h3>Coherent amplification</h3>
                <p className="cap">P(1) after N X gates. Ideal is 0. Tiny over-rotations add up coherently and bend the hardware curve; the Forger&apos;s errors are incoherent and stay near-linear.</p>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                {(["plain", "sx sandwich"] as const).map((v) => (
                  <button key={v} className="tab" aria-pressed={variant === v} onClick={() => setVariant(v)}>{v}</button>
                ))}
              </div>
            </div>
            <Legend />
            <LineChart key={`${runId}${variant}`} label="Coherent amplification: P(1) vs number of X gates"
              series={[{ name: "Genuine", color: COLORS.genuine, pts: gc }, ...(t ? [{ name: "Forged", color: COLORS.forged, pts: tc }] : [])]}
              xTicks={[0, 16, 32, 64, 128]} xLabel="X gates (N)" yLabel="P(1)" />
          </motion.div>
          <motion.div className="card" {...rise}>
            <h3>Spectator crosstalk</h3>
            <p className="cap">How much an idle qubit shifts when its neighbor flips 0 to 1. Gate-local noise models say this should be 0.</p>
            <Legend />
            <LineChart key={`s${runId}`} label="Spectator shift vs idle time"
              series={[{ name: "Genuine", color: COLORS.genuine, pts: spec(g) }, ...(t ? [{ name: "Forged", color: COLORS.forged, pts: spec(t) }] : [])]}
              xTicks={[0, 4, 8, 12, 16]} xLabel="idle time (µs)" yLabel="|shift in P(1)|" />
          </motion.div>
          <motion.div className="card" {...rise}>
            <h3>Readout in context</h3>
            <p className="cap">Readout error of the target, by what it and its neighbor hold. The Forger uses one fixed number per qubit.</p>
            <Legend />
            <GroupedBars key={`r${runId}`} label="Readout error by target and neighbor state" yLabel="readout error"
              groups={["t=0 n=0", "t=0 n=1", "t=1 n=0", "t=1 n=1"]}
              series={[{ name: "Genuine", color: COLORS.genuine, values: ro(g) }, ...(t ? [{ name: "Forged", color: COLORS.forged, values: ro(t) }] : [])]} />
          </motion.div>
        </div>
      </div>
    </section>
  );
}

function Coherent3D({ runId, setRunId }: { runId: string; setRunId: (id: string) => void }) {
  const [sandwich, setSandwich] = useState(false);
  const g = runById(runId);
  return (
    <section className="section">
      <div className="wrap">
        <motion.div {...rise}>
          <div className="stage">Per placement, in 3D</div>
          <h2 className="title">Four qubit pairs. One verdict.</h2>
          <p className="lede">
            The curve above is an average. Here every placement gets its own ribbon: blue ribbons climb with N on real hardware, orange
            ones lie almost flat. Drag to orbit.
          </p>
        </motion.div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <RunTabs runId={runId} setRunId={setRunId} />
          <div style={{ display: "flex", gap: 8 }}>
            <button className="tab" aria-pressed={!sandwich} onClick={() => setSandwich(false)}>plain</button>
            <button className="tab" aria-pressed={sandwich} onClick={() => setSandwich(true)}>sx sandwich</button>
          </div>
        </div>
        <Legend />
        <div style={{ marginTop: 14 }}>
          <Scene camera={[6, 4.5, 6.5]} label="3D ribbons of P(1) vs X gate count for each canary placement">
            <CoherentScene genuine={g} twin={twinOf(runId)} sandwich={sandwich} />
          </Scene>
        </div>
      </div>
    </section>
  );
}

function Shots({ runId }: { runId: string }) {
  const g = runById(runId);
  const t = twinOf(runId);
  const ones = (bits: number[][]) => mean(bits.map((s) => s.filter((_, i) => i % 2 === 0).reduce((a, b) => a + b, 0) / (s.length / 2)));
  return (
    <section className="section">
      <div className="wrap">
        <motion.div {...rise}>
          <div className="stage">Shot record · {jobLabel(runId)}</div>
          <h2 className="title">Read it shot by shot.</h2>
          <p className="lede">
            The first {g.raster.length} shots of the N={g.raster_circuit.n} coherent Canary, in the order the QPU fired them. Each column is one shot;
            the 8 rows are the clbits of the 4 placements (target, neighbor). Every lit cell is a 1, which here means an error.
          </p>
        </motion.div>
        <div style={{ display: "grid", gap: 28, marginTop: 40 }}>
          {[[g, COLORS.genuine, "Genuine"], ...(t ? [[t, COLORS.forged, "Forged Twin"]] : [])].map(([r, c, name]) => {
            const run = r as typeof g;
            return (
              <motion.div key={name as string} {...rise}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }} className="mono">
                  <span style={{ color: c as string }}>{name as string}</span>
                  <span style={{ color: "var(--mute)", fontSize: 13 }}>target P(1) in these shots: {pct(ones(run.raster))}</span>
                </div>
                <ShotRaster key={run.id} bits={run.raster} color={c as string} label={`${name} shot record`} />
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Verdict() {
  const jobs = useMemo(() => {
    const ids = [...new Set([...D.report.predictions, ...D.fresh_scores].map((c) => c.run_id))];
    // Deterministic shuffle so the job number does not give the answer away.
    return ids.map((id) => ({ id, k: [...id].reduce((a, ch) => (a * 31 + ch.charCodeAt(0)) % 9973, 7) })).sort((a, b) => a.k - b.k).map((j) => j.id);
  }, []);
  const [pick, setPick] = useState(jobs[0]);
  const [truth, setTruth] = useState(false);
  const isFresh = D.fresh_ids.includes(pick);
  const chunks = (isFresh ? D.fresh_scores : D.report.predictions).filter((c) => c.run_id === pick).sort((a, b) => a.chunk - b.chunk);
  const score = mean(chunks.map((c) => c.forged_score));
  const label = score >= 0.65 ? "Forged" : score <= 0.35 ? "Genuine" : "Inconclusive";
  const color = label === "Forged" ? COLORS.forged : label === "Genuine" ? "var(--good)" : "var(--mute)";
  const origin = runById(pick).origin;
  return (
    <section className="section" style={{ background: "linear-gradient(180deg, transparent, #0e121a 20%, #0e121a 80%, transparent)" }}>
      <div className="wrap">
        <motion.div {...rise}>
          <div className="stage">The Detector</div>
          <h2 className="title">Pick a job. Get a Verdict.</h2>
          <p className="lede">
            A logistic regression on 12 Signature features, scored on 8 time-ordered chunks per job. Every score below comes from a Detector that
            never saw that job or its Twin. Jobs collected after 10 Oct come from new calibration cycles and were scored by the frozen Detector.
          </p>
        </motion.div>
        <div className="tabs" role="group" aria-label="Job">
          {jobs.map((id, i) => (
            <button key={id} className="tab" aria-pressed={id === pick} onClick={() => { setPick(id); setTruth(false); }}>
              Job {String(i + 1).padStart(2, "0")}
            </button>
          ))}
        </div>
        <div className="grid2" style={{ alignItems: "stretch" }}>
          <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", gap: 24 }}>
            <AnimatePresence mode="wait">
              <motion.div key={pick} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
                <div className="unit">Verdict</div>
                <div className="big display" style={{ color, textShadow: `0 0 40px ${color}55` }}>{label}</div>
                <div className="mono" style={{ marginTop: 10, color: "var(--mute)" }}>
                  forged score <span style={{ color: "var(--frost)", fontSize: 22 }}>{score.toFixed(2)}</span>
                  <span style={{ marginLeft: 12, fontSize: 12 }}>(0.35 to 0.65 is inconclusive)</span>
                </div>
              </motion.div>
            </AnimatePresence>
            <div>
              <button className="tab" aria-pressed={truth} onClick={() => setTruth((v) => !v)}>{truth ? "Hide the truth" : "Reveal the truth"}</button>
              <AnimatePresence>
                {truth && (
                  <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} style={{ marginTop: 12, color: "var(--mute)", fontSize: 15 }}>
                    <b style={{ color: origin === "genuine" ? COLORS.genuine : COLORS.forged }}>
                      {origin === "genuine" ? "Executed on IBM ibm_marrakesh." : "Forged by the calibration-matched simulator."}
                    </b>{" "}
                    {jobLabel(pick)}{isFresh ? ", new calibration cycle" : ""}. <span className="mono" style={{ fontSize: 12 }}>{pick}</span>
                  </motion.p>
                )}
              </AnimatePresence>
            </div>
          </div>
          <div className="card">
            <h3>Score over time</h3>
            <p className="cap">Probability of Forged for each eighth of the job&apos;s shots.</p>
            <ScoreBars key={pick} scores={chunks.map((c) => c.forged_score)} color={color} label="Forged score per time chunk" />
          </div>
        </div>

        <div className="grid4" style={{ marginTop: 56 }}>
          {[
            [D.report.auc.toFixed(2), "AUC, held out", `split ${D.report.split}`],
            [pct(D.report.run_accuracy, 0), "job-level accuracy", `${D.report.n_pairs} Genuine/Forged pairs`],
            [scoreOf(D.fresh_scores, fresh.id).toFixed(2), "new-cycle Genuine score", `frozen Detector ${J1.fingerprint}`],
            [NULL_TEST_AUC.toFixed(2), "null test AUC", "simulator on both sides: must be near 0.5, passes"],
          ].map(([v, l, s], i) => (
            <motion.div key={l} {...rise} transition={{ ...rise.transition, delay: i * 0.1 }} style={{ borderTop: "1px solid var(--gold-dim)", paddingTop: 16 }}>
              <div className="big">{v}</div>
              <div className="unit">{l}</div>
              <div style={{ color: "var(--mute)", fontSize: 13, marginTop: 4 }}>{s}</div>
            </motion.div>
          ))}
        </div>

        <motion.div className="card" {...rise} style={{ marginTop: 56 }}>
          <h3>What the Detector looks at</h3>
          <p className="cap">Standardized weights of a model fit on the development runs. Blue means a larger value points to Genuine: each effect is stronger on real hardware, so a job that lacks them looks forged.</p>
          <WeightBars weights={D.report.weights} labels={FEATURE_LABELS} />
        </motion.div>
      </div>
    </section>
  );
}

const AXES = ["coh_plain_rise", "spec_shift_max_abs", "ro_vs_calibration"] as const;

function SignatureSpace() {
  const points = useMemo(() => {
    const range = AXES.map((f) => {
      const v = D.signatures.map((s) => s[f]);
      return [Math.min(...v), Math.max(...v)];
    });
    const norm = (v: number, i: number) => (v - range[i][0]) / (range[i][1] - range[i][0] || 1);
    return D.signatures.map((s) => ({
      x: norm(s[AXES[0]], 0), y: norm(s[AXES[1]], 1), z: norm(s[AXES[2]], 2), origin: s.origin,
      fresh: D.fresh_ids.includes(s.run_id), label: `${jobLabel(s.run_id)} ${s.origin} · chunk ${s.chunk + 1}`,
    }));
  }, []);
  return (
    <section className="section">
      <div className="wrap">
        <motion.div {...rise}>
          <div className="stage">Signature space</div>
          <h2 className="title">Two clouds that never touch.</h2>
          <p className="lede">
            All {D.signatures.length} time chunks of all {D.runs.length} Runs, placed by three of their Signature features. Spheres are the 10 Oct
            development runs; wireframe diamonds are jobs from later calibration cycles. Hover a point, drag to orbit.
          </p>
        </motion.div>
        <div style={{ marginTop: 28 }}>
          <div className="legend" style={{ marginBottom: 12 }}>
            <span><i style={{ background: COLORS.genuine }} />Genuine</span>
            <span><i style={{ background: COLORS.forged }} />Forged</span>
            <span>◇ new cycle</span>
          </div>
          <Scene camera={[6.5, 5, 7]} label="3D scatter of Signature features for every chunk of every run">
            <SignatureScene points={points} axes={[FEATURE_LABELS[AXES[0]], FEATURE_LABELS[AXES[1]], FEATURE_LABELS[AXES[2]]]} />
          </Scene>
        </div>
      </div>
    </section>
  );
}

function StressTest() {
  const S = STRONGER_FORGER;
  return (
    <section className="section">
      <div className="wrap">
        <motion.div {...rise}>
          <div className="stage">Stress test · research branch</div>
          <h2 className="title">Then we tried to beat ourselves.</h2>
          <p className="lede">
            A stronger Forger learns over-rotation, detuning and neighbor-dependent readout from one Genuine probe run, and applies them by physical
            qubit. Against the Canaries it works: the Detector trained on stock Twins scored its output as Genuine. Retraining brings it back, with
            a thinner margin. On circuits it was not fitted on, it learned almost nothing.
          </p>
        </motion.div>
        <div className="grid3" style={{ marginTop: 40 }}>
          {[
            [`${S.stockTwins.toFixed(2)}`, "stock Twins", "caught", COLORS.forged],
            [S.v2Twins.map((v) => v.toFixed(2)).join(" / "), "stronger Forger, original Detector", "slips through", "var(--good)"],
            [S.retrainedV2.map((v) => v.toFixed(2)).join(" / "), "stronger Forger, retrained", `Genuine now ${S.retrainedGenuine.join(" / ")}`, COLORS.forged],
          ].map(([v, l, s, c], i) => (
            <motion.div key={l} className="card" {...rise} transition={{ ...rise.transition, delay: i * 0.1 }}>
              <div className="unit">forged score</div>
              <div className="big" style={{ color: c, fontSize: "clamp(44px, 5vw, 72px)" }}>{v}</div>
              <div style={{ fontWeight: 500 }}>{l}</div>
              <div style={{ color: "var(--mute)", fontSize: 14 }}>{s}</div>
            </motion.div>
          ))}
        </div>

        <div className="grid2" style={{ marginTop: 28 }}>
          <motion.div className="card" {...rise}>
            <h3>Distance from real hardware</h3>
            <p className="cap">Total variation distance on Workload circuits (lower is closer). The dashed floor is shot noise alone. Neither forger reaches it on GHZ.</p>
            <div className="legend">
              <span><i style={{ background: COLORS.forged }} />stock Forger</span>
              <span><i style={{ background: "#c9a24a" }} />stronger Forger</span>
              <span><i style={{ background: "#3a4456" }} />shot-noise floor</span>
            </div>
            <GroupedBars label="TVD from real hardware per workload circuit" yLabel="TVD"
              groups={WORKLOAD_TVD.filter((w) => w.cz > 0).map((w) => `${w.run} ${w.circuit.replace("random4_", "r")}`)}
              series={[
                { name: "stock", color: COLORS.forged, values: WORKLOAD_TVD.filter((w) => w.cz > 0).map((w) => w.stock) },
                { name: "stronger", color: "#c9a24a", values: WORKLOAD_TVD.filter((w) => w.cz > 0).map((w) => w.v2) },
                { name: "floor", color: "#3a4456", values: WORKLOAD_TVD.filter((w) => w.cz > 0).map((w) => w.floor) },
              ]} />
          </motion.div>
          <motion.div className="card" {...rise}>
            <h3>Forgeries are too clean</h3>
            <p className="cap">Distance from the ideal noiseless output. Real GHZ results are noisier than either forger predicts: unmodeled two-qubit error.</p>
            <div className="legend">
              <span><i style={{ background: COLORS.genuine }} />real</span>
              <span><i style={{ background: COLORS.forged }} />stock</span>
              <span><i style={{ background: "#c9a24a" }} />stronger</span>
            </div>
            <GroupedBars label="TVD to ideal output" yLabel="TVD to ideal"
              groups={IDEAL_TVD.slice(0, 4).map((r) => r.label.replace("random4_", "r"))}
              series={[
                { name: "real", color: COLORS.genuine, values: IDEAL_TVD.slice(0, 4).map((r) => r.real) },
                { name: "stock", color: COLORS.forged, values: IDEAL_TVD.slice(0, 4).map((r) => r.stock) },
                { name: "stronger", color: "#c9a24a", values: IDEAL_TVD.slice(0, 4).map((r) => r.v2) },
              ]} />
          </motion.div>
        </div>

        <motion.div className="card" {...rise} style={{ marginTop: 28 }}>
          <h3>Next Canary: repeated CNOT</h3>
          <p className="cap">
            Local simulation only. If the real CZ carries a coherent conditional-phase error ε that the noise model lacks, P(target wrong) after
            CNOT<sup>N</sup> grows far faster than the stock Forger predicts. The ε values are hypotheses to test on hardware, not measurements.
          </p>
          <div className="legend">
            <span><i style={{ background: COLORS.forged }} />stock Forger</span>
            <span><i style={{ background: "#c9a24a" }} />ε = 0.02 rad</span>
            <span><i style={{ background: COLORS.genuine }} />ε = 0.05 rad</span>
          </div>
          <LineChart label="Simulated CNOT canary error growth" xTicks={[0, 16, 32, 48, 64]} xLabel="CNOT repeats (N)" yLabel="P(target wrong)" yMax={0.9}
            series={CNOT_SIM.map((s, i) => ({ name: s.name, color: [COLORS.forged, "#c9a24a", COLORS.genuine][i], dashed: i > 0, pts: CNOT_N.map((n, k) => [n, s.values[k]] as [number, number]) }))} />
        </motion.div>

        <motion.div {...rise} style={{ marginTop: 56, color: "var(--mute)", maxWidth: "72ch", fontSize: 15 }}>
          <div className="stage">Limits, stated plainly</div>
          <p>
            {genuineRuns.length} Genuine jobs on {new Set(D.runs.map((r) => r.info.backend ?? "ibm_marrakesh")).size} backend(s),{" "}
            {new Set(genuineRuns.map((r) => r.cycle)).size} calibration cycles. {freshLimit()} J1&apos;s Genuine score rose from about 0.01 in sample
            to {scoreOf(D.fresh_scores, J1_ID).toFixed(2)}, mostly because the coherent features weakened on the new qubits. J1 waited {J1.queue} in
            the queue, ran for {J1.wall}, and billed {J1.billed} QPU seconds.
          </p>
        </motion.div>
      </div>
    </section>
  );
}

function freshLimit() {
  const ids = D.fresh_ids.filter((id) => runById(id).origin === "genuine");
  const wrong = ids.filter((id) => scoreOf(D.fresh_scores, id) > 0.5).length;
  const n = ids.length;
  // One-sided 95% Clopper-Pearson bound for 0 errors in n runs is 1 - 0.05^(1/n).
  return wrong
    ? `The frozen Detector called ${wrong} of ${n} new-cycle Genuine jobs Forged.`
    : `With zero errors in ${n} new-cycle Genuine job${n > 1 ? "s" : ""}, the 95% upper bound on the false-positive rate is still ${(1 - 0.05 ** (1 / n)).toFixed(2)}.`;
}

function Footer() {
  const links = [
    ["Source code", "https://github.com/Karthikeya47/GhostQPU"],
    ["Live Streamlit dashboard", "https://ghostqpu-xk84u6gxdnv2bb26lvakuj.streamlit.app/?data=hardware"],
    ["Demo video", "https://drive.google.com/drive/folders/1M0DklU9nP6OGHuq1RZSj4r4Gzi0MHY0b"],
  ];
  return (
    <footer className="section" style={{ borderTop: "1px solid var(--line)", paddingBottom: 48 }}>
      <div className="wrap" style={{ display: "flex", justifyContent: "space-between", gap: 32, flexWrap: "wrap" }}>
        <div>
          <div className="display" style={{ fontSize: 48, fontWeight: 900 }}>GhostQPU</div>
          <div style={{ color: "var(--mute)", fontSize: 14 }}>Q-Hack India 2026 · Team lwyrup · Quantum Security &amp; Cryptography</div>
        </div>
        <nav style={{ display: "grid", gap: 8 }}>
          {links.map(([l, h]) => <a key={h} href={h} target="_blank" rel="noreferrer">{l} ↗</a>)}
        </nav>
      </div>
    </footer>
  );
}
