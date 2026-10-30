"""How few Canaries are enough, and does the Detector work forward in time? No QPU time, offline only.

1. Cost: drop Canary families or shots, then re-score every Run with the Detector held out by Calibration cycle.
   Drift features are left out of every row: they read all Canaries at once, so they cannot be priced per family.
2. Forward: order Calibration cycles in time; score each cycle with a Detector trained only on earlier cycles.

Writes docs/research/cost-and-forward.md and web/public/cost.json.
Run from the repo root:  PYTHONPATH=. python scripts/cost_and_forward.py
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

from ghostqpu.detector import dataset, evaluate, train
from ghostqpu.runs import FORGED, load_runs

CHUNKS = 8
SECONDS_PER_SHOT = 11 / 34_000  # every 34 x 1000-shot Batch so far billed 11 QPU seconds
FAMILIES = {  # feature prefix -> Canary circuits it needs in one Batch
    "coh_plain_": ("coherent, plain", 7),
    "coh_sx_": ("coherent, sx sandwich", 7),
    "spec_": ("spectator", 12),
    "ro_": ("readout context", 4),
}
CONFIGS = [
    ("all families (today)", ["coh_plain_", "coh_sx_", "spec_", "ro_"]),
    ("coherent plain + spectator", ["coh_plain_", "spec_"]),
    ("coherent plain + readout", ["coh_plain_", "ro_"]),
    ("coherent plain only", ["coh_plain_"]),
    ("spectator only", ["spec_"]),
    ("readout only", ["ro_"]),
]
SHOTS = (1000, 500, 250)


def summarize(pred) -> dict:
    per_run = pred.groupby("run_id").agg(origin=("origin", "first"), score=("forged_score", "mean"))
    forged = per_run["origin"] == FORGED
    return {
        "auc": float(roc_auc_score(pred["origin"] == FORGED, pred["forged_score"])),
        "correct": int(((per_run["score"] > 0.5) == forged).sum()),
        "jobs": len(per_run),
        "worst_genuine": float(per_run.loc[~forged, "score"].max()),
        "worst_forged": float(per_run.loc[forged, "score"].min()),
    }


def keep(df, prefixes):
    meta = ["run_id", "pair", "origin", "cycle", "backend", "chunk"]
    return df[meta + [c for c in df.columns if any(c.startswith(p) for p in prefixes)]]


def forward(df) -> tuple[dict, list[dict]]:
    cycles = sorted(df["cycle"].unique())
    held = []
    for i, cycle in enumerate(cycles):
        past = df[df["cycle"].isin(cycles[:i])]
        if past["origin"].nunique() < 2:
            continue
        test = df[df["cycle"] == cycle]
        model = train(past)
        feats = [c for c in df.columns if c not in ("run_id", "pair", "origin", "cycle", "backend", "chunk")]
        held.append(test[["run_id", "origin", "cycle", "backend"]].assign(
            forged_score=model.predict_proba(test[feats])[:, 1], trained_on=i))
    import pandas as pd

    pred = pd.concat(held, ignore_index=True)
    rows = pred.groupby("run_id").agg(
        origin=("origin", "first"), cycle=("cycle", "first"), backend=("backend", "first"),
        trained_on=("trained_on", "first"), score=("forged_score", "mean")).reset_index()
    return summarize(pred), rows.sort_values(["cycle", "run_id"]).to_dict(orient="records")


def main() -> None:
    runs = load_runs(Path("data/runs")) + load_runs(Path("data/fresh"))
    cost = []
    for shots in SHOTS:
        df = dataset([replace(r, shots=[s[:shots] for s in r.shots]) for r in runs], CHUNKS)
        for name, prefixes in CONFIGS:
            if shots != 1000 and name != CONFIGS[0][0] and name != "coherent plain + spectator":
                continue
            circuits = sum(FAMILIES[p][1] for p in prefixes)
            row = {"config": name, "shots": shots, "canary_circuits": circuits,
                   "qpu_seconds": round(circuits * shots * SECONDS_PER_SHOT, 1),
                   **summarize(evaluate(keep(df, prefixes)).predictions)}
            cost.append(row)
            print(row)
    fwd, fwd_runs = forward(dataset(runs, CHUNKS))
    print("forward", fwd)

    assert cost[0]["jobs"] == len(runs), "every Run must be scored once"
    lines = ["# How few Canaries are enough, and does it work forward in time? (2026-10-30)", "",
             f"Offline, no QPU time. {len(runs)} Runs ({len(runs) // 2} Genuine + Twins), "
             f"{dataset(runs, CHUNKS)['cycle'].nunique()} Calibration cycles, 3 Backends. "
             "Script: `scripts/cost_and_forward.py`. Fewer shots means the first N shots of each 1000-shot Run.",
             "", "## Cost: Canary families and shots vs detection (held out by Calibration cycle)", "",
             "QPU seconds are for the Canaries alone at 11 s per 34,000 shots. "
             "Drift features are excluded from every row.", "",
             "| Canaries | shots | circuits | QPU s | AUC | jobs correct | worst Genuine score | worst Twin score |",
             "|---|---|---|---|---|---|---|---|"]
    for r in cost:
        lines.append(f"| {r['config']} | {r['shots']} | {r['canary_circuits']} | {r['qpu_seconds']} | {r['auc']:.3f} | "
                     f"{r['correct']}/{r['jobs']} | {r['worst_genuine']:.2f} | {r['worst_forged']:.2f} |")
    lines += ["", "## Forward in time: train only on earlier cycles", "",
              f"AUC {fwd['auc']:.3f}, {fwd['correct']}/{fwd['jobs']} jobs correct, "
              f"worst Genuine {fwd['worst_genuine']:.2f}, worst Twin {fwd['worst_forged']:.2f}. "
              "The first cycle has nothing earlier to train on and is not scored.", "",
              "| job | backend | cycle | cycles trained on | score |", "|---|---|---|---|---|"]
    for r in fwd_runs:
        lines.append(f"| {r['run_id']} | {r['backend']} | {r['cycle'][:16]} | {r['trained_on']} | {r['score']:.3f} |")
    Path("docs/research/cost-and-forward.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path("web/public/cost.json").write_text(json.dumps({"cost": cost, "forward": fwd, "forward_runs": fwd_runs},
                                                        default=float), encoding="utf-8")
    print("wrote docs/research/cost-and-forward.md and web/public/cost.json", np.round(fwd["auc"], 3))


if __name__ == "__main__":
    main()
