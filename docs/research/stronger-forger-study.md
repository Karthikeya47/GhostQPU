# The stronger Forger against every Detector (2026-10-31)

Offline, no QPU time. Script: `scripts/stronger_forger_study.py`; per-job numbers in `stronger-forger-study.csv`.

**Attacker.** For each Genuine Run that shares its Backend and qubit placements with an earlier Genuine Run, the
stronger Forger (`ghostqpu/forger.py`) fits a profile from the earlier Run (over-rotation, Ramsey detuning and ZZ, and
neighbor-dependent readout per physical qubit), as a provider with one past real job on those qubits could, and forges
the later Run. 13 such pairs exist across the three Backends.

**Defenders.** Each forgery is scored by three Detectors:

| Detector | Trained on | Stronger forgeries caught (score > 0.5) |
|---|---|---|
| Frozen | the four 10 October Runs (stock Twins only) | 1 / 13 |
| Stock-only | every other Calibration cycle's Runs and stock Twins | 0 / 13 |
| Retrained | the same, plus the stronger forgeries of every other cycle | 12 / 13 |

Under the retrained Detector, 12 of the 13 real target jobs are still called Genuine; the exception is J4
(ibm_marrakesh, 2026-10-30 21:03, score 0.60), the job that was already the closest call. The one missed forgery is
F4 (ibm_fez, 0.48).

## What this means

- The perfect scores elsewhere in this repo are against a Forger that uses only public calibration data. That Forger
  has no coherent-error term, so the separation is total. They are not a claim that GhostQPU is unbeatable.
- A Forger that learns hardware effects from a real job on the same qubits beats a Detector that has never seen such a
  Forger. Learning those effects requires real QPU time on those qubits, so the attack is no longer free.
- A Detector that has seen this attacker on other days catches it on new days (12 of 13), at the cost of one false alarm
  in 13 real jobs. Detection becomes an arms race the defender can keep up with, not a solved problem.
- Next: require evidence from more than one Canary family, and add families the profile does not cover (disguised
  mirror Canaries and CNOT Canaries test two-qubit error, which this Forger does not model).
