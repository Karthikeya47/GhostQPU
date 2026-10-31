# Disguised Canaries: mirror circuits on hardware (2026-10-31)

**Question.** The production Canaries (long X chains, Ramsey pairs, readout preparations) look different from customer
circuits. A provider that recognizes them could run only the Canaries on hardware and simulate the customer's real work.
Can a Canary look exactly like a customer circuit and still catch the Forger?

**Design** (`scripts/mirror_pilot.py`). Each circuit is a random 4-qubit circuit U (Qiskit `random_circuit`, two-qubit
gates allowed) followed by U inverse, so the ideal outcome is all zeros. It is compiled exactly like a Workload circuit
(optimization level 1, transpiler chooses the qubits); a barrier stops U and U inverse from cancelling. 16 circuits per
job: depth 4 and depth 8, eight each, 8 to 98 CZ gates after compilation. On a noiseless simulator every circuit returns
all zeros (checked). The Twin is the stock Forger under the execution-time calibration, as for Batches.

| Job | Backend | Calibration cycle | QPU s | P(all zeros) hardware | P(all zeros) Forger | Forger cleaner | z > 3 |
|---|---|---|---|---|---|---|---|
| `dbimgjlep8hs73ao6cvg` | ibm_marrakesh | 2026-10-31T08:57:31+05:30 | 7 | 0.756 | 0.879 | 15/16 | 13/16 |
| `dbimgmo1h92s7383ps6g` | ibm_kingston | 2026-10-31T09:20:22+05:30 | 6 | 0.875 | 0.912 | 15/16 | 9/16 |
| `dbimgrohoj4c73b6hsm0` | ibm_fez | 2026-10-31T09:20:53+05:30 | 6 | 0.762 | 0.878 | 15/16 | 9/16 |

By depth (hardware vs Forger): marrakesh 0.821 vs 0.920 at depth 4 and 0.691 vs 0.837 at depth 8; kingston 0.905 vs
0.940 and 0.845 vs 0.885; fez 0.856 vs 0.922 and 0.668 vs 0.834. z is a two-proportion test per circuit on 1000 shots
each (Forger minus hardware).

## Interpretation

- On every machine the Forger is too clean on circuits that are indistinguishable from customer work: 45 of 48
  circuits, with the gap growing with depth. This matches the earlier Workload finding (real GHZ output farther from
  ideal than the Forger's; [workload-generalization.md](workload-generalization.md)) and the CNOT pilot's CZ-linked
  coherent error ([cnot-pilot-hardware.md](cnot-pilot-hardware.md)).
- So Canaries can be hidden inside customer-looking circuits. A provider cannot pick out mirror circuits by structure.

## Limits

- This measures the overall error level, not its shape. A Forger that adds extra uniform noise could narrow the gap; the
  X-chain Canaries measure the shape (curvature with N, neighbor dependence), so a Forger would have to get both right at
  once, which needs the real per-qubit physics.
- One job per machine, one cycle each, no Detector trained on mirror features yet; these are pilot statistics.
- The barrier between U and U inverse is visible in the compiled circuit. A production version should hide it, for
  example by compiling U inverse separately with a different seed.
