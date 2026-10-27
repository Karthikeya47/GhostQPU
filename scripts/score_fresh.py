"""Score fresh Runs with the frozen Detector. No QPU time, no retraining.

The Detector is fit once on exactly the four Runs in data/runs that it was always trained on
(two Genuine ibm_marrakesh Runs from one Calibration cycle and their stock Twins). Fresh Runs
collected with `python -m ghostqpu collect --into data/fresh` are only scored, never trained on.

The independent unit is the Genuine Run (and, more strictly, its Calibration cycle), not the
chunk. With k wrong Verdicts in n Runs the 95% upper bound is one-sided Clopper-Pearson.

Run from the repo root:  PYTHONPATH=. python scripts/score_fresh.py
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from scipy.stats import beta

from ghostqpu.detector import dataset, train, verdict
from ghostqpu.runs import FORGED, GENUINE, load_runs

TRAINING = Path("data/runs")
FRESH = Path("data/fresh")
FROZEN_RUN_IDS = {
    "ibm_marrakesh_20261010T061458_12894",
    "ibm_marrakesh_20261010T061458_12894_forged",
    "ibm_marrakesh_20261010T061841_13117",
    "ibm_marrakesh_20261010T061841_13117_forged",
}
CHUNKS = 8
TRAINED_SHOTS = 1000


def upper_95(k: int, n: int) -> float:
    return 1.0 if k >= n else float(beta.ppf(0.95, k + 1, n - k))


def main() -> None:
    training = load_runs(TRAINING)
    ids = {r.run_id for r in training}
    if ids != FROZEN_RUN_IDS:
        raise SystemExit(f"data/runs is not the frozen training set. Extra: {sorted(ids - FROZEN_RUN_IDS)}, "
                         f"missing: {sorted(FROZEN_RUN_IDS - ids)}")
    model = train(dataset(training, CHUNKS))
    coef = np.concatenate([model[0].mean_, model[0].scale_, model[-1].coef_[0], model[-1].intercept_])
    print(f"frozen Detector fingerprint {hashlib.sha256(coef.round(12).tobytes()).hexdigest()[:16]}")

    fresh = load_runs(FRESH)
    if not fresh:
        print(f"no fresh Runs in {FRESH}")
        return
    training_cycles = {r.snapshot.cycle for r in training}
    tally = {GENUINE: [0, 0], FORGED: [0, 0]}
    cycles: dict[str, set[str]] = {GENUINE: set(), FORGED: set()}
    print(f"\n{'run':<46} {'origin':<8} {'cycle':<26} {'score':>6}  verdict")
    for run in fresh:
        if run.info.get("shots") != TRAINED_SHOTS:
            print(f"   WARNING {run.run_id}: {run.info.get('shots')} shots, trained on {TRAINED_SHOTS}")
        v = verdict(model, run, CHUNKS)
        wrong = v.label != run.origin
        tally[run.origin][0] += wrong
        tally[run.origin][1] += 1
        cycles[run.origin].add(run.snapshot.cycle)
        seen = " (training cycle!)" if run.snapshot.cycle in training_cycles else ""
        print(f"{run.run_id:<46} {run.origin:<8} {run.snapshot.cycle:<26} {v.forged_score:6.3f}  "
              f"{v.label}{'  WRONG' if wrong else ''}{seen}  placements {run.batch.placements}")

    for origin, name in ((GENUINE, "false-positive rate (Genuine called Forged)"),
                         (FORGED, "miss rate (stock Twin called Genuine)")):
        k, n = tally[origin]
        if n:
            print(f"\n{name}: {k}/{n} Runs, 95% upper bound {upper_95(k, n):.3f}; "
                  f"{len(cycles[origin])} distinct Calibration cycles")


if __name__ == "__main__":
    main()
