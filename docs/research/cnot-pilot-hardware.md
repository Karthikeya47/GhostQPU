# CNOT pilot on hardware (2026-10-29)

First hardware run of the CNOT pilot (`ghostqpu/pilot.py`, `scripts/cnot_pilot.py`). Not a Canary family: the frozen
Detector never sees these Runs.

| Item | Value |
|---|---|
| Job | `dbhlvcune4hc73bd5vng`, ibm_marrakesh, 32 circuits x 1000 shots |
| Placements | (87,86), (5,6), (14,15), (107,108): the same qubits and Calibration cycle (2026-10-29T20:01:36+05:30) as J2 |
| Billed QPU time | 11 s (estimate was 10.4 s) |
| Analysis | `PYTHONPATH=. python scripts/cnot_pilot.py analyze --curves`; stock curve from 200,000-shot density-matrix Aer |

## Fitted coherent turn per repeat the stock Forger misses (theta, rad), z against theta = 0

| Placement | cnot, control 1 | cnot, control 0 | idle, control 1 | idle, control 0 |
|---|---|---|---|---|
| 107-108 | 0.072 (z 40.5) | 0.068 (z 40.8) | 0.004 (z 1.6) | 0.005 (z 2.9) |
| 14-15 | 0.031 (z 18.4) | 0.029 (z 16.1) | 0.037 (z 35.4) | 0.034 (z 25.5) |
| 5-6 | 0.008 (z 2.3) | 0.008 (z 3.3) | 0 | 0 |
| 87-86 | 0 | 0 | 0 | 0 |

Detection threshold z > 3.2 (pre-registered, Bonferroni over 4 placements).

Raw example, 107-108, control 1: P(target wrong) after N = 32 repeats is 0.733 on hardware vs 0.096 from the stock
Forger; N = 16 gives 0.332 vs 0.053.

## Interpretation

- **H1 (conditional-phase error on CZ) is not supported.** On every placement the control-0 and control-1 fits agree
  within about 0.004 rad, and a conditional phase would only show with the control in 1.
- **107-108 shows a large coherent error tied to the CZ pulse itself.** It appears with the control in 0 or 1, and
  vanishes when the CZ is replaced by an idle of equal length. A local Z phase on the target during the CZ pulse fits
  this pattern. The stock Forger has no coherent CZ term, so it misses it by a factor of 5 to 8 at N = 16 to 32.
- **14-15 is different:** the idle circuits show the same turn as the CNOT circuits, so the error there comes from the
  single-qubit gates or from detuning during the wait, not from the CZ.
- **The effect is strongly placement dependent** (0 to 0.07 rad), like the X-gate over-rotation. A CNOT Canary should
  run on several placements and use curve-shape features, not one absolute threshold.
- The sin^2 model is imperfect: chi2 per degree of freedom reaches 3.5 to 5.6 on several curves (the hardware curve is
  non-monotonic beyond N = 32 on 107-108), so the theta intervals are optimistic. The z-scores are large enough that
  the detection conclusions do not depend on this.

## Limitations

- One job, one Calibration cycle, one Backend. Whether 107-108's CZ phase error persists after recalibration is unknown.
- A Forger that fits a per-edge Z phase on CZ from one probe job would erase this gap, in the same way the stronger
  Forger (`ghostqpu/forger.py`) erased the X-gate gap. It would need hardware data for every edge it might be asked to run.
