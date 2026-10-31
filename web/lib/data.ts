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
  info: { shots: number; backend?: string;  qpu_seconds?: number; job_id?: string; started_at?: string; twin_of?: string; timestamps?: Record<string, string> };
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
  hero_id: string;
  by_cycle: { split: string; auc: number; run_accuracy: number; n_cycles: number; runs: { run_id: string; origin: Origin; cycle: string; backend: string; forged_score: number }[]; chunks: { run_id: string; chunk: number; forged_score: number }[] };
  frozen: { features: string[]; mean: number[]; scale: number[]; coef: number[]; intercept: number };
  pilot: { id: string; cycle: string; qpu_seconds: number; curves: { placement: string; family: string; control: number; n: number; hardware: number; stock: number; se: number }[]; fits: { placement: string; family: string; control: number; theta: number; z: number; chi2_per_dof: number }[] }[];
  features: string[];
  signatures: (Record<string, number> & { run_id: string; origin: Origin; chunk: number })[];
  report: { split: string; auc: number; run_accuracy: number; n_pairs: number; predictions: Chunk[]; weights: [string, number][] };
  fresh_scores: Chunk[];
  chips: { dev: Chip; fresh: Chip };
};

export const D = raw as unknown as Data;
export const runById = (id: string) => D.runs.find((r) => r.id === id)!;
export const twinOf = (id: string) => D.runs.find((r) => r.id === `${id}_forged`);
// A Twin is always shown beside the Genuine Run it was forged from.
export const genuineIdOf = (id: string) => id.replace(/_forged$/, "");
export const genuineRuns = D.runs.filter((r) => r.origin === "genuine");

export const COLORS = { genuine: "#2a78d6", forged: "#eb6834", gold: "#8fd3ff" };

export function jobLabel(id: string) {
  const base = id.replace("_forged", "");
  // Run ids are <backend>_<YYYYMMDD>T<time>_<seed>; A, B and J1 are the names the research notes use.
  const [, ymd, seed] = base.match(/_(\d{8})T\d+_(\d+)$/) ?? [];
  const name = ({ "12894": "Job A", "13117": "Job B", "77679": "Job J1", "85181": "Job J2", "86034": "Job F1", "88635": "Job K1", "89619": "Job K2", "89673": "Job F2", "75072": "Job J3", "75084": "Job F3", "75097": "Job K3", "75600": "Job J4", "75616": "Job K4", "75630": "Job F4", "80201": "Job J5", "80240": "Job K5", "80270": "Job F5", "81197": "Job J6", "18122": "Job J7", "18137": "Job K6", "18152": "Job F6", "19081": "Job F7", "19072": "Job J8", "19126": "Job F8", "19168": "Job K7", "21758": "Job K8", "23409": "Job J9", "23428": "Job K9", "23445": "Job J10", "23460": "Job K10" } as Record<string, string>)[seed] ?? `Job ${seed ?? base}`;
  const backend = base.match(/^ibm_([a-z]+)_/)?.[1];
  const tag = backend && backend !== "marrakesh" ? ` · ${backend}` : "";
  if (!ymd) return name + tag;
  const when = new Date(`${ymd.slice(0, 4)}-${ymd.slice(4, 6)}-${ymd.slice(6)}T00:00:00Z`);
  return `${name} · ${when.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" })}${tag}`;
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
export type Pilot = Data["pilot"][number];
