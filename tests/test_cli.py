from pathlib import Path

from ghostqpu.cli import main

J2 = Path("data/fresh/ibm_marrakesh_20261029T144625_85181")


def test_verify_calls_a_committed_genuine_run_and_its_twin(capsys):
    main(["verify", str(J2)])
    main(["verify", str(J2) + "_forged"])
    genuine, forged = capsys.readouterr().out.strip().splitlines()[0::2]
    assert ": Genuine (forged score" in genuine
    assert ": Forged (forged score" in forged
