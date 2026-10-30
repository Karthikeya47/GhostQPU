<p align="center">
  <img src="assets/readme/hero.svg" width="100%" alt="GhostQPU: catch quantum jobs that never touched a quantum computer. After 128 X gates a real ibm_kingston qubit reads wrong 91% of the time; the calibration-matched Forger predicts 2%.">
</p>

<p align="center">
  <b>Q-Hack India 2026</b> · Team <b>lwyrup</b> (lead: Neelagiri Karthikeya) · Quantum Security &amp; Cryptography
  <br>
  <a href="#run-it">Run the demo</a> · <a href="docs/PRESENTATION.md">Presenter notes</a> · <a href="https://drive.google.com/drive/folders/1M0DklU9nP6OGHuq1RZSj4r4Gzi0MHY0b">Demo video</a> · <a href="#results">Results</a> · <a href="docs/research/">Research notes</a>
</p>

You pay a cloud reseller for time on a quantum computer. How do you know your job ever ran on one? IBM publishes calibration data for every machine, and anyone can turn it into a simulator that returns believable results. **GhostQPU hides small Canary circuits in your Batch** that probe physics the published calibration leaves out, and a small Detector turns their results into a Verdict: **Genuine** or **Forged**.

We built both sides: the **Forger** (the attack, simulating each job from the exact calibration that was live when it ran) and the **Detector**. Vocabulary is in [CONTEXT.md](CONTEXT.md).

## Proof

<p align="center">
  <img src="assets/readme/proof.svg" width="100%" alt="24 of 24 later jobs called correctly by a Detector frozen on 10 October; 3 IBM machines and 9 calibration cycles; 1.5 QPU seconds of Canaries still catches all 28 jobs.">
</p>

- **Frozen and blind.** Trained once on two jobs from 10 October, never retrained, then scored every later job: **24 of 24 correct** (12 real jobs and their forged copies) over 9 calibration cycles, including **ibm_fez and ibm_kingston, which it had never seen**.
- **Forward in time.** Trained only on earlier days and scored on the next: **24 of 24**, AUC 1.00.
- **Cheap.** **1.5 QPU seconds** of Canaries (19 circuits x 250 shots) still calls all 28 jobs correctly, 85% less than our current Batches use. No single Canary family manages it alone.
- **It detects physics, not formatting.** With a simulator on both sides, the same pipeline scores AUC **0.52**, chance level, as it must.
- **Real hardware, real data.** Every Run, Twin and calibration snapshot is committed in [data/](data/).

<p align="center"><img src="assets/readme/wire-how.svg" width="100%" alt=""></p>

## How it works

<p align="center">
  <img src="assets/readme/how-it-works.svg" width="100%" alt="Your Batch hides 30 Canary circuits. Either an IBM quantum computer or the Forger runs it. Twelve Canary features over eight time chunks feed the Detector, which returns Genuine or Forged.">
</p>

1. **Hide the Canaries.** Each Batch is 34 circuits: 4 of yours and 30 Canaries with a known ideal answer, compiled to native gates on physical qubits and shuffled, so the provider cannot tell them apart.
2. **Run.** An honest provider runs it on IBM hardware. A Forger runs the same circuits through Qiskit Aer with the noise model built from the calibration that was live at execution time.
3. **Measure what calibration leaves out.** Coherent over-rotation (P(1) after up to 128 X gates), neighbor crosstalk (an idle qubit shifting when its neighbor flips), readout that depends on the neighbor, and drift during the job. Twelve features per eighth of the job.
4. **Decide.** A logistic-regression Detector returns a forged score. Below 0.35 is Genuine, above 0.65 is Forged, in between is Inconclusive.

<p align="center"><img src="assets/readme/wire-run.svg" width="100%" alt=""></p>

## Run it

**The interactive site** tells the story in six chapters, with a console that replays any real job, a Bloch sphere driven by measured data, and a lab where you play the Forger against the real frozen Detector. No IBM account needed:

```sh
cd web
npm install
npm run dev        # http://localhost:3000
```

Chapters are linkable: `#problem`, `#trap`, `#run`, `#evidence`, `#verdict`, `#break`. For an offline copy, `npm run build` writes static files to `web/out/`; serve them with `python -m http.server 8080 -d web/out`.

**The Python pipeline:**

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # macOS / Linux: .venv/bin/python
.venv/Scripts/python -m ghostqpu null-test                # simulator vs Forger, must score near chance
.venv/Scripts/python -m ghostqpu evaluate                 # held-out Detector report on data/runs
```

<details>
<summary><b>Collect your own hardware runs</b> (spends IBM QPU time, about 11 s per job)</summary>

The commands below use `python` for the venv's interpreter.

1. Save each IBM account (the API key is read hidden; get it from quantum.cloud.ibm.com):

   ```sh
   python -m ghostqpu add-account alice
   python -m ghostqpu accounts          # backends + remaining QPU time per account
   ```

2. Submit a Batch (34 circuits: 30 hidden Canaries + 4 workload circuits, 1000 shots by default):

   ```sh
   python -m ghostqpu submit --account alice --backend ibm_kingston
   ```

3. When the job finishes, collect it. This saves the Genuine Run, fetches the calibration that was valid when the job **started**, and forges its Twin right away. Use `--into data/fresh` to score it blind with the frozen Detector:

   ```sh
   python -m ghostqpu collect --into data/fresh
   PYTHONPATH=. python scripts/score_fresh.py
   ```

4. Refresh the site's data:

   ```sh
   PYTHONPATH=. python scripts/export_web_data.py
   PYTHONPATH=. python scripts/cost_and_forward.py
   ```

</details>

<p align="center"><img src="assets/readme/wire-results.svg" width="100%" alt=""></p>

## Results

### First jobs (10 October)

Two real jobs on IBM **ibm_marrakesh** (34 circuits x 1000 shots, 11 QPU seconds each), each with a forged Twin from the calibration that was live when it ran.

| Canary | Real hardware | Forger |
|---|---|---|
| Error after 128 X gates | 32% | 4% |
| Idle-qubit shift from neighbor (16 us) | 7.8% | 0.4% |
| Readout error | 1.1 to 1.4% | 0.3 to 0.5% |

Detector, each job held out from training: **AUC 1.00**, all 4 jobs correct (Genuine scores 0.02 and 0.06, Forged 0.96 and 0.98). Both jobs share one calibration cycle. This Detector was then frozen.

### Frozen Detector, later days and other machines (27, 29 and 30 October)

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

24 of 24 correct: 12 Genuine jobs and their Twins over 9 calibration cycles, including two backends the Detector never saw.

- **Each machine is caught by a different effect:** fez mainly by neighbor crosstalk, kingston by coherent over-rotation (90% error after 128 X gates vs 3% for the Forger). Kingston's over-rotation survived a recalibration on the same qubits; fez's crosstalk stayed stable while its over-rotation doubled ([details](docs/research/recalibration-persistence.md)).
- **Closest calls:** J3 (0.36) and J4 (0.43). Two separate jobs in the same cycle agreeing shows the thin margin belongs to that cycle and those qubits, not to shot noise ([details](docs/research/cross-day-2026-10-30.md)).
- **With every cycle held out in turn** (`evaluate()` on data/runs + data/fresh): AUC 1.00, all 28 jobs correct over 10 cycles; J3 and J4 move to a clear Genuine (0.29 and 0.34).
- **Cost and forward in time:** [docs/research/cost-and-forward.md](docs/research/cost-and-forward.md).
- Earlier notes: [J1](docs/research/fresh-hardware-j1.md), [J2](docs/research/fresh-hardware-j2.md), [ibm_fez](docs/research/cross-backend-fez.md), [ibm_kingston](docs/research/cross-backend-kingston.md).

### Next Canary: repeated CNOT, on hardware

On ibm_marrakesh qubits 107-108, after 32 repeated CNOTs the target reads wrong **73%** of the time; the calibration-matched Forger predicts **10%**. Control circuits show the error comes from the CZ pulse itself (a coherent phase, z = 40), and that it varies strongly between qubit pairs: across four pilot jobs on three machines it is detected on 13 of 16 pairs ([details](docs/research/cnot-pilot-hardware.md)).

## Limits

- **Small sample.** With 0 errors in 12 Genuine jobs the 95% upper bound on the false-positive rate is 0.22, and the J3/J4, F3/F4 and K3/K4 pairs share a cycle, so they are not fully independent. More cycles are needed.
- **A Forger with hardware access can do better.** Our stronger Forger ([ghostqpu/forger.py](ghostqpu/forger.py)) fits over-rotation, crosstalk and readout from one real probe job and fooled the original Detector. It needs real QPU access to do so, and it does not generalize to the customer's own circuits ([details](docs/research/workload-generalization.md)).
- **If the Detector cannot separate them,** that is a result too: "public calibration data is enough to fake a quantum computer."
- Related work and what is new: [docs/research/prior-work.md](docs/research/prior-work.md).

<details>
<summary><b>Repository layout and development</b></summary>

```
ghostqpu/
  snapshot.py    calibration snapshot: capture, save, rebuild into a noisy simulator
  canaries.py    builds a Batch: hidden Canary circuits shuffled among workload circuits
  execution.py   submit to / collect from IBM hardware, and the Forger (Aer + calibration)
  runs.py        a Run: shot records + batch + calibration, saved to disk
  signature.py   12 Canary features per time chunk of a Run
  detector.py    logistic regression, held-out evaluation, Verdicts
  cli.py         add-account | accounts | submit | collect | evaluate | null-test
  forger.py      stronger Forger fitted from a Genuine probe run
  pilot.py       CNOT pilot circuits and analysis
scripts/         frozen scorer, CNOT pilot, cost and forward-in-time study, web data export
web/             Next.js site (reads web/public/data.json and cost.json)
data/runs/       2 Genuine ibm_marrakesh runs and their Twins (the frozen Detector's training set)
data/fresh/      later runs on marrakesh, fez and kingston, scored blind
data/pilot/runs/ CNOT pilot runs
docs/            presenter notes and research notes
assets/readme/   README images (SVG)
tests/           pytest suite, no QPU time needed
```

```sh
python -m pytest        # no QPU time
python -m ruff check .
```

</details>
