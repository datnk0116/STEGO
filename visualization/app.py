from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from visualization.utils import (  # noqa: E402
    BLUE3_PATH,
    SLEEPY_REFERENCE_PATH,
    SLEEPY_TARGET_PATH,
    run_blue3,
    run_sleepy_alarm,
)

st.set_page_config(page_title="STEGO Challenge Visualizations", page_icon="🔎", layout="wide")
st.title("STEGO Challenge Visualizations")
st.caption("Decoder-backed views for Blue 3 and Sleepy Alarm. Status below comes from decoder runs against the repository's challenge files.")

with st.spinner("Running the challenge decoders…"):
    blue3_run = run_blue3(BLUE3_PATH)
    assisted_run = run_sleepy_alarm(SLEEPY_TARGET_PATH, SLEEPY_REFERENCE_PATH)
    blind_run = run_sleepy_alarm(SLEEPY_TARGET_PATH)


def show_run(title: str, run: dict) -> None:
    with st.container(border=True):
        st.subheader(title)
        if run["status"] == "Success":
            st.success("Success — decoder returned format_valid = true")
        else:
            st.error("Failed — decoder did not return a format-valid result")
        if run["error"]:
            st.caption(run["error"])
        elif run["result"] is not None:
            result = run["result"]
            output = result.get("flag", result.get("decoded_text"))
            if output is not None:
                st.code(output)
            st.caption(f"format_valid: {result.get('format_valid')}")


st.markdown("Two challenge decoders are available from the page navigation: image-domain extraction for **Blue 3** and audio-domain extraction for **Sleepy Alarm**.")
col1, col2, col3 = st.columns(3)
with col1:
    show_run("Blue 3", blue3_run)
with col2:
    show_run("Sleepy Alarm · reference-assisted", assisted_run)
with col3:
    show_run("Sleepy Alarm · reference-free", blind_run)

st.info("Reference-assisted Sleepy Alarm uses the original recording for alignment and subtraction. Reference-free mode omits it; the two outcomes are shown independently.")
