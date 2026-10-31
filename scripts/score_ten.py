"""A bigger Detector: train on the 10 earliest Genuine Runs and their Twins, score every later Run blind.

The frozen Detector (scripts/score_fresh.py) is trained on 2 Genuine Runs. This one keeps the same model and
features but trains on the first 10 Genuine Runs in time order (and their Twins), so every later Run is still
unseen. data/runs is not touched.

Run from the repo root:  PYTHONPATH=. python scripts/score_ten.py
"""

from __future__ import annotations

from pathlib import Path

from ghostqpu.detector import dataset, train, verdict
from ghostqpu.runs import GENUINE, load_runs

N_TRAIN = 10
CHUNKS = 8


def stamp(run) -> str:
    return run.run_id.split("_")[2]  # ibm_<backend>_<YYYYMMDDTHHMMSS>_<n>


def main() -> None:
    runs = [r for r in load_runs(Path("data/runs")) + load_runs(Path("data/fresh")) if r.info.get("shots") == 1000]
    by_id = {r.run_id: r for r in runs}
    genuine = sorted((r for r in runs if r.origin == GENUINE), key=stamp)
    train_ids = {r.run_id for r in genuine[:N_TRAIN]}
    train_ids |= {f"{i}_forged" for i in train_ids if f"{i}_forged" in by_id}
    train_runs = [by_id[i] for i in sorted(train_ids)]
    model = train(dataset(train_runs, CHUNKS))
    last = max(stamp(r) for r in train_runs)
    print(f"trained on {len(train_runs)} Runs ({N_TRAIN} Genuine + Twins), latest {last}, "
          f"{len({r.snapshot.cycle for r in train_runs})} cycles, "
          f"{len({r.batch.backend_name for r in train_runs})} Backends")

    scored = [r for r in runs if r.run_id not in train_ids]
    assert all(stamp(r) > last for r in scored if r.origin == GENUINE), "a scored Genuine Run predates training"
    right = 0
    for r in sorted(scored, key=lambda r: (stamp(r), r.origin)):
        s = verdict(model, r, CHUNKS).forged_score
        ok = (s < 0.5) == (r.origin == GENUINE)
        right += ok
        print(f"{r.run_id:<48} {r.origin:<8} {s:6.3f} {'ok' if ok else 'WRONG'}")
    print(f"\n{right}/{len(scored)} correct over {len({r.snapshot.cycle for r in scored})} cycles")


if __name__ == "__main__":
    main()
