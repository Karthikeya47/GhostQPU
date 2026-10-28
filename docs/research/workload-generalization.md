# Does the stronger Forger generalize to Workload circuits?

Test: the stronger Forger (`ghostqpu/forger.py`) was fitted only on Canary circuits. Does it match real
`ibm_marrakesh` hardware better than the stock Forger on the Workload circuits (GHZ and random) it never saw?
Data: the two saved Genuine Runs in `data/runs` (1000 shots each, 8 Workload circuits in total). No new QPU
jobs. The Detector was not retrained or used.

## Setup

- Real, stock and stronger-forger results use the same circuit objects (asserted in the script) and the same
  shot-record convention (clbit i = column i). The saved stock Twins are used as-is.
- v2 for Run A uses a profile fitted on Run B, and the reverse. v2_xfer is exploratory: v2 plus the median
  fitted amplitude error on qubits the probe never measured.
- Metric: total variation distance (TVD) between outcome distributions. Shot noise is handled two ways:
  (1) TVD to a 100,000-shot version of each forger, so only the real data's 1000 shots add noise, with the
  expected shot-noise TVD (`floor`) and a p-value from resampling; (2) a permutation test on the saved
  1000-shot Twins. The stock-minus-v2 difference gets a bootstrap 95% CI over the real shots.
- "Closer" means the CI of (TVD_stock - TVD_v2) excludes 0. Otherwise it is inconclusive.

## What the forgers model for two-qubit gates

Checked on the stock noise model rebuilt from the snapshot (`NoiseModel.from_backend`):

- CZ errors are Pauli (depolarizing-type) plus reset/Z (relaxation-type) channels, one per coupled pair.
  Everything is incoherent. There is no coherent CZ over-rotation, no ZZ phase during gates, no leakage, no
  crosstalk to neighbors and no correlated readout.
- The stronger Forger adds nothing for CZ. Its effects act only on `x`/`sx` pulses (amplitude error), on
  explicit `delay` instructions (detuning and ZZ), and on readout of the probed qubits. Workload circuits have
  neither delays nor, apart from a few qubits, probed qubits.
- Coverage: the profile has effects on only 2 to 3 qubits of each 4 to 5 qubit Workload circuit (column
  "qubits with fitted effects"). random4_1 in run 13117 has no CZ at all.
- The fitted amplitude error is about 0.003 (0.3% of a pi pulse). That is about 0.01 rad per gate, so about
  2e-5 error probability per gate. It only matters when amplified 128 times, as in the Canaries. On a Workload
  circuit with 20 to 40 gates its effect is far below shot noise, so a small difference from the stock Forger
  here was expected.

So neither forger is a complete physical simulation of the two-qubit gates.

## Results

## Distance from real hardware (total variation distance, lower is closer)

TVD to the near-exact forger distribution. `floor` is the TVD expected from shot noise alone
(1000 real shots), `p` is P(shot noise alone >= observed).

### ghz5

| run | circuit | CZ | qubits with fitted effects | ideal vs real | stock | floor | p | v2 | floor | p | v2_xfer | floor | p | stock minus v2 [95% CI] | stock minus v2_xfer [95% CI] | verdict v2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 12894 | ghz5 | 4 | 0,1 | 0.132 | 0.081 | 0.026 | 0.000 | 0.081 | 0.026 | 0.000 | 0.081 | 0.026 | 0.000 | +0.002 [-0.002, +0.007] | +0.000 [-0.002, +0.002] | inconclusive |
| 13117 | ghz5 | 4 | 0,1 | 0.123 | 0.072 | 0.026 | 0.000 | 0.073 | 0.027 | 0.000 | 0.075 | 0.026 | 0.000 | -0.003 [-0.012, +0.002] | -0.004 [-0.009, -0.000] | inconclusive |

### random4

| run | circuit | CZ | qubits with fitted effects | ideal vs real | stock | floor | p | v2 | floor | p | v2_xfer | floor | p | stock minus v2 [95% CI] | stock minus v2_xfer [95% CI] | verdict v2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 12894 | random4_1 | 12 | 5,6 | 0.064 | 0.048 | 0.042 | 0.246 | 0.042 | 0.042 | 0.501 | 0.044 | 0.043 | 0.435 | +0.004 [-0.006, +0.011] | +0.002 [-0.009, +0.010] | inconclusive |
| 12894 | random4_0 | 16 | 5,6 | 0.112 | 0.072 | 0.032 | 0.000 | 0.064 | 0.033 | 0.003 | 0.063 | 0.033 | 0.003 | +0.007 [-0.005, +0.015] | +0.008 [-0.003, +0.016] | inconclusive |
| 12894 | random4_2 | 6 | 5,6 | 0.059 | 0.034 | 0.015 | 0.018 | 0.035 | 0.018 | 0.020 | 0.037 | 0.018 | 0.018 | -0.002 [-0.019, +0.020] | -0.003 [-0.021, +0.020] | inconclusive |
| 13117 | random4_0 | 10 | 5,6 | 0.055 | 0.048 | 0.039 | 0.168 | 0.051 | 0.041 | 0.128 | 0.051 | 0.041 | 0.130 | -0.001 [-0.008, +0.008] | -0.001 [-0.009, +0.007] | inconclusive |
| 13117 | random4_2 | 5 | 5,6,104 | 0.090 | 0.078 | 0.033 | 0.000 | 0.063 | 0.033 | 0.002 | 0.065 | 0.033 | 0.002 | +0.014 [+0.010, +0.018] | +0.013 [+0.009, +0.017] | closer than stock |
| 13117 | random4_1 | 0 | 0,1 | 0.053 | 0.020 | 0.022 | 0.579 | 0.021 | 0.023 | 0.582 | 0.021 | 0.023 | 0.568 | -0.001 [-0.015, +0.011] | -0.001 [-0.015, +0.011] | no CZ gates: not a two-qubit test |

## Same comparison using the saved 1000-shot Twins only (permutation test)

| run | circuit | stock TVD | p | v2 TVD | p | v2_xfer TVD | p | shot-noise floor |
|---|---|---|---|---|---|---|---|---|
| 12894 | random4_1 | 0.070 | 0.245 | 0.053 | 0.697 | 0.079 | 0.097 | 0.061 |
| 12894 | random4_0 | 0.077 | 0.025 | 0.085 | 0.008 | 0.077 | 0.026 | 0.048 |
| 12894 | random4_2 | 0.034 | 0.145 | 0.036 | 0.144 | 0.067 | 0.000 | 0.023 |
| 12894 | ghz5 | 0.080 | 0.011 | 0.076 | 0.014 | 0.096 | 0.001 | 0.040 |
| 13117 | random4_0 | 0.074 | 0.115 | 0.053 | 0.614 | 0.062 | 0.347 | 0.057 |
| 13117 | random4_2 | 0.108 | 0.000 | 0.053 | 0.342 | 0.055 | 0.308 | 0.048 |
| 13117 | random4_1 | 0.038 | 0.294 | 0.030 | 0.581 | 0.020 | 0.910 | 0.033 |
| 13117 | ghz5 | 0.082 | 0.004 | 0.078 | 0.006 | 0.088 | 0.002 | 0.037 |

## TVD to the ideal (noiseless) output, to compare overall error level

| run | circuit | real | stock | v2 | v2_xfer |
|---|---|---|---|---|---|
| 12894 | random4_1 | 0.064 | 0.048 | 0.062 | 0.094 |
| 12894 | random4_0 | 0.112 | 0.057 | 0.054 | 0.076 |
| 12894 | random4_2 | 0.059 | 0.026 | 0.059 | 0.081 |
| 12894 | ghz5 | 0.132 | 0.080 | 0.082 | 0.066 |
| 13117 | random4_0 | 0.055 | 0.064 | 0.041 | 0.036 |
| 13117 | random4_2 | 0.090 | 0.049 | 0.047 | 0.056 |
| 13117 | random4_1 | 0.053 | 0.043 | 0.060 | 0.063 |
| 13117 | ghz5 | 0.123 | 0.072 | 0.076 | 0.090 |

## Reading the results

- **GHZ (2 circuits):** both forgers are clearly different from real hardware (TVD 0.07 to 0.08 against a
  shot-noise floor of 0.026, p < 0.001). The stronger Forger is not closer (differences +0.002 and -0.003,
  CIs include 0). Real hardware is also further from the ideal output (0.12 to 0.13) than either forger
  (0.07 to 0.08): the forged GHZ results are too clean.
- **Random circuits (6 circuits):** stronger Forger closer than stock in 1 (13117 random4_2, +0.014, CI
  [+0.010, +0.018]). Inconclusive in 4. random4_1 in 13117 has no CZ gates, so it says nothing about two-qubit
  behavior. Even in the one improved case the stronger Forger is still different from real (TVD 0.063, floor
  0.033, p = 0.002).
- **Indistinguishable from real already:** 12894 random4_1 and 13117 random4_0 are consistent with both
  forgers (p > 0.1). There is nothing for the stronger Forger to improve there.
- **Across the 7 circuits that contain CZ gates:** stronger Forger closer in 1, inconclusive in 6, farther in
  0. The mean improvement is about +0.003 TVD, against typical forger-to-real distances of 0.03 to 0.08. For
  both forgers, 5 of the 7 are significantly different from real hardware.
- **v2_xfer** (extending the amplitude error to unprobed qubits) does not help: no circuit improves
  conclusively, and the results are often slightly worse.

Conclusion: the existing data does not show that the stronger Forger generalizes beyond the Canaries. It
matches the Canary curves it was fitted on, but on Workload circuits it is statistically no better than the
stock Forger, and both are still distinguishable from real hardware. The gap points to unmodeled two-qubit
or circuit-level error (real outputs are further from ideal than forged ones). That explanation is a
hypothesis, not tested here.

## Limitations

- Only 2 Genuine Runs, 1 backend, 1 calibration cycle, 8 Workload circuits, 1000 shots each. Intervals are wide
  and several circuits are inconclusive. No multiple-comparison correction was applied.
- The comparison is between near-exact forger distributions and 1000 real shots. The 100,000-shot forgers have
  their own small sampling error (a few thousandths of TVD).
- The two Runs ran minutes apart on the same calibration, so this does not test other days or other qubits.
- TVD-to-ideal for each variant uses the 1000-shot samples, so it includes a small upward shot-noise bias.
- Workload circuits only partly overlap the probed qubits, so the stronger Forger is mostly unchanged on them
  by construction. This test checks whether Canary-fitted effects carry over, not whether a better-fitted
  forger could match the workloads.

## Reproduce

```sh
PYTHONPATH=. .venv/bin/python -W ignore scripts/workload_generalization.py
```

The script is `scripts/workload_generalization.py`. The tables above came from one run with seed 0.
