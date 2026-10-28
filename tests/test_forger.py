import numpy as np
import pytest
from qiskit_ibm_runtime.fake_provider import FakeFez

from ghostqpu.canaries import Batch, build_batch
from ghostqpu.execution import forge_twin, stand_in_run
from ghostqpu.forger import ForgerProfile, Readout, fit_profile, forge_twin_v2
from ghostqpu.runs import FORGED
from ghostqpu.signature import canary_curves
from ghostqpu.snapshot import CalibrationSnapshot

SHOTS = 600


@pytest.fixture(scope="module")
def batch():
    return build_batch(CalibrationSnapshot.capture(FakeFez()), seed=3, n_placements=2)


def _only(batch: Batch, family: str) -> Batch:
    keep = [i for i, s in batch.canaries(family)]
    return Batch(
        backend_name=batch.backend_name,
        seed=batch.seed,
        placements=batch.placements,
        circuits=[batch.circuits[i] for i in keep],
        specs=[batch.specs[i] for i in keep],
    )


def _targets(batch: Batch) -> list[int]:
    return [t for t, _ in batch.placements]


@pytest.fixture(scope="module")
def coherent_run(batch):
    return stand_in_run(FakeFez(), _only(batch, "coherent"), SHOTS, "coherent_probe")


def _p1_at(run, n: int, variant: str = "plain") -> float:
    curve = canary_curves(run)["coherent"]
    return float(curve[(curve["variant"] == variant) & (curve["n"] == n)]["p1"].iloc[0])


def test_amplitude_error_bends_the_coherent_curve_the_stock_forger_leaves_flat(batch, coherent_run):
    profile = ForgerProfile(amp_error={t: 0.004 for t in _targets(batch)})
    stock, strong = forge_twin(coherent_run), forge_twin_v2(coherent_run, profile)
    assert strong.origin == FORGED and strong.info["twin_of"] == coherent_run.run_id
    assert _p1_at(stock, 128) < 0.15
    assert _p1_at(strong, 128) > 0.35


@pytest.fixture(scope="module")
def spectator_run(batch):
    return stand_in_run(FakeFez(), _only(batch, "spectator"), SHOTS, "spectator_probe")


def _shift_at(run, delay_us: int) -> float:
    curve = canary_curves(run)["spectator"]
    return float(curve[curve["delay_us"] == delay_us]["shift"].iloc[0])


def test_detuning_and_zz_make_the_ramsey_phase_depend_on_the_neighbor(batch, spectator_run):
    profile = ForgerProfile(
        detuning={t: 0.1 for t, _ in batch.placements},
        zz={(t, n): 0.05 for t, n in batch.placements},
    )
    stock, strong = forge_twin(spectator_run), forge_twin_v2(spectator_run, profile)
    assert _shift_at(stock, 16) < 0.15
    assert _shift_at(strong, 16) > 0.4


@pytest.fixture(scope="module")
def readout_run(batch):
    return stand_in_run(FakeFez(), _only(batch, "readout"), SHOTS, "readout_probe")


def _readout_error(run, target: int, neighbor: int) -> float:
    curve = canary_curves(run)["readout"]
    return float(curve[(curve["target"] == target) & (curve["neighbor"] == neighbor)]["error"].iloc[0])


def test_readout_error_that_depends_on_the_neighbor_shows_up_in_the_readout_canaries(batch, readout_run):
    # p_read_1[own][partner]: P(read 1) given the qubit's own state and its partner's state.
    table = np.array([[0.01, 0.15], [0.97, 0.90]])
    profile = ForgerProfile(readout={t: Readout(partner=n, p_read_1=table) for t, n in batch.placements})
    stock, strong = forge_twin(readout_run), forge_twin_v2(readout_run, profile)
    assert _readout_error(stock, 0, 1) < 0.05
    assert _readout_error(strong, 0, 0) < 0.05
    assert _readout_error(strong, 0, 1) == pytest.approx(0.15, abs=0.05)
    assert _readout_error(strong, 1, 1) == pytest.approx(0.10, abs=0.05)


def test_fitting_a_probe_run_recovers_the_effects_that_were_injected(batch):
    targets = _targets(batch)
    truth = ForgerProfile(
        amp_error={t: 0.003 for t in targets},
        detuning={t: 0.1 for t in targets},
        zz={(t, n): 0.04 for t, n in batch.placements},
        readout={
            t: Readout(partner=n, p_read_1=np.array([[0.01, 0.12], [0.97, 0.90]]))
            for t, n in batch.placements
        },
    )
    probe = forge_twin_v2(stand_in_run(FakeFez(), batch, 1000, "fit_probe"), truth)
    fitted = fit_profile(probe)
    for t, n in batch.placements:
        assert fitted.amp_error[t] == pytest.approx(0.003, rel=0.15)
        assert fitted.detuning[t] == pytest.approx(0.1, abs=0.02)
        assert fitted.zz[(t, n)] == pytest.approx(0.04, abs=0.02)
        assert fitted.readout[t].partner == n
        assert fitted.readout[t].p_read_1 == pytest.approx(np.array([[0.01, 0.12], [0.97, 0.90]]), abs=0.04)
