# How few Canaries are enough, and does it work forward in time? (2026-10-30)

Offline, no QPU time. 34 Runs (17 Genuine + Twins), 13 Calibration cycles, 3 Backends. Script: `scripts/cost_and_forward.py`. Fewer shots means the first N shots of each 1000-shot Run.

## Cost: Canary families and shots vs detection (held out by Calibration cycle)

QPU seconds are for the Canaries alone at 11 s per 34,000 shots. Drift features are excluded from every row.

| Canaries | shots | circuits | QPU s | AUC | jobs correct | worst Genuine score | worst Twin score |
|---|---|---|---|---|---|---|---|
| all families (today) | 1000 | 30 | 9.7 | 1.000 | 34/34 | 0.37 | 0.97 |
| coherent plain + spectator | 1000 | 19 | 6.1 | 1.000 | 34/34 | 0.35 | 0.96 |
| coherent plain + readout | 1000 | 11 | 3.6 | 0.996 | 33/34 | 0.85 | 0.89 |
| coherent plain only | 1000 | 7 | 2.3 | 0.997 | 33/34 | 0.84 | 0.92 |
| spectator only | 1000 | 12 | 3.9 | 0.991 | 34/34 | 0.44 | 0.76 |
| readout only | 1000 | 4 | 1.3 | 0.718 | 29/34 | 0.63 | 0.42 |
| all families (today) | 500 | 30 | 4.9 | 1.000 | 34/34 | 0.27 | 0.96 |
| coherent plain + spectator | 500 | 19 | 3.1 | 1.000 | 34/34 | 0.30 | 0.96 |
| all families (today) | 250 | 30 | 2.4 | 1.000 | 34/34 | 0.33 | 0.95 |
| coherent plain + spectator | 250 | 19 | 1.5 | 1.000 | 34/34 | 0.33 | 0.95 |

## Forward in time: train only on earlier cycles

AUC 1.000, 30/30 jobs correct, worst Genuine 0.29, worst Twin 0.97. The first cycle has nothing earlier to train on and is not scored.

| job | backend | cycle | cycles trained on | score |
|---|---|---|---|---|
| ibm_marrakesh_20261027T050804_77679 | ibm_marrakesh | 2026-10-27T12:06 | 1 | 0.182 |
| ibm_marrakesh_20261027T050804_77679_forged | ibm_marrakesh | 2026-10-27T12:06 | 1 | 0.990 |
| ibm_fez_20261029T150038_86034 | ibm_fez | 2026-10-29T19:59 | 2 | 0.006 |
| ibm_fez_20261029T150038_86034_forged | ibm_fez | 2026-10-29T19:59 | 2 | 0.991 |
| ibm_marrakesh_20261029T144625_85181 | ibm_marrakesh | 2026-10-29T20:01 | 3 | 0.000 |
| ibm_marrakesh_20261029T144625_85181_forged | ibm_marrakesh | 2026-10-29T20:01 | 3 | 0.974 |
| ibm_kingston_20261029T154358_88635 | ibm_kingston | 2026-10-29T20:38 | 4 | 0.000 |
| ibm_kingston_20261029T154358_88635_forged | ibm_kingston | 2026-10-29T20:38 | 4 | 0.990 |
| ibm_kingston_20261029T160023_89619 | ibm_kingston | 2026-10-29T21:18 | 5 | 0.000 |
| ibm_kingston_20261029T160023_89619_forged | ibm_kingston | 2026-10-29T21:18 | 5 | 0.990 |
| ibm_fez_20261029T160116_89673 | ibm_fez | 2026-10-29T21:22 | 6 | 0.003 |
| ibm_fez_20261029T160116_89673_forged | ibm_fez | 2026-10-29T21:22 | 6 | 0.983 |
| ibm_kingston_20261030T154500_75097 | ibm_kingston | 2026-10-30T21:01 | 7 | 0.003 |
| ibm_kingston_20261030T154500_75097_forged | ibm_kingston | 2026-10-30T21:01 | 7 | 0.994 |
| ibm_kingston_20261030T155339_75616 | ibm_kingston | 2026-10-30T21:01 | 7 | 0.027 |
| ibm_kingston_20261030T155339_75616_forged | ibm_kingston | 2026-10-30T21:01 | 7 | 0.987 |
| ibm_marrakesh_20261030T154436_75072 | ibm_marrakesh | 2026-10-30T21:03 | 8 | 0.246 |
| ibm_marrakesh_20261030T154436_75072_forged | ibm_marrakesh | 2026-10-30T21:03 | 8 | 0.984 |
| ibm_marrakesh_20261030T155324_75600 | ibm_marrakesh | 2026-10-30T21:03 | 8 | 0.289 |
| ibm_marrakesh_20261030T155324_75600_forged | ibm_marrakesh | 2026-10-30T21:03 | 8 | 0.987 |
| ibm_fez_20261030T154448_75084 | ibm_fez | 2026-10-30T21:05 | 9 | 0.000 |
| ibm_fez_20261030T154448_75084_forged | ibm_fez | 2026-10-30T21:05 | 9 | 0.989 |
| ibm_fez_20261030T155353_75630 | ibm_fez | 2026-10-30T21:05 | 9 | 0.000 |
| ibm_fez_20261030T155353_75630_forged | ibm_fez | 2026-10-30T21:05 | 9 | 0.987 |
| ibm_marrakesh_20261030T171006_80201 | ibm_marrakesh | 2026-10-30T22:05 | 10 | 0.000 |
| ibm_marrakesh_20261030T171006_80201_forged | ibm_marrakesh | 2026-10-30T22:05 | 10 | 0.980 |
| ibm_kingston_20261030T171044_80240 | ibm_kingston | 2026-10-30T22:06 | 11 | 0.000 |
| ibm_kingston_20261030T171044_80240_forged | ibm_kingston | 2026-10-30T22:06 | 11 | 0.989 |
| ibm_fez_20261030T171114_80270 | ibm_fez | 2026-10-30T22:32 | 12 | 0.000 |
| ibm_fez_20261030T171114_80270_forged | ibm_fez | 2026-10-30T22:32 | 12 | 0.991 |

## Real 250-shot jobs (data/short)

Submitted at 250 shots on hardware, not truncated. Each is scored by a Detector trained on every other Run cut to 250 shots, leaving out all Runs from its own Calibration cycle.

| job | backend | Canaries | score | Verdict |
|---|---|---|---|---|
| ibm_fez_20261030T171133_80290 | ibm_fez | all families (today) | 0.000 | Genuine (right) |
| ibm_fez_20261030T171133_80290_forged | ibm_fez | all families (today) | 0.990 | Forged (right) |
| ibm_kingston_20261030T171059_80256 | ibm_kingston | all families (today) | 0.000 | Genuine (right) |
| ibm_kingston_20261030T171059_80256_forged | ibm_kingston | all families (today) | 0.989 | Forged (right) |
| ibm_marrakesh_20261030T171025_80221 | ibm_marrakesh | all families (today) | 0.000 | Genuine (right) |
| ibm_marrakesh_20261030T171025_80221_forged | ibm_marrakesh | all families (today) | 0.954 | Forged (right) |
| ibm_fez_20261030T171133_80290 | ibm_fez | coherent plain + spectator | 0.000 | Genuine (right) |
| ibm_fez_20261030T171133_80290_forged | ibm_fez | coherent plain + spectator | 0.981 | Forged (right) |
| ibm_kingston_20261030T171059_80256 | ibm_kingston | coherent plain + spectator | 0.000 | Genuine (right) |
| ibm_kingston_20261030T171059_80256_forged | ibm_kingston | coherent plain + spectator | 0.973 | Forged (right) |
| ibm_marrakesh_20261030T171025_80221 | ibm_marrakesh | coherent plain + spectator | 0.000 | Genuine (right) |
| ibm_marrakesh_20261030T171025_80221_forged | ibm_marrakesh | coherent plain + spectator | 0.920 | Forged (right) |
