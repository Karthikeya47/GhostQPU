# Fresh-hardware check J1 (2026-10-27)

First evaluation of the frozen Detector on a Genuine Run from a new Calibration cycle. The Detector
was fit only on the four development Runs in `data/runs` (2 Genuine from cycle 2026-10-10T11:01:13+05:30
and their stock Twins), fingerprint `51a3b821bbcd587d`, threshold 0.5. Nothing was retrained or tuned.

## Measured

| Item | Value |
|---|---|
| Job | `dbg33ctjm0ks73efpbc0`, final status DONE |
| Backend | ibm_marrakesh, 34 circuits x 1000 shots, code `8a0ac5d` (manifest in run.json) |
| Placements | (6,7), (53,54), (12,11), (98,91). Development Runs used (137,147), (5,6), (1,0), (104,105) |
| Calibration cycle at execution | 2026-10-27T12:06:00+05:30. At submission it was 09:51:58+05:30: IBM recalibrated while the job was queued. The Twin uses the execution-time cycle |
| Queue time (created to running) | 1 h 49 min 31 s, not billed |
| Execution wall-clock (running to finished) | 70.1 s |
| Billed QPU time | 11 s (`qpu_charge_time_seconds`), 0.1807 resource units. Same as both development jobs |
| Allowance after J1 | 567 s of 600 s remaining in the rolling 28-day window (API, 2026-10-27 ~07:05 UTC) |
| Verdict, Genuine Run | **Genuine**, mean forged score 0.182. Chunk scores 0.02 to 0.37, all below 0.5 |
| Verdict, stock Twin | **Forged**, mean forged score 0.990. Chunk scores 0.984 to 0.995 |

## Features (mean of 8 chunks)

| Feature | dev Genuine A | dev Genuine B | J1 Genuine | dev Forged A | dev Forged B | J1 Forged |
|---|---|---|---|---|---|---|
| coh_plain_rise | 0.310 | 0.297 | 0.208 | 0.035 | 0.033 | 0.021 |
| coh_plain_curvature | 0.196 | 0.167 | 0.145 | -0.003 | 0.005 | -0.002 |
| coh_plain_nonlinearity | 0.037 | 0.034 | 0.030 | 0.006 | 0.007 | 0.006 |
| coh_sx_rise | 0.284 | 0.279 | 0.166 | 0.055 | 0.064 | 0.042 |
| coh_sx_curvature | 0.180 | 0.177 | 0.120 | -0.007 | 0.018 | -0.003 |
| coh_sx_nonlinearity | 0.036 | 0.036 | 0.026 | 0.009 | 0.008 | 0.007 |
| spec_shift_mean_abs | 0.051 | 0.049 | 0.047 | 0.021 | 0.022 | 0.020 |
| spec_shift_max_abs | 0.099 | 0.106 | 0.103 | 0.045 | 0.049 | 0.045 |
| ro_context_shift | 0.024 | 0.016 | 0.015 | 0.009 | 0.014 | 0.007 |
| ro_vs_calibration | 0.024 | 0.020 | 0.016 | 0.010 | 0.009 | 0.008 |
| drift_lag1 | -0.002 | -0.001 | -0.003 | -0.009 | -0.006 | -0.007 |
| drift_dispersion | 1.023 | 1.033 | 1.019 | 1.021 | 1.015 | 1.053 |

## Interpretation

- One correct pair of Verdicts on a new cycle. With 0 errors in 1 Run the one-sided 95% upper bound on
  the false-positive rate is 0.95, so this is a preliminary pass, not evidence of cross-day generalization.
- The margin shrank. The development Genuine Runs score about 0.01 in sample (an optimistic reference,
  since the model was fit on them); J1 scores 0.18. The coherent-amplification features moved most:
  coh_plain_rise and coh_sx_rise are 4.1 and 3.8 development-Genuine chunk SDs below the development
  Genuine mean, and in the model's standardized space they sit near the midpoint between the Genuine and
  Forged training clusters. They remain 6 to 10 times the Forged values in raw terms.
- The spectator features are almost unchanged (spec_shift_max_abs shift +0.04 SD) and carried most of the
  Genuine evidence for J1.
- New placements and a new cycle changed together, so this Run cannot say whether the weaker coherent
  signal comes from different qubits or from the recalibration. Over-rotation is a per-qubit calibration
  residual, so both are plausible.
- Not changed after seeing this result: Detector, threshold, features, Forger, Canaries.

## Limitations

- n = 1 Genuine Run in 1 new cycle.
- The stock Twin is not reproducible bit for bit (Aer runs without `seed_simulator`); the saved Twin is the record.
- Within-cycle repeats would not add cross-day evidence.
