# Cross-backend check on ibm_fez (2026-10-29)

First Genuine Run on a second Backend. The frozen Detector (fit only on the four 2026-10-10 ibm_marrakesh development
Runs, fingerprint `51a3b821bbcd587d`, threshold 0.5) was applied unchanged. Scored with `scripts/score_fresh.py`.

| Item | Value |
|---|---|
| Job | `dbhlv5k2d77s739d0no0`, ibm_fez (Heron r2, 156 qubits), 34 circuits x 1000 shots |
| Placements | (144,143), (86,85), (146,147), (22,23) |
| Calibration cycle | 2026-10-29T19:59:10+05:30 |
| Billed QPU time | 11 s |
| Verdict, Genuine Run | **Genuine**, mean forged score 0.023 |
| Verdict, stock Twin | **Forged**, mean forged score 0.992 (seeded Twin) |

## Features (mean of 8 chunks)

| Feature | fez Genuine | fez Forged | marrakesh Genuine range (4 Runs) |
|---|---|---|---|
| coh_plain_rise | 0.076 | 0.028 | 0.208 to 0.534 |
| coh_sx_rise | 0.056 | 0.037 | 0.166 to 0.492 |
| spec_shift_mean_abs | 0.148 | 0.017 | 0.045 to 0.051 |
| spec_shift_max_abs | 0.299 | 0.038 | 0.098 to 0.106 |
| ro_context_shift | 0.011 | 0.008 | 0.013 to 0.024 |

## Interpretation

- Correct pair of Verdicts on a Backend the Detector never saw. n = 1, so this is a feasibility result.
- The evidence came from a different place than on marrakesh: the coherent-amplification signal on these fez qubits
  is weak (rise 0.08, close to the Forger's 0.03), while the spectator shift is about three times larger than on any
  marrakesh Run. The Detector still worked because every feature weight points the same way (hardware shows more of
  each effect than the Forger).
- A spectator value this far outside the training range is an extrapolation in the model's standardized space. It
  pushed the score toward Genuine here; a Backend with weaker effects everywhere would be the real test.
