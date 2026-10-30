"use client";
import { useState } from "react";
import { LineChart } from "@/components/charts";
import { COLORS, D, mean } from "@/lib/data";

const MACHINE_COLORS: Record<string, string> = { ibm_marrakesh: "#5aa0f2", ibm_fez: "#b48cf0", ibm_kingston: "#5ec8c0" };
const METRICS = [
  { key: "coh_plain_rise", name: "Over-rotation", y: "P(1) rise after 128 X gates" },
  { key: "spec_shift_max_abs", name: "Neighbor crosstalk", y: "max spectator shift" },
  { key: "score", name: "Detector score", y: "held-out forged score" },
] as const;

const dayOf = (cycle: string) => cycle.slice(0, 10);
const fmtDay = (d: string) => new Date(`${d}T00:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });

/** One point per machine per calendar day: the mean over that day's Runs, Genuine vs the Forger's Twins. */
export function DayVariance() {
  const [metric, setMetric] = useState<(typeof METRICS)[number]["key"]>("coh_plain_rise");
  const days = [...new Set(D.runs.map((r) => dayOf(r.cycle)))].sort();
  const value = (runId: string) =>
    metric === "score"
      ? D.by_cycle.runs.find((r) => r.run_id === runId)?.forged_score ?? NaN
      : mean(D.signatures.filter((s) => s.run_id === runId).map((s) => s[metric]));
  const machines = [...new Set(D.runs.map((r) => r.info.backend ?? "ibm_marrakesh"))].sort();
  const series = machines.map((m) => ({
    name: m.replace("ibm_", ""),
    color: MACHINE_COLORS[m] ?? COLORS.genuine,
    pts: days.flatMap((d, i) => {
      const runs = D.runs.filter((r) => r.origin === "genuine" && (r.info.backend ?? "ibm_marrakesh") === m && dayOf(r.cycle) === d);
      return runs.length ? [[i, mean(runs.map((r) => value(r.id)))] as [number, number]] : [];
    }),
  }));
  const forger = {
    name: "Forger (all machines)",
    color: COLORS.forged,
    dashed: true,
    pts: days.map((d, i) => [i, mean(D.runs.filter((r) => r.origin === "forged" && dayOf(r.cycle) === d).map((r) => value(r.id)))] as [number, number]),
  };
  const spread = machines.map((m) => {
    const v = D.runs.filter((r) => r.origin === "genuine" && (r.info.backend ?? "ibm_marrakesh") === m).map((r) => value(r.id));
    return { m, lo: Math.min(...v), hi: Math.max(...v), n: v.length };
  });
  const M = METRICS.find((x) => x.key === metric)!;
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
        <div>
          <h3>Day to day</h3>
          <p className="cap">Each line is one machine, averaged over that day&apos;s jobs. Real hardware wanders between calibrations; the Forger&apos;s baseline barely moves. Days are evenly spaced, not to scale, and placements differ between days.</p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {METRICS.map((x) => <button key={x.key} className="tab" aria-pressed={x.key === metric} onClick={() => setMetric(x.key)}>{x.name}</button>)}
        </div>
      </div>
      <div className="legend">
        {series.map((s) => <span key={s.name}><i style={{ background: s.color }} />{s.name}</span>)}
        <span><i style={{ background: COLORS.forged }} />Forger</span>
        {metric === "score" && <span style={{ color: "var(--gold)" }}>0.5 = threshold</span>}
      </div>
      <LineChart key={metric} label={`${M.name} by day and machine`} series={[...series, forger]}
        xTicks={days.map((_, i) => i)} xFmt={(i) => fmtDay(days[Math.round(i)] ?? "")} xLabel="calibration day" yLabel={M.y}
        yMax={metric === "score" ? 1 : undefined} />
      <div className="scrollx" style={{ marginTop: 12 }}>
        <table className="data">
          <thead><tr><th>machine</th><th>Genuine jobs</th><th>lowest</th><th>highest</th></tr></thead>
          <tbody>
            {spread.map((r) => (
              <tr key={r.m}><td>{r.m.replace("ibm_", "")}</td><td>{r.n}</td><td>{r.lo.toFixed(3)}</td><td>{r.hi.toFixed(3)}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
