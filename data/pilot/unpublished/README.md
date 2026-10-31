# Unpublished pilot Runs

Pilot Runs kept out of the site on purpose: `scripts/export_web_data.py` reads only `data/pilot/runs/`.

## pilot_ibm_marrakesh_20261028T155610_1

CNOT pilot job `dbh1m6kdgr2s73cshlj0` on ibm_marrakesh, submitted 2026-10-28 and only collected on 2026-10-31.
Calibration cycle 2026-10-28T21:23:43+05:30, 1000 shots, 11 QPU seconds. Placements (87,86), (5,6), (14,15), (107,108).

Fit with `ghostqpu.pilot.analyze` against the stock Forger (detected means z > 3.2):

| Placement | cnot, control 0 | cnot, control 1 | idle, control 0 | idle, control 1 |
|---|---|---|---|---|
| 5-6 | z 15.0, detected | z 10.7, detected | z 6.1, detected | z 3.2, detected |
| 14-15 | z 10.2, detected | z 0.0 | z 4.9, detected | z 4.2, detected |
| 87-86 | z 7.3, detected | z 1.2 | z 0.0 | z 0.0 |
| 107-108 | z 0.6 | z 0.0 | z 0.0 | z 2.4 |

Pair 107-108, which carries the "73% vs 10% after 32 CNOTs" result in the 29 Oct pilot, shows no coherent CZ error in
this earlier cycle. The effect on that pair is cycle dependent, which supports needing several placements for a CNOT
Canary. Pair 5-6 shows it in every condition. Several fits have chi2 per dof well above 1 (5-6, 87-86), so treat the
z values there as indicative.
