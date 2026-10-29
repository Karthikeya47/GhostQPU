from datetime import UTC, datetime

import numpy as np
import pytest
from qiskit_ibm_runtime.fake_provider import FakeFez

from ghostqpu.canaries import Batch, build_batch
from ghostqpu.execution import collect, forge_twin, manifest, stand_in_run, submit
from ghostqpu.runs import FORGED, GENUINE, load_runs
from ghostqpu.snapshot import CalibrationSnapshot


@pytest.fixture(scope="module")
def batch():
    return build_batch(CalibrationSnapshot.capture(FakeFez()), seed=3, n_placements=2)


@pytest.fixture(scope="module")
def runs(batch):
    genuine = stand_in_run(FakeFez(), batch, shots=300, run_id="local_test")
    return genuine, forge_twin(genuine)


def _assert_readout_columns_follow_preparation(run):
    # A bit-order mismatch between execution paths would let a Detector "win" for free.
    readout = run.batch.canaries("readout")
    assert readout
    for i, spec in readout:
        bits = run.bits(i)
        assert abs(bits[:, 0::2].mean() - spec.params["target"]) < 0.1
        assert abs(bits[:, 1::2].mean() - spec.params["neighbor"]) < 0.1


def test_genuine_and_forged_runs_have_identical_shape(runs):
    genuine, forged = runs
    assert genuine.origin == GENUINE and forged.origin == FORGED
    assert forged.info["twin_of"] == genuine.run_id
    assert len(genuine.shots) == len(forged.shots) == len(genuine.batch.circuits)
    for g, f in zip(genuine.shots, forged.shots, strict=True):
        assert g.shape == f.shape and g.dtype == f.dtype == np.uint8
        assert g.shape[0] == 300


def test_twin_is_reproducible_bit_for_bit(runs):
    genuine, forged = runs
    again = forge_twin(genuine)
    assert forged.info["seed_simulator"] == again.info["seed_simulator"] != genuine.info["seed_simulator"]
    assert all(np.array_equal(a, b) for a, b in zip(forged.shots, again.shots, strict=True))


def test_bit_columns_mean_the_same_qubits_in_both_origins(runs):
    for run in runs:
        _assert_readout_columns_follow_preparation(run)


def test_sampler_path_uses_the_same_bit_columns(batch):
    # The IBM path goes through the runtime Sampler; local mode runs the same code.
    readout = [i for i, _ in batch.canaries("readout")]
    tiny = Batch(
        backend_name=batch.backend_name,
        seed=batch.seed,
        placements=batch.placements,
        circuits=[batch.circuits[i] for i in readout],
        specs=[batch.specs[i] for i in readout],
    )
    backend = FakeFez()
    submission = {"run_id": "sampler_test", "backend": backend.name, "shots": 200,
                  "submitted_at": datetime.now(UTC).isoformat()}
    run = collect(submit(backend, tiny, shots=200), backend, tiny, submission)
    assert run.origin == GENUINE and run.shots[0].shape == (200, 2 * len(batch.placements))
    _assert_readout_columns_follow_preparation(run)


def test_runs_round_trip_through_disk(tmp_path, runs):
    for run in runs:
        run.save(tmp_path)
    loaded = {r.run_id: r for r in load_runs(tmp_path)}
    for run in runs:
        again = loaded[run.run_id]
        assert again.origin == run.origin
        assert again.info == run.info
        assert again.snapshot == run.snapshot
        assert all(np.array_equal(a, b) for a, b in zip(again.shots, run.shots, strict=True))


def test_load_runs_on_missing_folder_is_empty(tmp_path):
    assert load_runs(tmp_path / "nope") == []


def test_manifest_records_code_versions_and_sampler_settings():
    # A cross-day study is only comparable if every Run says what produced it.
    import qiskit
    import qiskit_ibm_runtime

    record = manifest(FakeFez())
    assert len(record["git"]["commit"]) == 40 and isinstance(record["git"]["dirty"], bool)
    assert record["packages"]["qiskit"] == qiskit.__version__
    assert record["packages"]["qiskit-ibm-runtime"] == qiskit_ibm_runtime.__version__
    options = record["sampler_options"]
    assert options["dynamical_decoupling"]["enable"] is False
    assert options["twirling"]["enable_gates"] is False and options["twirling"]["enable_measure"] is False
    assert record["transpile"] == {"canaries": 0, "workloads": 1}
