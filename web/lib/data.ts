// data.json is produced by scripts/export_web_data.py from the committed Runs; nothing here is invented.
import raw from "@/public/data.json";

export type Origin = "genuine" | "forged";
export type Qubit = { T1: number; T2: number; readout_error: number; prob_meas1_prep0: number; prob_meas0_prep1: number; x: number; y: number };
export type Chip = { cycle: string; qubits: Qubit[]; edges: [number, number, number | null][] };
export type Circuit = { role: "canary" | "workload"; family: string; params: Record<string, number | boolean>; depth: number; ops: Record<string, number> };
export type Run = {
  id: string;
  origin: Origin;
  cycle: string;
  placements: [number, number][];
  info: { shots: number; backend?: string; qpu_seconds?: number; job_id?: string; started_at?: string; twin_of?: string; timestamps?: Record<string, string> };
  circuits: Circuit[];
  curves: {
    coherent: { variant: string; n: number; p1: number }[];
    spectator: { delay_us: number; shift: number }[];
    readout: { target: number; neighbor: number; error: number }[];
  };
  per_placement: { placement: [number, number]; coherent: [number, boolean, number][] }[];
  raster: number[][];
  raster_circuit: { n: number; sandwich: boolean };
};
export type Chunk = { run_id: string; origin: Origin; chunk: number; forged_score: number };
export type Data = {
  runs: Run[];
  fresh_ids: string[];
  features: string[];
  signatures: (Record<string, number> & { run_id: string; origin: Origin; chunk: number })[];
  report: { split: string; auc: number; run_accuracy: number; n_pairs: number; predictions: Chunk[]; weights: [string, number][] };
  fresh_scores: Chunk[];
  chips: { dev: Chip; fresh: Chip };
};

export const D = raw as unknown as Data;
export const runById = (id: string) => D.runs.find((r) => r.id === id)!;
export const twinOf = (id: string) => D.runs.find((r) => r.id === `${id}_forged`);
export const genuineRuns = D.runs.filter((r) => r.origin === "genuine");

export const COLORS = { genuine: "#2a78d6", forged: "#eb6834", gold: "#c9a24a" };

export function jobLabel(id: string) {
  const base = id.replace("_forged", "");
  // Run ids are <backend>_<YYYYMMDD>T<time>_<seed>; A, B and J1 are the names the research notes use.
  const [, ymd, seed] = base.match(/_(\d{8})T\d+_(\d+)$/) ?? [];
  const name = ({ "12894": "Job A", "13117": "Job B", "77679": "Job J1" } as Record<string, string>)[seed] ?? `Job ${seed ?? base}`;
  if (!ymd) return name;
  const when = new Date(`${ymd.slice(0, 4)}-${ymd.slice(4, 6)}-${ymd.slice(6)}T00:00:00Z`);
  return `${name} · ${when.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" })}`;
}

export const FEATURE_LABELS: Record<string, string> = {
  coh_plain_rise: "Coherent: total rise",
  coh_plain_curvature: "Coherent: curvature",
  coh_plain_nonlinearity: "Coherent: non-linearity",
  coh_sx_rise: "Coherent (sx): total rise",
  coh_sx_curvature: "Coherent (sx): curvature",
  coh_sx_nonlinearity: "Coherent (sx): non-linearity",
  spec_shift_mean_abs: "Spectator: mean shift",
  spec_shift_max_abs: "Spectator: max shift",
  ro_context_shift: "Readout: neighbor context",
  ro_vs_calibration: "Readout: drift from calibration",
  drift_lag1: "Shot order: lag-1 correlation",
  drift_dispersion: "Shot order: drift over time",
};

export const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;
export const scoreOf = (chunks: Chunk[], id: string) => mean(chunks.filter((c) => c.run_id === id).map((c) => c.forged_score));
