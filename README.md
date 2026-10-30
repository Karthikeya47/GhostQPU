# GhostQPU

Detects quantum cloud jobs that never touched a quantum computer.

A dishonest reseller can take your job, simulate it from IBM's **public calibration data**, and bill you for QPU time. GhostQPU hides small **canary** circuits in your batch. Real hardware has effects that a calibration-based simulator leaves out (coherent over-rotation, neighbor crosstalk, context-dependent readout, drift over time). A small classifier on those effects says Genuine or Forged.

We built both sides: the **Forger** (the attack, using the exact calibration that was live when the job ran) and the **Detector**. Vocabulary is in [CONTEXT.md](CONTEXT.md), scope in [PLAN.md](PLAN.md).

**Q-Hack India 2026** · Team **lwyrup** (lead: Neelagiri Karthikeya) · Track: Quantum Security & Cryptography

## For reviewers

| What | Where |
|---|---|
| Interactive site | [web/](web/): six-chapter story with a live job console, Bloch sphere and "beat the Detector" lab (run it below) |
| Presenter notes | [docs/PRESENTATION.md](docs/PRESENTATION.md) |
| Demo video | [Google Drive](https://drive.google.com/drive/folders/1M0DklU9nP6OGHuq1RZSj4r4Gzi0MHY0b) (silent captioned cut: [demo/GhostQPU_demo.mp4](demo/GhostQPU_demo.mp4)) |
| Real IBM hardware runs + forged twins | [data/runs/](data/runs/) (training), [data/fresh/](data/fresh/) (scored blind), [data/pilot/runs/](data/pilot/runs/) (CNOT pilot) |
| Code | [ghostqpu/](ghostqpu/) (library + CLI), [web/](web/) (site), [scripts/](scripts/), [tests/](tests/) |

Run the site locally on the included real-hardware data (no IBM account needed):

```sh
cd web
npm install
npm run dev        # http://localhost:3000
```

### Repository layout

```
ghostqpu/
  snapshot.py    calibration snapshot: capture, save, rebuild into a noisy simulator
  canaries.py    builds a Batch: hidden canary circuits shuffled among workload circuits
  execution.py   submit to / collect from IBM hardware, and the Forger (Aer + calibration)
  runs.py        a Run: shot records + batch + calibration, saved to disk
  signature.py   12 canary features per time chunk of a Run
  detector.py    logistic regression, held-out evaluation, verdicts
  cli.py         add-account | accounts | submit | collect | evaluate | null-test
  forger.py      stronger Forger fitted from a Genuine probe run
  pilot.py       CNOT pilot circuits and analysis
scripts/         frozen scorer, CNOT pilot, cost and forward-in-time study, web data export
web/             Next.js site (reads web/public/data.json and cost.json)
data/runs/       2 genuine ibm_marrakesh runs and their forged twins (the frozen Detector's training set)
data/fresh/      later runs on marrakesh, fez and kingston, scored blind
tests/           pytest suite, no QPU time needed
```

## Results so far (Oct 10, 2026)

Two real jobs on IBM **ibm_marrakesh** (34 circuits x 1000 shots, 11 QPU seconds each), each with a forged twin from the calibration that was live when it ran.

| Canary | Real hardware | Forger |
|---|---|---|
| Error after 128 X gates | 32% | 4% |
| Idle-qubit shift from neighbor (16 us) | 7.8% | 0.4% |
| Readout error | 1.1 to 1.4% | 0.3 to 0.5% |

Detector, each job held out from training: **AUC 1.00**, all 4 jobs correct (genuine scores 0.02 and 0.06, forged 0.96 and 0.98). Both jobs share one calibration cycle.

### Cross-day and cross-backend check with the frozen Detector (Oct 27, 29 and 30)

The Detector above was frozen and never retrained. New jobs, each from a new calibration cycle, on ibm_marrakesh and two backends the Detector never saw:

| Job | Backend | Calibration cycle | Genuine score | Forged Twin score |
|---|---|---|---|---|
| J1 | ibm_marrakesh | 2026-10-27 12:06 | 0.18 (Genuine) | 0.99 (Forged) |
| J2 | ibm_marrakesh | 2026-10-29 20:01 | 0.00 (Genuine) | 0.99 (Forged) |
| F1 | **ibm_fez** | 2026-10-29 19:59 | 0.02 (Genuine) | 0.99 (Forged) |
| K1 | **ibm_kingston** | 2026-10-29 20:38 | 0.00 (Genuine) | 0.99 (Forged) |
| K2 | ibm_kingston, same qubits | 2026-10-29 21:18 | 0.00 (Genuine) | 0.99 (Forged) |
| F2 | ibm_fez, same qubits | 2026-10-29 21:22 | 0.00 (Genuine) | 0.99 (Forged) |
| J3 | ibm_marrakesh, new qubits | 2026-10-30 21:03 | 0.36 (Genuine, near the Inconclusive band) | 0.99 (Forged) |
| F3 | ibm_fez, new qubits | 2026-10-30 21:05 | 0.00 (Genuine) | 0.99 (Forged) |
| K3 | ibm_kingston, new qubits | 2026-10-30 21:01 | 0.00 (Genuine) | 1.00 (Forged) |
| J4 | ibm_marrakesh, repeat of J3 (same cycle, same qubits) | 2026-10-30 21:03 | 0.43 (Genuine, inside the Inconclusive band) | 0.99 (Forged) |
| F4 | ibm_fez, repeat of F3 | 2026-10-30 21:05 | 0.00 (Genuine) | 0.99 (Forged) |
| K4 | ibm_kingston, repeat of K3 | 2026-10-30 21:01 | 0.02 (Genuine) | 0.99 (Forged) |

24 of 24 correct: 12 Genuine jobs and their Twins over 9 calibration cycles, including two backends the Detector never saw. Each backend was caught by a different effect: fez mainly by neighbor crosstalk, kingston by coherent over-rotation (90% error after 128 X gates vs 3% for the Forger). Kingston's over-rotation survived a recalibration on the same qubits; fez's crosstalk stayed stable while its over-rotation doubled ([details](docs/research/recalibration-persistence.md)). With 0 errors in 12 Genuine jobs the 95% upper bound on the false-positive rate is 0.22, but the J3/J4, F3/F4 and K3/K4 pairs share a cycle and are not fully independent, so more cycles are still needed. J3 (0.36) and J4 (0.43) are the closest calls so far, and two separate jobs in the same cycle agreeing shows the thin margin belongs to that cycle and those qubits, not to shot noise ([details](docs/research/cross-day-2026-10-30.md)).

Pooling every Run and holding out one whole calibration cycle at a time (`evaluate()` on data/runs + data/fresh), the Detector scores AUC 1.00 with all 28 jobs correct (10 cycles, 3 backends); J3 and J4 move to a clear Genuine (0.29 and 0.34). Details: [J1](docs/research/fresh-hardware-j1.md), [J2](docs/research/fresh-hardware-j2.md), [ibm_fez](docs/research/cross-backend-fez.md), [ibm_kingston](docs/research/cross-backend-kingston.md).

### Next Canary: repeated CNOT, now on hardware

On ibm_marrakesh qubits 107-108, after 32 repeated CNOTs the target reads wrong **73%** of the time; the calibration-matched Forger predicts **10%**. Control circuits show the error comes from the CZ pulse itself (a coherent phase, z = 40), not from the conditional phase we hypothesized, and that it varies strongly between qubit pairs. Details: [docs/research/cnot-pilot-hardware.md](docs/research/cnot-pilot-hardware.md).

Related work and what is new: [docs/research/prior-work.md](docs/research/prior-work.md).

How few Canaries are enough, and does it work forward in time: [docs/research/cost-and-forward.md](docs/research/cost-and-forward.md). Demo video: [Google Drive](https://drive.google.com/drive/folders/1M0DklU9nP6OGHuq1RZSj4r4Gzi0MHY0b).

## Setup

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# .venv/bin/python -m pip install -r requirements.txt     # macOS / Linux
```

The commands below use `python` for the venv's interpreter.

## Hardware day

1. Save each IBM account (the API key is read hidden; get it from quantum.cloud.ibm.com):

   ```sh
   python -m ghostqpu add-account alice
   python -m ghostqpu accounts          # backends + remaining QPU time per account
   ```

2. Submit a batch (34 circuits: 30 hidden canaries + 4 workload circuits). Start with fewer shots to measure the cost:

   ```sh
   python -m ghostqpu submit --account alice --backend ibm_kingston --shots 1000
   ```

3. When the job finishes, collect it. This saves the Genuine run, fetches the calibration that was valid when the job **started**, and forges its Twin right away:

   ```sh
   python -m ghostqpu collect           # prints QPU seconds used
   ```

4. You need at least **two** Genuine runs before the Detector can be evaluated. Runs from different calibration cycles (different days) make the result stronger, and the evaluation then holds out whole cycles.

   ```sh
   python -m ghostqpu evaluate
   ```

## Demo

The site in [web/](web/) (see "Web frontend" below) is the demo. Its chapters are linkable: `#problem`, `#trap`, `#run`, `#evidence`, `#verdict`, `#break`.

- **Run a job**: replays any of the real recorded jobs end to end and gives a Verdict scored without that job's calibration cycle.
- **Evidence**: canary curves from hardware vs the Forger, for the same circuits and calibration.
- **Verdict**: held-out accuracy, cost of verification, forward-in-time test, day-to-day variation.
- **Break it**: run the frozen Detector in the browser and try to fake your way past it.

## The null test

```sh
python -m ghostqpu null-test
```

This runs the whole pipeline with a simulator on **both** sides. The Detector must fail here (AUC near 0.5). If it succeeded, it would be detecting a formatting artifact instead of physics. Current result: AUC 0.52, PASS (rerun 2026-10-30 with the seeded Forger; it was 0.40 before).

## If the Detector can't separate them

That is a result too: "public calibration data is enough to fake a quantum computer." The Evidence chapter shows how close the forgery gets.

## Development

```sh
python -m pytest        # about 1 minute, no QPU time
python -m ruff check .
```

## Web frontend

A 3D, animated Next.js site in [web/](web/) tells the story in six chapters (problem, trap, run a job, evidence, verdict, break it) with the same data: the real ibm_marrakesh lattice, a job console that replays any real job end to end, a data-driven Bloch sphere, a "beat the Detector" lab that runs the frozen Detector in the browser, Canary curves, day-to-day variation, held-out Verdicts and the research stress tests.

```sh
PYTHONPATH=. python scripts/export_web_data.py   # regenerate web/public/data.json from data/runs and data/fresh
cd web && npm install && npm run dev             # http://localhost:3000
```
