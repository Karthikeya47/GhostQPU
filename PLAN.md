# GhostQPU MVP plan

Terms in **bold** are defined in [CONTEXT.md](CONTEXT.md). Goal: a working demo for a hackathon, not a paper.

## The demo story (what judges see)

1. "Quantum time is sold through resellers. You can't check that your job ran on a QPU, and small jobs are cheap to fake from IBM's public calibration data."
2. We built the **Forger**: it takes the **Calibration snapshot** from when the job ran and simulates the same circuits.
3. We hide a few **Canaries** in the Customer's **Batch**. Plot: Genuine vs Forged canary curves side by side.
4. Live: pick a Run you haven't seen, and the **Detector** gives a **Verdict** with a score.
5. If the Detector fails, the pitch flips to "public calibration data is enough to fake a QPU". Either way we show real IBM data.

## Scope

In:

- Calibration snapshot capture and rebuild into a simulator.
- Three Canary families, hidden among a few Workload circuits.
- Submit to IBM, collect later (free-plan queues can be long), forge a Twin automatically on collect.
- Signature features, logistic regression Detector, leave-one-Run-out evaluation.
- A Streamlit demo page.
- A null test: local simulator vs Forger must score about chance, which proves we aren't detecting a formatting artifact.

Out (mention as future work on a slide): canary-aware forger, cross-backend study, statistical rigor beyond a bootstrap CI.

## Code layout

```
ghostqpu/
  snapshot.py    CalibrationSnapshot: capture / save / load / simulator_backend
  canaries.py    build_batch(snapshot, seed) -> Batch (ISA circuits + hidden index)
  runs.py        Run (shot records + batch + snapshot), save / load_runs
  execution.py   submit / collect (IBM Sampler), forge_twin(run), stand_in_run (local)
  signature.py   signatures(run, n_chunks), canary_curves(run)
  detector.py    dataset / evaluate (held out by cycle or pair) / train / verdict
  cli.py         add-account | accounts | submit | collect | evaluate | null-test
app.py           Streamlit demo
tests/
```

The honest runner and the Forger both produce the same `Run` shape. That swap is exactly the attack. The Forger calls Aer directly with a noise model rebuilt from the snapshot (seconds per Run). The honest path uses the IBM runtime Sampler with twirling and dynamical decoupling off. A test proves both paths put the same qubit in the same bit column.

## Canaries

All placements run in parallel on non-adjacent qubit pairs. Dynamical decoupling and twirling are off.

| Family | Circuits | Genuine expectation | Forger expectation |
|---|---|---|---|
| Coherent amplification | X^N with barriers, N in {0,4,8,16,32,64,128}, plain and inside sx...sxdg | P(1) curves or oscillates | smooth, near-linear |
| Spectator | Ramsey on target, neighbor in 0 or 1, delays up to 16 us | phase depends on neighbor (ZZ) | no dependence |
| Readout context | target 0/1 x neighbor 0/1, measured together | readout error shifts with neighbor | fixed per qubit |

## Calibration snapshot timing

Capture at submission. On collect, also fetch the properties valid when the job started (`backend.properties(datetime=...)`). The Forger uses the execution-time snapshot.

## Day-1 checks (need your IBM accounts)

- `python -m ghostqpu accounts`: lists the backends and remaining QPU time per saved account.
- The first job reports its QPU seconds, then we set shots so the budget covers several calibration cycles.
