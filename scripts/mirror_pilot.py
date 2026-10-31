"""Mirror pilot: Canaries disguised as customer circuits. Build, submit, collect, analyze.

Each circuit is a random 4-qubit circuit U followed by U inverse, so the ideal outcome is all zeros, but it looks
like the random Workload circuits a customer sends (unlike the X-chain Canaries, which a provider could spot).
Compiled exactly like Workloads (optimization level 1); a barrier keeps U and U inverse from cancelling.

  check     local only: build the pilot on the newest saved snapshot and show its shape
  submit    SPENDS QPU TIME: send the pilot to an IBM backend (same Sampler settings as Batches)
  collect   fetch finished jobs into data/mirror/runs and forge each Twin
  analyze   P(all zeros) on hardware vs the Twin, per circuit, with a two-proportion z-test

Run from the repo root:  PYTHONPATH=. python scripts/mirror_pilot.py check
"""

from __future__ import annotations

import argparse
import shutil
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from qiskit import transpile
from qiskit.circuit.random import random_circuit

from ghostqpu.canaries import WORKLOAD_OPTIMIZATION_LEVEL, Batch, CircuitSpec
from ghostqpu.runs import GENUINE, load_runs

ROOT = Path("data/mirror")
PENDING = ROOT / "pending"
RUNS = ROOT / "runs"
DEPTHS = (4, 8)
PER_DEPTH = 8
WIDTH = 4


def build_mirror(snapshot, seed: int) -> Batch:
    backend = snapshot.simulator_backend()
    circuits, specs = [], []
    for depth in DEPTHS:
        for k in range(PER_DEPTH):
            u = random_circuit(WIDTH, depth, max_operands=2, seed=seed * 100 + depth * 10 + k)
            qc = u.copy()
            qc.barrier()
            qc.compose(u.inverse(), inplace=True)
            qc.measure_all()
            circuits.append(transpile(qc, backend, optimization_level=WORKLOAD_OPTIMIZATION_LEVEL,
                                      seed_transpiler=seed))
            specs.append(CircuitSpec("mirror", f"mirror_d{depth}_{k}", {"depth": depth}))
    order = np.random.default_rng(seed).permutation(len(circuits))
    return Batch(backend_name=snapshot.backend_name, seed=seed, placements=[],
                 circuits=[circuits[i] for i in order], specs=[specs[i] for i in order])


def all_zero(bits: np.ndarray) -> float:
    return float((bits.sum(axis=1) == 0).mean())


def cmd_check(args) -> None:
    run = sorted(load_runs("data/fresh"), key=lambda r: r.snapshot.cycle)[-1]
    batch = build_mirror(run.snapshot, args.seed)
    ops = [dict(qc.count_ops()) for qc in batch.circuits]
    print(f"{run.snapshot.backend_name}: {len(batch.circuits)} circuits, CZ per circuit "
          f"{min(o.get('cz', 0) for o in ops)} to {max(o.get('cz', 0) for o in ops)}")
    assert all(o.get("cz", 0) > 0 for o in ops), "every mirror circuit should contain two-qubit gates"


def cmd_submit(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService

    from ghostqpu.execution import manifest, save_submission, submit
    from ghostqpu.snapshot import CalibrationSnapshot

    backend = QiskitRuntimeService(name=args.account).backend(args.backend)
    snapshot = CalibrationSnapshot.capture(backend)
    batch = build_mirror(snapshot, args.seed)
    job = submit(backend, batch, args.shots)
    now = datetime.now(UTC)
    submission = {"run_id": f"mirror_{backend.name}_{now:%Y%m%dT%H%M%S}_{args.seed}", "backend": backend.name,
                  "account": args.account, "shots": args.shots, "submitted_at": now.isoformat(),
                  "manifest": manifest(backend)}
    folder = save_submission(PENDING, job, batch, snapshot, submission)
    print(f"submitted mirror job {job.job_id()} ({len(batch.circuits)} circuits x {args.shots} shots), "
          f"saved to {folder}")


def cmd_collect(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService

    from ghostqpu.execution import collect, forge_twin, load_submission

    folders = [f for f in sorted(PENDING.glob("*")) if (f / "submission.json").exists()] if PENDING.exists() else []
    if not folders:
        print("no pending mirror jobs")
        return
    for folder in folders:
        batch, submission = load_submission(folder)
        service = QiskitRuntimeService(name=submission["account"])
        job = service.job(submission["job_id"])
        if str(job.status()) != "DONE":
            print(f"{submission['run_id']}: {job.status()}")
            continue
        run = collect(job, service.backend(submission["backend"]), batch, submission)
        run.save(RUNS)
        forge_twin(run).save(RUNS)
        (PENDING / "collected").mkdir(parents=True, exist_ok=True)
        shutil.move(str(folder), str(PENDING / "collected" / folder.name))
        print(f"{run.run_id}: collected, {run.info['qpu_seconds']} QPU seconds, Twin forged")


def cmd_analyze(args) -> None:
    runs = {r.run_id: r for r in load_runs(RUNS)}
    for rid, run in sorted(runs.items()):
        if run.origin != GENUINE or f"{rid}_forged" not in runs:
            continue
        twin = runs[f"{rid}_forged"]
        n = run.shots[0].shape[0]
        hw = np.array([all_zero(b) for b in run.shots])
        fz = np.array([all_zero(b) for b in twin.shots])
        pooled = (hw + fz) / 2
        z = (fz - hw) / np.sqrt(np.maximum(pooled * (1 - pooled) * 2 / n, 1e-12))
        print(f"== {rid}  cycle {run.snapshot.cycle}  {run.info.get('qpu_seconds')} QPU s")
        print(f"   P(all zeros) mean: hardware {hw.mean():.3f}  Forger {fz.mean():.3f}  "
              f"Forger cleaner on {int((fz > hw).sum())}/{len(hw)} circuits, z > 3 on {int((z > 3).sum())}")
        for depth in DEPTHS:
            idx = [i for i, s in enumerate(run.batch.specs) if s.params["depth"] == depth]
            print(f"   depth {depth}: hardware {hw[idx].mean():.3f}  Forger {fz[idx].mean():.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check")
    p.add_argument("--seed", type=int, default=7)
    p = sub.add_parser("submit")
    p.add_argument("--account", required=True)
    p.add_argument("--backend", required=True)
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--seed", type=int, default=7)
    sub.add_parser("collect")
    sub.add_parser("analyze")
    args = parser.parse_args()
    {"check": cmd_check, "submit": cmd_submit, "collect": cmd_collect, "analyze": cmd_analyze}[args.command](args)


if __name__ == "__main__":
    main()
