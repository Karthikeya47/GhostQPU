"use client";
import { AnimatePresence, motion, MotionConfig } from "framer-motion";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { GroupedBars, LineChart, WeightBars } from "@/components/charts";
import { ShotRaster } from "@/components/ShotRaster";
import { Wire } from "@/components/Wire";
import { DayVariance } from "@/components/DayVariance";
import { ForgerLab } from "@/components/ForgerLab";
import { JobConsole } from "@/components/JobConsole";
import { Vault } from "@/components/Vault";
import { COLORS, D, FEATURE_LABELS, genuineRuns, jobLabel, mean, type Pilot, runById, scoreOf, twinOf } from "@/lib/data";
import { IDEAL_TVD, J1, NULL_TEST_AUC, STRONGER_FORGER, WORKLOAD_TVD } from "@/lib/research";

const Scene = dynamic(() => import("@/components/three").then((m) => m.Scene), { ssr: false });
const ChipScene = dynamic(() => import("@/components/three").then((m) => m.ChipScene), { ssr: false });
const CoherentScene = dynamic(() => import("@/components/three").then((m) => m.CoherentScene), { ssr: false });
const BlochScene = dynamic(() => import("@/components/three").then((m) => m.BlochScene), { ssr: false });
const SignatureScene = dynamic(() => import("@/components/three").then((m) => m.SignatureScene), { ssr: false });

const fresh = runById(D.hero_id);
const J1_ID = "ibm_marrakesh_20261027T050804_77679";
const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;

const rise = { initial: { opacity: 0, y: 40 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-10%" }, transition: { duration: 0.8, ease: [0.2, 0.8, 0.2, 1] as const } };

const CHAPTERS = [
  { id: "problem", title: "The problem" },
  { id: "trap", title: "The trap" },
  { id: "run", title: "Run a job" },
  { id: "evidence", title: "The evidence" },
  { id: "verdict", title: "The verdict" },
  { id: "break", title: "Break it" },
] as const;

export default function Page() {
  const [runId, setRunId] = useState(genuineRuns[genuineRuns.length - 1].id);
  const [ch, setCh] = useState(0);
  const go = useCallback((i: number) => setCh(Math.max(0, Math.min(CHAPTERS.length - 1, i))), []);
  const first = useRef(true);

  useEffect(() => {
    if (first.current) { first.current = false; return; }
    window.history.replaceState(null, "", `#${CHAPTERS[ch].id}`);
    window.scrollTo({ top: 0 });
  }, [ch]);

  useEffect(() => {
    const i = CHAPTERS.findIndex((c) => `#${c.id}` === window.location.hash);
    if (i > 0) setCh(i);
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (t.closest("input, textarea, select, [contenteditable]") || e.altKey || e.ctrlKey || e.metaKey) return;
      if (e.key === "ArrowRight") setCh((c) => Math.min(c + 1, CHAPTERS.length - 1));
      if (e.key === "ArrowLeft") setCh((c) => Math.max(c - 1, 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const body = [
    <><Hero go={go} /><Threat /></>,
    <><BatchSection /><BlochSection /></>,
    <RunIt key="run" />,
    <><Evidence runId={runId} setRunId={setRunId} /><Coherent3D runId={runId} setRunId={setRunId} /><Shots runId={runId} /></>,
    <><Verdict /><SignatureSpace /></>,
    <><BeatIt /><StressTest /><Footer /></>,
  ][ch];

  return (
    <MotionConfig reducedMotion="user">
      <Vault strength={ch === 0 ? 0.95 : 0.32} />
      <div className="app">
        <nav className="chapnav" aria-label="Story chapters">
          <button className="brand" onClick={() => go(0)}>GhostQPU</button>
          <div className="chaps">
            {CHAPTERS.map((c, i) => (
              <button key={c.id} className={`chap${i < ch ? " done" : ""}`} aria-current={i === ch ? "step" : undefined} onClick={() => go(i)}>
                <span className="n">{i + 1}</span><span className="t">{c.title}</span>
              </button>
            ))}
          </div>
          <motion.div className="progress" animate={{ width: `${((ch + 1) / CHAPTERS.length) * 100}%` }} transition={{ type: "spring", stiffness: 120, damping: 22 }} />
        </nav>
        <AnimatePresence mode="wait">
          <motion.main key={ch} className="chapter" initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }}
            transition={{ duration: 0.45, ease: [0.2, 0.8, 0.2, 1] }}>
            {body}
          </motion.main>
        </AnimatePresence>
        <div className="pager">
          {ch > 0 ? <button onClick={() => go(ch - 1)}>← {CHAPTERS[ch - 1].title}</button> : <span />}
          <span className="hint">← → to move between chapters</span>
          {ch < CHAPTERS.length - 1 ? <button className="next" onClick={() => go(ch + 1)}>{CHAPTERS[ch + 1].title} →</button> : <span />}
        </div>
      </div>
    </MotionConfig>
  );
}

function Hero({ go }: { go: (i: number) => void }) {
  const canaries = fresh.circuits.filter((c) => c.role === "canary").length;
  return (
    <header style={{ position: "relative", minHeight: "calc(100svh - 60px)", display: "flex", alignItems: "flex-end", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0 }}>
        <Scene camera={[0, 7.5, 9.5]} className="hero3d" label="3D model of the 156-qubit ibm_marrakesh chip with its forged copy floating above">
          <ChipScene chip={D.chips.fresh} placements={fresh.placements} />
        </Scene>
      </div>
      <div className="hero-shade" style={{ position: "absolute", inset: 0, pointerEvents: "none", background: "linear-gradient(180deg, transparent 40%, rgba(3,11,23,0.85) 92%)" }} />
      <div className="wrap" style={{ position: "relative", width: "100%", padding: "0 var(--gutter) 56px", pointerEvents: "none" }}>
        <motion.div className="stage" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
          ibm_marrakesh · 156 qubits · live calibration
        </motion.div>
        <h1 className="display" style={{ fontWeight: 500, fontSize: "clamp(34px, 5.4vw, 80px)", lineHeight: 1.02, maxWidth: "15ch", letterSpacing: "-0.04em" }}>
          {"Did your job ever touch a quantum computer?".split(" ").map((w, i) => (
            <motion.span key={i} style={{ display: "inline-block", marginRight: "0.24em", color: w === "touch" ? "var(--gold)" : undefined, textShadow: w === "touch" ? "0 0 30px #8fd3ff88" : undefined }}
              initial={{ opacity: 0, y: 40, filter: "blur(10px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ delay: 0.4 + i * 0.08, duration: 0.9, ease: [0.2, 0.8, 0.2, 1] }}>{w}</motion.span>
          ))}
        </h1>
        <motion.p className="lede" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.3 }}>
          The bright lattice is the real chip, drawn from its published coupling map. The orange copy floating above it is the <b>Forger</b>: a
          simulator built from the same public calibration. GhostQPU hides {canaries} <b>Canaries</b> in your Batch to tell them apart.
        </motion.p>
        <motion.div style={{ marginTop: 28, display: "flex", gap: 12, flexWrap: "wrap", pointerEvents: "auto" }}
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.7 }}>
          <button className="run-btn" style={{ marginLeft: 0 }} onClick={() => go(1)}>Start the story →</button>
          <button className="tab" onClick={() => go(2)}>▶ Jump to the live demo</button>
        </motion.div>
        <motion.div className="mono" style={{ marginTop: 22, fontSize: 12, color: "var(--mute)", display: "flex", gap: 24, flexWrap: "wrap" }}
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.9 }}>
          <span><span style={{ color: "var(--gold)" }}>●</span> canary placements</span>
          <span>brightness = T1</span>
          <span>hover a qubit for its calibration</span>
        </motion.div>
      </div>
    </header>
  );
}

function RunIt() {
  return (
    <section className="section" id="run" style={{ paddingTop: 48 }}>
      <div className="wrap">
        <motion.div {...rise}>
          <Wire gate="U">Run it yourself</Wire>
          <h2 className="title">Submit a job. Catch the ghost.</h2>
          <p className="lede">
            Each press replays one of the <b>{D.by_cycle.runs.length} real jobs</b> we ran on IBM quantum computers or forged from their
            calibration. The shots, Signatures and scores are the recorded ones; only the pacing is staged. Make your call before the Detector does.
          </p>
        </motion.div>
        <motion.div {...rise} style={{ marginTop: 32 }}>
          <JobConsole />
        </motion.div>
      </div>
    </section>
  );
}

function BlochSection() {
  const machines = [...new Set(genuineRuns.map((r) => r.info.backend ?? "ibm_marrakesh"))].sort();
  const latest = (m: string) => [...genuineRuns].reverse().find((r) => (r.info.backend ?? "ibm_marrakesh") === m)!;
  const [machine, setMachine] = useState(machines.includes("ibm_kingston") ? "ibm_kingston" : machines[0]);
  const [n, setN] = useState(0);
  const [playing, setPlaying] = useState(false);
  const g = latest(machine);
  const t = twinOf(g.id);
  // The placement with the largest error at N = 128 shows the effect most clearly.
  const pl = g.per_placement.reduce((b, p) => {
    const at = (x: typeof p) => x.coherent.find((c) => c[0] === 128 && !c[1])?.[2] ?? 0;
    return at(p) > at(b) ? p : b;
  });
  const k = g.per_placement.indexOf(pl);
  const curve = (r: typeof g) => r.per_placement[k].coherent.filter((c) => !c[1]).sort((a, b) => a[0] - b[0]).map((c) => [c[0], c[2]] as [number, number]);
  const hw = curve(g);
  const fz = t ? curve(t) : hw.map(([x]) => [x, 0] as [number, number]);
  const at = (c: [number, number][]) => {
    const i = c.findIndex(([x]) => x >= n);
    if (i <= 0) return c[0][1];
    return c[i - 1][1] + ((c[i][1] - c[i - 1][1]) * (n - c[i - 1][0])) / (c[i][0] - c[i - 1][0]);
  };
  const play = () => {
    setPlaying(true);
    setN(0);
    let v = 0;
    const id = window.setInterval(() => {
      v += 2;
      setN(Math.min(v, 128));
      if (v >= 128) { window.clearInterval(id); setPlaying(false); }
    }, 40);
  };
  return (
    <section className="section">
      <div className="wrap">
        <motion.div {...rise}>
          <Wire gate="Xⁿ">One qubit, 128 gates</Wire>
          <h2 className="title">Watch the qubit drift off the pole.</h2>
          <p className="lede">
            An X gate flips a qubit; two flips should bring it home to |0⟩. Real pulses overshoot by a hair, and the overshoot adds up coherently: the
            <b style={{ color: COLORS.genuine }}> hardware&apos;s state</b> swings away from the pole. The <b style={{ color: COLORS.forged }}>Forger&apos;s</b>{" "}
            noise model only knows random error, so its state just fades toward the centre. Measured on Q{pl.placement[0]} of {machine}.
          </p>
        </motion.div>
        <div className="grid2" style={{ marginTop: 28, alignItems: "center" }}>
          <Scene camera={[3.6, 2.2, 4.4]} label="Bloch sphere: hardware state vector rotates away from |0⟩, forger vector shrinks">
            <BlochScene hardware={hw} forger={fz} n={n} />
          </Scene>
          <div className="card">
            <div className="tabs" role="group" aria-label="Machine" style={{ marginTop: 0 }}>
              {machines.map((m) => <button key={m} className="tab" aria-pressed={m === machine} onClick={() => { setMachine(m); setN(0); }}>{m.replace("ibm_", "")}</button>)}
            </div>
            <label style={{ display: "grid", gap: 8 }}>
              <span className="mono" style={{ fontSize: 13, color: "var(--mute)" }}>X gates applied: <b style={{ color: "var(--frost)", fontSize: 20 }}>{Math.round(n)}</b></span>
              <input className="slider" style={{ accentColor: "var(--gold)" }} type="range" min={0} max={128} step={1} value={n} onChange={(e) => setN(+e.target.value)} />
            </label>
            <button className="run-btn" style={{ marginLeft: 0, marginTop: 16 }} onClick={play} disabled={playing}>▶ Apply 128 X gates</button>
            <div className="grid2" style={{ marginTop: 24, gap: 12 }}>
              <div><div className="unit">hardware P(1)</div><div className="big" style={{ fontSize: 48, color: COLORS.genuine }}>{pct(at(hw), 0)}</div></div>
              <div><div className="unit">Forger P(1)</div><div className="big" style={{ fontSize: 48, color: COLORS.forged }}>{pct(at(fz), 0)}</div></div>
            </div>
            <p className="cap" style={{ marginTop: 12 }}>
              Measured at N = 0, 4, 8, 16, 32, 64, 128 and interpolated between. Drawn as pure rotation for hardware and pure decay for the Forger, which
              is what the curve shapes indicate; real states have some of both.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function BeatIt() {
  return (
    <section className="section">
      <div className="wrap">
        <motion.div {...rise}>
          <Wire gate="U†">Play the Forger</Wire>
          <h2 className="title">Try to beat the Detector.</h2>
          <p className="lede">
            You are the dishonest provider. Your simulator already matches IBM&apos;s published calibration. How much real hardware physics do you have to
            fake before the frozen Detector waves your job through?
          </p>
        </motion.div>
        <motion.div {...rise} style={{ marginTop: 32 }}>
          <ForgerLab />
        </motion.div>
      </div>
    </section>
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
          <Wire gate="X">The threat</Wire>
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

const FAMILY_COLOR: Record<string, string> = { coherent: "#8fd3ff", spectator: "#5aa0f2", readout: "#b48cf0" };

function BatchSection() {
  const [reveal, setReveal] = useState(false);
  return (
    <section className="section" style={{ background: "linear-gradient(180deg, transparent, rgba(6,24,45,0.5) 30%, rgba(6,24,45,0.5) 70%, transparent)" }}>
      <div className="wrap">
        <motion.div {...rise}>
          <Wire gate="H">Inside one Batch · {jobLabel(fresh.id)}</Wire>
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
              <span><i style={{ background: "#eaf4ff" }} />workload</span>
            </div>
          )}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(118px, 1fr))", gap: 10 }}>
          {fresh.circuits.map((c, i) => {
            const color = c.role === "workload" ? "#eaf4ff" : FAMILY_COLOR[c.family];
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
                    <motion.div key="h" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={{ marginTop: 4, color: "#c2d6ea" }}>
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
    <label className="picker">
      <span className="unit">Genuine job</span>
      <select value={runId} onChange={(e) => setRunId(e.target.value)}>
        {genuineRuns.map((r) => (
          <option key={r.id} value={r.id}>{jobLabel(r.id)}{D.fresh_ids.includes(r.id) ? " · scored blind" : " · training"}</option>
        ))}
      </select>
    </label>
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
          <Wire gate="Rx(ε)">Evidence</Wire>
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
          <Wire gate="⊗4">Per placement, in 3D</Wire>
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
          <Wire gate="M">Shot record · {jobLabel(runId)}</Wire>
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
  const fresh_ = [...new Set(D.fresh_scores.map((c) => c.run_id))];
  const frozenRight = fresh_.filter((id) => (scoreOf(D.fresh_scores, id) > 0.5 ? "forged" : "genuine") === runById(id).origin).length;
  const cycles = new Set(fresh_.map((id) => runById(id).cycle)).size;
  return (
    <section className="section" style={{ background: "linear-gradient(180deg, transparent, rgba(6,24,45,0.5) 20%, rgba(6,24,45,0.5) 80%, transparent)" }}>
      <div className="wrap">
        <motion.div {...rise}>
          <Wire gate="M">The Detector</Wire>
          <h2 className="title">How sure is the Detector?</h2>
          <p className="lede">
            A logistic regression on 12 Signature features, scored on 8 time-ordered chunks per job. The frozen version was trained once on two
            jobs from 10 Oct and never retrained; every later job, on every machine, was scored by it blind.
          </p>
        </motion.div>


        <div className="grid4" style={{ marginTop: 56 }}>
          {[
            [D.report.auc.toFixed(2), "AUC, held out", `split ${D.report.split}`],
            [pct(D.report.run_accuracy, 0), "job-level accuracy", `${D.report.n_pairs} Genuine/Forged pairs`],
            [`${frozenRight}/${fresh_.length}`, "frozen Detector, later jobs", `${cycles} new calibration cycles · fingerprint ${J1.fingerprint}`],
            [NULL_TEST_AUC.toFixed(2), "null test AUC", "simulator on both sides: must be near 0.5, passes"],
          ].map(([v, l, s], i) => (
            <motion.div key={l} {...rise} transition={{ ...rise.transition, delay: i * 0.1 }} style={{ borderTop: "1px solid var(--gold-dim)", paddingTop: 16 }}>
              <div className="big">{v}</div>
              <div className="unit">{l}</div>
              <div style={{ color: "var(--mute)", fontSize: 13, marginTop: 4 }}>{s}</div>
            </motion.div>
          ))}
        </div>

        <ByCycle />

        <motion.div {...rise} style={{ marginTop: 28 }}>
          <DayVariance />
        </motion.div>

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
          <Wire gate="Σ">Signature space</Wire>
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
          <Wire gate="CZ">Stress test · research branch</Wire>
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
              <span><i style={{ background: "#8fd3ff" }} />stronger Forger</span>
              <span><i style={{ background: "#24476d" }} />shot-noise floor</span>
            </div>
            <GroupedBars label="TVD from real hardware per workload circuit" yLabel="TVD"
              groups={WORKLOAD_TVD.filter((w) => w.cz > 0).map((w) => `${w.run} ${w.circuit.replace("random4_", "r")}`)}
              series={[
                { name: "stock", color: COLORS.forged, values: WORKLOAD_TVD.filter((w) => w.cz > 0).map((w) => w.stock) },
                { name: "stronger", color: "#8fd3ff", values: WORKLOAD_TVD.filter((w) => w.cz > 0).map((w) => w.v2) },
                { name: "floor", color: "#24476d", values: WORKLOAD_TVD.filter((w) => w.cz > 0).map((w) => w.floor) },
              ]} />
          </motion.div>
          <motion.div className="card" {...rise}>
            <h3>Forgeries are too clean</h3>
            <p className="cap">Distance from the ideal noiseless output. Real GHZ results are noisier than either forger predicts: unmodeled two-qubit error.</p>
            <div className="legend">
              <span><i style={{ background: COLORS.genuine }} />real</span>
              <span><i style={{ background: COLORS.forged }} />stock</span>
              <span><i style={{ background: "#8fd3ff" }} />stronger</span>
            </div>
            <GroupedBars label="TVD to ideal output" yLabel="TVD to ideal"
              groups={IDEAL_TVD.slice(0, 4).map((r) => r.label.replace("random4_", "r"))}
              series={[
                { name: "real", color: COLORS.genuine, values: IDEAL_TVD.slice(0, 4).map((r) => r.real) },
                { name: "stock", color: COLORS.forged, values: IDEAL_TVD.slice(0, 4).map((r) => r.stock) },
                { name: "stronger", color: "#8fd3ff", values: IDEAL_TVD.slice(0, 4).map((r) => r.v2) },
              ]} />
          </motion.div>
        </div>

        {D.pilot.length ? <PilotCard /> : null}

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

function ByCycle() {
  const B = D.by_cycle;
  const pairs = genuineRuns.map((g) => ({ g, s: B.runs.find((r) => r.run_id === g.id), t: B.runs.find((r) => r.run_id === `${g.id}_forged`) }));
  return (
    <motion.div className="card" {...rise} style={{ marginTop: 56 }}>
      <h3>Hold out a whole calibration cycle</h3>
      <p className="cap">
        Every job below is scored by a Detector trained on all the other {B.n_cycles - 1} calibration cycles, never on its own, across all three
        machines. AUC {B.auc.toFixed(2)}, {pct(B.run_accuracy, 0)} of jobs correct.
      </p>
      <div className="scrollx">
        <table className="data">
          <thead><tr><th>job</th><th>machine</th><th>calibration cycle</th><th>Genuine scored</th><th>its Twin scored</th></tr></thead>
          <tbody>
            {pairs.map(({ g, s, t }) => (
              <tr key={g.id}>
                <td>{jobLabel(g.id).split(" · ")[0]}</td>
                <td>{(s?.backend ?? "").replace("ibm_", "")}</td>
                <td>{g.cycle.slice(0, 16).replace("T", " ")}</td>
                <td style={{ color: COLORS.genuine }}>{s ? s.forged_score.toFixed(2) : "n/a"}</td>
                <td style={{ color: COLORS.forged }}>{t ? t.forged_score.toFixed(2) : "n/a"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="cap" style={{ marginTop: 12 }}>Scores are the probability of Forged. Below 0.5 is a Genuine Verdict.</p>
    </motion.div>
  );
}

function PilotCard() {
  const machine = (id: string) => id.match(/^pilot_ibm_([a-z]+)_/)?.[1] ?? id;
  const detected = (r: Pilot) => new Set(r.fits.filter((f) => f.family === "cnot" && f.z > 3.2).map((f) => f.placement)).size;
  const [pi, setPi] = useState(() => D.pilot.reduce((b, r, i) => (detected(r) >= detected(D.pilot[b]) && machine(r.id) === "marrakesh" ? i : b), 0));
  const total = D.pilot.reduce((a, r) => a + detected(r), 0);
  const pairs = D.pilot.reduce((a, r) => a + new Set(r.curves.map((c) => c.placement)).size, 0);
  return (
    <motion.div className="card" {...rise} style={{ marginTop: 28 }}>
      <div className="stage" style={{ marginBottom: 8 }}>New on hardware · {D.pilot.length} jobs · {D.pilot.reduce((a, r) => a + (r.qpu_seconds ?? 0), 0)} QPU seconds</div>
      <h3>The next Canary: repeated CNOT</h3>
      <p className="cap">
        CNOT<sup>N</sup> with N even, so the ideal target reads 0. A coherent error tied to the CZ pulse, which the Forger does not model, passes the
        pre-registered threshold on <b>{total} of {pairs}</b> qubit pairs across {D.pilot.length} machines. The control rows separate the causes:
        control 0 isolates a local phase on the target, control 1 adds any conditional phase, and the idle rows swap the CZ for an equal-length wait.
      </p>
      <div className="tabs" role="group" aria-label="Machine">
        {D.pilot.map((r, i) => <button key={r.id} className="tab" aria-pressed={i === pi} onClick={() => setPi(i)}>{machine(r.id)} · {detected(r)}/4 pairs</button>)}
      </div>
      <PilotBody key={pi} run={D.pilot[pi]} />
    </motion.div>
  );
}

function PilotBody({ run }: { run: Pilot }) {
  const placements = [...new Set(run.curves.map((c) => c.placement))];
  // Open on the pair with the strongest CZ-linked signal; the reader can step through the rest.
  const top = [...run.fits].filter((f) => f.family === "cnot").sort((a, b) => b.z - a.z)[0];
  const [pl, setPl] = useState(top.placement);
  const pts = (family: string, control: number, key: "hardware" | "stock") =>
    run.curves.filter((c) => c.placement === pl && c.family === family && c.control === control)
      .sort((a, b) => a.n - b.n).map((c) => [c.n, c[key]] as [number, number]);
  const fit = (family: string, control: number) => run.fits.find((f) => f.placement === pl && f.family === family && f.control === control)!;
  return (
    <>
      <div className="tabs" role="group" aria-label="Qubit pair">
        {placements.map((p) => <button key={p} className="tab" aria-pressed={p === pl} onClick={() => setPl(p)}>Q{p}</button>)}
      </div>
      <div className="legend">
        <span><i style={{ background: COLORS.genuine }} />hardware, control 1</span>
        <span><i style={{ background: COLORS.forged }} />Forger, control 1</span>
        <span><i style={{ background: COLORS.gold }} />hardware, control 0</span>
        <span><i style={{ background: "#7f97b3" }} />hardware, CZ replaced by idle</span>
      </div>
      <LineChart key={pl} label={`CNOT canary on qubits ${pl}: P(target wrong) vs repeats`} xTicks={[0, 32, 64, 96, 128]} xLabel="CNOT repeats (N)"
        yLabel="P(target wrong)" yMax={1}
        series={[
          { name: "hardware c=1", color: COLORS.genuine, pts: pts("cnot", 1, "hardware") },
          { name: "Forger c=1", color: COLORS.forged, pts: pts("cnot", 1, "stock") },
          { name: "hardware c=0", color: COLORS.gold, dashed: true, pts: pts("cnot", 0, "hardware") },
          { name: "hardware idle", color: "#7f97b3", dashed: true, pts: pts("idle", 1, "hardware") },
        ]} />
      <div className="scrollx" style={{ marginTop: 16 }}>
        <table className="data">
          <thead><tr><th>circuit</th><th>coherent turn the Forger misses (rad per repeat)</th><th>z vs none</th></tr></thead>
          <tbody>
            {[["cnot", 1], ["cnot", 0], ["idle", 1], ["idle", 0]].map(([f, c]) => {
              const r = fit(f as string, c as number);
              return <tr key={`${f}${c}`}><td>{f} · control {c}</td><td>{r.theta.toFixed(3)}</td><td style={{ color: r.z > 3.2 ? "var(--frost)" : "var(--mute)" }}>{r.z.toFixed(1)}</td></tr>;
            })}
          </tbody>
        </table>
      </div>
      <p className="cap" style={{ marginTop: 12 }}>
        One job per machine, in calibration cycle {run.cycle.slice(0, 16).replace("T", " ")}. The fit&apos;s χ² per degree of freedom is well above 1
        on several curves, so the intervals are optimistic. z above 3.2 is the pre-registered detection threshold.
      </p>
    </>
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
