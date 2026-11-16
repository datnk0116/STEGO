from pathlib import Path
import sys

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from visualization.utils import (  # noqa: E402
    SLEEPY_REFERENCE_PATH,
    SLEEPY_TARGET_PATH,
    audio_metadata,
    read_waveform,
    run_sleepy_alarm,
)

st.title("Sleepy Alarm · Audio extraction")
st.caption("Waveforms are sampled only for display. Both decoder runs receive the original full-resolution audio files.")

with st.spinner("Running reference-assisted and reference-free decoders…"):
    assisted = run_sleepy_alarm(SLEEPY_TARGET_PATH, SLEEPY_REFERENCE_PATH)
    reference_free = run_sleepy_alarm(SLEEPY_TARGET_PATH)


def show_audio_info(label: str, path: Path) -> dict | None:
    st.markdown(f"**{label}**")
    try:
        info = audio_metadata(path)
    except Exception as exc:
        st.error(f"Unavailable: {type(exc).__name__}: {exc}")
        return None
    columns = st.columns(3)
    columns[0].metric("Sample rate", f"{info['sample_rate']:,} Hz")
    columns[1].metric("Channels", str(info["channels"]))
    columns[2].metric("Duration", f"{info['duration_seconds']:.3f} s")
    columns = st.columns(2)
    columns[0].metric("Samples per channel (frames)", f"{info['samples_per_channel']:,}")
    columns[1].metric("Total samples across channels", f"{info['total_samples']:,}")
    return info


st.subheader("Audio files")
target_info = show_audio_info("Target audio · morning_n_breakfast.mp3", SLEEPY_TARGET_PATH)
reference_info = show_audio_info("Reference audio · morning_n_breakfast_original.mp3", SLEEPY_REFERENCE_PATH)

waveforms: list[tuple[str, np.ndarray, np.ndarray]] = []
for label, path, info in (
    ("Target", SLEEPY_TARGET_PATH, target_info),
    ("Reference", SLEEPY_REFERENCE_PATH, reference_info),
):
    if info is None:
        continue
    try:
        seconds, samples = read_waveform(path)
        waveforms.append((label, seconds, samples))
    except Exception as exc:
        st.error(f"Could not read {label.lower()} waveform: {type(exc).__name__}: {exc}")

if waveforms:
    st.subheader("Waveforms")
    st.caption("Each trace is a bounded sample of the source waveform, plotted in seconds and amplitude.")
    fig = make_subplots(
        rows=len(waveforms),
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.12,
        subplot_titles=[label for label, _, _ in waveforms],
    )
    for row, (label, seconds, samples) in enumerate(waveforms, start=1):
        for channel in range(samples.shape[1]):
            fig.add_trace(
                go.Scattergl(
                    x=seconds,
                    y=samples[:, channel],
                    mode="lines",
                    name=f"{label} · channel {channel + 1}",
                    line={"width": 0.8},
                ),
                row=row,
                col=1,
            )
        fig.update_yaxes(title_text="Amplitude", row=row, col=1)
    fig.update_xaxes(title_text="Time (seconds)", row=len(waveforms), col=1)
    fig.update_layout(
        height=300 * len(waveforms),
        hovermode="x unified",
        margin={"l": 20, "r": 20, "t": 45, "b": 20},
        legend_title="Audio channel",
    )
    st.plotly_chart(fig, width="stretch")


def show_decoder_mode(title: str, run: dict) -> None:
    with st.container(border=True):
        st.subheader(title)
        if run["status"] == "Success":
            st.success("Success — format_valid = true")
        else:
            st.error("Failed — decoder did not return a format-valid result")
        if run["error"]:
            st.caption(run["error"])
            return

        result = run["result"]
        st.markdown("**Decoded text**")
        st.code(result["decoded_text"] or "(empty)")
        first = st.columns(3)
        first[0].metric("format_valid", str(result["format_valid"]).lower())
        first[1].metric("reference_assisted", str(result["reference_assisted"]).lower())
        first[2].metric("Symbol count", f"{result['symbol_count']:,}")
        second = st.columns(3)
        second[0].metric("Separator count", f"{result['separator_count']:,}")
        second[1].metric("Byte errors", f"{len(result['errors']):,}")
        centers = result["amplitude_centers"]
        second[2].metric("Amplitude centers", str(len(centers)))
        st.code(", ".join(f"{value:.8g}" for value in centers), language=None)

        alignment = result["alignment"]
        st.markdown("**Alignment**")
        if alignment is None:
            st.caption("Not performed in reference-free mode.")
        else:
            align_cols = st.columns(3)
            align_cols[0].metric("Lag", f"{alignment['lag_samples']:,} samples")
            align_cols[1].metric("Correlation", f"{alignment['correlation']:.9f}")
            align_cols[2].metric("Target start", f"{alignment['target_start_sample']:,} samples")

        if result["errors"]:
            with st.expander("Malformed byte groups returned by the decoder"):
                st.dataframe(result["errors"], width="stretch", hide_index=True)
        else:
            st.caption("Byte errors: none")


st.subheader("Decoder results")
assisted_col, free_col = st.columns(2)
with assisted_col:
    show_decoder_mode("Reference-assisted", assisted)
with free_col:
    show_decoder_mode("Reference-free", reference_free)
