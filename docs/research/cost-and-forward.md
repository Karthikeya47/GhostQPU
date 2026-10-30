# How few Canaries are enough, and does it work forward in time? (2026-10-30)

Offline, no QPU time. 28 Runs (14 Genuine + Twins), 10 Calibration cycles, 3 Backends. Script: `scripts/cost_and_forward.py`. Fewer shots means the first N shots of each 1000-shot Run.

## Cost: Canary families and shots vs detection (held out by Calibration cycle)

QPU seconds are for the Canaries alone at 11 s per 34,000 shots. Drift features are excluded from every row.

| Canaries | shots | circuits | QPU s | AUC | jobs correct | worst Genuine score | worst Twin score |
|---|---|---|---|---|---|---|---|
| all families (today) | 1000 | 30 | 9.7 | 1.000 | 28/28 | 0.33 | 0.96 |
| coherent plain + spectator | 1000 | 19 | 6.1 | 1.000 | 28/28 | 0.32 | 0.96 |
| coherent plain + readout | 1000 | 11 | 3.6 | 0.994 | 27/28 | 0.84 | 0.88 |
| coherent plain only | 1000 | 7 | 2.3 | 0.995 | 27/28 | 0.83 | 0.91 |
| spectator only | 1000 | 12 | 3.9 | 0.988 | 28/28 | 0.46 | 0.74 |
| readout only | 1000 | 4 | 1.3 | 0.701 | 23/28 | 0.64 | 0.43 |
| all families (today) | 500 | 30 | 4.9 | 1.000 | 28/28 | 0.24 | 0.95 |
| coherent plain + spectator | 500 | 19 | 3.1 | 1.000 | 28/28 | 0.27 | 0.95 |
| all families (today) | 250 | 30 | 2.4 | 1.000 | 28/28 | 0.30 | 0.94 |
| coherent plain + spectator | 250 | 19 | 1.5 | 1.000 | 28/28 | 0.30 | 0.94 |

## Forward in time: train only on earlier cycles

AUC 1.000, 24/24 jobs correct, worst Genuine 0.29, worst Twin 0.97. The first cycle has nothing earlier to train on and is not scored.

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
