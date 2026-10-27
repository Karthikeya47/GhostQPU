"""CNOT pilot: does the real CZ carry a coherent error that the stock Forger lacks?

Not a Canary family yet. Pilot Runs live in their own folder, so the frozen Detector and its
12 features never see them. Each circuit repeats CNOT (H, CZ, H on the target) N times with
the neighbor as control, on every placement in parallel. N is even, so the ideal target is 0.

  cnot, control 1   a conditional phase e on the CZ turns the target by N*e: P(1) grows as sin^2(N*e/2)
  cnot, control 0   the CZ pulse fires but acts trivially: only a local phase on the target shows
  idle, control 0/1 the same single-qubit gates with the CZ replaced by an idle of equal length

For every (placement, family, control) the hardware curve is compared with the stock Forger's
curve under the execution-time calibration, and fitted as
    hardware - stock = a + k N + (1 - 2 stock) sin^2(N theta / 2)
theta is the coherent turn per repeat the Forger misses. a absorbs a readout mismatch with the
published calibration and k a mismatch in incoherent error per repeat.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

from ghostqpu.canaries import CANARY_OPTIMIZATION_LEVEL, Batch, CircuitSpec, choose_placements
from ghostqpu.runs import Run
from ghostqpu.snapshot import CalibrationSnapshot

PILOT_REPEATS = (0, 2, 4, 8, 16, 32, 64, 128)
FAMILIES = ("cnot", "idle")
REF_SHOTS = 200_000  # the stock curve is near exact, so only the hardware's shot noise is left
THETA_GRID = np.linspace(0.0, 0.1, 5001)  # rad per repeat
DETECTION_Z = 3.2  # pre-registered: about 0.05 two-sided over 4 placements, Bonferroni


def build_pilot(snapshot: CalibrationSnapshot, seed: int, n_placements: int = 4) -> Batch:
    """Pilot circuits on the same placements build_batch would choose, shuffled by `seed`."""
    backend = snapshot.simulator_backend()
    target = backend.target
    placements = choose_placements(target, n_placements)
    layout = [q for pair in placements for q in pair]
    cz_dt = max(round(target["cz"][pair].duration / target.dt) for pair in placements)

    n = len(placements)
    targets, controls = list(range(0, 2 * n, 2)), list(range(1, 2 * n, 2))
    logical, specs = [], []
    for family in FAMILIES:
        for control in (0, 1):
            for repeats in PILOT_REPEATS:
                qc = QuantumCircuit(2 * n, 2 * n, name=f"pilot_{family}_c{control}_{repeats}")
                if control:
                    qc.x(controls)
                qc.barrier()
                for _ in range(repeats):
                    for c, t in zip(controls, targets, strict=True):
                        if family == "cnot":
                            qc.cx(c, t)
                        else:
                            qc.h(t)
                            qc.delay(cz_dt, [c, t], unit="dt")
                            qc.h(t)
                    qc.barrier()
                qc.measure(range(2 * n), range(2 * n))
                logical.append(qc)
                specs.append(CircuitSpec("pilot", family, {"control": control, "n": repeats}))

    circuits = transpile(logical, backend, initial_layout=layout, optimization_level=CANARY_OPTIMIZATION_LEVEL)
    order = np.random.default_rng(seed).permutation(len(circuits))
    return Batch(
        backend_name=snapshot.backend_name,
        seed=seed,
        placements=placements,
        circuits=[circuits[i] for i in order],
        specs=[specs[i] for i in order],
    )


def curves(run: Run, ref_shots: int = REF_SHOTS) -> pd.DataFrame:
    """P(target reads 1) per placement and circuit: hardware, stock Forger, hardware standard error."""
    sim = AerSimulator(method="density_matrix", noise_model=NoiseModel.from_backend(run.snapshot.simulator_backend()))
    result = sim.run(run.batch.circuits, shots=ref_shots).result()
    rows = []
    for i, spec in enumerate(run.batch.specs):
        hardware = run.shots[i][:, 0::2].mean(axis=0)
        stock = _p1_per_clbit(result.get_counts(i), n_clbits=run.shots[i].shape[1])[0::2]
        n_shots = run.shots[i].shape[0]
        for k, (t, c) in enumerate(run.batch.placements):
            se = max(np.sqrt(hardware[k] * (1 - hardware[k]) / n_shots), 1 / n_shots)
            rows.append({"placement": f"{t}-{c}", "family": spec.family, **spec.params,
                         "hardware": hardware[k], "stock": stock[k], "se": se})
    return pd.DataFrame(rows).sort_values(["placement", "family", "control", "n"], ignore_index=True)


def analyze(run: Run, ref_shots: int = REF_SHOTS) -> pd.DataFrame:
    """Fitted theta, its 1-sigma range and the z-score against theta = 0, per curve."""
    rows = []
    for (placement, family, control), g in curves(run, ref_shots).groupby(["placement", "family", "control"]):
        fit = _fit_theta(g["n"].to_numpy(float), (g["hardware"] - g["stock"]).to_numpy(),
                         g["stock"].to_numpy(), g["se"].to_numpy())
        rows.append({"placement": placement, "family": family, "control": control, **fit})
    return pd.DataFrame(rows)


def _fit_theta(n, delta, stock, se) -> dict[str, float]:
    # Profile likelihood: for each theta on the grid, the best offset a and slope k are closed form.
    w = 1 / se**2
    x = np.stack([np.ones_like(n), n], axis=1)
    residual = delta - (1 - 2 * stock) * np.sin(np.outer(THETA_GRID, n) / 2) ** 2  # (grid, len(n))
    coef = residual @ (w[:, None] * x) @ np.linalg.inv(x.T @ (w[:, None] * x))  # (grid, [a, k])
    chi2 = (w * (residual - coef @ x.T) ** 2).sum(axis=1)
    best = int(np.argmin(chi2))
    inside = THETA_GRID[chi2 <= chi2[best] + 1]
    return {
        "theta": float(THETA_GRID[best]),
        "theta_lo": float(inside.min()),
        "theta_hi": float(inside.max()),
        "z": float(np.sqrt(max(chi2[0] - chi2[best], 0.0))),
        "offset": float(coef[best, 0]),
        "slope": float(coef[best, 1]),
        "chi2_per_dof": float(chi2[best] / (len(n) - 3)),
    }


def _p1_per_clbit(counts: dict[str, int], n_clbits: int) -> np.ndarray:
    total = sum(counts.values())
    p1 = np.zeros(n_clbits)
    for key, count in counts.items():
        bits = key.replace(" ", "")[::-1]  # little-endian: index i is clbit i
        p1 += count * np.array([int(b) for b in bits[:n_clbits]])
    return p1 / total
