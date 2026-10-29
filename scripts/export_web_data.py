"""Export every Run, Detector result and Calibration snapshot in the repo to web/public/data.json.

No QPU time, no retraining beyond what app.py and score_fresh.py already do.
Run from the repo root:  PYTHONPATH=. python scripts/export_web_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ghostqpu.detector import dataset, evaluate, features_of, train
from ghostqpu.pilot import analyze, curves
from ghostqpu.runs import load_runs
from ghostqpu.signature import _p1_targets, canary_curves

CHUNKS = 8
OUT = Path("web/public/data.json")
RASTER_SHOTS = 240


def chip(snapshot) -> dict:
    """Qubit grid positions, per-qubit calibration and CZ edges of a Heron snapshot."""
    props = snapshot.properties
    n = snapshot.configuration["n_qubits"]
    qubits = []
    for q in range(n):
        v = {p["name"]: p["value"] for p in props["qubits"][q]}
        qubits.append({k: v.get(k) for k in ("T1", "T2", "readout_error", "prob_meas1_prep0", "prob_meas0_prep1")})
    edges = {}
    for g in props["gates"]:
        if g["gate"] == "cz":
            a, b = sorted(g["qubits"])
            err = next((p["value"] for p in g["parameters"] if p["name"] == "gate_error"), None)
            edges[(a, b)] = err
    # Heron r2: rows of 16 qubits joined by 4 bridge qubits, repeating every 20 indices.
    pos = {}
    for q in range(n):
        block, k = divmod(q, 20)
        if k < 16:
            pos[q] = [k, block * 2]
    for q in range(n):
        if q not in pos:
            nb = [pos[b if a == q else a][0] for a, b in edges if q in (a, b) and (b if a == q else a) in pos]
            pos[q] = [float(np.mean(nb)) if nb else 0.0, (q // 20) * 2 + 1]
    return {
        "cycle": snapshot.cycle,
        "qubits": [{**qubits[q], "x": pos[q][0], "y": pos[q][1]} for q in range(n)],
        "edges": [[a, b, e] for (a, b), e in sorted(edges.items())],
    }


def run_record(run) -> dict:
    curves = canary_curves(run)
    per_placement = []
    for k, pl in enumerate(run.batch.placements):
        rows = sorted(
            (s.params["n"], s.params["sandwich"], float(_p1_targets(run.shots[i])[k]))
            for i, s in run.batch.canaries("coherent")
        )
        per_placement.append({"placement": list(pl), "coherent": [list(r) for r in rows]})
    circuits = []
    for qc, s in zip(run.batch.circuits, run.batch.specs, strict=True):
        circuits.append({"role": s.role, "family": s.family, "params": s.params,
                         "depth": qc.depth(), "ops": {k: int(v) for k, v in qc.count_ops().items()}})
    coh = run.batch.canaries("coherent")
    longest = max(coh, key=lambda t: (t[1].params["n"], not t[1].params["sandwich"]))[0]
    info = {k: v for k, v in run.info.items() if k not in ("manifest", "usage")}
    return {
        "id": run.run_id,
        "origin": run.origin,
        "cycle": run.snapshot.cycle,
        "placements": [list(p) for p in run.batch.placements],
        "info": info,
        "circuits": circuits,
        "curves": {k: v.to_dict(orient="records") for k, v in curves.items()},
        "per_placement": per_placement,
        "raster": run.shots[longest][:RASTER_SHOTS].tolist(),
        "raster_circuit": run.batch.specs[longest].params,
    }


def main() -> None:
    dev = load_runs(Path("data/runs"))
    fresh = load_runs(Path("data/fresh"))
    dev_df = dataset(dev, CHUNKS)
    report = evaluate(dev_df)

    model = train(dev_df)  # the frozen Detector, as in scripts/score_fresh.py
    fresh_df = dataset(fresh, CHUNKS)
    fresh_scores = fresh_df[["run_id", "origin", "cycle", "chunk"]].assign(
        forged_score=model.predict_proba(fresh_df[features_of(fresh_df)])[:, 1])

    # The page's hero chip is drawn as ibm_marrakesh, so it shows the newest Genuine marrakesh Run.
    hero = [r for r in dev + fresh if r.origin == "genuine" and r.batch.backend_name == "ibm_marrakesh"][-1]
    all_df = dataset(dev + fresh, CHUNKS)
    feats = features_of(all_df)
    out = {
        "runs": [run_record(r) for r in dev + fresh],
        "fresh_ids": [r.run_id for r in fresh],
        "features": feats,
        "signatures": all_df[["run_id", "origin", "chunk", *feats]].to_dict(orient="records"),
        "report": {
            "split": report.split, "auc": report.auc, "run_accuracy": report.run_accuracy,
            "n_pairs": report.n_pairs,
            "predictions": report.predictions[["run_id", "origin", "chunk", "forged_score"]].to_dict(orient="records"),
            "weights": [[k, float(v)] for k, v in report.weights.items()],
        },
        "fresh_scores": fresh_scores.to_dict(orient="records"),
        "hero_id": hero.run_id,
        "chips": {"dev": chip(dev[0].snapshot), "fresh": chip(hero.snapshot)},
    }
    # CNOT pilot Runs: hardware vs the stock Forger's near-exact curve, and the fitted coherent turn per repeat.
    out["pilot"] = [
        {"id": r.run_id, "cycle": r.snapshot.cycle, "qpu_seconds": r.info.get("qpu_seconds"),
         "curves": curves(r).to_dict(orient="records"), "fits": analyze(r).to_dict(orient="records")}
        for r in load_runs(Path("data/pilot/runs"))
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":"), default=float))
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB), AUC {report.auc:.2f}")
    for rid, g in fresh_scores.groupby("run_id"):
        print(f"  frozen score {rid}: {g['forged_score'].mean():.3f}")


if __name__ == "__main__":
    main()
