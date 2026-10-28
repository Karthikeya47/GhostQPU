"""Does the stronger Forger match real hardware on Workload circuits it was never fitted on?

Uses only the saved Runs in data/runs. No QPU time, no detector training. For each Genuine
Run, the Workload circuits (GHZ and random) are compared across:

  real      the Genuine shots
  stock     the stock Forger's saved Twin (calibration only)
  v2        forge_twin_v2 with a profile fitted on the OTHER Genuine Run
  v2_xfer   exploratory: v2 plus the median fitted amplitude error on qubits it never probed

Run from the repo root:  PYTHONPATH=. python scripts/workload_generalization.py
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from qiskit_aer import AerSimulator

from ghostqpu.canaries import Batch
from ghostqpu.execution import _memory_to_bits, forge_twin
from ghostqpu.forger import ForgerProfile, fit_profile, forge_twin_v2
from ghostqpu.runs import FORGED, GENUINE, Run, load_runs

RUNS = Path("data/runs")
REF_SHOTS = 100_000  # near-exact forger distributions, so only the real data's shot noise is left
RESAMPLES = 4000
VARIANTS = ("stock", "v2", "v2_xfer")


def workload_run(run: Run, shots: int | None = None) -> Run:
    """`run` restricted to its Workload circuits, optionally re-forgeable at another shot count."""
    keep = [i for i, s in enumerate(run.batch.specs) if s.role == "workload"]
    batch = Batch(
        backend_name=run.batch.backend_name,
        seed=run.batch.seed,
        placements=run.batch.placements,
        circuits=[run.batch.circuits[i] for i in keep],
        specs=[run.batch.specs[i] for i in keep],
    )
    info = {**run.info, "shots": shots or run.info["shots"]}
    return replace(run, batch=batch, shots=[run.shots[i] for i in keep], info=info)


def distribution(bits: np.ndarray) -> np.ndarray:
    """Outcome probabilities, clbit 0 = least significant bit."""
    index = bits.astype(int) @ (1 << np.arange(bits.shape[1]))
    return np.bincount(index, minlength=2**bits.shape[1]) / len(bits)


def tvd(p: np.ndarray, q: np.ndarray) -> float:
    return 0.5 * float(np.abs(p - q).sum())


def permutation_null(a: np.ndarray, b: np.ndarray, rng) -> np.ndarray:
    """TVD between two samples drawn from the same pooled distribution: the shot-noise floor."""
    pooled = np.concatenate([a, b])
    size = 2 ** a.shape[1]
    weights = 1 << np.arange(a.shape[1])
    index = pooled.astype(int) @ weights
    out = np.empty(RESAMPLES)
    for r in range(RESAMPLES):
        shuffled = rng.permutation(index)
        out[r] = tvd(
            np.bincount(shuffled[: len(a)], minlength=size) / len(a),
            np.bincount(shuffled[len(a):], minlength=size) / len(b),
        )
    return out


def sampling_null(reference: np.ndarray, n: int, rng) -> np.ndarray:
    """TVD of an n-shot sample drawn from `reference` back to `reference`."""
    return np.array([tvd(rng.multinomial(n, reference) / n, reference) for _ in range(RESAMPLES)])


def ideal_distribution(circuit, n_clbits: int) -> np.ndarray:
    result = AerSimulator().run(circuit, shots=200_000, memory=True).result()
    return distribution(_memory_to_bits(result.get_memory(0)))


@dataclass
class Row:
    run: str
    circuit: str
    n_cz: int
    covered: str
    tvd_ideal: dict[str, float]
    tvd_pair: dict[str, float]  # real vs 1000-shot variant
    floor_pair: float
    p_pair: dict[str, float]
    tvd_ref: dict[str, float]  # real vs near-exact variant
    floor_ref: dict[str, float]
    p_ref: dict[str, float]
    delta: dict[str, tuple[float, float, float]]  # stock minus variant: mean, 2.5%, 97.5%


def extended_profile(profile: ForgerProfile, circuits) -> ForgerProfile:
    """Exploratory: give qubits the probe never measured the median fitted amplitude error."""
    median = float(np.median(list(profile.amp_error.values())))
    amp = dict(profile.amp_error)
    for qc in circuits:
        for inst in qc.data:
            for qubit in inst.qubits:
                amp.setdefault(qc.find_bit(qubit).index, median)
    return replace(profile, amp_error=amp)


def analyse(victim: Run, probe: Run, stock_twin: Run, rng) -> list[Row]:
    profile = fit_profile(probe)
    work = workload_run(victim)
    circuits = work.batch.circuits
    profile_x = extended_profile(profile, circuits)
    ref_run = workload_run(victim, REF_SHOTS)

    data = {"real": work.shots}
    data["stock"] = workload_run(stock_twin).shots
    data["v2"] = forge_twin_v2(work, profile).shots
    data["v2_xfer"] = forge_twin_v2(work, profile_x).shots
    ref = {
        "stock": forge_twin(ref_run).shots,
        "v2": forge_twin_v2(ref_run, profile).shots,
        "v2_xfer": forge_twin_v2(ref_run, profile_x).shots,
    }

    rows = []
    for k, (qc, spec) in enumerate(zip(circuits, work.batch.specs, strict=True)):
        real = data["real"][k]
        p_real = distribution(real)
        n = len(real)
        used = {qc.find_bit(q).index for inst in qc.data for q in inst.qubits}
        covered = sorted(used & (set(profile.amp_error) | set(profile.readout)))
        ideal = ideal_distribution(qc, real.shape[1])
        p_var = {v: distribution(data[v][k]) for v in VARIANTS}
        p_ref = {v: distribution(ref[v][k]) for v in VARIANTS}

        floor_ref = {v: sampling_null(p_ref[v], n, rng) for v in VARIANTS}
        nulls = {v: permutation_null(real, data[v][k], rng) for v in VARIANTS}
        boot = rng.multinomial(n, p_real, size=RESAMPLES) / n
        boot_tvd = {v: 0.5 * np.abs(boot - p_ref[v]).sum(axis=1) for v in VARIANTS}

        def lo_hi(x):
            return float(x.mean()), float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))

        rows.append(Row(
            run=victim.run_id[-5:],
            circuit=spec.family,
            n_cz=sum(1 for inst in qc.data if inst.operation.name == "cz"),
            covered=",".join(map(str, covered)) or "none",
            tvd_ideal={"real": tvd(p_real, ideal), **{v: tvd(p_var[v], ideal) for v in VARIANTS}},
            tvd_pair={v: tvd(p_real, p_var[v]) for v in VARIANTS},
            floor_pair=float(np.mean(nulls["stock"])),
            p_pair={v: float((nulls[v] >= tvd(p_real, p_var[v])).mean()) for v in VARIANTS},
            tvd_ref={v: tvd(p_real, p_ref[v]) for v in VARIANTS},
            floor_ref={v: float(floor_ref[v].mean()) for v in VARIANTS},
            p_ref={v: float((floor_ref[v] >= tvd(p_real, p_ref[v])).mean()) for v in VARIANTS},
            delta={v: lo_hi(boot_tvd["stock"] - boot_tvd[v]) for v in ("v2", "v2_xfer")},
        ))
    return rows


def verdict(row: Row, variant: str) -> str:
    if row.n_cz == 0:
        return "no CZ gates: not a two-qubit test"
    mean, lo, hi = row.delta[variant]
    if lo > 0:
        return "closer than stock"
    if hi < 0:
        return "farther than stock"
    return "inconclusive"


def report(rows: list[Row]) -> None:
    print("## Distance from real hardware (total variation distance, lower is closer)\n")
    print("TVD to the near-exact forger distribution. `floor` is the TVD expected from shot noise alone")
    print("(1000 real shots), `p` is P(shot noise alone >= observed).\n")
    for group in ("ghz5", "random4"):
        print(f"### {group}\n")
        print("| run | circuit | CZ | qubits with fitted effects | ideal vs real | stock | floor | p | v2 | floor | p |"
              " v2_xfer | floor | p | stock minus v2 [95% CI] | stock minus v2_xfer [95% CI] | verdict v2 |")
        print("|" + "---|" * 17)
        for r in rows:
            if not r.circuit.startswith(group):
                continue
            d2, dx = r.delta["v2"], r.delta["v2_xfer"]
            print(
                f"| {r.run} | {r.circuit} | {r.n_cz} | {r.covered} | {r.tvd_ideal['real']:.3f} "
                f"| {r.tvd_ref['stock']:.3f} | {r.floor_ref['stock']:.3f} | {r.p_ref['stock']:.3f} "
                f"| {r.tvd_ref['v2']:.3f} | {r.floor_ref['v2']:.3f} | {r.p_ref['v2']:.3f} "
                f"| {r.tvd_ref['v2_xfer']:.3f} | {r.floor_ref['v2_xfer']:.3f} | {r.p_ref['v2_xfer']:.3f} "
                f"| {d2[0]:+.3f} [{d2[1]:+.3f}, {d2[2]:+.3f}] | {dx[0]:+.3f} [{dx[1]:+.3f}, {dx[2]:+.3f}] "
                f"| {verdict(r, 'v2')} |"
            )
        print()

    print("## Same comparison using the saved 1000-shot Twins only (permutation test)\n")
    print("| run | circuit | stock TVD | p | v2 TVD | p | v2_xfer TVD | p | shot-noise floor |")
    print("|" + "---|" * 9)
    for r in rows:
        print(
            f"| {r.run} | {r.circuit} | {r.tvd_pair['stock']:.3f} | {r.p_pair['stock']:.3f} "
            f"| {r.tvd_pair['v2']:.3f} | {r.p_pair['v2']:.3f} "
            f"| {r.tvd_pair['v2_xfer']:.3f} | {r.p_pair['v2_xfer']:.3f} | {r.floor_pair:.3f} |"
        )
    print("\n## TVD to the ideal (noiseless) output, to compare overall error level\n")
    print("| run | circuit | real | stock | v2 | v2_xfer |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        t = r.tvd_ideal
        print(f"| {r.run} | {r.circuit} | {t['real']:.3f} | {t['stock']:.3f} | {t['v2']:.3f} | {t['v2_xfer']:.3f} |")


def main() -> None:
    runs = load_runs(RUNS)
    genuine = {r.run_id: r for r in runs if r.origin == GENUINE}
    stock = {r.info["twin_of"]: r for r in runs if r.origin == FORGED}
    ids = sorted(genuine)
    rng = np.random.default_rng(0)
    rows: list[Row] = []
    for victim_id, probe_id in ((ids[0], ids[1]), (ids[1], ids[0])):
        victim, twin = genuine[victim_id], stock[victim_id]
        assert [qc.name for qc in victim.batch.circuits] == [qc.name for qc in twin.batch.circuits]
        assert all(a == b for a, b in zip(victim.batch.circuits, twin.batch.circuits, strict=True))
        rows += analyse(victim, genuine[probe_id], twin, rng)
    report(rows)


if __name__ == "__main__":
    main()
