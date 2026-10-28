# Extending GhostQPU to a genuine two-qubit system

Research note, 2026-10-26. Every paper below was located on arXiv (or the publisher page) and its abstract was read in this session. Summaries are paraphrases of the abstracts, not of the full texts, unless stated. Claims about the GhostQPU repo come from README.md, CONTEXT.md, ghostqpu/canaries.py and ghostqpu/signature.py (local files, not URLs).

## 1. Where GhostQPU stands today

- Canaries are three families: coherent amplification (N X gates, plain and SX-sandwiched), spectator Ramsey (target Ramsey with the neighbor in |0> or |1>), and readout context (target x neighbor prepared state). All gates are single-qubit (x, sx, sxdg, delay); the only two-qubit element is that the neighbor is a coupled qubit (canaries.py).
- Placements are CZ-coupled pairs chosen from the target's `cz` edges with low CZ and readout error (`choose_placements`). So the code already knows the native two-qubit gate is CZ, but never applies it in a canary. The only CZ/CX use is inside the `ghz5` workload circuit.
- Signature has 12 features: coherent rise/curvature/nonlinearity (plain and sx), spectator shift mean/max, readout context shift and readout-vs-calibration, and two drift statistics (signature.py).
- The Forger is Qiskit Aer with a noise model built from the live calibration (README.md). Per the Qiskit Aer docs, `NoiseModel.from_backend` gives one- and two-qubit depolarizing error followed by single-qubit thermal relaxation, plus single-qubit readout error; the page does not mention crosstalk, coherent errors or correlated readout ([NoiseModel docs](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.NoiseModel.html)). That absence is why today's canaries work: the Forger has no ZZ, no over-rotation and no readout context.

## 2. Papers

### 2.1 Crosstalk and ZZ characterization

**P1. Detecting crosstalk errors in quantum information processors.** Sarovar, Proctor, Rudinger, Young, Nielsen, Blume-Kohout. 2019, arXiv:1908.09855 (Quantum 4, 321, 2020). URL: https://arxiv.org/abs/1908.09855
Gives a rigorous, model-independent definition of crosstalk (correlated, nonlocal errors that violate the assumption of local errors). Builds a protocol that detects crosstalk from conditional dependencies among observed probabilities, with experiment count growing at most cubically in qubit number. Demonstrated in simulation for 2- and 6-qubit processors.
GhostQPU: gives a formal test (conditional independence of qubit A's outcome from what was done on qubit B) that could replace our ad hoc "spectator shift" feature and generalize it to 2-qubit gate contexts.

**P2. Characterizing crosstalk of superconducting transmon processors.** Ketterer, Wellens. 2023, arXiv:2303.14103 (Phys. Rev. Applied 20, 034065). URL: https://arxiv.org/abs/2303.14103
Defines crosstalk as correlated effects between gates run simultaneously on neighboring qubits and measures it chip-wide with randomized benchmarking. Tested on IBM hardware, finding significant fidelity changes due to crosstalk. Builds a crosstalk-aware noise model from the measurements.
GhostQPU: important in two ways. It shows simultaneous-gate crosstalk is measurable on IBM chips, and it also shows a Forger can in principle fit such a model from RB data, so any crosstalk canary must be judged against a crosstalk-aware Forger.

**P3. Suppression of Qubit Crosstalk in a Tunable Coupling Superconducting Circuit.** Mundada, Zhang, Hazard, Houck. 2018, arXiv:1810.04182 (Phys. Rev. Applied 12, 054023, 2019). URL: https://arxiv.org/abs/1810.04182
Shows static ZZ crosstalk can be cancelled in a two-qubit, two-coupler circuit by tuning the coupler so the two ZZ contributions interfere destructively. Simultaneous RB confirms the suppression. A parametric iSWAP gives Bell-state fidelity 98.5% and sqrt-iSWAP fidelity 94.8% by process tomography.
GhostQPU: background on why ZZ is a real, device-specific, always-on term. Note IBM Heron chips use tunable couplers, so static ZZ is engineered small, which changes how large our ZZ canary signal will be (to be measured, not assumed).

**P4. Demonstration of a High-Fidelity CNOT for Fixed-Frequency Transmons with Engineered ZZ Suppression.** Kandala, Wei, Srinivasan, Magesan, Carnevale, Keefe, Klaus, Dial, McKay. 2020, arXiv:2011.07050 (PRL 127, 130501, 2021). URL: https://arxiv.org/abs/2011.07050
Proposes a coupling architecture with two fixed-frequency coupling elements that suppresses static ZZ while keeping strong effective coupling (desired-to-undesired ratio improved by more than 6x). Demonstrates a 180 ns cross-resonance CNOT with 99.77(2)% fidelity from interleaved RB.
GhostQPU: documents the gate-speed versus ZZ trade-off that makes residual ZZ a per-edge fingerprint of the hardware.

### 2.2 Coherent errors in two-qubit gates

**P5. Procedure for systematically tuning up crosstalk in the cross resonance gate.** Sheldon, Magesan, Chow, Gambetta. 2016, arXiv:1603.04821. URL: https://arxiv.org/abs/1603.04821
Improves the theory and implementation of the cross-resonance (CR) gate, reaching interleaved RB fidelities above 99%. Presents a calibration procedure that measures the full CR Hamiltonian and reveals the error terms that limited fidelity. Adds a second drive tone on the target to cancel unwanted Hamiltonian components.
GhostQPU: shows ECR/CR gates have a multi-term Hamiltonian (IX, ZI, ZZ, IZ and others) whose residuals are coherent and measurable by amplification. Honest caveat: ibm_marrakesh and ibm_kingston use CZ, so CR specifics apply only to older Eagle/Falcon-style backends.

**P6. Reducing unitary and spectator errors in cross resonance with optimized rotary echoes.** Sundaresan, Lauer, Pritchett, Magesan, Jurcevic, Gambetta. 2020, arXiv:2007.02925. URL: https://arxiv.org/abs/2007.02925
Adds resonant rotary pulses on the target, in phase with the echoed CR pulses, and uses Hamiltonian error amplifying tomography (HEAT) to show they reduce error terms. The rotary also reduces unwanted entanglement between target and spectator qubits. Multi-qubit gains assessed with unitarity benchmarking and quantum volume.
GhostQPU: HEAT is the direct template for a two-qubit error-amplification canary (repeat the gate with interleaved single-qubit pulses so a chosen Hamiltonian term adds coherently). It also shows spectator-entangling errors from two-qubit gates exist on IBM hardware.

### 2.3 Readout error, correlated and context dependent

**P7. Mitigating measurement errors in multi-qubit experiments.** Bravyi, Sheldon, Kandala, McKay, Gambetta. 2020, arXiv:2006.14044 (PRA 103, 042605). URL: https://arxiv.org/abs/2006.14044
Proposes two mitigation schemes based on tensor-product and correlated Markovian noise models, with rates estimated from simple calibration data, and applies the inverse noise matrix. Demonstrated on IBM devices with graph-state stabilizer measurements up to 12 qubits.
GhostQPU: the paper's own "correlated Markovian" model is evidence that IBM treats multi-qubit readout correlations as real. Aer's readout error is single-qubit only (see section 1), so Bell-state or joint-readout correlation canaries (P(01) vs P(10) vs product of marginals) test something the stock Forger lacks.

**P8. Quantification and Characterization of Leakage Errors.** Wood, Gambetta. 2017, arXiv:1704.03081 (PRA 97, 032306, 2018). URL: https://arxiv.org/abs/1704.03081
Defines leakage and seepage rates and shows how to estimate them with a modified randomized benchmarking for Clifford gates, alongside average gate fidelity.
GhostQPU: leakage out of the computational subspace is a non-depolarizing, history-dependent effect Aer does not model; long repeated-gate canaries (including CZ) are sensitive to it. Also applies to readout of leaked population.

### 2.4 Benchmarking and tomography

**P9. Efficient measurement of quantum gate error by interleaved randomized benchmarking.** Magesan, Gambetta, Johnson, Ryan, Chow, Merkel, da Silva, Keefe, Rothwell, Ohki, Ketchen, Steffen. 2012, arXiv:1203.4550. URL: https://arxiv.org/abs/1203.4550
Interleaves random Cliffords with the gate under test to get a bounded estimate of its average error, robust to SPAM and scalable in qubit number. Compared against process tomography on superconducting qubits.
GhostQPU: IRB of CZ is the cheapest well-understood two-qubit probe. Its decay is exponential, which a depolarizing Forger reproduces by construction, so IRB alone will not separate Genuine from Forged. Its value is as a calibration-consistency check, not a coherent-error detector.

**P10. Characterizing large-scale quantum computers via cycle benchmarking.** Erhard, Wallman, Postler, Meth, Stricker, Martinez, Schindler, Monz, Emerson, Blatt. 2019, arXiv:1902.08543. URL: https://arxiv.org/abs/1902.08543
Introduces cycle benchmarking to characterize local and global errors, including crosstalk and correlated noise, across multi-qubit processors. Demonstrated on an ion trap with up to 10 qubits; entangling-gate process fidelity 99.6(1)% for 2 qubits to 86(2)% for 10.
GhostQPU: its Pauli-fidelity-per-cycle structure is a natural way to read out correlated (ZZ-type) error in a 2-qubit cycle, giving a few numbers instead of a full curve.

**P11. Demonstration of qubit operations below a rigorous fault tolerance threshold with gate set tomography.** Blume-Kohout, Gamble, Nielsen, Rudinger, Mizrahi, Fortier, Maunz. 2016, arXiv:1605.07674 (Nat. Commun. 8, 2017). URL: https://arxiv.org/abs/1605.07674
Argues RB does not capture all error types and cannot be compared directly to fault-tolerance thresholds. Uses gate set tomography on a trapped-ion qubit to certify diamond-norm error below 6.7e-4 with over 95% confidence.
GhostQPU: motivates the claim that RB-style averages hide coherent structure, which is exactly the structure a calibration-based Forger omits.

**P12. Gate Set Tomography.** Nielsen, Gamble, Rudinger, Scholten, Young, Blume-Kohout. 2020, arXiv:2009.07301 (Quantum 5, 557, 2021). URL: https://arxiv.org/abs/2009.07301
Describes GST, a calibration-free, self-consistent protocol characterizing all gates, states and measurements together, with Heisenberg-scaling precision for long sequences. Covers gauge fixing, error bars and the pyGSTi software.
GhostQPU: full two-qubit GST gives a Forger-independent model of the real CZ (a 16x16 process matrix) but costs many circuits. A reduced version (GST-style germs of only the CZ) is a candidate heavy canary; full 2Q GST is likely too expensive for a per-job check.

### 2.5 Verification of quantum execution, quantumness and spoofing

**P13. Quantum supremacy using a programmable superconducting processor (arXiv listing is the supplementary information).** Arute et al. (Google AI Quantum and collaborators). 2019, arXiv:1910.11333. URL: https://arxiv.org/abs/1910.11333
The arXiv entry is the supplement to the Nature paper; the page text I read describes it as such and lists v2 additions (qFlex code link, erratum, a figure on statistical versus total uncertainty for log and linear XEB). I did not read the supplement body, so the details of XEB below come from P14 and background knowledge, not from this fetch.
GhostQPU: the origin of cross-entropy benchmarking with random circuits containing entangling gates. XEB at small width is classically simulable, so it proves the data matches the circuit, not that a QPU produced it.

**P14. On the Classical Hardness of Spoofing Linear Cross-Entropy Benchmarking.** Aaronson, Gunn. 2019, arXiv:1910.12085. URL: https://arxiv.org/abs/1910.12085
Proves conditional hardness of spoofing linear XEB, including for noisy circuits: spoofing is hard if no efficient classical algorithm estimates the probability of a specific output string with lower variance than guessing 1/2^n.
GhostQPU: the spoofing hardness is a large-n statement. For 2 to 4 qubit canaries, a Forger can compute exact ideal probabilities, so XEB per se is not a hardness-based defense at our scale. What matters is the difference between real noise and modeled noise, not computational hardness.

**P15. Classical Verification of Quantum Computations.** Mahadev. 2018, arXiv:1804.01082. URL: https://arxiv.org/abs/1804.01082
A protocol for a classical verifier to check the output of a quantum computation through interaction, treating the prover as a measurement device, secure assuming Learning With Errors is hard for quantum computers.
GhostQPU: gold standard for cryptographic verification but requires interactive rounds and circuits far beyond current NISQ hardware (as far as I know; the abstract does not discuss resource counts). Not usable for a per-job check today. Our statistical, physics-based test is a pragmatic complement.

**P16. A Cryptographic Test of Quantumness and Certifiable Randomness from a Single Quantum Device.** Brakerski, Christiano, Mahadev, Vazirani, Vidick. 2018, arXiv:1804.00640. URL: https://arxiv.org/abs/1804.00640
Two protocols between a classical verifier and a single quantum device: one verifies the device is quantum, one certifies randomness, both from trapdoor claw-free functions with an adaptive hardcore bit built from LWE.
GhostQPU: the cryptographic version of our question (was a quantum device used). Differs in threat model: here the prover is computationally bounded, whereas our Forger has unlimited classical simulation at small scale but lacks private hardware physics. Worth citing as the "theory-ideal" contrast.

**P17. Verification of quantum computation: An overview of existing approaches.** Gheorghiu, Kapourniotis, Kashefi. 2017, arXiv:1709.06984. URL: https://arxiv.org/abs/1709.06984
Reviews verification approaches, comparing structure, complexity and resources, including cryptographic techniques, fault tolerance and experimental implementations.
GhostQPU: gives the taxonomy for the write-up; GhostQPU falls in the "heuristic / device-characterization" branch, not the interactive-proof branch.

### 2.6 Device fingerprinting and fraud detection

**P18. Learning the noise fingerprint of quantum devices.** Martina, Buffoni, Gherardini, Caruso. 2021, arXiv:2109.11405 (Quantum Machine Intelligence 4, 8, 2022). URL: https://arxiv.org/abs/2109.11405
Characterizes the noise fingerprint of IBM cloud quantum computers and classifies noise distributions from time-ordered sequences of measured outcome probabilities using machine learning. Notes noise features depend on the platform and can change over time.
GhostQPU: supports using shot-ordered data (as our drift features do) and ML classifiers. Their question (which device) differs from ours (device versus simulator), which CONTEXT.md already notes under "Signature".

**P19. Detecting Fraudulent Services on Quantum Cloud Platforms via Dynamic Fingerprinting.** Wu, Hu, Li. 2024, arXiv:2408.11203. URL: https://arxiv.org/abs/2408.11203
Targets machine substitution and profile fabrication by cloud providers. A single probing circuit captures device error characteristics, and the user compares the provider's fingerprint to a user-side prediction computed with a linear-complexity estimate. Tested on seven IBM devices.
GhostQPU: the closest published prior work on cloud-provider fraud. As far as the abstract says, it addresses substituting a different device or fabricating a profile, not full classical simulation from calibration data; I have not read the full text to confirm whether simulation is in its threat model.

### 2.7 Fidelity of noise models: drift, TLS, non-Markovianity

**P20. Fluctuations of Energy-Relaxation Times in Superconducting Qubits.** Klimov et al. (Google). 2018, arXiv:1809.01043 (PRL 121, 090502). URL: https://arxiv.org/abs/1809.01043
Uses qubits as spectral and temporal probes of individual two-level-system defects, giving direct evidence that TLS cause the largest T1 fluctuations, which drift unpredictably in frequency and time.
GhostQPU: calibration snapshots are taken at one instant; TLS-driven T1 drift makes hardware deviate from them, which a snapshot-based Forger cannot reproduce and which our drift features already exploit.

**P21. Detecting and tracking drift in quantum information processors.** Proctor, Revelle, Nielsen, Rudinger, Lobser, Maunz, Blume-Kohout, Young. 2019, arXiv:1907.13608 (Nat. Commun. 11, 5396, 2020). URL: https://arxiv.org/abs/1907.13608
Presents a spectral-analysis method that detects time dependence from any time-series experiment data, demonstrated on trapped-ion RB, GST and Ramsey data, including localizing and suppressing an instability.
GhostQPU: a principled replacement for our lag-1 and block-dispersion drift features (a power-spectrum test per canary), applicable to two-qubit correlators as well.

**P22. Measuring the Capabilities of Quantum Computers.** Proctor, Rudinger, Young, Nielsen, Blume-Kohout. 2020, arXiv:2008.11294 (Nature Physics, 2022). URL: https://arxiv.org/abs/2008.11294
Tests twelve processors and finds hardware errors are complex, so structured programs fail at much smaller sizes than random ones, and error metrics from random programs do not predict performance on structured programs.
GhostQPU: direct evidence that depolarizing-style noise models mispredict structured circuits. Structured two-qubit circuits (mirror, GHZ-like, repeated-gate) are therefore good canary candidates.

### 2.8 Not verified (left out of the main list)

- Smith et al., calibration-based fingerprinting of 25 IBM transmon machines (ACM). Seen only as a search-result snippet; the publisher page (par.nsf.gov/servlets/purl/10493755) could not be fetched. Not summarized.
- Wu, Hu, Li journal version (QuanGuard, IEEE Trans. Computers, 2026): known only from a search snippet.
- A student thesis claiming ML separates QPUs from simulators at over 99.9%: snippet only (https://www.insec.cit.tum.de/i20/student-work/approximate-quantumness-certification-of-nisq-devices-using-machine-learning), not a paper, not verified.
- Qiskit Aer docs do not explicitly list "no crosstalk, no coherent error, no correlated readout" as exclusions. Section 1 inference is from what the docs list as included.

## 3. Verdict

**Partially yes.** GhostQPU can be extended with canaries that use native CZ gates and entangled states, and the literature supports that CZ-level coherent errors, ZZ coupling, correlated readout, leakage and TLS-driven drift all exist on IBM hardware and are absent from a stock calibration-built Aer model. But "genuine two-qubit system" should be read as "two-qubit canary families added to the existing detector", not a new architecture, and the gain is in robustness against a smarter Forger, not necessarily in AUC on the current (already 1.00) data.

### 3.1 Feasible two-qubit canary families

1. **CZ error amplification (HEAT-style, from P5, P6, P8).** Repeat CZ N times (N even, so the ideal is identity or a known Clifford, check that CZ^2 = I) with a prepared state such as |+>|+> or |+>|1>, measure in a basis that turns a chosen error into population (for example H on the target before measure to read ZZ or IZ phase). Features: curvature and rise vs N, as in the existing coherent family. The Forger's depolarizing CZ gives a linear, symmetric curve; a coherent over-rotation or conditional phase gives a quadratic bend and an asymmetric, state-dependent shift. Include a leakage-sensitive variant (P8): large N, watch population loss.
2. **Entangling-gate ZZ Ramsey / echo.** Ramsey on the target with the neighbor in |0> versus |1>, but with a CZ inserted (or CZ-conjugated) so the conditional phase from the gate itself, plus the static ZZ during the idle, is measured. A two-qubit echo (X on one qubit midway) separates static ZZ from gate-induced phase. Extends the current spectator family; the neighbor is already a coupled qubit.
3. **Bell-state correlated readout (P1, P7).** Prepare Bell/GHZ-like states via H plus CZ (native on these chips, with single-qubit gates around CZ), and prepare the four computational states. Feature: joint outcome table versus the product of single-qubit marginals, and P(01) versus P(10) asymmetry. Single-qubit-only readout models (Aer's) give a product structure; correlated readout and crosstalk during simultaneous measurement break it. Cheap: a handful of circuits.
4. **Simultaneous-gate crosstalk (P2, P1).** Run gates on two adjacent pairs simultaneously versus alone and compare the target pair's fidelity, using the conditional-independence test of P1. This means relaxing `choose_placements`, which currently blocks neighbors of chosen pairs, to deliberately include nearby pairs.
5. **XEB-style structured circuits (P13, P14, P22).** Shallow random or mirror two-qubit circuits with known ideal output; compare to the Forger's prediction. At 2 to 4 qubits this is only a noise-model-accuracy test, not a hardness test (P14), so rank it below families 1 to 3 unless the width is raised.
6. **Reduced interleaved RB or cycle benchmarking of CZ (P9, P10).** Useful as a consistency check against published CZ error, probably weak as a discriminator because decay is near exponential. A cycle-benchmarking-style per-Pauli fidelity is more informative than plain IRB.

Not recommended for a per-job check: full two-qubit GST (P12) and Mahadev/BCMVV-style interactive proofs (P15, P16), because of circuit count and hardware requirements.

### 3.2 What the Forger would need to model to evade them

- Coherent CZ errors: unitary over-rotation and conditional-phase errors per edge (for example a fitted `ZZ(theta)` or `RZ` residual on each CZ), which Aer supports as custom unitary errors, but the parameters are not in the public calibration and would have to be fitted from hardware data or estimated from IBM's own characterization.
- Static ZZ and its idle dependence, per edge, plus simultaneous-gate crosstalk (P2 shows a method to build such a model from RB data on IBM chips).
- Correlated, context-dependent readout (P7's correlated Markovian model is the obvious Forger upgrade).
- Leakage and seepage during repeated CZ (P8).
- Time-varying T1 and frequency from TLS defects and drift (P20, P21).
- Practical point: every added effect needs hardware data the Forger does not get from the public snapshot. A Forger who collects its own small amount of real QPU data to fit these terms becomes a stronger adversary, and GhostQPU should say so (the existing README line "if the Detector can't separate them, that is a result too" already covers this honestly). The two-qubit canaries raise the number of parameters the Forger must fit (per edge, per context), which raises its cost but does not make evasion impossible.

### 3.3 Risks

- **QPU cost.** A Batch today is 34 circuits x 1000 shots = 11 QPU seconds (README.md). CZ-amplification sweeps are cheap per circuit (CZ about tens of ns on Heron, but unverified here, check backend properties), so 20 to 40 extra circuits is likely a modest increase; measure it before committing, as the README advises for shots.
- **Connectivity and placement.** `choose_placements` picks pairs with CZ error under 2% and blocks neighbors. Two-qubit canaries need the same edge to be good for both CZ and readout, and simultaneous-gate tests need nearby edges; fewer placements may qualify. Heavy-hex (older) versus square-lattice (Heron) connectivity differ.
- **Transpilation.** The batch is built with `optimization_level=0` and barriers. Repeated CZ pairs must stay uncancelled: keep barriers between repeats, verify in the compiled ISA circuit that CZ count equals N, and watch for the scheduler inserting dynamical decoupling or twirling that changes the effective noise (dynamical decoupling and Pauli twirling behavior on the chosen runtime primitive should be checked in IBM docs, I did not verify the current defaults).
- **Calibration drift.** Coherent CZ parameters drift between calibration cycles, so absolute thresholds will not transfer across days; features should be self-referential (curve shape, asymmetry, correlation structure, cross-context differences), as the current ones are.
- **Overfitting and the null test.** More features on 2 genuine runs risks overfitting. Keep the null test (simulator on both sides, AUC near 0.5) as a gate for every new family, and keep holding out whole calibration cycles.
- **Scientific honesty.** The current AUC is already 1.00, so improvement is unmeasurable on present data; value shows only against a stronger Forger.

### 3.4 Suggested first experiments

1. **Offline, no QPU time.** Add a CZ-amplification family and a Bell-correlation family to `canaries.py` behind a flag, compile on the snapshot simulator, assert CZ counts and barriers survive transpilation, and confirm the null test still passes (AUC near 0.5) with the new features.
2. **Strengthened Forger, offline.** Build a "Forger v2" with a fitted coherent CZ error, static ZZ, and a correlated readout matrix (P2, P7 style) so you can test whether the existing 12 features and the new two-qubit features still separate it from hardware once you have hardware data. This is the experiment that tells you whether the extension is worth it.
3. **One short hardware job.** On one backend and 2 to 4 placements, run: CZ^N for N in (0, 2, 4, 8, 16, 32, 64) on two initial states, four-state readout correlation, and Bell-state correlation. Expect roughly 1 to 3 extra QPU seconds per 10 circuits at 1000 shots, but read the actual billed seconds from `collect` before scaling. Compare the genuine curves to the existing Forger's: if coherent CZ bending and joint-readout correlation already exceed the Forger's by a clear margin, the family is promising.
4. **Cross-cycle repeat.** Run the same batch on a different day to see whether the new features' sign and shape persist across calibration cycles (the README notes cross-day results are still outstanding even for current features).
5. **Optional.** Replace the lag-1 and dispersion drift features with the spectral test from P21, and add the P1 conditional-independence statistic as a crosstalk feature, then compare feature importances in the Detector.
