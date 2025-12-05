import streamlit as st
import tempfile
import os
import json
import shutil
from pathlib import Path
import sys


# ============================================================
# PROJECT IMPORTS
# ============================================================
# Add the project root to sys.path so we can import from src
current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.audio.pipeline import run_audio_pipeline
from src.body.pipeline import run_body_pipeline
from src.face.pipeline import run_face_pipeline


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
# SAFE FILE READER
# ============================================================
def read_file_safe(path, mode="r"):
    """Reads a file if it exists; returns None otherwise."""
    if os.path.exists(path):
        with open(path, mode) as f:
            return f.read()
    return None


# ============================================================
# RUN ALL PIPELINES
# ============================================================
def process_video(video_path):

    output_root = tempfile.mkdtemp(prefix="pipeline_outputs_")
    results = {}

    with st.status("🔄 Starting analysis...", expanded=True) as status:

        # ---------------- AUDIO ----------------
        status.write("🎧 Running audio pipeline...")
        audio_dir = os.path.join(output_root, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        try:
            run_audio_pipeline(video_path, audio_dir)
            results["results_audio.json"] = read_file_safe(os.path.join(audio_dir, "results_audio.json"))
            results["metrics_audio.csv"] = read_file_safe(os.path.join(audio_dir, "metrics_audio.csv"))
        except Exception as e:
            st.error(f"Audio Pipeline Error: {e}")

        # ---------------- BODY ----------------
        status.write("🕺 Running body pipeline...")
        body_dir = os.path.join(output_root, "body")
        os.makedirs(body_dir, exist_ok=True)
        try:
            run_body_pipeline(video_path, output_dir=body_dir)
            results["results_body.json"] = read_file_safe(os.path.join(body_dir, "results_body.json"))
            results["metrics_body.csv"] = read_file_safe(os.path.join(body_dir, "metrics_body.csv"))
            results["debug_pose.mp4"] = read_file_safe(os.path.join(body_dir, "debug_pose.mp4"), "rb")
        except Exception as e:
            st.error(f"Body Pipeline Error: {e}")

        # ---------------- FACE ----------------
        status.write("🙂 Running face pipeline...")
        face_dir = os.path.join(output_root, "face")
        os.makedirs(face_dir, exist_ok=True)
        try:
            run_face_pipeline(video_path, output_dir=face_dir)
            results["results_face.json"] = read_file_safe(os.path.join(face_dir, "results_face.json"))
            results["metrics_face.csv"] = read_file_safe(os.path.join(face_dir, "metrics_face.csv"))
            results["debug_face.mp4"] = read_file_safe(os.path.join(face_dir, "debug_face.mp4"), "rb")
        except Exception as e:
            st.error(f"Face Pipeline Error: {e}")

        status.update(label="✅ Processing complete!", state="complete")

    # Cleanup outputs
    if os.path.exists(output_root):
        shutil.rmtree(output_root)

    return results



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

    # Save uploaded video to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(uploaded_video.read())
        temp_video_path = tmp.name

    st.success("Video uploaded successfully. Ready to analyze! 🚀")

    # Process Video Button
    if st.button("Start Analysis", type="primary"):

        results = process_video(temp_video_path)

        st.write("## 📊 Analysis Results")

        # ---- Optional Score Cards ----
        st.write("### Global Scores Overview")
        score_cols = st.columns(3)

        # Audio Score
        if results.get("results_audio.json"):
            audio_json = json.loads(results["results_audio.json"])
            if "audio_global_score" in audio_json:
                score_cols[0].metric("🎤 Audio Score", f"{audio_json['audio_global_score']:.2f}")

        # Body Score
        if results.get("results_body.json"):
            body_json = json.loads(results["results_body.json"])
            if "body_global_score" in body_json:
                score_cols[1].metric("🕺 Body Score", f"{body_json['body_global_score']:.2f}")

        # Face Score
        if results.get("results_face.json"):
            face_json = json.loads(results["results_face.json"])
            if "face_global_score" in face_json:
                score_cols[2].metric("🙂 Face Score", f"{face_json['face_global_score']:.2f}")


        # ============================================================
        # RESULT TABS
        # ============================================================
        tab_audio, tab_body, tab_face = st.tabs(["🎧 Audio", "🕺 Body", "🙂 Face"])

        # ---------------- AUDIO TAB ----------------
        with tab_audio:
            st.header("🎧 Audio Analysis")

            if results.get("results_audio.json"):
                with st.expander("📄 Audio JSON Output"):
                    st.json(json.loads(results["results_audio.json"]))
                st.download_button("Download results_audio.json", data=results["results_audio.json"],
                                   file_name="results_audio.json", mime="application/json")

            if results.get("metrics_audio.csv"):
                st.download_button("Download metrics_audio.csv", data=results["metrics_audio.csv"],
                                   file_name="metrics_audio.csv", mime="text/csv")

        # ---------------- BODY TAB ----------------
        with tab_body:
            st.header("🕺 Body Analysis")

            if results.get("results_body.json"):
                with st.expander("📄 Body JSON Output"):
                    st.json(json.loads(results["results_body.json"]))
                st.download_button("Download results_body.json", data=results["results_body.json"],
                                   file_name="results_body.json", mime="application/json")

            if results.get("metrics_body.csv"):
                st.download_button("Download metrics_body.csv", data=results["metrics_body.csv"],
                                   file_name="metrics_body.csv", mime="text/csv")

            if results.get("debug_pose.mp4"):
                st.video(results["debug_pose.mp4"])
                st.download_button("Download debug_pose.mp4", data=results["debug_pose.mp4"],
                                   file_name="debug_pose.mp4", mime="video/mp4")

        # ---------------- FACE TAB ----------------
        with tab_face:
            st.header("🙂 Face Analysis")

            if results.get("results_face.json"):
                with st.expander("📄 Face JSON Output"):
                    st.json(json.loads(results["results_face.json"]))
                st.download_button("Download results_face.json", data=results["results_face.json"],
                                   file_name="results_face.json", mime="application/json")

            if results.get("metrics_face.csv"):
                st.download_button("Download metrics_face.csv", data=results["metrics_face.csv"],
                                   file_name="metrics_face.csv", mime="text/csv")

            if results.get("debug_face.mp4"):
                st.video(results["debug_face.mp4"])
                st.download_button("Download debug_face.mp4", data=results["debug_face.mp4"],
                                   file_name="debug_face.mp4", mime="video/mp4")
