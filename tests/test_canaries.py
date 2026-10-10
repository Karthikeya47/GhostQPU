import pytest
from qiskit_ibm_runtime.fake_provider import FakeFez

from ghostqpu.canaries import COHERENT_REPEATS, Batch, build_batch
from ghostqpu.snapshot import CalibrationSnapshot


@pytest.fixture(scope="module")
def snapshot():
    return CalibrationSnapshot.capture(FakeFez())


@pytest.fixture(scope="module")
def batch(snapshot):
    return build_batch(snapshot, seed=7)


def test_x_trains_survive_compilation(batch):
    for i, spec in batch.canaries("coherent"):
        x_count = batch.circuits[i].count_ops().get("x", 0)
        assert x_count == spec.params["n"] * len(batch.placements)


def test_placements_are_coupled_and_isolated(snapshot, batch):
    coupling = {tuple(e) for e in snapshot.configuration["coupling_map"]}
    used = [q for pair in batch.placements for q in pair]
    assert len(set(used)) == len(used)
    for a, b in batch.placements:
        assert (a, b) in coupling or (b, a) in coupling
    for i, (a, _) in enumerate(batch.placements):
        for c, d in batch.placements[i + 1 :]:
            assert not {(a, c), (a, d), (c, a), (d, a)} & coupling


def test_canaries_measure_their_placement_in_clbit_order(batch):
    expected = [q for pair in batch.placements for q in pair]
    for i, _ in batch.canaries("readout"):
        qc = batch.circuits[i]
        measured = {
            qc.find_bit(inst.clbits[0]).index: qc.find_bit(inst.qubits[0]).index
            for inst in qc.data
            if inst.operation.name == "measure"
        }
        assert [measured[c] for c in range(len(expected))] == expected


def test_canaries_are_hidden_among_workload(batch):
    roles = [s.role for s in batch.specs]
    assert roles.count("canary") == 2 * len(COHERENT_REPEATS) + 12 + 4
    assert roles.count("workload") == 4
    assert roles != sorted(roles) and roles != sorted(roles, reverse=True)


def test_same_seed_same_batch(snapshot, batch):
    again = build_batch(snapshot, seed=7)
    assert again.specs == batch.specs
    assert again.placements == batch.placements


def test_save_load_round_trip(tmp_path, batch):
    batch.save(tmp_path)
    loaded = Batch.load(tmp_path)
    assert loaded.specs == batch.specs
    assert loaded.placements == batch.placements
    assert [c.count_ops() for c in loaded.circuits] == [c.count_ops() for c in batch.circuits]
