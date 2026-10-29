# Do the hardware effects survive recalibration? (2026-10-29)

Two repeat Batches on the same qubits after IBM recalibrated the Backend. `choose_placements` picks the same pairs when
the calibration ranks them the same, so each pair below is a before/after comparison on identical physical qubits.
Frozen Detector unchanged (fingerprint `51a3b821bbcd587d`).

| Job | Backend | Calibration cycle | Placements | Genuine score | Twin score |
|---|---|---|---|---|---|
| K1 `dbhmjfk2d77s739d1vsg` | ibm_kingston | 2026-10-29T20:38:00+05:30 | (148,149), (11,10), (50,49), (93,79) | 0.000 | 0.993 |
| K2 `dbhmr5mne4hc73bd7jcg` | ibm_kingston | 2026-10-29T21:18:38+05:30 | same | 0.000 | 0.993 |
| F1 `dbhlv5k2d77s739d0no0` | ibm_fez | 2026-10-29T19:59:10+05:30 | (144,143), (86,85), (146,147), (22,23) | 0.023 | 0.992 |
| F2 `dbhmrj01h92s738234a0` | ibm_fez | 2026-10-29T21:22:18+05:30 | same | 0.004 | 0.988 |

F2's submission recorded the 19:59 cycle; IBM published 21:22 while it was queued, and collect stored the
execution-time calibration, which the Twin used.

## Features (mean of 8 chunks, Genuine Runs)

| Feature | K1 | K2 | F1 | F2 |
|---|---|---|---|---|
| coh_plain_rise | 0.904 | 0.902 | 0.076 | 0.196 |
| coh_plain_curvature | 0.210 | 0.251 | 0.042 | 0.120 |
| spec_shift_max_abs | 0.070 | 0.078 | 0.299 | 0.284 |
| spec_shift_mean_abs | 0.032 | 0.034 | 0.148 | 0.126 |
| ro_vs_calibration | 0.013 | 0.014 | 0.009 | 0.009 |

P(1) after 128 X gates per placement: K1 0.814 / 0.885 / 0.945 / 0.979, K2 0.791 / 0.929 / 0.924 / 0.969;
F1 0.037 / 0.080 / 0.159 / 0.039, F2 0.106 / 0.230 / 0.356 / 0.102. The Twins stay at 0.01 to 0.04 throughout.

## Interpretation

- **Kingston's over-rotation persists through recalibration** on every placement. The earlier hypothesis in
  [cross-backend-kingston.md](cross-backend-kingston.md), a one-cycle pulse miscalibration, is not supported. Whatever
  causes it is not corrected by IBM's routine calibration, and it is not in the published calibration data.
- **Fez's spectator crosstalk is stable** across the two cycles (max shift 0.30 vs 0.28) while its coherent signal
  more than doubled. Static ZZ coupling is a property of the coupler design, so stability is what physics predicts;
  over-rotation is a calibration residual, so it moves.
- Practical consequence: no single Canary family is reliable on every Backend and cycle, but at least one family gave a
  strong signal in every Run so far. That is the argument for the multi-family Signature.
- The two cycles on each Backend were 40 minutes apart on the same day. Day-to-day behavior is still untested.

## Frozen Detector totals

0/6 Genuine Runs called Forged and 0/6 stock Twins called Genuine, over 6 distinct calibration cycles on 3 Backends.
One-sided 95% upper bound on each error rate: 0.39.
