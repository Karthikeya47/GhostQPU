"""GhostQPU demo. Run with: streamlit run app.py"""

from __future__ import annotations

import zlib

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from ghostqpu.cli import RUNS, STAND_IN
from ghostqpu.detector import dataset, evaluate
from ghostqpu.runs import FORGED, GENUINE, load_runs
from ghostqpu.signature import canary_curves

ORIGIN_COLORS = alt.Scale(domain=["Genuine", "Forged"], range=["#2a78d6", "#eb6834"])
GOOD, CRITICAL = "#0ca30c", "#d03b3b"
INK_SECONDARY, INK_MUTED, GRID, AXIS = "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
CHUNKS = 8
INCONCLUSIVE = 0.35  # forged scores within 0.35..0.65 get no verdict
FEATURE_LABELS = {
    "coh_plain_rise": "Coherent: total rise",
    "coh_plain_curvature": "Coherent: curvature",
    "coh_plain_nonlinearity": "Coherent: non-linearity",
    "coh_sx_rise": "Coherent (sx): total rise",
    "coh_sx_curvature": "Coherent (sx): curvature",
    "coh_sx_nonlinearity": "Coherent (sx): non-linearity",
    "spec_shift_mean_abs": "Spectator: mean shift",
    "spec_shift_max_abs": "Spectator: max shift",
    "ro_context_shift": "Readout: neighbor context",
    "ro_vs_calibration": "Readout: drift from calibration",
    "drift_lag1": "Shot order: lag-1 correlation",
    "drift_dispersion": "Shot order: drift over time",
}

st.set_page_config(page_title="GhostQPU", page_icon="👻", layout="wide")


def style(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_axis(gridColor=GRID, domainColor=AXIS, tickColor=AXIS, labelColor=INK_MUTED,
                             titleColor=INK_MUTED, titleFontWeight="normal", labelFontSize=12)
        .configure_legend(orient="top", title=None, labelFontSize=12, symbolStrokeWidth=2)
        .configure_view(strokeWidth=0)
    )


@st.cache_data(show_spinner="Reading runs and scoring them...")
def load(source: str, _stamp: float):
    runs = load_runs(RUNS if source == "hardware" else STAND_IN)
    df = dataset(runs, CHUNKS) if runs else pd.DataFrame()
    report = None
    if not df.empty and df["pair"].nunique() >= 2:
        report = evaluate(df)
    return runs, df, report


def folder_stamp(source: str) -> float:
    root = RUNS if source == "hardware" else STAND_IN
    return max((p.stat().st_mtime for p in root.glob("*/run.json")), default=0.0) if root.exists() else 0.0


st.title("👻 GhostQPU")
st.markdown("**Did your quantum job ever touch a quantum computer?** Canaries hidden in your batch "
            "catch results that were simulated from IBM's public calibration data.")

SOURCES = {"hardware": "IBM hardware runs", "stand_in": "Local stand-ins (null test)"}
with st.sidebar:
    initial = st.query_params.get("data", "hardware")
    source = st.radio("Data", list(SOURCES), format_func=SOURCES.get,
                      index=list(SOURCES).index(initial) if initial in SOURCES else 0)
    st.query_params["data"] = source
    if source == "stand_in":
        st.info("Stand-ins are simulated on both sides. The Detector **should fail** here; "
                "that is the null test that proves we detect physics, not formatting.")

runs, df, report = load(source, folder_stamp(source))
if not runs:
    st.warning("No runs yet. Submit with `python -m ghostqpu submit ...`, then `python -m ghostqpu collect`. "
               "For stand-ins: `python -m ghostqpu null-test`.")
    st.stop()

by_id = {r.run_id: r for r in runs}
genuine_runs = [r for r in runs if r.origin == GENUINE]
verify, evidence, detector = st.tabs(["Verify a job", "Evidence", "Detector"])

with verify:
    if report is None:
        st.warning("Need at least two Genuine/Forged pairs before the Detector can score anything.")
    else:
        held_out = report.predictions.groupby("run_id")["forged_score"].mean()
        order = sorted(held_out.index, key=lambda rid: zlib.crc32(rid.encode()))
        labels = {f"Job {k + 1:02d}  ({by_id[rid].batch.backend_name})": rid for k, rid in enumerate(order)}
        st.caption("Each job's score comes from a Detector that never saw that job or its twin.")
        choice = st.selectbox("Pick a job you received from your provider", list(labels))
        rid = labels[choice]
        score = float(held_out[rid])
        run = by_id[rid]

        left, right = st.columns([1, 2])
        with left:
            if score >= 1 - INCONCLUSIVE:
                st.markdown(f"<h2 style='color:{CRITICAL};margin:0'>⚠ Forged</h2>", unsafe_allow_html=True)
                st.markdown("These results look like they came from a **classical simulator**.")
            elif score <= INCONCLUSIVE:
                st.markdown(f"<h2 style='color:{GOOD};margin:0'>✔ Genuine</h2>", unsafe_allow_html=True)
                st.markdown("These results carry **hardware effects** a calibration-based simulator lacks.")
            else:
                st.markdown(f"<h2 style='color:{INK_SECONDARY};margin:0'>◐ Inconclusive</h2>", unsafe_allow_html=True)
                st.markdown("The canaries can't tell this job apart from a simulator's output.")
            st.metric("Forged score", f"{score:.2f}", help="Mean held-out probability over time chunks of the job")
            st.caption(f"{len(run.batch.circuits)} circuits x {run.info['shots']} shots · "
                       f"{sum(s.role == 'canary' for s in run.batch.specs)} hidden canaries")
        with right:
            chunks = report.predictions[report.predictions["run_id"] == rid]
            bar = alt.Chart(chunks).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=INK_MUTED).encode(
                x=alt.X("chunk:O", title="time-ordered chunk of the job", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("forged_score:Q", title="forged score", scale=alt.Scale(domain=[0, 1])),
                tooltip=[alt.Tooltip("chunk:O"), alt.Tooltip("forged_score:Q", format=".2f")],
            )
            rule = alt.Chart(pd.DataFrame({"y": [0.5]})).mark_rule(color=AXIS).encode(y="y:Q")
            st.altair_chart(style((bar + rule).properties(height=220)), width="stretch")
        with st.expander("Reveal the truth"):
            if run.origin == FORGED:
                truth = "Forged by the calibration-matched simulator"
            elif run.info.get("stand_in"):
                truth = "Local stand-in for hardware (also a simulator, so no verdict should be confident)"
            else:
                truth = "Executed on IBM hardware"
            st.write(f"**{truth}.** Run id `{rid}`.")

with evidence:
    if not genuine_runs:
        st.info("No Genuine runs to show.")
    else:
        rid = st.selectbox("Genuine run", [r.run_id for r in genuine_runs])
        genuine = by_id[rid]
        twin = by_id.get(f"{rid}_forged")
        st.caption(f"Calibration cycle {genuine.snapshot.cycle} · placements {genuine.batch.placements}. "
                   "The Twin is the Forger's output for the exact same circuits and calibration.")

        def tidy(name: str) -> pd.DataFrame:
            parts = [canary_curves(genuine)[name].assign(origin="Genuine")]
            if twin is not None:
                parts.append(canary_curves(twin)[name].assign(origin="Forged"))
            return pd.concat(parts, ignore_index=True)

        color = alt.Color("origin:N", scale=ORIGIN_COLORS, title=None)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("Coherent amplification")
            st.caption("P(1) after N X gates (ideal: 0). Over-rotations bend the hardware curve.")
            data = tidy("coherent").query("variant == 'plain'")
            chart = alt.Chart(data).mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=64, filled=True)).encode(
                x=alt.X("n:Q", title="X gates (N)"), y=alt.Y("p1:Q", title="P(1)"), color=color,
                tooltip=["origin", "n", alt.Tooltip("p1:Q", format=".3f")],
            ).properties(height=300)
            st.altair_chart(style(chart), width="stretch")
        with c2:
            st.subheader("Spectator crosstalk")
            st.caption("|Change in the idle qubit| when its neighbor flips 0 to 1. Gate-local models say 0.")
            data = tidy("spectator")
            chart = alt.Chart(data).mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=64, filled=True)).encode(
                x=alt.X("delay_us:Q", title="idle time (µs)"), y=alt.Y("shift:Q", title="shift in P(1)"), color=color,
                tooltip=["origin", "delay_us", alt.Tooltip("shift:Q", format=".3f")],
            ).properties(height=300)
            st.altair_chart(style(chart), width="stretch")
        with c3:
            st.subheader("Readout in context")
            st.caption("Readout error of the target qubit, by what the neighbor holds.")
            data = tidy("readout").assign(prepared=lambda d: "target prepared " + d["target"].astype(str))
            chart = alt.Chart(data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("neighbor:O", title="neighbor state", axis=alt.Axis(labelAngle=0)),
                xOffset=alt.XOffset("origin:N", scale=alt.Scale(paddingInner=0.1)),
                y=alt.Y("error:Q", title="readout error", axis=alt.Axis(tickCount=5)), color=color,
                column=alt.Column("prepared:N", title=None),
                tooltip=["origin", "target", "neighbor", alt.Tooltip("error:Q", format=".4f")],
            ).properties(height=300, width=110)
            st.altair_chart(style(chart))
        with st.expander("Table view"):
            st.dataframe(pd.concat({k: tidy(k) for k in ("coherent", "spectator", "readout")}), width="stretch")

with detector:
    if report is None:
        st.warning("Need at least two Genuine/Forged pairs.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("AUC (held out)", f"{report.auc:.2f}", help="0.5 is a coin flip, 1.0 is perfect")
        m2.metric("Job-level accuracy", f"{report.run_accuracy:.0%}")
        m3.metric("Genuine/Forged pairs", report.n_pairs)
        st.caption(f"Held-out split: {report.split}. Logistic regression on {CHUNKS} time chunks per job.")
        weights = report.weights.rename("weight").reset_index().rename(columns={"index": "feature"})
        weights["points to"] = np.where(weights["weight"] > 0, "Forged", "Genuine")
        weights["feature"] = weights["feature"].map(lambda f: FEATURE_LABELS.get(f, f))
        chart = alt.Chart(weights).mark_bar(cornerRadiusEnd=4, size=14).encode(
            y=alt.Y("feature:N", sort=None, title=None, axis=alt.Axis(labelLimit=260, labelColor=INK_SECONDARY)),
            x=alt.X("weight:Q", title="standardized weight", axis=alt.Axis(tickCount=6)),
            color=alt.Color("points to:N", scale=ORIGIN_COLORS, title="A higher value points to"),
            tooltip=["feature", alt.Tooltip("weight:Q", format="+.3f"), "points to"],
        ).properties(height=alt.Step(26))  # fixed row height; Vega notes it drops "fit-y", which is intended
        st.altair_chart(style(chart), width="stretch")
        if (weights["points to"] == "Genuine").all():
            st.caption("Every bar points to Genuine: each effect is larger on real hardware than in the Forger, "
                       "so a job that lacks them looks forged.")
        per_run = report.predictions.groupby("run_id").agg(
            origin=("origin", "first"), cycle=("cycle", "first"), forged_score=("forged_score", "mean"))
        st.dataframe(per_run.style.format({"forged_score": "{:.2f}"}), width="stretch")
