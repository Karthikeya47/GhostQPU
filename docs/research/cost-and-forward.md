# How few Canaries are enough, and does it work forward in time? (2026-10-30)

Offline, no QPU time. 60 Runs (30 Genuine + Twins), 21 Calibration cycles, 3 Backends. Script: `scripts/cost_and_forward.py`. Fewer shots means the first N shots of each 1000-shot Run.

## Cost: Canary families and shots vs detection (held out by Calibration cycle)

QPU seconds are for the Canaries alone at 11 s per 34,000 shots. Drift features are excluded from every row.

| Canaries | shots | circuits | QPU s | AUC | jobs correct | worst Genuine score | worst Twin score |
|---|---|---|---|---|---|---|---|
| all families (today) | 1000 | 30 | 9.7 | 1.000 | 60/60 | 0.14 | 0.97 |
| coherent plain + spectator | 1000 | 19 | 6.1 | 1.000 | 60/60 | 0.22 | 0.97 |
| coherent plain + readout | 1000 | 11 | 3.6 | 0.999 | 59/60 | 0.80 | 0.90 |
| coherent plain only | 1000 | 7 | 2.3 | 0.999 | 59/60 | 0.78 | 0.91 |
| spectator only | 1000 | 12 | 3.9 | 0.996 | 60/60 | 0.43 | 0.81 |
| readout only | 1000 | 4 | 1.3 | 0.713 | 52/60 | 0.64 | 0.39 |
| all families (today) | 500 | 30 | 4.9 | 1.000 | 60/60 | 0.12 | 0.95 |
| coherent plain + spectator | 500 | 19 | 3.1 | 1.000 | 60/60 | 0.16 | 0.94 |
| all families (today) | 250 | 30 | 2.4 | 1.000 | 60/60 | 0.12 | 0.95 |
| coherent plain + spectator | 250 | 19 | 1.5 | 1.000 | 60/60 | 0.16 | 0.93 |

## Forward in time: train only on earlier cycles

AUC 1.000, 56/56 jobs correct, worst Genuine 0.29, worst Twin 0.97. The first cycle has nothing earlier to train on and is not scored.

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
| ibm_marrakesh_20261030T172641_81197 | ibm_marrakesh | 2026-10-30T22:40 | 13 | 0.000 |
| ibm_marrakesh_20261030T172641_81197_forged | ibm_marrakesh | 2026-10-30T22:40 | 13 | 0.968 |
| ibm_marrakesh_20261031T034206_18122 | ibm_marrakesh | 2026-10-31T08:57 | 14 | 0.000 |
| ibm_marrakesh_20261031T034206_18122_forged | ibm_marrakesh | 2026-10-31T08:57 | 14 | 0.989 |
| ibm_marrakesh_20261031T035824_19072 | ibm_marrakesh | 2026-10-31T08:57 | 14 | 0.000 |
| ibm_marrakesh_20261031T035824_19072_forged | ibm_marrakesh | 2026-10-31T08:57 | 14 | 0.990 |
| ibm_fez_20261031T034236_18152 | ibm_fez | 2026-10-31T09:00 | 15 | 0.000 |
| ibm_fez_20261031T034236_18152_forged | ibm_fez | 2026-10-31T09:00 | 15 | 0.990 |
| ibm_kingston_20261031T034221_18137 | ibm_kingston | 2026-10-31T09:00 | 16 | 0.000 |
| ibm_kingston_20261031T034221_18137_forged | ibm_kingston | 2026-10-31T09:00 | 16 | 0.993 |
| ibm_kingston_20261031T035941_19168 | ibm_kingston | 2026-10-31T09:20 | 17 | 0.033 |
| ibm_kingston_20261031T035941_19168_forged | ibm_kingston | 2026-10-31T09:20 | 17 | 0.994 |
| ibm_kingston_20261031T044247_21758 | ibm_kingston | 2026-10-31T09:20 | 17 | 0.182 |
| ibm_kingston_20261031T044247_21758_forged | ibm_kingston | 2026-10-31T09:20 | 17 | 0.991 |
| ibm_fez_20261031T035839_19081 | ibm_fez | 2026-10-31T09:20 | 18 | 0.000 |
| ibm_fez_20261031T035839_19081_forged | ibm_fez | 2026-10-31T09:20 | 18 | 0.989 |
| ibm_fez_20261031T035904_19126 | ibm_fez | 2026-10-31T09:20 | 18 | 0.000 |
| ibm_fez_20261031T035904_19126_forged | ibm_fez | 2026-10-31T09:20 | 18 | 0.992 |
| ibm_marrakesh_20261031T051013_23409 | ibm_marrakesh | 2026-10-31T09:57 | 19 | 0.061 |
| ibm_marrakesh_20261031T051013_23409_forged | ibm_marrakesh | 2026-10-31T09:57 | 19 | 0.987 |
| ibm_marrakesh_20261031T051048_23445 | ibm_marrakesh | 2026-10-31T09:57 | 19 | 0.047 |
| ibm_marrakesh_20261031T051048_23445_forged | ibm_marrakesh | 2026-10-31T09:57 | 19 | 0.994 |
| ibm_kingston_20261031T051031_23428 | ibm_kingston | 2026-10-31T10:16 | 20 | 0.011 |
| ibm_kingston_20261031T051031_23428_forged | ibm_kingston | 2026-10-31T10:16 | 20 | 0.993 |
| ibm_kingston_20261031T051104_23460 | ibm_kingston | 2026-10-31T10:16 | 20 | 0.033 |
| ibm_kingston_20261031T051104_23460_forged | ibm_kingston | 2026-10-31T10:16 | 20 | 0.993 |

## Real 250-shot jobs (data/short)

Submitted at 250 shots on hardware, not truncated. Each is scored by a Detector trained on every other Run cut to 250 shots, leaving out all Runs from its own Calibration cycle.

| job | backend | Canaries | score | Verdict |
|---|---|---|---|---|
| ibm_fez_20261030T171133_80290 | ibm_fez | all families (today) | 0.000 | Genuine (right) |
| ibm_fez_20261030T171133_80290_forged | ibm_fez | all families (today) | 0.993 | Forged (right) |
| ibm_fez_20261031T040024_19221 | ibm_fez | all families (today) | 0.000 | Genuine (right) |
| ibm_fez_20261031T040024_19221_forged | ibm_fez | all families (today) | 0.979 | Forged (right) |
| ibm_kingston_20261030T171059_80256 | ibm_kingston | all families (today) | 0.000 | Genuine (right) |
| ibm_kingston_20261030T171059_80256_forged | ibm_kingston | all families (today) | 0.992 | Forged (right) |
| ibm_kingston_20261031T040010_19205 | ibm_kingston | all families (today) | 0.039 | Genuine (right) |
| ibm_kingston_20261031T040010_19205_forged | ibm_kingston | all families (today) | 0.989 | Forged (right) |
| ibm_marrakesh_20261030T171025_80221 | ibm_marrakesh | all families (today) | 0.000 | Genuine (right) |
| ibm_marrakesh_20261030T171025_80221_forged | ibm_marrakesh | all families (today) | 0.950 | Forged (right) |
| ibm_marrakesh_20261031T040052_19242 | ibm_marrakesh | all families (today) | 0.000 | Genuine (right) |
| ibm_marrakesh_20261031T040052_19242_forged | ibm_marrakesh | all families (today) | 0.982 | Forged (right) |
| ibm_fez_20261030T171133_80290 | ibm_fez | coherent plain + spectator | 0.000 | Genuine (right) |
| ibm_fez_20261030T171133_80290_forged | ibm_fez | coherent plain + spectator | 0.986 | Forged (right) |
| ibm_fez_20261031T040024_19221 | ibm_fez | coherent plain + spectator | 0.000 | Genuine (right) |
| ibm_fez_20261031T040024_19221_forged | ibm_fez | coherent plain + spectator | 0.964 | Forged (right) |
| ibm_kingston_20261030T171059_80256 | ibm_kingston | coherent plain + spectator | 0.000 | Genuine (right) |
| ibm_kingston_20261030T171059_80256_forged | ibm_kingston | coherent plain + spectator | 0.974 | Forged (right) |
| ibm_kingston_20261031T040010_19205 | ibm_kingston | coherent plain + spectator | 0.059 | Genuine (right) |
| ibm_kingston_20261031T040010_19205_forged | ibm_kingston | coherent plain + spectator | 0.986 | Forged (right) |
| ibm_marrakesh_20261030T171025_80221 | ibm_marrakesh | coherent plain + spectator | 0.000 | Genuine (right) |
| ibm_marrakesh_20261030T171025_80221_forged | ibm_marrakesh | coherent plain + spectator | 0.905 | Forged (right) |
| ibm_marrakesh_20261031T040052_19242 | ibm_marrakesh | coherent plain + spectator | 0.000 | Genuine (right) |
| ibm_marrakesh_20261031T040052_19242_forged | ibm_marrakesh | coherent plain + spectator | 0.972 | Forged (right) |
