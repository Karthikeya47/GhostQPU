# Cross-backend check on ibm_kingston (2026-10-29)

Third Backend. Frozen Detector (fit only on the four 2026-10-10 ibm_marrakesh development Runs, fingerprint
`51a3b821bbcd587d`, threshold 0.5), applied unchanged with `scripts/score_fresh.py`.

| Item | Value |
|---|---|
| Job | `dbhmjfk2d77s739d1vsg`, ibm_kingston (Heron r2, 156 qubits), 34 circuits x 1000 shots |
| Placements | (148,149), (11,10), (50,49), (93,79) |
| Calibration cycle | 2026-10-29T20:38:00+05:30 (IBM recalibrated between our status check at 20:04 and submission) |
| Queue / wall-clock / billed | 5 s / 15.6 s / 11 s. 122 jobs were listed as pending, but the job started almost at once |
| Verdict, Genuine Run | **Genuine**, mean forged score 0.000 |
| Verdict, stock Twin | **Forged**, mean forged score 0.993 (seeded Twin) |

## Coherent amplification, P(1) after N X gates, per placement

| N | Genuine (4 placements) | Forged (4 placements) |
|---|---|---|
| 32 | 0.030 / 0.124 / 0.074 / 0.075 | 0.005 / 0.009 / 0.013 / 0.012 |
| 64 | 0.225 / 0.494 / 0.322 / 0.353 | 0.012 / 0.006 / 0.017 / 0.008 |
| 128 | 0.814 / 0.885 / 0.945 / 0.979 | 0.010 / 0.021 / 0.037 / 0.026 |

The hardware curves follow sin^2(N e / 2) with e of about 0.019 rad per X gate (about 0.6% of a pi pulse) on all four
placements, the signature of a coherent amplitude error. Mean coh_plain_rise is 0.904, against 0.21 to 0.53 on
marrakesh and 0.08 on fez. The spectator shift (max 0.070) is the weakest of the three Backends.

## Interpretation

- Correct pair of Verdicts on a third Backend the Detector never saw.
- Each Backend was caught by a different effect: marrakesh by a mix, fez mainly by spectator crosstalk, kingston mainly
  by coherent over-rotation. A multi-family Canary set is what makes one frozen Detector work across all three.
- An over-rotation that is the same size on every qubit looks like a device-wide pulse amplitude miscalibration for
  this cycle. It is a hypothesis, not tested: a second kingston cycle would show whether it persists.
- Frozen Detector totals so far: 0/4 Genuine Runs called Forged and 0/4 Twins called Genuine, over 4 calibration
  cycles on 3 Backends. One-sided 95% upper bound on each error rate: 0.53.
