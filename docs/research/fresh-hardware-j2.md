# Fresh-hardware check J2 (2026-10-29)

Second evaluation of the frozen Detector on a new Calibration cycle. Same protocol as J1: the Detector was fit
only on the four development Runs in `data/runs` (fingerprint `51a3b821bbcd587d`, threshold 0.5). Nothing was
retrained or tuned. Scored with `PYTHONPATH=. python scripts/score_fresh.py`.

## Measured

| Item | Value |
|---|---|
| Job | `dbhlogdep8hs73amdtfg`, ibm_marrakesh, 34 circuits x 1000 shots, code `2d7db48` |
| Placements | (87,86), (5,6), (14,15), (107,108). (5,6) was also used by the development Runs |
| Calibration cycle at execution | 2026-10-29T20:01:36+05:30 (third distinct cycle overall) |
| Queue time (created to running) | 69 s, not billed |
| Execution wall-clock (running to finished) | 15.6 s |
| Billed QPU time | 11 s. Allowance after J2: 589 s of 600 s |
| Twin | stock Forger, `seed_simulator` 4229637115 (first reproducible Twin) |
| Verdict, Genuine Run | **Genuine**, mean forged score 0.000 |
| Verdict, stock Twin | **Forged**, mean forged score 0.985 |

## Features (mean of 8 chunks)

| Feature | J1 Genuine | J2 Genuine | J1 Forged | J2 Forged |
|---|---|---|---|---|
| coh_plain_rise | 0.208 | 0.534 | 0.020 | 0.047 |
| coh_plain_curvature | 0.145 | 0.318 | -0.002 | -0.000 |
| coh_sx_rise | 0.166 | 0.492 | 0.042 | 0.056 |
| spec_shift_max_abs | 0.103 | 0.098 | 0.045 | 0.045 |
| ro_context_shift | 0.015 | 0.013 | 0.007 | 0.012 |
| ro_vs_calibration | 0.016 | 0.011 | 0.008 | 0.009 |

## Interpretation

- Two correct pairs of Verdicts on two new cycles. 0 errors in 2 Genuine Runs gives a one-sided 95% upper bound
  of 0.776 on the false-positive rate: still preliminary.
- J1's margin had shrunk (0.18) because the coherent features were weak on its qubits. J2's coherent signal is
  the strongest seen so far (rise 0.53 vs 0.21 to 0.31), so the coherent strength varies a lot by placement and
  cycle. The spectator features stayed almost constant across all three cycles (max shift 0.098 to 0.106), which
  makes them the most stable evidence.
- ro_context_shift of the J2 Twin (0.012) is close to the J2 Genuine value (0.013): readout context alone would not
  have separated this pair.
