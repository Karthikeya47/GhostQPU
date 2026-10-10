"""The Detector: logistic regression on Signatures, evaluated so no Run leaks into its own test."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from ghostqpu.runs import FORGED, GENUINE, Run
from ghostqpu.signature import signatures

META = ["run_id", "pair", "origin", "cycle", "backend", "chunk"]


@dataclass
class Report:
    split: str  # how train and test were separated
    auc: float  # chunk-level ROC AUC for "forged"
    run_accuracy: float  # Verdicts on whole Runs (mean chunk score > 0.5)
    n_pairs: int
    predictions: pd.DataFrame  # one row per held-out chunk, with its forged score
    weights: pd.Series  # standardized coefficients of a model fit on everything


@dataclass
class Verdict:
    label: str  # GENUINE or FORGED
    forged_score: float


def dataset(runs: list[Run], n_chunks: int = 8) -> pd.DataFrame:
    rows = []
    for run in runs:
        pair = run.info.get("twin_of", run.run_id)
        for k, features in enumerate(signatures(run, n_chunks)):
            rows.append({
                "run_id": run.run_id, "pair": pair, "origin": run.origin,
                "cycle": run.snapshot.cycle, "backend": run.batch.backend_name, "chunk": k,
                **features,
            })
    return pd.DataFrame(rows)


def features_of(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in META]


def train(df: pd.DataFrame) -> Pipeline:
    model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))
    return model.fit(df[features_of(df)], df["origin"] == FORGED)


def verdict(model: Pipeline, run: Run, n_chunks: int = 8) -> Verdict:
    df = dataset([run], n_chunks)
    score = float(model.predict_proba(df[features_of(df)])[:, 1].mean())
    return Verdict(FORGED if score > 0.5 else GENUINE, score)


def evaluate(df: pd.DataFrame) -> Report:
    """Hold out by Calibration cycle when there are several, otherwise by Genuine/Twin pair."""
    if df["cycle"].nunique() >= 2:
        split, groups = "by calibration cycle", df["cycle"]
    elif df["pair"].nunique() >= 2:
        split, groups = "by run pair", df["pair"]
    else:
        raise ValueError("need at least two Genuine/Forged pairs to evaluate")

    held_out = []
    for group in groups.unique():
        test = groups == group
        train_df = df[~test]
        if train_df["origin"].nunique() < 2:
            continue
        scores = train(train_df).predict_proba(df.loc[test, features_of(df)])[:, 1]
        held_out.append(df.loc[test, META].assign(forged_score=scores))
    predictions = pd.concat(held_out, ignore_index=True)

    truth = predictions["origin"] == FORGED
    per_run = predictions.groupby("run_id").agg(origin=("origin", "first"), score=("forged_score", "mean"))
    model = train(df)
    weights = pd.Series(model[-1].coef_[0], index=features_of(df)).sort_values(key=np.abs, ascending=False)
    return Report(
        split=split,
        auc=float(roc_auc_score(truth, predictions["forged_score"])),
        run_accuracy=float(((per_run["score"] > 0.5) == (per_run["origin"] == FORGED)).mean()),
        n_pairs=int(df["pair"].nunique()),
        predictions=predictions,
        weights=weights,
    )
