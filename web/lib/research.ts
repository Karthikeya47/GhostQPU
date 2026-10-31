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

// mirror-canaries.md: disguised Canaries (random U then U inverse, ideal all zeros), one job per machine on 2026-10-31.
export const MIRROR = [
  { machine: "marrakesh", hardware: 0.756, forger: 0.879, cleaner: 15, strong: 13 },
  { machine: "kingston", hardware: 0.875, forger: 0.912, cleaner: 15, strong: 9 },
  { machine: "fez", hardware: 0.762, forger: 0.878, cleaner: 15, strong: 9 },
];
