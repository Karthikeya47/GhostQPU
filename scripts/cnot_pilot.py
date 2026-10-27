"""CNOT pilot on hardware: check locally, submit, collect, analyze. See ghostqpu/pilot.py.

  check     local only: build the pilot on the last saved snapshot, verify it, estimate QPU cost
  submit    SPENDS QPU TIME: send the pilot to an IBM backend (same Sampler settings as Batches)
  collect   fetch finished pilot jobs into data/pilot/runs
  analyze   fit theta per placement against the stock Forger under the execution-time calibration

Run from the repo root:  PYTHONPATH=. python scripts/cnot_pilot.py check
"""

from __future__ import annotations

import argparse
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from ghostqpu.pilot import analyze, build_pilot, curves
from ghostqpu.runs import GENUINE, load_runs

ROOT = Path("data/pilot")
PENDING = ROOT / "pending"
RUNS = ROOT / "runs"
# Billed 11 s for the 34 x 1000-shot Batch, whose rep delay plus circuit time is 8.70 s.
BILLED_PER_MODELED = 11 / 8.70
REP_DELAY_S = 250e-6
DETECTION_Z = 3.2  # about 0.05 two-sided over 4 placements, Bonferroni


def cmd_check(args) -> None:
    snapshot = next(r for r in load_runs("data/runs") if r.origin == GENUINE).snapshot
    batch = build_pilot(snapshot, seed=args.seed)
    target = snapshot.simulator_backend().target
    durations = [qc.estimate_duration(target, unit="s") for qc in batch.circuits]
    modeled = args.shots * (len(batch.circuits) * REP_DELAY_S + sum(durations))
    print(f"snapshot {snapshot.backend_name}, cycle {snapshot.cycle}, placements {batch.placements}")
    print(f"{len(batch.circuits)} circuits x {args.shots} shots, longest {max(durations) * 1e6:.1f} us")
    print(f"QPU estimate: {modeled:.1f} s modeled, about {modeled * BILLED_PER_MODELED:.1f} s billed "
          f"if overhead scales like the last Batch (unverified)")


def cmd_submit(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService

    from ghostqpu.execution import manifest, save_submission, submit
    from ghostqpu.snapshot import CalibrationSnapshot

    backend = QiskitRuntimeService(name=args.account).backend(args.backend)
    snapshot = CalibrationSnapshot.capture(backend)
    batch = build_pilot(snapshot, seed=args.seed)
    job = submit(backend, batch, args.shots)
    now = datetime.now(UTC)
    submission = {
        "run_id": f"pilot_{backend.name}_{now:%Y%m%dT%H%M%S}_{args.seed}",
        "backend": backend.name,
        "account": args.account,
        "shots": args.shots,
        "submitted_at": now.isoformat(),
        "manifest": manifest(backend),
    }
    folder = save_submission(PENDING, job, batch, snapshot, submission)
    print(f"submitted pilot job {job.job_id()} ({len(batch.circuits)} circuits x {args.shots} shots)")
    print(f"placements {batch.placements}, calibration cycle {snapshot.cycle}, saved to {folder}")


def cmd_collect(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService

    from ghostqpu.execution import collect, load_submission

    folders = [f for f in sorted(PENDING.glob("*")) if (f / "submission.json").exists()] if PENDING.exists() else []
    if not folders:
        print("no pending pilot jobs")
        return
    for folder in folders:
        batch, submission = load_submission(folder)
        service = QiskitRuntimeService(name=submission["account"])
        job = service.job(submission["job_id"])
        status = str(job.status())
        if status != "DONE":
            print(f"{submission['run_id']}: {status}")
            continue
        run = collect(job, service.backend(submission["backend"]), batch, submission)
        run.save(RUNS)
        (PENDING / "collected").mkdir(parents=True, exist_ok=True)
        shutil.move(str(folder), str(PENDING / "collected" / folder.name))
        print(f"{run.run_id}: collected, {run.info['qpu_seconds']} QPU seconds, timestamps {run.info['timestamps']}")


def cmd_analyze(args) -> None:
    pd.set_option("display.width", 160)
    for run in load_runs(RUNS):
        print(f"== {run.run_id}  cycle {run.snapshot.cycle}  {run.info.get('qpu_seconds')} QPU s")
        if args.curves:
            print(curves(run).round(4).to_string(index=False))
        report = analyze(run)
        report["detected"] = report["z"] > DETECTION_Z
        print(report.round(4).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check")
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--seed", type=int, default=1)
    p = sub.add_parser("submit")
    p.add_argument("--account", required=True)
    p.add_argument("--backend", required=True)
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--seed", type=int, default=1)
    sub.add_parser("collect")
    p = sub.add_parser("analyze")
    p.add_argument("--curves", action="store_true", help="also print every hardware and stock point")
    args = parser.parse_args()
    {"check": cmd_check, "submit": cmd_submit, "collect": cmd_collect, "analyze": cmd_analyze}[args.command](args)


if __name__ == "__main__":
    main()
