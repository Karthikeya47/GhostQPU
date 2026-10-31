"""The stronger Forger against every Detector we have. Offline, no QPU time.

For each Genuine Run that shares its Backend and qubit placements with an earlier Genuine Run, the stronger Forger
(ghostqpu/forger.py) learns a profile from the earlier Run, as a real attacker with one past job would, and forges
the later one. Each forgery is then scored by:
  frozen      the Detector trained once on the four 10 October Runs (stock Twins only)
  stock-only  a Detector trained on every other cycle's Runs and stock Twins
  retrained   the same, plus the stronger forgeries of every other cycle (the defender has seen this attacker)

Run from the repo root:  PYTHONPATH=. python scripts/stronger_forger_study.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ghostqpu.detector import dataset, features_of, train
from ghostqpu.forger import fit_profile, forge_twin_v2
from ghostqpu.runs import GENUINE, load_runs

CHUNKS = 8


def main() -> None:
    dev = load_runs(Path("data/runs"))
    runs = dev + load_runs(Path("data/fresh"))
    genuine = sorted([r for r in runs if r.origin == GENUINE], key=lambda r: r.info.get("started_at", ""))
    pairs = []
    for i, target in enumerate(genuine):
        earlier = [p for p in genuine[:i] if p.batch.backend_name == target.batch.backend_name
                   and p.batch.placements == target.batch.placements]
        if earlier:
            pairs.append((earlier[-1], target))
    print(f"{len(pairs)} probe -> target pairs")

    forged = []
    for probe, target in pairs:
        v2 = forge_twin_v2(target, fit_profile(probe))
        forged.append(v2)
        print(f"  forged {target.run_id} from {probe.run_id}")

    base = dataset(runs, CHUNKS)
    v2df = dataset(forged, CHUNKS)
    feats = features_of(base)
    frozen = train(dataset(dev, CHUNKS))
    rows = []
    for probe, target in pairs:
        cyc = target.snapshot.cycle
        test = v2df[v2df["run_id"] == f"{target.run_id}_forged_v2"]
        real = base[base["run_id"] == target.run_id]
        stock_only = train(base[base["cycle"] != cyc])
        retrained = train(pd.concat([base[base["cycle"] != cyc], v2df[v2df["cycle"] != cyc]]))
        score = lambda m, df: float(m.predict_proba(df[feats])[:, 1].mean())  # noqa: E731
        rows.append({"target": target.run_id, "backend": target.batch.backend_name, "probe": probe.run_id,
                     "frozen": score(frozen, test), "stock_only": score(stock_only, test),
                     "retrained": score(retrained, test), "real_retrained": score(retrained, real)})
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(out.round(3).to_string(index=False))
    for col in ("frozen", "stock_only", "retrained"):
        print(f"{col:<11} caught (score > 0.5): {(out[col] > 0.5).sum()}/{len(out)}")
    print(f"real jobs still Genuine under the retrained Detector: {(out['real_retrained'] < 0.5).sum()}/{len(out)}")
    out.to_csv("docs/research/stronger-forger-study.csv", index=False)


if __name__ == "__main__":
    main()
