from pathlib import Path
import sys

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from visualization.utils import BLUE3_PATH, image_summary, run_blue3  # noqa: E402

st.title("Blue 3 · Image extraction")
st.caption("Image measurements and candidates come from the supplied image and the existing decode_blue3() implementation.")

run = run_blue3(BLUE3_PATH)
if run["status"] == "Success":
    st.success("Success — format_valid = true")
else:
    st.error("Failed — no format-valid candidate was returned")
if run["error"]:
    st.error(run["error"])

try:
    pixels, baseline, baseline_count = image_summary(BLUE3_PATH)
except Exception as exc:
    st.error(f"Could not read the challenge image: {type(exc).__name__}: {exc}")
    st.stop()

height, width, _ = pixels.shape
left, right = st.columns([1, 1])
with left:
    st.image(pixels, caption="data/blue3/blue.png", width="stretch")
with right:
    st.metric("Image size", f"{width} × {height} px")
    st.metric("Most common RGB baseline", str(baseline))
    st.caption(f"This color appears in {baseline_count:,} pixels. The baseline uses the same most-frequent RGB calculation as decode_blue3().")

st.subheader("RGB channel distribution")
st.caption("Histogram of pixel values in each channel (0–255); counts are shown per channel.")
fig = go.Figure()
for channel, name, color in ((0, "Red", "#d1495b"), (1, "Green", "#2a9d8f"), (2, "Blue", "#457b9d")):
    fig.add_trace(go.Histogram(x=pixels[:, :, channel].ravel(), name=name, nbinsx=256, opacity=0.58, marker_color=color))
fig.update_layout(
    barmode="overlay",
    xaxis_title="Channel value",
    yaxis_title="Pixel count",
    legend_title="RGB channel",
    margin={"l": 20, "r": 20, "t": 20, "b": 20},
    height=360,
)
st.plotly_chart(fig, width="stretch")

st.subheader("Decoder candidates")
if run["result"] is not None:
    result = run["result"]
    st.metric("format_valid", str(result["format_valid"]).lower())
    st.markdown("**Final candidate**")
    st.code(result["flag"] if result["flag"] is not None else "No valid candidate")
    st.caption("Candidate list returned directly by decode_blue3().")
    st.dataframe(result["attempts"], width="stretch", hide_index=True)
else:
    st.info("Candidate list is unavailable because the decoder could not complete.")
