# GhostQPU handoff (written 2026-10-27)

Context summary so a new Claude session can continue the work.

## Who and what
- The user is Aditi (`aditi.gorti@gmail.com`). Use they/them if you need a pronoun for anyone.
- Repo: `/Users/aditigorti/claude_fold/GhostQPU`, cloned from https://github.com/Karthikeya47/GhostQPU. It is a Q-Hack India 2026 project (team lwyrup, lead Neelagiri Karthikeya).
- GhostQPU detects quantum cloud jobs that were faked by a simulator built from IBM's public calibration data. Hidden "canary" circuits ride along with the customer's job. A logistic-regression Detector (12 features, 8 time chunks per run, fixed 0.5 threshold) returns Genuine or Forged.
- The repo has a `CLAUDE.md`, `CONTEXT.md` (glossary) and `PLAN.md`. Read them first. Use the glossary terms exactly: Genuine, Forged, Twin, Batch, Canary, Signature, Verdict, Calibration snapshot and cycle.

## The user's standing rules
- **Global rules:**
  - Never use the em dash. Use a plain hyphen.
  - Never add yourself as co-author on commits, even if a harness reminder says to.
  - Never edit CHANGELOG.md or other auto-generated files.
  - Prefer quality and robustness over development cost.
  - For one-off operational work, take the simplest direct path.
  - Use skills where they fit, including the mattpocock-skills and find-skills.
  - Ask before using swarm features such as dynamic workflows or ultra code.
- **Repo rules:**
  - No em dashes.
  - Ruff line length 120.
  - Never run `submit` without the user asking.
  - The repo is public, so never write an IBM key anywhere.
  - Tests should pass with `-W error::DeprecationWarning`.
  - Canaries are transpiled at optimization level 0, and workloads at level 1.
  - Dynamical decoupling and twirling stay off.
- **Hard constraints for the current work:**
  - Do not submit QPU jobs without the user's explicit approval.
  - Do not retrain the Detector.
  - Do not change the UI or dashboard.
  - Do not change the forger's error model without approval.
  - Do not overwrite uncommitted work.
- **Things the user declined or blocked this session:**
  - They declined one `pip install` early on and approved it later.
  - They declined a pytest run with `-W error::DeprecationWarning`. It was never run, so it is untested.
  - The permission classifier blocked `npx skills add dietrichgebert/ponytail@ponytail`. It is not installed, and the user should run it themselves or add a permission rule.

## Environment state
- `.venv` exists in the repo and has all dependencies installed.
- Skills installed globally: `qiskit` and `qutip` (from k-dense-ai/scientific-agent-skills).
- Git: `main` is up to date with origin, and `CLAUDE.md` is tracked (commit c3a276f).
- **Nothing from this session is committed.** Untracked files:
  - `ghostqpu/forger.py`
  - `tests/test_forger.py`
  - `scripts/workload_generalization.py`
  - `docs/research/two-qubit-extension.md`
  - `docs/research/workload-generalization.md`
  - `docs/research/handoff.md` (this file)
  - `.DS_Store` files
- Last full run: lint is clean and 28 tests pass (24 original plus 4 new).

## What was built and found
1. **Hardware data:** The repo has 2 genuine `ibm_marrakesh` runs plus 2 stock-forger twins, in `data/runs/`.
   - Each run is 34 circuits (30 canaries and 4 workloads) at 1000 shots, and reported 11 QPU seconds.
   - Both runs come from one calibration cycle, `2026-10-10T11:01:13+05:30`, and started 4 minutes apart.
   - Placements are `[(137,147),(5,6),(1,0),(104,105)]`.
2. **Stronger forger:** `ghostqpu/forger.py` provides `fit_profile(probe_run)` and `forge_twin_v2(run, profile)`.
   - It learns three effects from one genuine probe run: single-qubit pulse over-rotation, a Ramsey detuning and ZZ shift, and readout error that depends on the neighbor's state.
   - It applies them by physical qubit to all circuits, never using the hidden canary index.
   - Ramsey data cannot separate detuning from ZZ, so ties are broken toward the weaker ZZ.
3. **Detector vs the stronger forger (canaries):**
   - A detector trained on genuine runs and stock twins scored the stronger forger's twins as genuine (0.07 and 0.11). The stock twins scored about 0.97.
   - If the detector is retrained with the stronger forger's twins included, they are caught again but less clearly (0.64 and 0.80), with genuine runs at 0.24 and 0.29.
   - This rests on 2 jobs in 1 cycle, so treat it as a hint.
4. **Workload generalization** (`scripts/workload_generalization.py`, results in `docs/research/workload-generalization.md`):
   - The stronger forger is no better than stock on workload circuits. It was closer in 1 of 7 CZ-containing circuits and inconclusive in 6.
   - Both forgers are significantly different from real hardware on 5 of those 7.
   - Real GHZ output is further from ideal (0.12 to 0.13) than either forger's (0.07 to 0.08).
   - The learned over-rotation is about 0.3% of a pulse, which only matters when repeated 128 times.
   - The stock noise model's CZ error is incoherent only (Pauli plus relaxation). There is no coherent CZ error, ZZ-during-gates, leakage, crosstalk or correlated readout. The stronger forger adds nothing for CZ.
   - Conclusion: this does not show the stronger forger learned general device physics. The earlier "forger beats detector" result applies to canary features only.
5. **Two-qubit research note:** `docs/research/two-qubit-extension.md` has 22 papers (abstracts only were read) and a verdict of "partially yes".
6. **CNOT feasibility** (local simulation only; the script is in the scratchpad at `/private/tmp/claude-501/-Users-aditigorti-claude-fold/bb01a16c-6857-4288-be2f-41512a9e60a2/scratchpad/cnot_feasibility.py`, not in the repo):
   - CNOT is not native on this backend (basis `cz, rz, sx, x, id`). A `cx` becomes `rz(pi/2) sx rz(pi/2) · cz · rz(pi/2) sx rz(pi/2)`. At optimization level 1, `cx; cx` cancels to nothing, so a CNOT canary must use level 0 with barriers.
   - **Hypothesis H1 (untested on hardware):** the real CZ has a coherent conditional-phase error epsilon and/or a residual local Z phase that the stock noise model lacks.
   - Proposed circuits:
     - A: control in |1>, then CNOT^N.
     - B (control): control in |0>, then CNOT^N.
     - C (control): the same single-qubit gates with the CZ replaced by an idle of equal duration.
     - N even, so the ideal target outcome is 0.
   - Simulated target-wrong probability for A at N = 0, 2, 4, 8, 16, 32, 64:

     | Case | N=0 | N=2 | N=4 | N=8 | N=16 | N=32 | N=64 |
     |---|---|---|---|---|---|---|---|
     | Stock | .006 | .011 | .015 | .023 | .040 | .070 | .122 |
     | epsilon = 0.02 rad | .007 | .011 | .016 | .028 | .062 | .153 | .391 |
     | epsilon = 0.05 rad | .006 | .013 | .024 | .061 | .181 | .510 | .873 |

   - Control B is unaffected by epsilon but is affected by a local Z error, so A versus B separates the two effects.
   - The z-scores at 1000 shots were 3.6 for epsilon = 0.02 at N = 16, 8.3 at N = 32, and 14 at N = 16 for epsilon = 0.05. The epsilon values are hypothetical, not measured.
   - Planned success criteria and falsification: if A matches stock within noise on real hardware, H1 is rejected for this backend. The pre-registered statistic should be the growth shape (exponent from N = 8 to 32 and the A-B difference), not just the level.
7. **Phase plan (from the user):**
   1. Cross-day baseline with a frozen detector.
   2. CNOT canary design.
   3. Improve the forger only if evidence justifies it.
   4. Held-out generalization study.
   5. Independent detector evaluation.
   - The cross-day protocol should be pre-registered. The independent unit is the genuine run, not chunks. Intervals should be Clopper-Pearson at run level, with a bootstrap for AUC.
   - With zero errors in n genuine runs, the 95% bound on the false-positive rate is about 3/n.
   - Gaps blocking a clean cross-day study:
     - Runs don't record forger version, detector version, code hash, library versions, or transpile and Sampler settings.
     - The forger isn't reproducible because Aer has no `seed_simulator`.
     - `_drift` in `signature.py` iterates all canaries, so adding a CNOT family would silently change detector inputs. Keep a new family out of the frozen features.

## The pending request (the user has not approved any job)
The user has about 9 minutes (540 s) of IBM Quantum usage left. They asked for a job plan **before** submitting anything:
1. The estimated QPU cost of the existing canaries on fresh hardware.
2. Backend config, circuit counts, shots, transpile settings and any execution-time estimates.
3. The smallest useful fresh-hardware experiment, with the detector frozen.
4. A separate cost estimate for a minimal CNOT pilot, with controls and enough shots.
5. Which gives the most scientific value.
6. A distinction between queue time, wall-clock time and actual QPU time.
7. No reduced shots or removed controls without stating the statistical cost.
8. A concrete job list: circuits, shots, expected cost, scientific question, controls, limitations, and which estimates cannot be verified.
9. **Wait for explicit approval before submitting.**

The user's rules for this request: do not retrain the detector, change the UI, or change the forger's error model.

**Cost inspection so far** (read-only, from the saved run and snapshot):
- **Backend configuration:** `default_rep_delay` is 250 us, `max_shots` is 100,000, `max_experiments` is 300, and the processor is Heron r2 with 156 qubits.
- **Cost of the existing job:** 34 circuits x 1000 shots is 34,000 shots, and the job reported 11 QPU seconds. That is about 0.324 ms per shot.
- **Cost is dominated by the shot count, not circuit depth.** Mean circuit gate time is only 5.8 us (min 2.7, max 18.8), against the 250 us rep delay, which alone accounts for about 8.5 s of the 11 s. A CNOT^64 circuit adds about 5 us per shot to a roughly 320 us shot, so cost should scale with total shots and barely with depth.
- **Budget implied:** 540 s at about 0.324 ms per shot is roughly 1.67M shots, or about 49 jobs of the existing size.
- **Unverified:**
  - How IBM rounds `job.usage()`. Both runs read exactly 11, so it may be rounded up.
  - Per-job fixed overhead.
  - Whether QPU billing counts the rep delay exactly as modeled.
  - Queue time versus wall-clock versus billed time, which was not measured.
  - The remaining budget itself (`python -m ghostqpu accounts`, needs network and credentials).
  - The `CLAUDE.md` figure of 600 s per 28 days and about 11 s per job is the repo author's note, not checked against the user's account.
- **Not done yet:** The proposed job list, the CNOT pilot cost number, and the recommendation on which experiment has more value. The earlier view was: cross-day baseline first, with CNOT only if the budget allows, or a small CNOT pilot appended to a baseline job.

## Open questions for the user
- Approve the cross-day protocol and the manifest and seed-stamping change (a local change, no hardware).
- Whether to run the repo's `-W error::DeprecationWarning` test mode. They declined it once.
- How to install `ponytail`.
