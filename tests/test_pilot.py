import numpy as np
import pytest
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime.fake_provider import FakeFez

from ghostqpu.execution import _memory_to_bits
from ghostqpu.pilot import analyze, build_pilot
from ghostqpu.runs import GENUINE, Run
from ghostqpu.snapshot import CalibrationSnapshot

SHOTS = 1000


@pytest.fixture(scope="module")
def snapshot():
    return CalibrationSnapshot.capture(FakeFez())


@pytest.fixture(scope="module")
def batch(snapshot):
    return build_pilot(snapshot, seed=5, n_placements=2)


def _fake_hardware(snapshot, batch, conditional_phase: float) -> Run:
    """A Genuine-shaped pilot Run whose CZ carries an extra phase on |11> the stock model lacks."""
    circuits = []
    for qc in batch.circuits:
        out = qc.copy_empty_like()
        for inst in qc.data:
            out.append(inst.operation, inst.qubits, inst.clbits)
            if inst.operation.name == "cz" and conditional_phase:
                out.cp(conditional_phase, *inst.qubits)
        circuits.append(out)
    sim = AerSimulator(noise_model=NoiseModel.from_backend(snapshot.simulator_backend()), seed_simulator=11)
    result = sim.run(circuits, shots=SHOTS, memory=True).result()
    shots = [_memory_to_bits(result.get_memory(i)) for i in range(len(circuits))]
    return Run("pilot_test", GENUINE, batch, snapshot, shots, {"shots": SHOTS})


def test_cnot_and_idle_circuits_differ_only_in_the_cz(batch):
    by_key = {(s.family, s.params["control"], s.params["n"]): c
              for s, c in zip(batch.specs, batch.circuits, strict=True)}
    pairs = len(batch.placements)
    for (family, control, n), qc in by_key.items():
        if family != "cnot":
            continue
        idle = by_key[("idle", control, n)].count_ops()
        cnot = qc.count_ops()
        assert cnot.get("cz", 0) == n * pairs and idle.get("cz", 0) == 0
        assert cnot.get("sx", 0) == idle.get("sx", 0)


def test_analysis_recovers_a_planted_conditional_phase(snapshot, batch):
    report = analyze(_fake_hardware(snapshot, batch, conditional_phase=0.02))
    control_one = report.query("family == 'cnot' and control == 1")
    assert (control_one["z"] > 5).all()
    assert np.allclose(control_one["theta"], 0.02, atol=0.004)
    assert (report.query("family == 'idle'")["z"] < 3.2).all()


def test_analysis_stays_quiet_when_hardware_matches_the_stock_model(snapshot, batch):
    report = analyze(_fake_hardware(snapshot, batch, conditional_phase=0.0))
    assert (report["z"] < 3.2).all()
