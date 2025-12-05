import streamlit as st
import tempfile
import os
import json
import shutil
from pathlib import Path
import sys


# Add the project root to sys.path so we can import from src
current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.audio.pipeline import run_audio_pipeline
from src.body.pipeline import run_body_pipeline
from src.face.pipeline import run_face_pipeline

# ------------------------------------------------------------

st.title("Multi-Pipeline Video Analyzer")
st.write("Upload a video and run audio, body, and face pipelines to generate results.")


# ------------------------------------------------------------
# HELPER: Safe File Reading
# ------------------------------------------------------------
def read_file_safe(path, mode="r"):
    """Reads a file if it exists, otherwise returns None."""
    if os.path.exists(path):
        with open(path, mode) as f:
            return f.read()
    return None

# ------------------------------------------------------------
# PIPELINE RUNNER
# ------------------------------------------------------------
def process_video(video_path):

    # Create temporary output root for all pipelines
    output_root = tempfile.mkdtemp(prefix="pipeline_outputs_")

    results = {}

    try:
        # ============================================================
        # 1. AUDIO PIPELINE
        # ============================================================
        audio_dir = os.path.join(output_root, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        try:
            run_audio_pipeline(video_path, audio_dir)
            results["results_audio.json"] = read_file_safe(os.path.join(audio_dir, "results_audio.json"))
            results["metrics_audio.csv"] = read_file_safe(os.path.join(audio_dir, "metrics_audio.csv"))
        except Exception as e:
            st.error(f"Audio Pipeline Failed: {e}")

        # ============================================================
        # 2. BODY PIPELINE
        # ============================================================
        body_dir = os.path.join(output_root, "body")
        os.makedirs(body_dir, exist_ok=True)

        try:
            run_body_pipeline(video_path, output_dir=body_dir)
            results["results_body.json"] = read_file_safe(os.path.join(body_dir, "results_body.json"))
            results["metrics_body.csv"] = read_file_safe(os.path.join(body_dir, "metrics_body.csv"))
            results["debug_pose.mp4"] = read_file_safe(os.path.join(body_dir, "debug_pose.mp4"), "rb")
        except Exception as e:
            st.error(f"Body Pipeline Failed: {e}")

        # ============================================================
        # 3. FACE PIPELINE
        # ============================================================
        face_dir = os.path.join(output_root, "face")
        os.makedirs(face_dir, exist_ok=True)

        try:
            run_face_pipeline(video_path, output_dir=face_dir)
            results["results_face.json"] = read_file_safe(os.path.join(face_dir, "results_face.json"))
            results["metrics_face.csv"] = read_file_safe(os.path.join(face_dir, "metrics_face.csv"))
            results["debug_face.mp4"] = read_file_safe(os.path.join(face_dir, "debug_face.mp4"), "rb")
        except Exception as e:
            st.error(f"Face Pipeline Failed: {e}")

    finally:
        # Cleanup temporary directory
        if os.path.exists(output_root):
            shutil.rmtree(output_root)

    return results



# ------------------------------------------------------------
# STREAMLIT UI
# ------------------------------------------------------------
uploaded_video = st.file_uploader("Upload a video", type=["mp4", "mov", "avi", "mkv"])

if uploaded_video is not None:

    st.write("### Uploaded Video Preview")
    st.video(uploaded_video)

    # Save uploaded video to a temporary path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(uploaded_video.read())
        temp_video_path = tmp.name

    st.success("Video uploaded and saved. Ready to process!")

    # -------------------- RUN PIPELINES -----------------------
    if st.button("Start Analysis"):
        st.write("### Processing Video...")
        with st.spinner("Running audio, body, and face pipelines..."):
            results = process_video(temp_video_path)

        st.success("Processing complete!")

        # -------------------- SHOW RESULTS -------------------------
        st.write("## Pipeline Output Files")

        for file_name, content in results.items():
            if content is None:
                continue # Skip missing files

            st.subheader(file_name)

            # JSON files
            if file_name.endswith(".json"):
                try:
                    st.json(json.loads(content))
                    st.download_button(
                        label=f"Download {file_name}",
                        data=content,
                        file_name=file_name,
                        mime="application/json"
                    )
                except json.JSONDecodeError:
                    st.error(f"Could not parse {file_name}")

            # CSV files
            elif file_name.endswith(".csv"):
                st.download_button(
                    label=f"Download {file_name}",
                    data=content,
                    file_name=file_name,
                    mime="text/csv"
                )

            # MP4 video files
            elif file_name.endswith(".mp4"):
                st.video(content)
                st.download_button(
                    label=f"Download {file_name}",
                    data=content,
                    file_name=file_name,
                    mime="video/mp4"
                )
