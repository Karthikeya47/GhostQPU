"""Runs: the shot-by-shot outcome of one Batch, Genuine or Forged, stored one folder per Run."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ghostqpu.canaries import Batch
from ghostqpu.snapshot import CalibrationSnapshot

GENUINE = "genuine"
FORGED = "forged"


@dataclass
class Run:
    run_id: str
    origin: str
    batch: Batch
    snapshot: CalibrationSnapshot  # calibration valid when the Run executed
    shots: list[np.ndarray]  # per circuit: (n_shots, n_clbits) uint8, rows in shot order
    info: dict  # job_id, account, timestamps, qpu_seconds, twin_of, ...

    def bits(self, index: int) -> np.ndarray:
        return self.shots[index]

    def save(self, root: Path) -> Path:
        folder = Path(root) / self.run_id
        folder.mkdir(parents=True, exist_ok=True)
        self.batch.save(folder)
        self.snapshot.save(folder / "snapshot.json")
        np.savez_compressed(folder / "shots.npz", *self.shots)
        record = {"run_id": self.run_id, "origin": self.origin, **self.info}
        (folder / "run.json").write_text(json.dumps(record, indent=1))
        return folder

    @classmethod
    def load(cls, folder: Path) -> Run:
        folder = Path(folder)
        record = json.loads((folder / "run.json").read_text())
        with np.load(folder / "shots.npz") as npz:
            shots = [npz[f"arr_{i}"] for i in range(len(npz.files))]
        return cls(
            run_id=record.pop("run_id"),
            origin=record.pop("origin"),
            batch=Batch.load(folder),
            snapshot=CalibrationSnapshot.load(folder / "snapshot.json"),
            shots=shots,
            info=record,
        )


def load_runs(root: Path) -> list[Run]:
    root = Path(root)
    if not root.exists():
        return []
    return [Run.load(f) for f in sorted(root.iterdir()) if (f / "run.json").exists()]
