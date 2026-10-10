"""Executing a Batch: honestly on a Backend, or by the Forger from a Calibration snapshot.

Both return the same Run shape. The Forger is exactly what a dishonest Provider would
swap in. Local stand-in Runs let us exercise everything without spending QPU time.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from qiskit.providers import BackendV2
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime.executor_sampler import Sampler

from ghostqpu.canaries import Batch
from ghostqpu.runs import FORGED, GENUINE, Run
from ghostqpu.snapshot import CalibrationSnapshot


def submit(backend: BackendV2, batch: Batch, shots: int):
    """Send `batch` to `backend` with every error-suppression trick turned off."""
    return _sampler(backend).run(batch.circuits, shots=shots)


def collect(job, backend: BackendV2, batch: Batch, submission: dict) -> Run:
    """Turn a finished job into a Genuine Run, with the calibration valid when it executed."""
    result = job.result()
    info = dict(submission)
    if _is_ibm(backend):
        started = _started_at(job)
        snapshot = CalibrationSnapshot.capture(backend, at=started)
        info.update(started_at=started.isoformat(), qpu_seconds=job.usage(), job_id=job.job_id())
    else:
        snapshot = CalibrationSnapshot.capture(backend)
        info.update(started_at=datetime.now(UTC).isoformat(), qpu_seconds=None)
    return Run(
        run_id=info["run_id"],
        origin=GENUINE,
        batch=batch,
        snapshot=snapshot,
        shots=_shot_records(result),
        info={k: v for k, v in info.items() if k != "run_id"},
    )


def forge_twin(run: Run) -> Run:
    """The Forger: simulate `run`'s exact circuits from the calibration valid when it ran."""
    return Run(
        run_id=f"{run.run_id}_forged",
        origin=FORGED,
        batch=run.batch,
        snapshot=run.snapshot,
        shots=_simulate(run.snapshot.simulator_backend(), run.batch, run.info["shots"]),
        info={**run.info, "twin_of": run.run_id, "qpu_seconds": 0.0, "forged_at": _now()},
    )


def stand_in_run(backend: BackendV2, batch: Batch, shots: int, run_id: str, **info) -> Run:
    """A Genuine-shaped Run from a local fake backend's own noise. Never real data."""
    return Run(
        run_id=run_id,
        origin=GENUINE,
        batch=batch,
        snapshot=CalibrationSnapshot.capture(backend),
        shots=_simulate(backend, batch, shots),
        info={"backend": backend.name, "shots": shots, "stand_in": True, "qpu_seconds": None,
              "submitted_at": _now(), "started_at": _now(), **info},
    )


def save_submission(root: Path, job, batch: Batch, snapshot: CalibrationSnapshot, submission: dict) -> Path:
    folder = Path(root) / submission["run_id"]
    folder.mkdir(parents=True, exist_ok=True)
    batch.save(folder)
    snapshot.save(folder / "snapshot_submit.json")
    (folder / "submission.json").write_text(json.dumps({**submission, "job_id": job.job_id()}, indent=1))
    return folder


def load_submission(folder: Path) -> tuple[Batch, dict]:
    folder = Path(folder)
    return Batch.load(folder), json.loads((folder / "submission.json").read_text())


def _simulate(backend: BackendV2, batch: Batch, shots: int) -> list[np.ndarray]:
    sim = AerSimulator(noise_model=NoiseModel.from_backend(backend))
    result = sim.run(batch.circuits, shots=shots, memory=True).result()
    return [_memory_to_bits(result.get_memory(i)) for i in range(len(batch.circuits))]


def _sampler(backend: BackendV2) -> Sampler:
    # Twirling and dynamical decoupling would hide exactly the hardware effects Canaries
    # look for, and twirling would also reorder shots.
    sampler = Sampler(mode=backend)
    sampler.options.dynamical_decoupling.enable = False
    sampler.options.twirling.enable_gates = False
    sampler.options.twirling.enable_measure = False
    return sampler


def _shot_records(result) -> list[np.ndarray]:
    # Little-endian columns: column i is clbit i. Rows stay in the order the shots were taken.
    return [pub.join_data().to_bool_array(order="little").astype(np.uint8) for pub in result]


def _memory_to_bits(memory: list[str]) -> np.ndarray:
    # Aer writes each shot as big-endian registers, last register first. Reversing the
    # whole string gives clbit order, matching _shot_records.
    rows = [[int(c) for c in reversed(shot.replace(" ", ""))] for shot in memory]
    return np.array(rows, dtype=np.uint8)


def _started_at(job) -> datetime:
    stamp = job.metrics().get("timestamps", {}).get("running")
    if not stamp:
        return datetime.now(UTC)
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def _is_ibm(backend: BackendV2) -> bool:
    from qiskit_ibm_runtime import IBMBackend

    return isinstance(backend, IBMBackend)


def _now() -> str:
    return datetime.now(UTC).isoformat()
