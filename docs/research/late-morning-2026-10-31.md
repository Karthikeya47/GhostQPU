# Late morning: the frozen Detector's first false alarms (2026-10-31)

Two more 1000-shot Batches after IBM recalibrated marrakesh (09:57) and kingston (10:16). Same qubits as the earlier
morning Runs on each Backend. Frozen Detector unchanged (fingerprint `51a3b821bbcd587d`), scored with
`scripts/score_fresh.py`.

| Job | Backend | Calibration cycle | Placements | Frozen score | Twin score |
|---|---|---|---|---|---|
| J9 `dbindmene4hc73bf05pg` | ibm_marrakesh | 2026-10-31T09:57:59+05:30 | same as J7, J8 | **0.765, Forged (wrong)** | 0.988 |
| K9 `dbindcg1h92s7383s1eg` | ibm_kingston | 2026-10-31T10:16:44+05:30 | same as K6, K7, K8 | **0.830, Forged (wrong)** | 0.992 |

Frozen Detector totals: 2/26 Genuine Runs called Forged (95% upper bound 0.22), 0/26 Twins called Genuine (0.11), over
20 Calibration cycles.

## Why

Coherent over-rotation on these qubits collapsed after recalibration, while crosstalk did not:

| Run | Cycle | coh_plain_rise | coh_plain_curvature | spec_shift_max_abs |
|---|---|---|---|---|
| K6 | 09:00 | 0.424 | 0.272 | 0.112 |
| K7 | 09:20 | 0.194 | 0.119 | 0.120 |
| K8 | 09:20 | 0.136 | 0.068 | 0.118 |
| K9 | 10:16 | 0.099 | 0.008 | 0.103 |
| J7, J8 | 08:57 | 0.346, 0.473 | 0.237, 0.302 | 0.099, 0.091 |
| J9 | 09:57 | 0.089 | 0.030 | 0.096 |
| K9, J9 Twins | | 0.027, 0.047 | 0.002, 0.004 | 0.036, 0.036 |

The frozen Detector was trained on one marrakesh cycle and weights the six coherent features most. When IBM's
calibration removes most of the over-rotation, those features fall toward the Twin values and the Run looks forged,
even though spectator crosstalk is still about three times the Forger's.

## A Detector trained on more cycles gets both right

Held out by Calibration cycle (trained on every other cycle, all Backends): AUC 1.00, every Run on the correct side of
0.5. J9 scores 0.279 (Genuine), K9 0.412 (correct side, inside the Inconclusive band).

## Takeaway

This is the limit [cross-day-2026-10-30.md](cross-day-2026-10-30.md) predicted: a Detector frozen on one cycle leans on
whichever effect was strongest then. Over-rotation is a calibration residual that IBM can shrink; ZZ crosstalk is a
property of the coupler and stays. A deployed Detector should be retrained across cycles and weight the stable
families. These Runs are not yet in `web/public/data.json`.
