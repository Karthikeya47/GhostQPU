"""A stronger Forger: calibration data plus hardware effects learned from a probe Run.

The stock Forger (execution.forge_twin) knows only the public Calibration snapshot. This one
also holds a ForgerProfile, the extra effects a dishonest Provider could fit after paying for
a single probe job. Forging never looks at which circuits are Canaries: the profile is applied
to every circuit by physical qubit, exactly as a real device would act on it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

from ghostqpu.canaries import Batch
from ghostqpu.execution import _memory_to_bits, _now, forge_twin
from ghostqpu.runs import FORGED, Run


@dataclass
class Readout:
    """A qubit's readout, which also depends on the state of one `partner` qubit."""

    partner: int
    p_read_1: np.ndarray  # [own state][partner state] -> P(read 1)


@dataclass
class ForgerProfile:
    # Fractional pulse-amplitude error per physical qubit: x turns by pi * (1 + e), sx by pi/2 * (1 + e).
    amp_error: dict[int, float] = field(default_factory=dict)
    # Ramsey frequency offset per qubit (rad/us), seen while its neighbors sit in |0>.
    detuning: dict[int, float] = field(default_factory=dict)
    # (qubit, partner) -> ZZ shift (rad/us): the qubit's phase advances at detuning +/- zz, set by the partner's state.
    zz: dict[tuple[int, int], float] = field(default_factory=dict)
    # Qubits whose readout is context dependent. Every other qubit reads out as the calibration says.
    readout: dict[int, Readout] = field(default_factory=dict)


AMP_GRID = np.linspace(0, 0.02, 2001)
DETUNING_GRID = np.arange(0, 0.6001, 0.005)
ZZ_GRID = np.arange(-0.6, 0.6001, 0.005)


def fit_profile(probe: Run) -> ForgerProfile:
    """Learn a ForgerProfile from a Genuine probe Run of a Batch whose structure the forger knows.

    The stock Forger's simulation of the same circuits is the baseline. Each effect is whatever
    must be added to that baseline to match the probe.
    """
    baseline = forge_twin(probe)
    profile = ForgerProfile()
    for i, (target, neighbor) in enumerate(probe.batch.placements):
        _fit_amp_error(profile, probe, baseline, i, target)
        _fit_ramsey(profile, probe, baseline, i, target, neighbor)
        _fit_readout(profile, probe, i, target, neighbor)
    return profile


def _fit_amp_error(profile: ForgerProfile, probe: Run, baseline: Run, i: int, target: int) -> None:
    curve = sorted(
        (spec.params["n"], probe.shots[k][:, 2 * i].mean(), baseline.shots[k][:, 2 * i].mean())
        for k, spec in probe.batch.canaries("coherent")
        if not spec.params["sandwich"]
    )
    n, observed, floor = (np.array(col) for col in zip(*curve, strict=True))
    # Coherent over-rotation of n even x gates leaves the qubit at sin^2(n pi e / 2), on top of the stock noise.
    model = floor + (1 - 2 * floor) * np.sin(np.outer(AMP_GRID, n) * np.pi / 2) ** 2
    profile.amp_error[target] = float(AMP_GRID[np.argmin(((model - observed) ** 2).sum(axis=1))])


def _fit_ramsey(profile: ForgerProfile, probe: Run, baseline: Run, i: int, target: int, neighbor: int) -> None:
    keys, observed, floor = [], [], []
    for k, spec in probe.batch.canaries("spectator"):
        keys.append((spec.params["neighbor"], spec.params["delay_us"]))
        observed.append(probe.shots[k][:, 2 * i].mean())
        floor.append(baseline.shots[k][:, 2 * i].mean())
    state, delay = np.array(keys).T
    observed, contrast = np.array(observed), np.array(floor) - 0.5
    # The neighbor in |1> moves the target's Ramsey phase from (c + a) t to (c - a) t.
    rate = DETUNING_GRID[:, None, None] + np.where(state == 0, 1, -1) * ZZ_GRID[None, :, None]
    model = 0.5 + contrast * np.cos(rate * delay)
    # Ramsey fringes only fix |c + a| and |c - a|, so (c, a) and (|a|, c) fit equally well.
    # Both give the same forged curves. The tiny penalty just picks the weaker ZZ.
    error = ((model - observed) ** 2).sum(axis=-1) + 1e-9 * np.abs(ZZ_GRID)[None, :]
    c, a = np.unravel_index(np.argmin(error), error.shape)
    profile.detuning[target] = float(DETUNING_GRID[c])
    profile.zz[(target, neighbor)] = float(ZZ_GRID[a])


def _fit_readout(profile: ForgerProfile, probe: Run, i: int, target: int, neighbor: int) -> None:
    for qubit, partner, column in ((target, neighbor, 2 * i), (neighbor, target, 2 * i + 1)):
        table = np.zeros((2, 2))
        for k, spec in probe.batch.canaries("readout"):
            own, other = (spec.params["target"], spec.params["neighbor"])
            if column % 2:
                own, other = other, own
            table[own, other] = probe.shots[k][:, column].mean()
        profile.readout[qubit] = Readout(partner=partner, p_read_1=table)


def forge_twin_v2(run: Run, profile: ForgerProfile) -> Run:
    """Simulate `run`'s exact circuits from its calibration plus the effects in `profile`."""
    batch = Batch(
        backend_name=run.batch.backend_name,
        seed=run.batch.seed,
        placements=run.batch.placements,
        circuits=[_with_effects(qc, profile, _dt_us(run)) for qc in run.batch.circuits],
        specs=run.batch.specs,
    )
    return Run(
        run_id=f"{run.run_id}_forged_v2",
        origin=FORGED,
        batch=run.batch,
        snapshot=run.snapshot,
        shots=_simulate(run, batch.circuits, profile),
        info={**run.info, "twin_of": run.run_id, "qpu_seconds": 0.0, "forged_at": _now(), "forger": "v2"},
    )


def _with_effects(qc: QuantumCircuit, profile: ForgerProfile, dt_us: float) -> QuantumCircuit:
    out = qc.copy_empty_like()
    for inst in qc.data:
        out.append(inst.operation, inst.qubits, inst.clbits)
        name = inst.operation.name
        q = qc.find_bit(inst.qubits[0]).index if inst.qubits else None
        if name in ("x", "sx"):
            error = profile.amp_error.get(q, 0.0)
            if error:
                out.rx(np.pi * error * (1 if name == "x" else 0.5), inst.qubits[0])
        elif name == "delay":
            us = _delay_us(inst.operation, dt_us)
            if profile.detuning.get(q):
                out.rz(profile.detuning[q] * us, inst.qubits[0])
            for (qubit, partner), rate in profile.zz.items():
                if qubit == q:
                    out.rzz(rate * us, inst.qubits[0], qc.qubits[partner])
    return out


def _delay_us(delay, dt_us: float) -> float:
    scale = {"dt": dt_us, "us": 1.0, "ns": 1e-3, "ms": 1e3, "s": 1e6}[delay.unit]
    return delay.duration * scale


def _dt_us(run: Run) -> float:
    return run.snapshot.configuration["dt"] * 1e-3  # IBM publishes dt in ns


def _simulate(run: Run, circuits: list[QuantumCircuit], profile: ForgerProfile) -> list[np.ndarray]:
    # Readout is applied afterwards, so gate noise comes from the calibration alone.
    noise = NoiseModel.from_backend(run.snapshot.simulator_backend(), readout_error=False)
    sim = AerSimulator(noise_model=noise)
    result = sim.run(circuits, shots=run.info["shots"], memory=True).result()
    rng = np.random.default_rng(run.batch.seed)
    return [
        _read_out(_memory_to_bits(result.get_memory(i)), _measured_qubits(qc), run, profile, rng)
        for i, qc in enumerate(circuits)
    ]


def _measured_qubits(qc: QuantumCircuit) -> dict[int, int]:
    """clbit index -> physical qubit measured into it."""
    return {
        qc.find_bit(inst.clbits[0]).index: qc.find_bit(inst.qubits[0]).index
        for inst in qc.data
        if inst.operation.name == "measure"
    }


def _read_out(bits: np.ndarray, measured: dict[int, int], run: Run, profile: ForgerProfile, rng) -> np.ndarray:
    """Turn ideal measured bits into read bits: context dependent where the profile says, else per calibration."""
    column = {q: c for c, q in measured.items()}
    out = bits.copy()
    for c, q in measured.items():
        own = bits[:, c].astype(int)
        context = profile.readout.get(q)
        if context is not None and context.partner in column:
            partner = bits[:, column[context.partner]].astype(int)
            p1 = context.p_read_1[own, partner]
        else:
            prep0, prep1 = run.snapshot.readout_errors(q)
            p1 = np.where(own == 0, prep0, 1 - prep1)
        out[:, c] = rng.random(len(p1)) < p1
    return out
