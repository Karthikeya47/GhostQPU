"""Signatures: features of a Run's Canary Shot records that a gate-local simulator gets wrong.

Clbit 2i is placement i's target qubit and 2i+1 its neighbor (see canaries.py). Every
feature is averaged over placements.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ghostqpu.runs import Run

DRIFT_BLOCKS = 10


def signatures(run: Run, n_chunks: int = 1) -> list[dict[str, float]]:
    """One Signature per contiguous, time-ordered chunk of the Run's shots."""
    n_shots = run.shots[0].shape[0]
    edges = np.linspace(0, n_shots, n_chunks + 1).astype(int)
    return [_signature(run, slice(a, b)) for a, b in zip(edges[:-1], edges[1:], strict=True)]


def canary_curves(run: Run) -> dict[str, pd.DataFrame]:
    """Tidy per-Canary measurements for plotting, averaged over placements."""
    coherent = pd.DataFrame([
        {"variant": "sx sandwich" if s.params["sandwich"] else "plain", "n": s.params["n"],
         "p1": float(_p1_targets(run.shots[i]).mean())}
        for i, s in run.batch.canaries("coherent")
    ])
    spec = {
        (s.params["neighbor"], s.params["delay_us"]): _p1_targets(run.shots[i])
        for i, s in run.batch.canaries("spectator")
    }
    spectator = pd.DataFrame([
        {"delay_us": d, "shift": float(np.mean(np.abs(spec[(1, d)] - spec[(0, d)])))}
        for d in sorted({d for _, d in spec})
    ])
    readout = pd.DataFrame([
        {"target": s.params["target"], "neighbor": s.params["neighbor"],
         "error": float(np.mean(_readout_error(run.shots[i], s.params["target"])))}
        for i, s in run.batch.canaries("readout")
    ])
    return {"coherent": coherent, "spectator": spectator, "readout": readout}


def _signature(run: Run, rows: slice) -> dict[str, float]:
    bits = [s[rows] for s in run.shots]
    features: dict[str, float] = {}
    features.update(_coherent(run, bits))
    features.update(_spectator(run, bits))
    features.update(_readout(run, bits))
    features.update(_drift(run, bits))
    return features


def _p1_targets(b: np.ndarray) -> np.ndarray:
    """P(1) on each placement's target qubit."""
    return b[:, 0::2].mean(axis=0)


def _readout_error(b: np.ndarray, prepared: int) -> np.ndarray:
    """P(read the wrong value) on each placement's target qubit."""
    p1 = _p1_targets(b)
    return p1 if prepared == 0 else 1 - p1


def _coherent(run: Run, bits) -> dict[str, float]:
    out = {}
    for sandwich, name in ((False, "plain"), (True, "sx")):
        curve = sorted(
            (s.params["n"], _p1_targets(bits[i]))
            for i, s in run.batch.canaries("coherent")
            if s.params["sandwich"] == sandwich
        )
        n = np.array([c[0] for c in curve], dtype=float)
        p = np.array([c[1] for c in curve])  # (len(n), placements)
        half = int(np.argmin(abs(n - n[-1] / 2)))
        # Linear error growth gives zero curvature. Coherent over-rotation bends the curve.
        curvature = (p[-1] - p[half]) - (p[half] - p[0])
        slope, intercept = np.polyfit(n, p, 1)
        residual = p - (np.outer(n, slope) + intercept)
        out[f"coh_{name}_rise"] = float(np.mean(p[-1] - p[0]))
        out[f"coh_{name}_curvature"] = float(np.mean(curvature))
        out[f"coh_{name}_nonlinearity"] = float(np.mean(np.sqrt((residual**2).mean(axis=0))))
    return out


def _spectator(run: Run, bits) -> dict[str, float]:
    by_key = {
        (s.params["neighbor"], s.params["delay_us"]): _p1_targets(bits[i])
        for i, s in run.batch.canaries("spectator")
    }
    delays = sorted({d for _, d in by_key if d > 0})
    shifts = np.array([by_key[(1, d)] - by_key[(0, d)] for d in delays])  # (delays, placements)
    return {
        "spec_shift_mean_abs": float(np.mean(np.abs(shifts))),
        "spec_shift_max_abs": float(np.mean(np.max(np.abs(shifts), axis=0))),
    }


def _readout(run: Run, bits) -> dict[str, float]:
    p1 = {(s.params["target"], s.params["neighbor"]): _p1_targets(bits[i]) for i, s in run.batch.canaries("readout")}
    err0 = {n: p1[(0, n)] for n in (0, 1)}  # P(read 1 | target 0)
    err1 = {n: 1 - p1[(1, n)] for n in (0, 1)}  # P(read 0 | target 1)
    context = np.abs(err0[1] - err0[0]) + np.abs(err1[1] - err1[0])

    published = np.array([run.snapshot.readout_errors(t) for t, _ in run.batch.placements])
    vs_calibration = np.abs(err0[0] - published[:, 0]) + np.abs(err1[0] - published[:, 1])
    return {
        "ro_context_shift": float(np.mean(context)),
        "ro_vs_calibration": float(np.mean(vs_calibration)),
    }


def _drift(run: Run, bits) -> dict[str, float]:
    """Hardware drifts during a job; simulated shots are independent and identically distributed."""
    lag1, dispersion = [], []
    for i, _ in [(i, s) for i, s in enumerate(run.batch.specs) if s.role == "canary"]:
        for col in bits[i].T.astype(float):
            p = col.mean()
            if not 0.05 < p < 0.95 or len(col) < 4 * DRIFT_BLOCKS:
                continue
            centered = col - p
            lag1.append((centered[:-1] * centered[1:]).mean() / centered.var())
            blocks = np.array_split(col, DRIFT_BLOCKS)
            block_var = np.var([b.mean() for b in blocks], ddof=1)
            dispersion.append(block_var / (p * (1 - p) / np.mean([len(b) for b in blocks])))
    return {
        "drift_lag1": float(np.mean(lag1)) if lag1 else 0.0,
        "drift_dispersion": float(np.mean(dispersion)) if dispersion else 1.0,
    }
