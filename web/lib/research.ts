// Numbers transcribed from docs/research/*.md (computed by scripts in the repo, not by this site).

// workload-generalization.md: TVD from real hardware to the near-exact forger distribution.
export const WORKLOAD_TVD = [
  { run: "A", circuit: "ghz5", cz: 4, stock: 0.081, v2: 0.081, floor: 0.026 },
  { run: "B", circuit: "ghz5", cz: 4, stock: 0.072, v2: 0.073, floor: 0.026 },
  { run: "A", circuit: "random4_1", cz: 12, stock: 0.048, v2: 0.042, floor: 0.042 },
  { run: "A", circuit: "random4_0", cz: 16, stock: 0.072, v2: 0.064, floor: 0.032 },
  { run: "A", circuit: "random4_2", cz: 6, stock: 0.034, v2: 0.035, floor: 0.015 },
  { run: "B", circuit: "random4_0", cz: 10, stock: 0.048, v2: 0.051, floor: 0.039 },
  { run: "B", circuit: "random4_2", cz: 5, stock: 0.078, v2: 0.063, floor: 0.033 },
  { run: "B", circuit: "random4_1", cz: 0, stock: 0.02, v2: 0.021, floor: 0.022 },
];

// workload-generalization.md: TVD to the ideal noiseless output. Real hardware is noisier than both forgers.
export const IDEAL_TVD = [
  { label: "A ghz5", real: 0.132, stock: 0.08, v2: 0.082 },
  { label: "B ghz5", real: 0.123, stock: 0.072, v2: 0.076 },
  { label: "A random4_0", real: 0.112, stock: 0.057, v2: 0.054 },
  { label: "B random4_2", real: 0.09, stock: 0.049, v2: 0.047 },
  { label: "A random4_1", real: 0.064, stock: 0.048, v2: 0.062 },
  { label: "A random4_2", real: 0.059, stock: 0.026, v2: 0.059 },
  { label: "B random4_0", real: 0.055, stock: 0.064, v2: 0.041 },
  { label: "B random4_1", real: 0.053, stock: 0.043, v2: 0.06 },
];

// handoff.md: Detector trained on Genuine + stock Twins, then shown the stronger Forger (forger.py).
export const STRONGER_FORGER = {
  stockTwins: 0.97,
  v2Twins: [0.07, 0.11],
  retrainedV2: [0.64, 0.8],
  retrainedGenuine: [0.24, 0.29],
};

// fresh-hardware-j1.md
export const J1 = {
  job: "dbg33ctjm0ks73efpbc0",
  queue: "1 h 49 min 31 s",
  wall: "70.1 s",
  billed: 11,
  remaining: 567,
  fingerprint: "51a3b821bbcd587d",
};

// README.md
export const NULL_TEST_AUC = 0.52; // rerun 2026-10-30 with the seeded Forger

// scripts/score_ten.py: same model trained on the 10 earliest Genuine Runs and their Twins, every later Run scored blind.
export const TEN_JOB = { trained: 10, cycles: 9, machines: 3, right: 40, scored: 40, laterCycles: 14, worstGenuine: 0.22, frozenWorst: 0.43 };

// mirror-canaries.md: disguised Canaries (random U then U inverse, ideal all zeros), one job per machine on 2026-10-31.
export const MIRROR = [
  { machine: "marrakesh", hardware: 0.756, forger: 0.879, cleaner: 15, strong: 13 },
  { machine: "kingston", hardware: 0.875, forger: 0.912, cleaner: 15, strong: 9 },
  { machine: "fez", hardware: 0.762, forger: 0.878, cleaner: 15, strong: 9 },
];

// Every IBM job that is not a full 34-circuit Batch: data/short, data/pilot/runs, data/pilot/unpublished, data/mirror/runs.
export const OTHER_JOB_LIST = [
  {"kind": "CNOT pilot (first try)", "machine": "marrakesh", "at": "2026-10-28 15:59", "job": "dbh1m6kdgr2s73cshlj0", "qpu": 11, "result": "first pilot, Karthikeya's account; not analyzed"},
  {"kind": "CNOT pilot", "machine": "marrakesh", "at": "2026-10-29 15:01", "job": "dbhlvcune4hc73bd5vng", "qpu": 11, "result": "CZ error detected on 3 of 4 qubit pairs"},
  {"kind": "CNOT pilot", "machine": "fez", "at": "2026-10-29 16:00", "job": "dbhmrds2d77s739d2de0", "qpu": 11, "result": "CZ error detected on 4 of 4 qubit pairs"},
  {"kind": "CNOT pilot", "machine": "kingston", "at": "2026-10-29 16:00", "job": "dbhmr9o1h92s7382340g", "qpu": 11, "result": "CZ error detected on 4 of 4 qubit pairs"},
  {"kind": "CNOT pilot", "machine": "marrakesh", "at": "2026-10-30 15:54", "job": "dbibr8une4hc73be93a0", "qpu": 11, "result": "CZ error detected on 2 of 4 qubit pairs"},
  {"kind": "Short Batch, 250 shots", "machine": "marrakesh", "at": "2026-10-30 17:10", "job": "dbicv00hoj4c73b5unvg", "qpu": 5, "result": "real 0.00, Twin 0.95: both right"},
  {"kind": "Short Batch, 250 shots", "machine": "fez", "at": "2026-10-30 17:11", "job": "dbicvh8hoj4c73b5up00", "qpu": 4, "result": "real 0.00, Twin 0.99: both right"},
  {"kind": "Short Batch, 250 shots", "machine": "kingston", "at": "2026-10-30 17:11", "job": "dbicv8o1h92s73836q6g", "qpu": 5, "result": "real 0.00, Twin 0.99: both right"},
  {"kind": "Short Batch, 250 shots", "machine": "fez", "at": "2026-10-31 04:00", "job": "dbimflune4hc73betu70", "qpu": 4, "result": "real 0.00, Twin 0.98: both right"},
  {"kind": "Short Batch, 250 shots", "machine": "kingston", "at": "2026-10-31 04:00", "job": "dbimfiene4hc73bettug", "qpu": 5, "result": "real 0.04, Twin 0.99: both right"},
  {"kind": "Short Batch, 250 shots", "machine": "marrakesh", "at": "2026-10-31 04:00", "job": "dbimfstep8hs73ao6b6g", "qpu": 5, "result": "real 0.00, Twin 0.98: both right"},
  {"kind": "Disguised Canaries", "machine": "fez", "at": "2026-10-31 04:02", "job": "dbimgrohoj4c73b6hsm0", "qpu": 6, "result": "all zeros 76% real vs 88% Forger"},
  {"kind": "Disguised Canaries", "machine": "kingston", "at": "2026-10-31 04:02", "job": "dbimgmo1h92s7383ps6g", "qpu": 6, "result": "all zeros 88% real vs 91% Forger"},
  {"kind": "Disguised Canaries", "machine": "marrakesh", "at": "2026-10-31 04:02", "job": "dbimgjlep8hs73ao6cvg", "qpu": 7, "result": "all zeros 76% real vs 88% Forger"},
];
