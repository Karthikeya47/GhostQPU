"""Signatures on synthetic Runs whose per-shot probabilities we control exactly."""

import numpy as np
import pytest
from qiskit_ibm_runtime.fake_provider import FakeFez

from ghostqpu.canaries import build_batch
from ghostqpu.runs import GENUINE, Run
from ghostqpu.signature import canary_curves, signatures
from ghostqpu.snapshot import CalibrationSnapshot

SHOTS = 20000


@pytest.fixture(scope="module")
def snapshot():
    return CalibrationSnapshot.capture(FakeFez())


@pytest.fixture(scope="module")
def batch(snapshot):
    return build_batch(snapshot, seed=1, n_placements=2)


def published_readout(snapshot, batch):
    p10, p01 = snapshot.readout_errors(batch.placements[0][0])
    return p10, p01


def make_run(snapshot, batch, p_target, drift=0.0, seed=0) -> Run:
    """p_target(spec) -> P(1) for every target column; neighbor columns follow their preparation."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, SHOTS)[:, None]
    shots = []
    for qc, spec in zip(batch.circuits, batch.specs, strict=True):
        n_bits = qc.num_clbits
        p = np.full(n_bits, 0.5)
        if spec.role == "canary":
            p[0::2] = p_target(spec)
            p[1::2] = 0.98 if spec.params.get("neighbor") == 1 else 0.02
        p = np.clip(p + drift * np.sin(2 * np.pi * 3 * t), 0, 1)
        shots.append((rng.random((SHOTS, n_bits)) < p).astype(np.uint8))
    return Run("synthetic", GENUINE, batch, snapshot, shots, {"shots": SHOTS})


def baseline(snapshot, batch, x_error=2e-4, zz=0.0, ro_context=0.0, ro_offset=0.0, coherent=0.0):
    p10, p01 = published_readout(snapshot, batch)

    def p_target(spec):
        f, p = spec.family, spec.params
        if f == "coherent":
            stochastic = p["n"] * x_error
            return stochastic + np.sin(coherent * p["n"] / 2) ** 2
        if f == "spectator":
            return 0.5 + (zz * p["delay_us"] if p["neighbor"] else 0.0)
        if f == "readout":
            shift = ro_context if p["neighbor"] else 0.0
            return 1 - (p01 + ro_offset + shift) if p["target"] else p10 + ro_offset + shift
        raise AssertionError(f)

    return p_target


def sig(snapshot, batch, **kw):
    drift = kw.pop("drift", 0.0)
    return signatures(make_run(snapshot, batch, baseline(snapshot, batch, **kw), drift=drift))[0]


def test_coherent_over_rotation_bends_the_curve(snapshot, batch):
    linear = sig(snapshot, batch)
    coherent = sig(snapshot, batch, coherent=0.01)
    assert abs(linear["coh_plain_curvature"]) < 0.01
    assert coherent["coh_plain_curvature"] > 0.05
    assert coherent["coh_plain_nonlinearity"] > linear["coh_plain_nonlinearity"]


def test_neighbor_dependent_phase_shows_in_spectator(snapshot, batch):
    assert sig(snapshot, batch)["spec_shift_mean_abs"] < 0.01
    assert sig(snapshot, batch, zz=0.01)["spec_shift_mean_abs"] > 0.05


def test_readout_context_and_drift_from_calibration(snapshot, batch):
    clean = sig(snapshot, batch)
    assert clean["ro_context_shift"] < 0.02 and clean["ro_vs_calibration"] < 0.02
    assert sig(snapshot, batch, ro_context=0.03)["ro_context_shift"] > 0.04
    assert sig(snapshot, batch, ro_offset=0.03)["ro_vs_calibration"] > 0.04


def test_drift_over_shot_order_raises_dispersion(snapshot, batch):
    iid = sig(snapshot, batch)
    drifting = sig(snapshot, batch, drift=0.05)
    assert 0.5 < iid["drift_dispersion"] < 1.5
    assert drifting["drift_dispersion"] > 3


def test_canary_curves_for_plotting(snapshot, batch):
    run = make_run(snapshot, batch, baseline(snapshot, batch, coherent=0.01, zz=0.01))
    curves = canary_curves(run)
    coherent = curves["coherent"].query("variant == 'plain'").sort_values("n")
    assert coherent["p1"].iloc[-1] > 0.3 and coherent["p1"].iloc[0] < 0.05
    assert curves["spectator"]["shift"].iloc[-1] > 0.1
    assert len(curves["readout"]) == 4


def test_chunks_split_shots_in_time_order(snapshot, batch):
    run = make_run(snapshot, batch, baseline(snapshot, batch))
    chunks = signatures(run, n_chunks=4)
    assert len(chunks) == 4
    assert all(c.keys() == chunks[0].keys() for c in chunks)
    assert all(np.isfinite(v) for c in chunks for v in c.values())
