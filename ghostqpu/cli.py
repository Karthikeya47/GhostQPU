"""GhostQPU command line. Run `python -m ghostqpu --help`."""

from __future__ import annotations

import argparse
import getpass
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

DATA = Path("data")
RUNS = DATA / "runs"
PENDING = DATA / "pending"
COLLECTED = PENDING / "collected"
STAND_IN = DATA / "stand_in"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ghostqpu", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add-account", help="save an IBM Quantum account under a short name")
    p.add_argument("name")

    sub.add_parser("accounts", help="list saved accounts, their backends and remaining QPU time")

    p = sub.add_parser("submit", help="send a Batch with hidden Canaries to an IBM backend")
    p.add_argument("--account", required=True)
    p.add_argument("--backend", required=True)
    # 1000 matches every Run the frozen Detector was trained on (scripts/score_fresh.py warns otherwise).
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--seed", type=int, default=None)

    p = sub.add_parser("collect", help="fetch finished jobs, save Genuine Runs and forge their Twins")
    p.add_argument("--into", type=Path, default=RUNS, help="where to save the Runs (default data/runs)")

    p = sub.add_parser("evaluate", help="train and evaluate the Detector on saved Runs")
    p.add_argument("--chunks", type=int, default=8)
    p.add_argument("--stand-in", action="store_true", help="use local stand-in Runs instead of real ones")

    p = sub.add_parser("null-test", help="stand-in vs Forger on a fake backend: the Detector must fail")
    p.add_argument("--pairs", type=int, default=4)
    p.add_argument("--shots", type=int, default=2000)
    p.add_argument("--chunks", type=int, default=8)

    args = parser.parse_args(argv)
    {
        "add-account": cmd_add_account,
        "accounts": cmd_accounts,
        "submit": cmd_submit,
        "collect": cmd_collect,
        "evaluate": cmd_evaluate,
        "null-test": cmd_null_test,
    }[args.command](args)


def cmd_add_account(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService

    token = getpass.getpass("IBM Quantum API key (hidden): ").strip()
    instance = input("Instance CRN (blank to auto-select): ").strip() or None
    QiskitRuntimeService.save_account(
        channel="ibm_quantum_platform", token=token, instance=instance, name=args.name, overwrite=True
    )
    print(f"saved account '{args.name}'. Check it with: python -m ghostqpu accounts")


def cmd_accounts(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService

    saved = QiskitRuntimeService.saved_accounts()
    if not saved:
        print("no saved accounts. Add one with: python -m ghostqpu add-account <name>")
        return
    for name in saved:
        print(f"== {name}")
        try:
            service = QiskitRuntimeService(name=name)
            for b in service.backends(simulator=False):
                status = b.status()
                print(f"   {b.name:<16} {b.num_qubits:>4} qubits  pending jobs {status.pending_jobs:>5}"
                      f"  {'operational' if status.operational else 'DOWN'}")
            print(f"   usage: {json.dumps(service.usage(), default=str)}")
        except Exception as exc:  # report every account even if one is broken
            print(f"   ERROR: {exc}")


def cmd_submit(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService

    from ghostqpu.canaries import build_batch
    from ghostqpu.execution import manifest, save_submission, submit
    from ghostqpu.snapshot import CalibrationSnapshot

    backend = QiskitRuntimeService(name=args.account).backend(args.backend)
    seed = args.seed if args.seed is not None else int(datetime.now().timestamp()) % 100_000
    snapshot = CalibrationSnapshot.capture(backend)
    batch = build_batch(snapshot, seed=seed)
    job = submit(backend, batch, args.shots)
    now = datetime.now(UTC)
    submission = {
        "run_id": f"{backend.name}_{now:%Y%m%dT%H%M%S}_{seed}",
        "backend": backend.name,
        "account": args.account,
        "shots": args.shots,
        "submitted_at": now.isoformat(),
        "manifest": manifest(backend),
    }
    folder = save_submission(PENDING, job, batch, snapshot, submission)
    print(f"submitted job {job.job_id()} ({len(batch.circuits)} circuits x {args.shots} shots)")
    print(f"placements {batch.placements}, calibration cycle {snapshot.cycle}")
    print(f"saved to {folder}. Run `python -m ghostqpu collect` when it finishes.")


def cmd_collect(args) -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService

    from ghostqpu.execution import collect, forge_twin, load_submission

    folders = [f for f in sorted(PENDING.glob("*")) if (f / "submission.json").exists()] if PENDING.exists() else []
    if not folders:
        print("nothing pending")
        return
    for folder in folders:
        batch, submission = load_submission(folder)
        service = QiskitRuntimeService(name=submission["account"])
        job = service.job(submission["job_id"])
        status = str(job.status())
        if status != "DONE":
            print(f"{submission['run_id']}: {status}")
            continue
        backend = service.backend(submission["backend"])
        run = collect(job, backend, batch, submission)
        run.save(args.into)
        forge_twin(run).save(args.into)
        COLLECTED.mkdir(parents=True, exist_ok=True)
        shutil.move(str(folder), str(COLLECTED / folder.name))
        print(f"{run.run_id}: collected, {run.info['qpu_seconds']} QPU seconds, Twin forged")


def cmd_evaluate(args) -> None:
    from ghostqpu.detector import dataset, evaluate
    from ghostqpu.runs import load_runs

    runs = load_runs(STAND_IN if args.stand_in else RUNS)
    if not runs:
        print("no runs yet")
        return
    _print_report(evaluate(dataset(runs, args.chunks)))


def cmd_null_test(args) -> None:
    from qiskit_ibm_runtime.fake_provider import FakeFez

    from ghostqpu.canaries import build_batch
    from ghostqpu.detector import dataset, evaluate
    from ghostqpu.execution import forge_twin, stand_in_run
    from ghostqpu.runs import load_runs
    from ghostqpu.snapshot import CalibrationSnapshot

    backend = FakeFez()
    snapshot = CalibrationSnapshot.capture(backend)
    existing = {r.run_id for r in load_runs(STAND_IN)}
    for k in range(args.pairs):
        run_id = f"stand_in_fez_{k}"
        if run_id in existing:
            continue
        run = stand_in_run(backend, build_batch(snapshot, seed=k), args.shots, run_id)
        run.save(STAND_IN)
        forge_twin(run).save(STAND_IN)
        print(f"made {run_id} and its Twin")
    report = evaluate(dataset(load_runs(STAND_IN), args.chunks))
    _print_report(report)
    verdict = "PASS" if 0.3 < report.auc < 0.7 else "FAIL: the pipeline leaks something besides physics"
    print(f"\nnull test {verdict}")


def _print_report(report) -> None:
    print(f"split: {report.split}, pairs: {report.n_pairs}")
    print(f"chunk AUC (forged): {report.auc:.3f}")
    print(f"run-level accuracy: {report.run_accuracy:.3f}")
    print("feature weights (standardized):")
    for name, w in report.weights.items():
        print(f"   {name:<26} {w:+.3f}")
