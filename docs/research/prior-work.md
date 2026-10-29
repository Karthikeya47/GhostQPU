# Prior work and what is new (checked 2026-10-29)

Search of arXiv, publisher pages and GitHub. Only abstracts and READMEs were read, not full texts, so this is a first
pass, not a systematic review. Older verification and benchmarking papers are covered in
[two-qubit-extension.md](two-qubit-extension.md).

## Closest work

| Work | What it detects | Relation to GhostQPU |
|---|---|---|
| Wu, Hu, Li, *Detecting Fraudulent Services on Quantum Cloud Platforms via Dynamic Fingerprinting*, 2024, [arXiv:2408.11203](https://arxiv.org/abs/2408.11203) | Machine substitution and fabricated device profiles, from one probing circuit's noisy output | Closest prior work. Its threat is a different device. A calibration-built simulator is designed to match published error rates, which is what such a fingerprint compares against |
| QuanGuard (same group, IEEE Trans. Computers, 2026), [ResearchGate](https://www.researchgate.net/publication/398804887_QuanGuard_Error_Evolution-based_Fingerprinting_for_Fraud_Detection_in_Quantum_Cloud_Services) | Same threat, fingerprints from error evolution, seven IBM devices | Same difference |
| Ma et al., *Raw-Curve Quantum Fingerprints*, 2026, [arXiv:2606.11644](https://arxiv.org/abs/2606.11644) | Hardware substitution, with adversarial perturbation tests | Substitution only. Simulators are not in the abstract's threat model |
| Yeniaras, Karimov, *QCIVET*, 2026, [arXiv:2605.13109](https://arxiv.org/abs/2605.13109) | Pipeline integrity and customer-side auditing of cloud QPUs. Noise models from IBM calibration, validated on ibm_fez | The abstract does not mention detecting classical simulation. **Full text not read; read it before claiming novelty in writing** |
| Canary, Qollab x IonQ hackathon, 9-11 Oct 2026, [GitHub](https://github.com/tomcode1000/Canary) | Wrong or lazy answers, via hidden Clifford trap circuits and a hypergeometric bound | Same "hidden traps" idea, different threat: its traps have exact answers, so a good noisy simulator passes them. Simulators only, no hardware runs |
| *Simulation and Benchmarking of Real Quantum Hardware*, 2025, [arXiv:2508.04483](https://arxiv.org/abs/2508.04483) | Not security. Calibration-built noise models track hardware closely; remaining gaps attributed to coherent errors, leakage and crosstalk | Independent support for the premise that those gaps are where Canaries should look |
| Cryptographic verification, e.g. Mahadev 2018 ([arXiv:1804.01082](https://arxiv.org/abs/1804.01082)); 2020 experiment on IBM cloud, [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S209592732030534X) | Whether a quantum device was used, provably | Needs circuits far beyond current hardware for a per-job check |

## What appears new in GhostQPU

As far as this search found, no published work or project does the following:

1. Treats a **full classical simulation built from the Backend's own public calibration, at execution time,** as the
   attacker (the Forger), and evaluates against it rather than against device substitution.
2. Uses Canaries aimed at what such a simulator leaves out: coherent amplification, spectator ZZ, readout context and
   shot-order drift.
3. Evaluates with matched Twins, a null test (simulator on both sides, AUC near 0.5) and a frozen Detector on new
   calibration cycles and a second Backend.
4. Tests its own defense with a stronger, hardware-fitted Forger (`ghostqpu/forger.py`) and shows where it breaks.
5. Measures a CZ-pulse coherent phase on hardware that the stock Forger misses ([cnot-pilot-hardware.md](cnot-pilot-hardware.md)).

## Honest limits for any novelty claim

- An adversary with some real QPU access can fit hardware effects, as our own stronger Forger shows. GhostQPU raises
  the cost of forging; it does not make it impossible.
- At the current scale (up to 8 qubits per circuit) the defense rests on noise physics, not computational hardness.
