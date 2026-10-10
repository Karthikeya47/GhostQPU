"""The Detector separates Runs that differ and cannot separate Runs that don't."""

import numpy as np
import pytest
from qiskit_ibm_runtime.fake_provider import FakeFez

from ghostqpu.canaries import build_batch
from ghostqpu.detector import dataset, evaluate, train, verdict
from ghostqpu.runs import FORGED, GENUINE
from ghostqpu.snapshot import CalibrationSnapshot
from tests.test_signature import baseline, make_run


@pytest.fixture(scope="module")
def snapshot():
    return CalibrationSnapshot.capture(FakeFez())


@pytest.fixture(scope="module")
def batch(snapshot):
    return build_batch(snapshot, seed=1, n_placements=2)


def pairs(snapshot, batch, hardware_effects: dict, n_pairs=4):
    runs = []
    for k in range(n_pairs):
        genuine = make_run(snapshot, batch, baseline(snapshot, batch, **hardware_effects), seed=2 * k)
        genuine.run_id = f"g{k}"
        forged = make_run(snapshot, batch, baseline(snapshot, batch), seed=2 * k + 1)
        forged.run_id, forged.origin, forged.info = f"g{k}_forged", FORGED, {**forged.info, "twin_of": f"g{k}"}
        runs += [genuine, forged]
    return runs


def test_detects_hardware_effects_the_forger_lacks(snapshot, batch):
    runs = pairs(snapshot, batch, {"coherent": 0.01, "zz": 0.01, "ro_context": 0.03})
    report = evaluate(dataset(runs, n_chunks=4))
    assert report.split == "by run pair"
    assert report.auc > 0.95 and report.run_accuracy == 1.0


def test_null_identical_physics_is_not_separable(snapshot, batch):
    report = evaluate(dataset(pairs(snapshot, batch, {}), n_chunks=4))
    assert 0.2 < report.auc < 0.8


def test_verdict_on_an_unseen_run(snapshot, batch):
    effects = {"coherent": 0.01, "zz": 0.01, "ro_context": 0.03}
    model = train(dataset(pairs(snapshot, batch, effects), n_chunks=4))
    unseen = make_run(snapshot, batch, baseline(snapshot, batch, **effects), seed=99)
    assert verdict(model, unseen, n_chunks=4).label == GENUINE
    forged = make_run(snapshot, batch, baseline(snapshot, batch), seed=98)
    result = verdict(model, forged, n_chunks=4)
    assert result.label == FORGED and np.isfinite(result.forged_score)


def test_needs_two_pairs(snapshot, batch):
    with pytest.raises(ValueError):
        evaluate(dataset(pairs(snapshot, batch, {}, n_pairs=1), n_chunks=4))
