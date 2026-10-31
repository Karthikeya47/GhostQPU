"""Canaries hidden among Workload circuits, compiled into a Batch for one Backend.

Every circuit in a Batch is already ISA (native gates, physical qubits), so the honest
runner and the Forger execute exactly the same instructions.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, qpy, transpile
from qiskit.circuit.random import random_circuit

from ghostqpu.snapshot import CalibrationSnapshot

COHERENT_REPEATS = (0, 4, 8, 16, 32, 64, 128)
SPECTATOR_DELAYS_US = (0, 2, 4, 8, 12, 16)
MAX_READOUT_ERROR = 0.05
MAX_CZ_ERROR = 0.02
# Canaries must run exactly as written; Workloads get the light optimization a customer would use.
CANARY_OPTIMIZATION_LEVEL = 0
WORKLOAD_OPTIMIZATION_LEVEL = 1


@dataclass(frozen=True)
class CircuitSpec:
    """What a circuit in the Batch is. Clbit 2i is placement i's target, 2i+1 its neighbor."""

    role: str  # "canary" or "workload"
    family: str  # "coherent", "spectator", "readout" or a workload name
    params: dict = field(default_factory=dict)


@dataclass
class Batch:
    backend_name: str
    seed: int
    placements: list[tuple[int, int]]
    circuits: list[QuantumCircuit]
    specs: list[CircuitSpec]

    def canaries(self, family: str):
        """(index, spec) of every Canary of `family`, in Batch order."""
        return [(i, s) for i, s in enumerate(self.specs) if s.role == "canary" and s.family == family]

    def save(self, folder: Path) -> None:
        folder = Path(folder)
        with open(folder / "batch.qpy", "wb") as f:
            qpy.dump(self.circuits, f)
        meta = {
            "backend_name": self.backend_name,
            "seed": self.seed,
            "placements": self.placements,
            "specs": [asdict(s) for s in self.specs],
        }
        (folder / "batch.json").write_text(json.dumps(meta, indent=1))

    @classmethod
    def load(cls, folder: Path) -> Batch:
        folder = Path(folder)
        meta = json.loads((folder / "batch.json").read_text())
        with open(folder / "batch.qpy", "rb") as f:
            circuits = qpy.load(f)
        return cls(
            backend_name=meta["backend_name"],
            seed=meta["seed"],
            placements=[tuple(p) for p in meta["placements"]],
            circuits=circuits,
            specs=[CircuitSpec(**s) for s in meta["specs"]],
        )


def build_batch(snapshot: CalibrationSnapshot, seed: int, n_placements: int = 4) -> Batch:
    """Canaries plus Workload circuits for `snapshot`'s Backend, shuffled by `seed`."""
    backend = snapshot.simulator_backend()
    placements = choose_placements(backend.target, n_placements)
    layout = [q for pair in placements for q in pair]

    logical, specs = _canary_circuits(len(placements))
    circuits = transpile(logical, backend, initial_layout=layout, optimization_level=CANARY_OPTIMIZATION_LEVEL)

    for name, qc in _workload_circuits(seed):
        circuits.append(transpile(qc, backend, optimization_level=WORKLOAD_OPTIMIZATION_LEVEL,
                                  seed_transpiler=seed))
        specs.append(CircuitSpec("workload", name))

    order = np.random.default_rng(seed).permutation(len(circuits))
    return Batch(
        backend_name=snapshot.backend_name,
        seed=seed,
        placements=placements,
        circuits=[circuits[i] for i in order],
        specs=[specs[i] for i in order],
    )


def choose_placements(target, n: int) -> list[tuple[int, int]]:
    """Best (target, neighbor) qubit pairs that are coupled and far from each other."""
    readout = {q: target["measure"][(q,)].error for q in range(target.num_qubits)}
    edges = []
    for (a, b), props in target["cz"].items():
        if a > b or props is None or props.error is None or props.error > MAX_CZ_ERROR:
            continue
        if readout[a] is None or readout[b] is None or max(readout[a], readout[b]) > MAX_READOUT_ERROR:
            continue
        edges.append((readout[a] + readout[b] + props.error, a, b))

    neighbors: dict[int, set[int]] = {}
    for a, b in target["cz"]:
        neighbors.setdefault(a, set()).add(b)
        neighbors.setdefault(b, set()).add(a)

    chosen: list[tuple[int, int]] = []
    blocked: set[int] = set()
    for _, a, b in sorted(edges):
        if a in blocked or b in blocked:
            continue
        pair = (a, b) if readout[a] <= readout[b] else (b, a)
        chosen.append(pair)
        for q in pair:
            blocked |= {q} | neighbors.get(q, set())
        if len(chosen) == n:
            return chosen
    raise ValueError(f"only found {len(chosen)} usable qubit pairs, wanted {n}")


def _canary_circuits(n_pairs: int) -> tuple[list[QuantumCircuit], list[CircuitSpec]]:
    targets = list(range(0, 2 * n_pairs, 2))
    neighbors = list(range(1, 2 * n_pairs, 2))
    circuits, specs = [], []

    def new(name: str) -> QuantumCircuit:
        return QuantumCircuit(2 * n_pairs, 2 * n_pairs, name=name)

    def measure_all(qc: QuantumCircuit) -> None:
        qc.barrier()
        qc.measure(range(2 * n_pairs), range(2 * n_pairs))

    # Coherent amplification: N even X gates is ideally identity, but small over-rotations add up.
    for sandwich in (False, True):
        for n in COHERENT_REPEATS:
            qc = new(f"coherent_{'sx' if sandwich else 'plain'}_{n}")
            if sandwich:
                qc.sx(targets)
                qc.barrier()
            for _ in range(n):
                qc.x(targets)
                qc.barrier()
            if sandwich:
                qc.sxdg(targets)
            measure_all(qc)
            circuits.append(qc)
            specs.append(CircuitSpec("canary", "coherent", {"n": n, "sandwich": sandwich}))

    # Spectator: Ramsey on the target while its neighbor sits in |0> or |1>.
    for neighbor_state in (0, 1):
        for delay in SPECTATOR_DELAYS_US:
            qc = new(f"spectator_n{neighbor_state}_{delay}us")
            if neighbor_state:
                qc.x(neighbors)
            qc.sx(targets)
            qc.barrier()
            if delay:
                qc.delay(delay, range(2 * n_pairs), unit="us")
                qc.barrier()
            qc.sx(targets)
            measure_all(qc)
            circuits.append(qc)
            specs.append(CircuitSpec("canary", "spectator", {"neighbor": neighbor_state, "delay_us": delay}))

    # Readout context: the same target measurement with the neighbor in |0> or |1>.
    for target_state in (0, 1):
        for neighbor_state in (0, 1):
            qc = new(f"readout_t{target_state}_n{neighbor_state}")
            if target_state:
                qc.x(targets)
            if neighbor_state:
                qc.x(neighbors)
            measure_all(qc)
            circuits.append(qc)
            specs.append(CircuitSpec("canary", "readout", {"target": target_state, "neighbor": neighbor_state}))

    return circuits, specs


def _workload_circuits(seed: int) -> list[tuple[str, QuantumCircuit]]:
    ghz = QuantumCircuit(5, name="ghz5")
    ghz.h(0)
    for q in range(4):
        ghz.cx(q, q + 1)
    ghz.measure_all()

    work = [("ghz5", ghz)]
    for k in range(3):
        qc = random_circuit(4, depth=4, max_operands=2, measure=True, seed=seed * 10 + k)
        qc.name = f"random4_{k}"
        work.append((qc.name, qc))
    return work
