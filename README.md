<p align="center">
  <img src="assets/readme/hero.svg" width="100%" alt="GhostQPU: catch quantum jobs that never touched a quantum computer. After 128 X gates a real ibm_kingston qubit reads wrong 91% of the time; the calibration-matched Forger predicts 2%.">
</p>

<p align="center">
  <b>Q-Hack India 2026</b> · Team <b>lwyrup</b> · Quantum Security &amp; Cryptography
  <br>
  Neelagiri Karthikeya (lead) · L Mohit Jain · Tanvi Jain · Aditi Gorti
  <br>
  <a href="https://jacklachan.github.io/GhostQPU/"><b>Live site</b></a> · <a href="docs/GhostQPU_QHack_India26.pptx"><b>Slides (PPT)</b></a> · <a href="#run-it">Run it locally</a> · <a href="docs/PRESENTATION.md">Presenter notes</a> · <a href="https://drive.google.com/drive/folders/1M0DklU9nP6OGHuq1RZSj4r4Gzi0MHY0b">Demo video</a> · <a href="#results">Results</a> · <a href="docs/research/">Research notes</a>
</p>

You pay a cloud reseller for time on a quantum computer. How do you know your job ever ran on one? IBM publishes calibration data for every machine, and anyone can turn it into a simulator that returns believable results. **GhostQPU hides small Canary circuits in your Batch** that probe physics the published calibration leaves out, and a small Detector turns their results into a Verdict: **Genuine** or **Forged**.

<table align="center">
  <tr>
    <td align="center"><b>44</b><br><sub>jobs on real IBM<br>quantum computers</sub></td>
    <td align="center"><b>3</b><br><sub>machines: marrakesh,<br>fez, kingston</sub></td>
    <td align="center"><b>21</b><br><sub>calibration<br>cycles, 4 days</sub></td>
    <td align="center"><b>56 / 56</b><br><sub>later jobs right, Detector<br>frozen on 2 jobs</sub></td>
    <td align="center"><b>1.5 s</b><br><sub>of QPU time is<br>enough to verify</sub></td>
  </tr>
</table>

We built both sides: the **Forger** (the attack, simulating each job from the exact calibration that was live when it ran) and the **Detector**. Vocabulary is in [CONTEXT.md](CONTEXT.md).

## Where it's useful

Buying straight from IBM, there is little reason to doubt a job ran. The need appears whenever someone sits between the Customer and the QPU, and checking costs about 1.5 QPU seconds per job.

- **Customers of resellers and aggregators.** Labs, startups and students often buy cheaper QPU time through a third party. That Provider can bill QPU seconds and run Aer instead: the attack we built and caught on 56 of 56 later jobs.
- **Research and benchmarking papers.** "We ran this on ibm_kingston" is taken on trust today. Canaries in the Batch, saved with the Run and its calibration, let authors and reviewers check it later.
- **Audits of funded quantum programmes.** Grants and national programmes pay for cloud QPU time. An auditor can check the billed hardware time was real without trusting the invoice.
- **Brokers and marketplaces.** A platform reselling several vendors can verify its own suppliers and offer a "verified on hardware" badge.
- **Honest mistakes.** A misconfigured pipeline or overloaded queue that quietly falls back to a simulator is caught the same way.
- **Billing disputes.** A saved Verdict for every job is evidence when a Customer challenges a QPU bill or asks for a refund.

## Proof

<p align="center">
  <img src="assets/readme/proof.svg" width="100%" alt="56 of 56 later jobs called correctly by a Detector frozen on 10 October; 3 IBM machines and 20 calibration cycles; 1.5 QPU seconds of Canaries still catches all 60 jobs.">
</p>

- **Frozen and blind.** Trained once on two jobs from 10 October, never retrained, then scored every later job: **56 of 56 correct** (28 real jobs and their forged copies) over 20 calibration cycles and 4 days, including **ibm_fez and ibm_kingston, which it had never seen**.
- **Forward in time.** Trained only on earlier days and scored on the next: **56 of 56**, AUC 1.00.
- **More training, still blind.** Trained on the 10 earliest real jobs (and their forged copies, 9 cycles, 3 machines) instead of 2, it scores every later job **40 of 40** and the closest real job drops from 0.43 to 0.22 (`scripts/score_ten.py`).
- **Cheap.** **1.5 QPU seconds** of Canary time (19 circuits x 250 shots) still calls all 60 jobs correctly, 85% less than our current Batches use, and no single Canary family manages it alone. **Checked on hardware over two days:** 12 of 12 real 250-shot runs (6 jobs and their forged copies) called right; IBM bills about 2 s of fixed overhead per job on top, so each billed 4 to 5 s.
- **Why the scores are perfect:** public calibration has no coherent-error term, so a calibration-only Forger is 2 to 4% wrong after 128 X gates where real hardware is 30 to 90%. Against our stronger Forger, which learns hardware effects from a real job, the original Detector fails ([Limits](#limits)).
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

**The interactive site** is live at **https://jacklachan.github.io/GhostQPU/** (deployed by `.github/workflows/pages.yml` on every push). It tells the story in six chapters, with a console that replays any real job, a Bloch sphere driven by measured data, and a lab where you play the Forger against the real frozen Detector. No IBM account needed:

```sh
cd web
npm install
npm run dev        # http://localhost:3000
```

Chapters are linkable: `#problem`, `#trap`, `#run`, `#evidence`, `#verdict`, `#break`. For an offline copy, `npm run build` writes static files to `web/out/`; serve them with `python -m http.server 8080 -d web/out`.

**The backend API** (FastAPI) serves the frozen Detector and every committed Run over HTTP, with interactive docs at `/docs`:

```sh
.venv/Scripts/python -m uvicorn ghostqpu.api:app --port 8000
# GET /runs                      every committed Run
# GET /runs/{run_id}/verdict     the frozen Detector's Verdict, with per-chunk scores
# GET /detector                  features, weights and fingerprint
```

**The Python pipeline:**

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # macOS / Linux: .venv/bin/python
.venv/Scripts/python -m ghostqpu null-test                # simulator vs Forger, must score near chance
.venv/Scripts/python -m ghostqpu evaluate                 # held-out Detector report on data/runs
```

**Check one job** with the frozen Detector:

```sh
.venv/Scripts/python -m ghostqpu verify data/fresh/ibm_kingston_20261029T154358_88635
# ibm_kingston_20261029T154358_88635: Genuine (forged score 0.000; below 0.35 Genuine, above 0.65 Forged)
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

### Frozen Detector, scored blind on every later job

Trained on the two 10 October jobs above, then frozen. Nothing was retrained or tuned before scoring these.

| Machine | Seen in training? | Real jobs | Calibration cycles | Real jobs called Genuine | Forgeries caught | What gave it away |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **ibm_marrakesh** | 10 Oct only | 10 | 7 | **10 / 10** | **10 / 10** | a mix: over-rotation, crosstalk, readout |
| **ibm_fez** | never | 8 | 6 | **8 / 8** | **8 / 8** | neighbor crosstalk, then over-rotation |
| **ibm_kingston** | never | 10 | 7 | **10 / 10** | **10 / 10** | coherent over-rotation (91% vs 2% after 128 X gates) |
| **Total** | | **28** | **20** | **28 / 28** | **28 / 28** | 0 errors; 95% bound 0.10 per job, 0.14 per cycle |

<details>
<summary><b>Every job</b> (forged score: below 0.35 Genuine, above 0.65 Forged)</summary>

| Job | Machine | Calibration cycle | Qubits | IBM job id | Real job | Its forged Twin |
|---|---|---|---|---|:---:|:---:|
| J1 | marrakesh | 27 Oct 12:06 | new | `dbg33ctjm0ks73efpbc0` | 0.18 ✅ | 0.99 ✅ |
| F1 | fez | 29 Oct 19:59 | new | `dbhlv5k2d77s739d0no0` | 0.02 ✅ | 0.99 ✅ |
| J2 | marrakesh | 29 Oct 20:01 | new | `dbhlogdep8hs73amdtfg` | 0.00 ✅ | 0.99 ✅ |
| K1 | kingston | 29 Oct 20:38 | new | `dbhmjfk2d77s739d1vsg` | 0.00 ✅ | 0.99 ✅ |
| K2 | kingston | 29 Oct 21:18 | same as K1 | `dbhmr5mne4hc73bd7jcg` | 0.00 ✅ | 0.99 ✅ |
| F2 | fez | 29 Oct 21:22 | same as F1 | `dbhmrj01h92s738234a0` | 0.00 ✅ | 0.99 ✅ |
| K3 | kingston | 30 Oct 21:01 | new | `dbibmvdep8hs73anhfd0` | 0.00 ✅ | 1.00 ✅ |
| K4 | kingston | 30 Oct 21:01 | same cycle as K3 | `dbibr0mne4hc73be9300` | 0.02 ✅ | 0.99 ✅ |
| J3 | marrakesh | 30 Oct 21:03 | new | `dbibmp8hoj4c73b5snfg` | 0.36 ⚠️ | 0.99 ✅ |
| J4 | marrakesh | 30 Oct 21:03 | same cycle as J3 | `dbibqt0hoj4c73b5ssq0` | 0.43 ⚠️ | 0.99 ✅ |
| F3 | fez | 30 Oct 21:05 | new | `dbibmsene4hc73be8tp0` | 0.00 ✅ | 0.99 ✅ |
| F4 | fez | 30 Oct 21:05 | same cycle as F3 | `dbibr45ep8hs73anhkmg` | 0.00 ✅ | 0.99 ✅ |
| J5 | marrakesh | 30 Oct 22:05 | J3's, recalibrated | `dbicurene4hc73beasv0` | 0.00 ✅ | 0.99 ✅ |
| K5 | kingston | 30 Oct 22:06 | new | `dbicv56ne4hc73beateg` | 0.00 ✅ | 0.99 ✅ |
| F5 | fez | 30 Oct 22:32 | F3's, recalibrated | `dbicvcmne4hc73beatrg` | 0.00 ✅ | 0.99 ✅ |
| J6 | marrakesh | 30 Oct 22:40 | J3's, recalibrated | `dbid6k81h92s7383771g` | 0.00 ✅ | 0.98 ✅ |
| J7 | marrakesh | 31 Oct 08:57 | new | `dbim7381h92s7383p9f0` | 0.01 ✅ | 0.99 ✅ |
| F6 | fez | 31 Oct 09:00 | new | `dbim7atep8hs73ao5qlg` | 0.00 ✅ | 0.99 ✅ |
| K6 | kingston | 31 Oct 09:00 | new | `dbim775ep8hs73ao5qe0` | 0.00 ✅ | 0.99 ✅ |
| F7 | fez | 31 Oct 09:20 | F6's, recalibrated | `dbimerghoj4c73b6hnqg` | 0.00 ✅ | 0.99 ✅ |
| J8 | marrakesh | 31 Oct 08:57 | same cycle as J7 | `dbimeodep8hs73ao6890` | 0.00 ✅ | 0.99 ✅ |
| F8 | fez | 31 Oct 09:20 | same cycle as F7 | `dbimf2lep8hs73ao692g` | 0.00 ✅ | 0.99 ✅ |
| K7 | kingston | 31 Oct 09:20 | K6's, recalibrated | `dbimfbtep8hs73ao69mg` | 0.19 ✅ | 0.99 ✅ |
| K8 | kingston | 31 Oct 09:20 | same cycle as K7 | `dbin3ho1h92s7383ra1g` | 0.43 ⚠️ | 0.99 ✅ |
| J9 | marrakesh | 31 Oct 09:57 | J7's, recalibrated | `dbingd81h92s7383s8kg` | 0.37 ⚠️ | 0.99 ✅ |
| J10 | marrakesh | 31 Oct 09:57 | same cycle as J9 | `dbingm01h92s7383s950` | 0.28 ✅ | 0.99 ✅ |
| K9 | kingston | 31 Oct 10:16 | K6's, recalibrated | `dbinghohoj4c73b6kaog` | 0.22 ✅ | 0.99 ✅ |
| K10 | kingston | 31 Oct 10:16 | same cycle as K9 | `dbingq6ne4hc73bf0df0` | 0.31 ✅ | 0.99 ✅ |

✅ correct Verdict. ⚠️ correct side of 0.5 but inside the Inconclusive band. J3 and J4 were run by different team members; J are ibm_marrakesh, F fez, K kingston. J7 to J10, F6 to F8 and K6 to K10 ran on the morning of the presentation. The two 10 October training jobs are A (`db4tfp4vf2bc73cv3v1g`) and B (`db4thh2mb58s7389n1v0`).

</details>

<details>
<summary><b>The other 14 hardware jobs</b> (short Batches, CNOT pilots, disguised Canaries)</summary>

| Experiment | Machine | Ran at (UTC) | IBM job id | QPU s | Result |
|---|---|---|---|:---:|---|
| CNOT pilot (first try) | marrakesh | 2026-10-28 15:59 | `dbh1m6kdgr2s73cshlj0` | 11 | first pilot, Karthikeya's account; not analyzed |
| CNOT pilot | marrakesh | 2026-10-29 15:01 | `dbhlvcune4hc73bd5vng` | 11 | CZ error detected on 3 of 4 qubit pairs |
| CNOT pilot | fez | 2026-10-29 16:00 | `dbhmrds2d77s739d2de0` | 11 | CZ error detected on 4 of 4 qubit pairs |
| CNOT pilot | kingston | 2026-10-29 16:00 | `dbhmr9o1h92s7382340g` | 11 | CZ error detected on 4 of 4 qubit pairs |
| CNOT pilot | marrakesh | 2026-10-30 15:54 | `dbibr8une4hc73be93a0` | 11 | CZ error detected on 2 of 4 qubit pairs |
| Short Batch, 250 shots | marrakesh | 2026-10-30 17:10 | `dbicv00hoj4c73b5unvg` | 5 | real 0.00, Twin 0.95: both right |
| Short Batch, 250 shots | fez | 2026-10-30 17:11 | `dbicvh8hoj4c73b5up00` | 4 | real 0.00, Twin 0.99: both right |
| Short Batch, 250 shots | kingston | 2026-10-30 17:11 | `dbicv8o1h92s73836q6g` | 5 | real 0.00, Twin 0.99: both right |
| Short Batch, 250 shots | fez | 2026-10-31 04:00 | `dbimflune4hc73betu70` | 4 | real 0.00, Twin 0.98: both right |
| Short Batch, 250 shots | kingston | 2026-10-31 04:00 | `dbimfiene4hc73bettug` | 5 | real 0.04, Twin 0.99: both right |
| Short Batch, 250 shots | marrakesh | 2026-10-31 04:00 | `dbimfstep8hs73ao6b6g` | 5 | real 0.00, Twin 0.98: both right |
| Disguised Canaries | fez | 2026-10-31 04:02 | `dbimgrohoj4c73b6hsm0` | 6 | all zeros 76% real vs 88% Forger |
| Disguised Canaries | kingston | 2026-10-31 04:02 | `dbimgmo1h92s7383ps6g` | 6 | all zeros 88% real vs 91% Forger |
| Disguised Canaries | marrakesh | 2026-10-31 04:02 | `dbimgjlep8hs73ao6cvg` | 7 | all zeros 76% real vs 88% Forger |

</details>

- **Each machine is caught by a different effect:** fez mainly by neighbor crosstalk, kingston by coherent over-rotation (90% error after 128 X gates vs 3% for the Forger). Kingston's over-rotation survived a recalibration on the same qubits; fez's crosstalk stayed stable while its over-rotation doubled ([details](docs/research/recalibration-persistence.md)).
- **Closest calls:** J3 (0.36) and J4 (0.43). Two separate jobs in the same cycle agreeing shows the thin margin belongs to that cycle and those qubits, not to shot noise. J5 confirms it: the same qubits one recalibration later score a clear 0.00 ([details](docs/research/cross-day-2026-10-30.md)).
- **With every cycle held out in turn** (`evaluate()` on data/runs + data/fresh): AUC 1.00, all 60 jobs correct over 21 cycles. With that much training data every close call becomes a clear Genuine Verdict: J3 0.13, J4 0.16, K8 0.08 and J9 0.05.
- **Cost and forward in time:** [docs/research/cost-and-forward.md](docs/research/cost-and-forward.md).
- Earlier notes: [J1](docs/research/fresh-hardware-j1.md), [J2](docs/research/fresh-hardware-j2.md), [ibm_fez](docs/research/cross-backend-fez.md), [ibm_kingston](docs/research/cross-backend-kingston.md).

### Next Canary: repeated CNOT, on hardware

On ibm_marrakesh qubits 107-108, after 32 repeated CNOTs the target reads wrong **73%** of the time; the calibration-matched Forger predicts **10%**. Control circuits show the error comes from the CZ pulse itself (a coherent phase, z = 40), and that it varies strongly between qubit pairs: across four pilot jobs on three machines it is detected on 13 of 16 pairs ([details](docs/research/cnot-pilot-hardware.md)).

### Canaries disguised as customer circuits, on hardware

Could a provider spot our Canaries and run only those on real hardware? So we hid them inside random-looking circuits: a random circuit followed by its exact reverse, which ideally returns all zeros but is compiled and looks exactly like a customer's job. On all three machines the Forger is still too clean ([details](docs/research/mirror-canaries.md)):

| Machine | Real hardware returns all zeros | Forger predicts | Forger cleaner on |
|---|:---:|:---:|:---:|
| ibm_marrakesh | 76% | 88% | 15 / 16 circuits |
| ibm_kingston | 88% | 91% | 15 / 16 circuits |
| ibm_fez | 76% | 88% | 15 / 16 circuits |

This tests the overall error level, so it complements the X-chain Canaries, which test its shape.

## Limits

- **Small sample.** With 0 errors in 28 Genuine jobs the 95% upper bound on the false-positive rate is 0.10 per job, or 0.14 counting each of the 20 calibration cycles once (the J3/J4, F3/F4 and K3/K4 pairs share a cycle). More cycles are needed.
- **A Forger with hardware access can do better.** Our stronger Forger ([ghostqpu/forger.py](ghostqpu/forger.py)) learns over-rotation, crosstalk and readout from one earlier real job on the same qubits. Across 13 such pairs it fooled the frozen Detector on 12; a Detector retrained on this attacker's forgeries from other days catches 12 of 13, with 1 false alarm in 13 real jobs ([details](docs/research/stronger-forger-study.md)). It needs real QPU time to learn, and it does not generalize to the customer's own circuits ([details](docs/research/workload-generalization.md)).
- **If the Detector cannot separate them,** that is a result too: "public calibration data is enough to fake a quantum computer."
- Related work and what is new: [docs/research/prior-work.md](docs/research/prior-work.md).

## Next steps

1. **Drop-in adoption.** Wrap Qiskit's Sampler so Canaries are hidden automatically around any Customer circuit and a Verdict comes back with the results.
2. **More cycles.** One job per machine per day for weeks, to bring the false-positive bound well below 0.10.
3. **Against the stronger Forger.** Add the CNOT Canary to the Detector and randomize Canaries per job so they cannot be fitted in advance.
4. **Stronger disguised Canaries.** The mirror gap is 3 to 12 points, versus 30 to 90 for the X chains.
5. **Other vendors.** IonQ, Quantinuum or IQM have different error physics; the Canary families may not carry over.
6. **Partial forgery.** Not tested yet: a Provider that runs some circuits for real and forges the rest, or pads fewer shots.
7. **Ship a Detector trained on more than 2 jobs.** With more training data the close calls (J3, J4, K8, J9) all drop below 0.16.

## Team

Team **lwyrup**, Q-Hack India 2026, Quantum Security & Cryptography track.

| Name | Role |
|---|---|
| Neelagiri Karthikeya | Team lead |
| L Mohit Jain | Team member |
| Tanvi Jain | Team member |
| Aditi Gorti | Team member |

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
  cli.py         add-account | accounts | submit | collect | verify | evaluate | null-test
  forger.py      stronger Forger fitted from a Genuine probe run
  pilot.py       CNOT pilot circuits and analysis
  api.py         FastAPI backend: runs, verdicts, Detector
scripts/         frozen scorer, CNOT and mirror pilots, cost and forward-in-time study, web data export
web/             Next.js site (reads web/public/data.json and cost.json)
data/runs/       2 Genuine ibm_marrakesh runs and their Twins (the frozen Detector's training set)
data/fresh/      later runs on marrakesh, fez and kingston, scored blind
data/pilot/runs/ CNOT pilot runs
data/short/      real 250-shot runs that test the cost result (kept out of the frozen set)
data/mirror/     disguised (mirror) Canary pilot runs
docs/            presenter notes and research notes
assets/readme/   README images (SVG)
tests/           pytest suite, no QPU time needed
```

```sh
python -m pytest        # no QPU time
python -m ruff check .
```

</details>
