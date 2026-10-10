from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeFez

from ghostqpu.snapshot import CalibrationSnapshot


def test_round_trip_rebuilds_the_same_noise(tmp_path):
    real = FakeFez()
    snap = CalibrationSnapshot.capture(real)
    snap.save(tmp_path / "snap.json")
    rebuilt = CalibrationSnapshot.load(tmp_path / "snap.json").simulator_backend()

    assert rebuilt.num_qubits == real.num_qubits
    assert rebuilt.target["cz"][(0, 1)].error == real.target["cz"][(0, 1)].error
    assert rebuilt.qubit_properties(5).t1 == real.qubit_properties(5).t1
    assert snap.cycle == real.properties().to_dict()["last_update_date"].isoformat()


def test_readout_errors_match_published_values():
    real = FakeFez()
    p10, p01 = CalibrationSnapshot.capture(real).readout_errors(3)
    props = real.properties()
    assert p10 == props.qubit_property(3, "prob_meas1_prep0")[0]
    assert p01 == props.qubit_property(3, "prob_meas0_prep1")[0]


def test_simulator_models_idle_decay_during_delay():
    backend = CalibrationSnapshot.capture(FakeFez()).simulator_backend()
    sim = AerSimulator.from_backend(backend)

    circuits = []
    for delay_us in (0, 200):
        qc = QuantumCircuit(1, 1)
        qc.x(0)
        qc.delay(delay_us, 0, unit="us")
        qc.measure(0, 0)
        circuits.append(transpile(qc, backend, initial_layout=[3], optimization_level=0))
    result = sim.run(circuits, shots=4000, seed_simulator=1).result()
    p1 = [result.get_counts(i).get("1", 0) / 4000 for i in range(2)]

    assert p1[0] - p1[1] > 0.2
