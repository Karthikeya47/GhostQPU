"""GhostQPU HTTP API: the frozen Detector and the committed Runs over HTTP.

Run:   .venv/Scripts/python -m uvicorn ghostqpu.api:app --port 8000
Docs:  http://localhost:8000/docs (interactive, generated from these endpoints)
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException

from ghostqpu.detector import dataset, features_of, train
from ghostqpu.runs import Run, load_runs

DATA = Path("data")
TRAINING = DATA / "runs"
FOLDERS = ("runs", "fresh", "short")
CHUNKS = 8
INCONCLUSIVE = (0.35, 0.65)  # same bands as the site and the CLI

app = FastAPI(title="GhostQPU API", version="1.0",
              description="Did a quantum job run on IBM hardware, or was it forged from public calibration data?")


@lru_cache(maxsize=1)
def frozen():
    """The frozen Detector: trained once on the four 10 October Runs, never retrained."""
    model = train(dataset(load_runs(TRAINING), CHUNKS))
    coef = np.concatenate([model[0].mean_, model[0].scale_, model[-1].coef_[0], model[-1].intercept_])
    return model, hashlib.sha256(coef.round(12).tobytes()).hexdigest()[:16]


def _folder(run_id: str) -> Path:
    if "/" in run_id or "\\" in run_id or ".." in run_id:  # run ids are plain folder names; reject paths
        raise HTTPException(400, "invalid run id")
    for name in FOLDERS:
        path = DATA / name / run_id
        if (path / "run.json").exists():
            return path
    raise HTTPException(404, f"no run {run_id}")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/runs")
def runs() -> list[dict]:
    """Every committed Run: id, Backend, Calibration cycle, shots, and which folder it lives in."""
    out = []
    for name in FOLDERS:
        for folder in sorted((DATA / name).glob("*/run.json")):
            run = Run.load(folder.parent)
            out.append({"run_id": run.run_id, "backend": run.batch.backend_name, "cycle": run.snapshot.cycle,
                        "shots": run.info.get("shots"), "set": name, "origin": run.origin})
    return out


@app.get("/runs/{run_id}/verdict")
def verdict(run_id: str) -> dict:
    """The frozen Detector's Verdict for one Run, with the forged score for each time chunk."""
    run = Run.load(_folder(run_id))
    model, fingerprint = frozen()
    df = dataset([run], CHUNKS)
    chunks = model.predict_proba(df[features_of(df)])[:, 1]
    score = float(chunks.mean())
    label = "Forged" if score >= INCONCLUSIVE[1] else "Genuine" if score <= INCONCLUSIVE[0] else "Inconclusive"
    return {"run_id": run.run_id, "verdict": label, "forged_score": round(score, 4),
            "chunk_scores": [round(float(c), 4) for c in chunks], "backend": run.batch.backend_name,
            "cycle": run.snapshot.cycle, "in_training_set": (TRAINING / run.run_id).exists(),
            "detector_fingerprint": fingerprint}


@app.get("/detector")
def detector() -> dict:
    """What the frozen Detector looks at: its 12 features and their standardized weights."""
    model, fingerprint = frozen()
    feats = features_of(dataset(load_runs(TRAINING), CHUNKS))
    return {"fingerprint": fingerprint, "chunks_per_job": CHUNKS, "inconclusive_band": list(INCONCLUSIVE),
            "weights": dict(zip(feats, (round(float(w), 4) for w in model[-1].coef_[0]), strict=True))}
