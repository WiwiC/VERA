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

from src.main import run_pipelines  # ⬅️ Parallel main


# ============================================================
# HELPER: METRIC RENDERING
# ============================================================
def render_metric_panel(metric_name: str, metric_data: dict):
    """
    Pretty Streamlit panel for a single metric with:
    - score(s)
    - interpretation
    - coaching
    - what / how / why
    - score semantics
    - consistency details (if present)
    """
    nice_name = metric_name.replace("_", " ").title()

    st.markdown(f"---")
    st.markdown(f"### 🧩 **{nice_name}**")

    # Scores
    score_cols = st.columns(3)

    # Main / communication score
    main_score = metric_data.get("score")
    comm_score = metric_data.get("communication_score")
    cons_score = metric_data.get("consistency_score")

    with score_cols[0]:
        if main_score is not None:
            st.metric("Score", f"{float(main_score):.2f}")
        elif comm_score is not None:
            st.metric("Communication Score", f"{float(comm_score):.2f}")

    with score_cols[1]:
        if comm_score is not None and main_score is not None:
            st.metric("Communication Score", f"{float(comm_score):.2f}")
        elif cons_score is not None:
            st.metric("Consistency Score", f"{float(cons_score):.2f}")

    with score_cols[2]:
        if cons_score is not None and (main_score is not None or comm_score is not None):
            st.metric("Consistency Score", f"{float(cons_score):.2f}")

    # Interpretations + Coaching (primary / communication)
    interpretation = (
        metric_data.get("interpretation")
        or metric_data.get("communication_interpretation")
    )
    coaching = (
        metric_data.get("coaching")
        or metric_data.get("communication_coaching")
    )

    if interpretation:
        st.info(f"**Interpretation:** {interpretation}")

    if coaching:
        st.warning(f"**Coaching:** {coaching}")

    # Consistency details, if present
    has_consistency = (
        "consistency_interpretation" in metric_data
        or "consistency_coaching" in metric_data
        or cons_score is not None
    )
    if has_consistency:
        with st.expander("📏 Consistency details"):
            #if cons_score is not None:
            #    st.write(f"**Consistency score:** {float(cons_score):.2f}")
            if metric_data.get("consistency_interpretation"):
                st.write(
                    f"**Interpretation:** {metric_data['consistency_interpretation']}"
                )
            if metric_data.get("consistency_coaching"):
                st.write(
                    f"**Coaching:** {metric_data['consistency_coaching']}"
                )

    # What / How / Why
    with st.expander("ℹ️ What / How / Why"):
        st.write(f"**What:** {metric_data.get('what', 'N/A')}")
        st.write(f"**How:** {metric_data.get('how', 'N/A')}")
        st.write(f"**Why:** {metric_data.get('why', 'N/A')}")

    # Score semantics
    if "score_semantics" in metric_data:
        with st.expander("📘 Score meaning"):
            st.json(metric_data["score_semantics"])


# ============================================================
# CUSTOM PAGE STYLING
# ============================================================
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


# ============================================================
# PARALLEL PIPELINE EXECUTION
# ============================================================
def process_video(video_path):

    with st.status("🔄 Running pipelines in parallel...", expanded=True) as status:

        output_dir, results = run_pipelines(video_path)

        status.update(label="🎉 All pipelines complete!", state="complete")

    # Convert all produced files into a dictionary
    outputs = {}

    # Enriched Global file
    enriched_path = Path(output_dir) / "results_global_enriched.json"
    if enriched_path.exists():
        outputs["results_global_enriched.json"] = enriched_path.read_text()

    # Load media and CSVs
    for module in ["audio", "body", "face"]:
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
uploaded_video = st.sidebar.file_uploader(
    "Select a video file:", type=["mp4", "mov", "avi", "mkv"]
)


# ============================================================
# MAIN APP
# ============================================================
if uploaded_video is not None:

    st.write("### 📺 Uploaded Video Preview")
    st.video(uploaded_video)

    # Save video temporarily
    suffix = Path(uploaded_video.name).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_video.read())
        temp_video_path = tmp.name

    st.success("Video uploaded successfully. Ready to analyze! 🚀")

    # Run Pipelines
    if st.button("Start Analysis", type="primary"):

        results_files = process_video(temp_video_path)

        st.write("## 📊 Analysis Results")

        # Load Enriched Data
        enriched_data = {}
        if "results_global_enriched.json" in results_files:
            try:
                enriched_data = json.loads(
                    results_files["results_global_enriched.json"]
                )
            except Exception as e:
                st.error(f"Error loading enriched JSON: {e}")
                enriched_data = {}

        # ============================================================
        # GLOBAL SCORE CARDS (Audio / Body / Face) – FIRST
        # ============================================================
        st.write("### ⭐ Global Scores Overview")

        score_cols = st.columns(3)

        def get_global_score(data, module, key="communication_score"):
            try:
                module_data = data.get(module, {})
                global_block = module_data.get("global", {})
                # Audio uses "score", others use "communication_score"
                if module == "audio" and key == "communication_score":
                    key = "score"
                return float(global_block.get(key, 0.0))
            except Exception:
                return 0.0

        # AUDIO SCORE
        audio_score = get_global_score(enriched_data, "audio")
        score_cols[0].metric("🎤 Audio Score", f"{audio_score:.2f}")

        # BODY SCORE
        body_score = get_global_score(enriched_data, "body")
        score_cols[1].metric("🕺 Body Score", f"{body_score:.2f}")

        # FACE SCORE
        face_score = get_global_score(enriched_data, "face")
        score_cols[2].metric("🙂 Face Score", f"{face_score:.2f}")

        # ============================================================
        # TABS (Audio / Body / Face)
        # ============================================================
        tab_audio, tab_body, tab_face = st.tabs(["🎧 Audio", "🕺 Body", "🙂 Face"])

        # ---------------- AUDIO TAB ----------------
        with tab_audio:
            st.header("🎧 Audio Analysis")

            audio_block = enriched_data.get("audio", {})
            audio_global = audio_block.get("global", {})
            audio_metrics = audio_block.get("metrics", {})

            # Global summary
            if audio_global:
                st.subheader("🌐 Global audio summary")
                if "interpretation" in audio_global:
                    st.info(f"**Interpretation:** {audio_global['interpretation']}")
                with st.expander("ℹ️ What / Why (Global)"):
                    st.write(f"**What:** {audio_global.get('what', 'N/A')}")
                    st.write(f"**Why:** {audio_global.get('why', 'N/A')}")

            # Metric-level panels (coaching, etc.)
            if audio_metrics:
                st.subheader("🧠 Audio metrics & coaching")
                for metric_name, metric_data in audio_metrics.items():
                    render_metric_panel(metric_name, metric_data)
            else:
                st.write("No audio metric details available.")

            # Metrics CSV download
            if "metrics_audio.csv" in results_files:
                st.download_button(
                    "Download metrics_audio.csv",
                    data=results_files["metrics_audio.csv"],
                    file_name="metrics_audio.csv",
                    mime="text/csv",
                )

        # ---------------- BODY TAB ----------------
        with tab_body:
            st.header("🕺 Body Analysis")

            body_block = enriched_data.get("body", {})
            body_global = body_block.get("global", {})
            body_metrics = body_block.get("metrics", {})

            # Global summary
            if body_global:
                st.subheader("🌐 Global body summary")
                if "interpretation" in body_global:
                    st.info(f"**Interpretation:** {body_global['interpretation']}")
                with st.expander("ℹ️ What / Why (Global)"):
                    st.write(f"**What:** {body_global.get('what', 'N/A')}")
                    st.write(f"**Why:** {body_global.get('why', 'N/A')}")

            # Metric-level panels
            if body_metrics:
                st.subheader("🧠 Body metrics & coaching")
                for metric_name, metric_data in body_metrics.items():
                    render_metric_panel(metric_name, metric_data)
            else:
                st.write("No body metric details available.")

            # CSV & debug video
            if "metrics_body.csv" in results_files:
                st.download_button(
                    "Download metrics_body.csv",
                    data=results_files["metrics_body.csv"],
                    file_name="metrics_body.csv",
                    mime="text/csv",
                )

            if "debug_body.mp4" in results_files:
                st.write("### 🎬 Debug body video")
                st.video(results_files["debug_body.mp4"])
                st.download_button(
                    "Download debug_body.mp4",
                    data=results_files["debug_body.mp4"],
                    file_name="debug_body.mp4",
                    mime="video/mp4",
                )

        # ---------------- FACE TAB ----------------
        with tab_face:
            st.header("🙂 Face Analysis")

            face_block = enriched_data.get("face", {})
            face_global = face_block.get("global", {})
            face_metrics = face_block.get("metrics", {})

            # Global summary
            if face_global:
                st.subheader("🌐 Global face summary")
                if "interpretation" in face_global:
                    st.info(f"**Interpretation:** {face_global['interpretation']}")
                with st.expander("ℹ️ What / Why (Global)"):
                    st.write(f"**What:** {face_global.get('what', 'N/A')}")
                    st.write(f"**Why:** {face_global.get('why', 'N/A')}")

            # Metric-level panels
            if face_metrics:
                st.subheader("🧠 Face metrics & coaching")
                for metric_name, metric_data in face_metrics.items():
                    render_metric_panel(metric_name, metric_data)
            else:
                st.write("No face metric details available.")

            # CSV & debug video
            if "metrics_face.csv" in results_files:
                st.download_button(
                    "Download metrics_face.csv",
                    data=results_files["metrics_face.csv"],
                    file_name="metrics_face.csv",
                    mime="text/csv",
                )

            if "debug_face.mp4" in results_files:
                st.write("### 🎬 Debug face video")
                st.video(results_files["debug_face.mp4"])
                st.download_button(
                    "Download debug_face.mp4",
                    data=results_files["debug_face.mp4"],
                    file_name="debug_face.mp4",
                    mime="video/mp4",
                )

        # Download Enriched JSON
        if "results_global_enriched.json" in results_files:
            st.divider()
            st.download_button(
                "📥 Download Full Analysis (JSON)",
                data=results_files["results_global_enriched.json"],
                file_name="results_global_enriched.json",
                mime="application/json",
            )
