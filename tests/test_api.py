import warnings

import pytest

J2 = "ibm_marrakesh_20261029T144625_85181"


@pytest.fixture(scope="module")
def client():
    # Starlette's TestClient uses an anyio API that newer anyio deprecates on import; not our code.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from fastapi.testclient import TestClient

        from ghostqpu.api import app

        with TestClient(app) as c:
            yield c


def test_verdict_for_a_committed_genuine_run_and_its_twin(client):
    real = client.get(f"/runs/{J2}/verdict").json()
    fake = client.get(f"/runs/{J2}_forged/verdict").json()
    assert real["verdict"] == "Genuine" and fake["verdict"] == "Forged"
    assert len(real["chunk_scores"]) == 8 and real["detector_fingerprint"] == "51a3b821bbcd587d"


def test_unknown_and_path_like_run_ids_are_rejected(client):
    assert client.get("/runs/nope/verdict").status_code == 404
    assert client.get("/runs/..%2Fruns/verdict").status_code in (400, 404)


def test_runs_and_detector_listings(client):
    runs = client.get("/runs").json()
    assert any(r["run_id"] == J2 for r in runs)
    assert len(client.get("/detector").json()["weights"]) == 12
