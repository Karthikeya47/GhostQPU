# GhostQPU

Detecting quantum cloud results that were produced by a classical simulator instead of the QPU the Customer paid for.

## Parties

**Customer**:
The party that pays for QPU time and receives results.
_Avoid_: user, buyer

**Provider**:
The party that accepts a Customer's Batch and returns Runs; it may be honest or a Forger.
_Avoid_: vendor, aggregator (when meaning the role)

**Forger**:
A Provider strategy that returns simulated Runs while billing for QPU time.
_Avoid_: attacker (too broad), fake backend (Qiskit's name for snapshot-based simulators)

## Executions

**Backend**:
A named IBM QPU, such as ibm_fez, ibm_kingston or ibm_torino.
_Avoid_: device, machine

**Batch**:
The ordered list of circuits a Customer submits together, with Canaries hidden among Workload circuits.
_Avoid_: job (IBM's name for the submission handle), payload

**Workload circuit**:
A circuit in a Batch whose results the Customer actually wants.
_Avoid_: user circuit, decoy

**Canary**:
A circuit with a known ideal outcome whose behavior on a Backend differs from what a gate-local noise model predicts.
_Avoid_: test circuit, probe, check

**Canary family**:
One of the kinds of Canary: coherent amplification, spectator, or readout context.

**Placement**:
The physical qubits a Canary is pinned to.
_Avoid_: layout (Qiskit's term for the full mapping)

**Run**:
The shot-by-shot outcome of executing one Batch, labeled with its Origin.
_Avoid_: result, job, execution

**Origin**:
Whether a Run is Genuine (executed on the Backend) or Forged (produced by a Forger).
_Avoid_: real/fake, hardware/sim

**Twin**:
The Forged Run produced from the same Batch and the same Calibration snapshot as a Genuine Run.

**Shot record**:
The ordered per-shot bitstrings for one circuit in a Run.
_Avoid_: memory, counts (counts discard order)

**QPU seconds**:
The quantum time IBM bills for a job.
_Avoid_: runtime, usage

## Calibration

**Calibration snapshot**:
A Backend's published properties and configuration as of one moment.
_Avoid_: props, calibration data

**Calibration cycle**:
The interval between two successive calibration updates of a Backend.

## Detection

**Signature**:
The feature vector computed from a Run's Canary Shot records.
_Avoid_: fingerprint (prior work uses it for identifying which device ran a job, a different question)

**Detector**:
The classifier that maps a Signature to a Verdict.

**Verdict**:
Genuine or Forged, with a score.
