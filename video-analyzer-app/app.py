import streamlit as st
import tempfile
import os
import json
from pathlib import Path
import shutil
import sys

# ============================================================
# PROJECT IMPORTS
# ============================================================
current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from tests.orchestrator import run_pipelines  # ⬅️ Parallel orchestrator


# ============================================================
# CUSTOM PAGE STYLING
# ============================================================
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 42px;
        color: #2C3E50;
        font-weight: 700;
        margin-bottom: -10px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #7F8C8D;
        margin-bottom: 25px;
    }
    .stApp {
        background-color: #f7f9fb;
    }
</style>

<h1 class="main-title">🎥 VERA</h1>
<p class="subtitle">AI analysis across <b>audio</b>, <b>body language</b>, and <b>facial expression</b>.</p>
""", unsafe_allow_html=True)


# ============================================================
# PARALLEL PIPELINE EXECUTION
# ============================================================
def process_video(video_path):

    with st.status("🔄 Running pipelines in parallel...", expanded=True) as status:

        output_dir, results = run_pipelines(video_path)

        status.update(label="🎉 All pipelines complete!", state="complete")

    # Convert all produced files into a dictionary
    outputs = {}

    # Global file
    global_json_path = Path(output_dir) / "results_global.json"
    if global_json_path.exists():
        outputs["results_global.json"] = global_json_path.read_text()

    # Load audio / body / face outputs
    for module in ["audio", "body", "face"]:
        # JSON
        json_path = Path(output_dir) / f"results_{module}.json"
        if json_path.exists():
            outputs[f"results_{module}.json"] = json_path.read_text()

        # CSV
        csv_path = Path(output_dir) / f"metrics_{module}.csv"
        if csv_path.exists():
            outputs[f"metrics_{module}.csv"] = csv_path.read_text()

        # MP4 debug files
        mp4_path = Path(output_dir) / f"debug_{module}.mp4"
        if mp4_path.exists():
            outputs[f"debug_{module}.mp4"] = mp4_path.read_bytes()

    return outputs


# ============================================================
# SIDEBAR UPLOAD
# ============================================================
st.sidebar.header("📤 Upload Your Video")
uploaded_video = st.sidebar.file_uploader("Select a video file:", type=["mp4", "mov", "avi", "mkv"])


# ============================================================
# MAIN APP
# ============================================================
if uploaded_video is not None:

    st.write("### 📺 Uploaded Video Preview")
    st.video(uploaded_video)

    # Save video temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(uploaded_video.read())
        temp_video_path = tmp.name

    st.success("Video uploaded successfully. Ready to analyze! 🚀")

    # Run Pipelines
    if st.button("Start Analysis", type="primary"):

        results = process_video(temp_video_path)

        st.write("## 📊 Analysis Results")

        # ============================================================
        # SCORE CARDS
        # ============================================================
        st.write("### Global Scores Overview")
        score_cols = st.columns(3)

        # AUDIO SCORE
        if "results_audio.json" in results:
            audio_data = json.loads(results["results_audio.json"])
            if "audio_global_score" in audio_data:
                score_cols[0].metric("🎤 Audio Score", f"{audio_data['audio_global_score']:.2f}")

        # BODY SCORE
        if "results_body.json" in results:
            body_data = json.loads(results["results_body.json"])
            if "body_global_score" in body_data:
                score_cols[1].metric("🕺 Body Score", f"{body_data['body_global_score']:.2f}")

        # FACE SCORE
        if "results_face.json" in results:
            face_data = json.loads(results["results_face.json"])
            if "face_global_score" in face_data:
                score_cols[2].metric("🙂 Face Score", f"{face_data['face_global_score']:.2f}")


        # ============================================================
        # TABS (Audio / Body / Face)
        # ============================================================
        tab_audio, tab_body, tab_face = st.tabs(["🎧 Audio", "🕺 Body", "🙂 Face"])

        # ---------------- AUDIO TAB ----------------
        with tab_audio:
            st.header("🎧 Audio Analysis")

            if "results_audio.json" in results:
                with st.expander("📄 Audio JSON Output"):
                    st.json(json.loads(results["results_audio.json"]))
                st.download_button(
                    "Download results_audio.json",
                    data=results["results_audio.json"],
                    file_name="results_audio.json",
                    mime="application/json"
                )

            if "metrics_audio.csv" in results:
                st.download_button(
                    "Download metrics_audio.csv",
                    data=results["metrics_audio.csv"],
                    file_name="metrics_audio.csv",
                    mime="text/csv"
                )


        # ---------------- BODY TAB ----------------
        with tab_body:
            st.header("🕺 Body Analysis")

            if "results_body.json" in results:
                with st.expander("📄 Body JSON Output"):
                    st.json(json.loads(results["results_body.json"]))
                st.download_button(
                    "Download results_body.json",
                    data=results["results_body.json"],
                    file_name="results_body.json",
                    mime="application/json"
                )

            if "metrics_body.csv" in results:
                st.download_button(
                    "Download metrics_body.csv",
                    data=results["metrics_body.csv"],
                    file_name="metrics_body.csv",
                    mime="text/csv"
                )

            if "debug_body.mp4" in results:
                st.video(results["debug_body.mp4"])
                st.download_button(
                    "Download debug_pose.mp4",
                    data=results["debug_body.mp4"],
                    file_name="debug_pose.mp4",
                    mime="video/mp4"
                )


        # ---------------- FACE TAB ----------------
        with tab_face:
            st.header("🙂 Face Analysis")

            if "results_face.json" in results:
                with st.expander("📄 Face JSON Output"):
                    st.json(json.loads(results["results_face.json"]))
                st.download_button(
                    "Download results_face.json",
                    data=results["results_face.json"],
                    file_name="results_face.json",
                    mime="application/json"
                )

            if "metrics_face.csv" in results:
                st.download_button(
                    "Download metrics_face.csv",
                    data=results["metrics_face.csv"],
                    file_name="metrics_face.csv",
                    mime="text/csv"
                )

            if "debug_face.mp4" in results:
                st.video(results["debug_face.mp4"])
                st.download_button(
                    "Download debug_face.mp4",
                    data=results["debug_face.mp4"],
                    file_name="debug_face.mp4",
                    mime="video/mp4"
                )
