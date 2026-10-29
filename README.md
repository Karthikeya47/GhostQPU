# GhostQPU

Detects quantum cloud jobs that never touched a quantum computer.

A dishonest reseller can take your job, simulate it from IBM's **public calibration data**, and bill you for QPU time. GhostQPU hides small **canary** circuits in your batch. Real hardware has effects that a calibration-based simulator leaves out (coherent over-rotation, neighbor crosstalk, context-dependent readout, drift over time). A small classifier on those effects says Genuine or Forged.

We built both sides: the **Forger** (the attack, using the exact calibration that was live when the job ran) and the **Detector**. Vocabulary is in [CONTEXT.md](CONTEXT.md), scope in [PLAN.md](PLAN.md).

**Q-Hack India 2026** · Team **lwyrup** (lead: Neelagiri Karthikeya) · Track: Quantum Security & Cryptography

## For reviewers

| What | Where |
|---|---|
| Live dashboard | [Streamlit Cloud](https://ghostqpu-xk84u6gxdnv2bb26lvakuj.streamlit.app/?data=hardware) (real IBM hardware data, nothing to install) |
| Presentation | [docs/GhostQPU_QHack_India26.pptx](docs/GhostQPU_QHack_India26.pptx) |
| Demo video | [Google Drive](https://drive.google.com/drive/folders/1M0DklU9nP6OGHuq1RZSj4r4Gzi0MHY0b) (silent captioned cut: [demo/GhostQPU_demo.mp4](demo/GhostQPU_demo.mp4)) |
| Plain-language explainer | [docs/GhostQPU_explained.pdf](docs/GhostQPU_explained.pdf) |
| Real IBM hardware runs + forged twins | [data/runs/](data/runs/) |
| Code | [ghostqpu/](ghostqpu/) (library + CLI), [app.py](app.py) (dashboard), [tests/](tests/) |

Or run the dashboard locally on the included real-hardware data (no IBM account needed):

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # macOS / Linux: .venv/bin/python
.venv/Scripts/python -m streamlit run app.py
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
app.py           Streamlit dashboard (Verify a job, Evidence, Detector)
data/runs/       2 genuine ibm_marrakesh runs and their forged twins
tests/           24 tests, no QPU time needed
```

## Results so far (Oct 10, 2026)

Two real jobs on IBM **ibm_marrakesh** (34 circuits x 1000 shots, 11 QPU seconds each), each with a forged twin from the calibration that was live when it ran.

| Canary | Real hardware | Forger |
|---|---|---|
| Error after 128 X gates | 32% | 4% |
| Idle-qubit shift from neighbor (16 us) | 7.8% | 0.4% |
| Readout error | 1.1 to 1.4% | 0.3 to 0.5% |

Detector, each job held out from training: **AUC 1.00**, all 4 jobs correct (genuine scores 0.02 and 0.06, forged 0.96 and 0.98). Both jobs share one calibration cycle.

### Cross-day and cross-backend check with the frozen Detector (Oct 27 and 29)

The Detector above was frozen and never retrained. Three new jobs, each from a new calibration cycle and new qubit placements, one on a second backend:

| Job | Backend | Calibration cycle | Genuine score | Forged Twin score |
|---|---|---|---|---|
| J1 | ibm_marrakesh | 2026-10-27 12:06 | 0.18 (Genuine) | 0.99 (Forged) |
| J2 | ibm_marrakesh | 2026-10-29 20:01 | 0.00 (Genuine) | 0.99 (Forged) |
| F1 | **ibm_fez** | 2026-10-29 19:59 | 0.02 (Genuine) | 0.99 (Forged) |

6 of 6 correct, on a backend the Detector never saw. With 0 errors in 3 Genuine jobs the 95% upper bound on the false-positive rate is 0.63, so more cycles are needed. Details: [J1](docs/research/fresh-hardware-j1.md), [J2](docs/research/fresh-hardware-j2.md), [ibm_fez](docs/research/cross-backend-fez.md).

### Next Canary: repeated CNOT, now on hardware

On ibm_marrakesh qubits 107-108, after 32 repeated CNOTs the target reads wrong **73%** of the time; the calibration-matched Forger predicts **10%**. Control circuits show the error comes from the CZ pulse itself (a coherent phase, z = 40), not from the conditional phase we hypothesized, and that it varies strongly between qubit pairs. Details: [docs/research/cnot-pilot-hardware.md](docs/research/cnot-pilot-hardware.md).

Slides: [docs/GhostQPU_QHack_India26.pptx](docs/GhostQPU_QHack_India26.pptx). Demo video: [Google Drive](https://drive.google.com/drive/folders/1M0DklU9nP6OGHuq1RZSj4r4Gzi0MHY0b). New to quantum computing? Start with the plain-language explainer: [docs/GhostQPU_explained.pdf](docs/GhostQPU_explained.pdf).

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

Live on [Streamlit Cloud](https://ghostqpu-xk84u6gxdnv2bb26lvakuj.streamlit.app/?data=hardware), or locally:

```sh
python -m streamlit run app.py
```

- **Verify a job**: pick an anonymized job and get a verdict (Genuine, Forged or Inconclusive). Every score comes from a Detector that never saw that job or its twin.
- **Evidence**: canary curves from hardware vs the Forger, for the same circuits and calibration.
- **Detector**: held-out AUC, job accuracy, and which features drive the decision.

`?data=stand_in` in the URL opens the null test view.

## The null test

```sh
python -m ghostqpu null-test
```

This runs the whole pipeline with a simulator on **both** sides. The Detector must fail here (AUC near 0.5). If it succeeded, it would be detecting a formatting artifact instead of physics. Current result: AUC 0.40, PASS.

## If the Detector can't separate them

That is a result too: "public calibration data is enough to fake a quantum computer." The Evidence tab shows how close the forgery gets.

## Development

```sh
python -m pytest        # about 1 minute, no QPU time
python -m ruff check .
```

## Web frontend

A 3D, animated Next.js site in [web/](web/) shows the same data: the real ibm_marrakesh lattice, Canary curves, per-placement ribbons, shot records, held-out Verdicts and the research-branch stress tests.

```sh
PYTHONPATH=. python scripts/export_web_data.py   # regenerate web/public/data.json from data/runs and data/fresh
cd web && npm install && npm run dev             # http://localhost:3000
```
