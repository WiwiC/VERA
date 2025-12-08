import streamlit as st
import tempfile
import json
from pathlib import Path
import sys
import base64

# ============================================================
# PROJECT IMPORTS
# ============================================================
current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.main import run_pipelines  # Your parallel pipeline runner


# ============================================================
# PAGE STATE CONTROLLER
# ============================================================
if "page" not in st.session_state:
    st.session_state.page = "landing"

if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None


# ============================================================
# CUSTOM METRIC UI PANEL
# ============================================================
def render_metric_panel(metric_name: str, metric_data: dict):
    """Renders a metric with score, interpretation, coaching, what/how/why, semantics."""

    nice_name = metric_name.replace("_", " ").title()

    st.markdown("---")
    st.markdown(f"### 🧩 **{nice_name}**")

    # Extract scores
    main_score = metric_data.get("score")                     # AUDIO
    comm_score = metric_data.get("communication_score")       # BODY/FACE
    cons_score = metric_data.get("consistency_score")         # BODY/FACE

    # Score display – only show consistency once (here, NOT inside expander)
    cols = st.columns(2)

    with cols[0]:
        if main_score is not None:
            st.metric("Score", f"{float(main_score):.2f}")
        elif comm_score is not None:
            st.metric("Communication Score", f"{float(comm_score):.2f}")

    with cols[1]:
        if comm_score is not None and main_score is not None:
            st.metric("Communication Score", f"{float(comm_score):.2f}")
        elif cons_score is not None:
            st.metric("Consistency Score", f"{float(cons_score):.2f}")

    # Interpretation
    interpretation = (
        metric_data.get("interpretation")
        or metric_data.get("communication_interpretation")
    )
    if interpretation:
        st.info(f"**Interpretation:** {interpretation}")

    # Coaching
    coaching = (
        metric_data.get("coaching")
        or metric_data.get("communication_coaching")
    )
    if coaching:
        st.warning(f"**Coaching:** {coaching}")

    # Consistency (ONLY textual, not numeric — avoids duplication)
    has_consistency_text = (
        metric_data.get("consistency_interpretation")
        or metric_data.get("consistency_coaching")
    )

    if has_consistency_text:
        with st.expander("📏 Consistency details"):
            if metric_data.get("consistency_interpretation"):
                st.write(f"**Interpretation:** {metric_data['consistency_interpretation']}")
            if metric_data.get("consistency_coaching"):
                st.write(f"**Coaching:** {metric_data['consistency_coaching']}")

    # What / How / Why
    with st.expander("ℹ️ What / How / Why"):
        st.write(f"**What:** {metric_data.get('what', 'N/A')}")
        st.write(f"**How:** {metric_data.get('how', 'N/A')}")
        st.write(f"**Why:** {metric_data.get('why', 'N/A')}")

    # Score semantics
    if "score_semantics" in metric_data:
        with st.expander("📘 Score Meaning"):
            st.json(metric_data["score_semantics"])


# ============================================================
# VIDEO PROCESSING
# ============================================================
def process_video(video_path):

    with st.status("🔄 Running VERA analysis...", expanded=True) as status:
        output_dir, results = run_pipelines(video_path)
        status.update(label="🎉 All pipelines complete!", state="complete")

    outputs = {}

    enriched = Path(output_dir) / "results_global_enriched.json"
    if enriched.exists():
        outputs["results_global_enriched.json"] = enriched.read_text()

    for module in ["audio", "body", "face"]:
        csv_path = Path(output_dir) / f"metrics_{module}.csv"
        if csv_path.exists():
            outputs[f"metrics_{module}.csv"] = csv_path.read_text()

        mp4_path = Path(output_dir) / f"debug_{module}.mp4"
        if mp4_path.exists():
            outputs[f"debug_{module}.mp4"] = mp4_path.read_bytes()

    return outputs


# ============================================================
# LANDING PAGE
# ============================================================
def landing_page():

    st.markdown("""
        <style>
            .stApp {
                background-color: #E7E7FF !important;
            }

            .landing-container {
                text-align: center;
                padding-top: 80px;
            }

            /* Main title (bigger text) */
            .hero-title {
                font-size: 32px;
                font-weight: 700;
                color: #2B3A8B;
                margin-bottom: 5px;
            }

            /* Subtitle under the title */
            .tagline-sub {
                font-size: 18px;
                color: #2B3A8B;
                margin-bottom: 30px;
            }

            /* Upload card styling */
            .upload-card {
                background: white;
                padding: 30px;
                border-radius: 18px;
                width: 420px;
                margin-left: auto;
                margin-right: auto;
                box-shadow: 0px 4px 18px rgba(0,0,0,0.12);
            }

            /* Start button container */
            .start-button-container {
                max-width: 420px;
                margin: 20px auto 0 auto;
            }

        </style>
    """, unsafe_allow_html=True)

    # --------------------- LOGO -----------------------
    logo_path = Path(__file__).parent / "logoVERA.png"

    st.markdown("<div class='landing-container'>", unsafe_allow_html=True)

    if logo_path.exists():
        st.image(str(logo_path), width=180)

    # ------------------- BIG TITLE + SUBTITLE ----------------------
    st.markdown("""
        <p class="hero-title">
            VERA (Vocal, Expressive & Relational Analyzer)
        </p>
        <p class="tagline-sub">
            evaluates how you communicate during pitches, interviews, or presentations.
        </p>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------- UPLOADER ---------------------
    st.markdown("<div class='upload-card'>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload your video:", type=["mp4", "mov", "avi", "mkv"])

    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded:
        st.session_state.uploaded_video = uploaded
        st.success("Video uploaded successfully!")

    # ------------------- START BUTTON ---------------------
    st.markdown("<div class='start-button-container'>", unsafe_allow_html=True)

    if st.button("🚀 Start Analyzer", use_container_width=True):
        if st.session_state.uploaded_video is None:
            st.error("Please upload a video first.")
        else:
            st.session_state.page = "analyze"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# ANALYZER PAGE
# ============================================================
def analysis_page():

    uploaded_video = st.session_state.uploaded_video

    st.write("## 📺 Video Preview")
    st.video(uploaded_video)

    # Save temp file
    suffix = Path(uploaded_video.name).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_video.read())
        temp_path = tmp.name

    st.write("### 🔄 Processing video…")

    results_files = process_video(temp_path)
    st.success("🎉 Analysis ready!")

    # Load enriched JSON
    enriched_data = json.loads(results_files["results_global_enriched.json"])

    # ============================================================
    # GLOBAL SCORE CARDS
    # ============================================================
    st.write("### ⭐ Global Scores Overview")

    def get_global(module):
        block = enriched_data.get(module, {}).get("global", {})
        if module == "audio":
            return float(block.get("score", 0))
        return float(block.get("communication_score", 0))

    cols = st.columns(3)
    cols[0].metric("🎤 Audio", f"{get_global('audio'):.2f}")
    cols[1].metric("🕺 Body", f"{get_global('body'):.2f}")
    cols[2].metric("🙂 Face", f"{get_global('face'):.2f}")

    # ============================================================
    # TABS FOR DETAILED ANALYSIS
    # ============================================================
    tab_audio, tab_body, tab_face = st.tabs(["🎧 Audio", "🕺 Body", "🙂 Face"])

    # ---------------- AUDIO ----------------
    with tab_audio:
        audio_block = enriched_data["audio"]
        st.subheader("🌐 Global Audio Summary")
        st.info(f"**Interpretation:** {audio_block['global']['interpretation']}")
        with st.expander("ℹ️ What / Why"):
            st.write(f"**What:** {audio_block['global']['what']}")
            st.write(f"**Why:** {audio_block['global']['why']}")

        st.subheader("🧠 Audio Metrics & Coaching")
        for name, metric in audio_block["metrics"].items():
            render_metric_panel(name, metric)

        if "metrics_audio.csv" in results_files:
            st.download_button("Download metrics_audio.csv",
                results_files["metrics_audio.csv"],
                "metrics_audio.csv", "text/csv")

    # ---------------- BODY ----------------
    with tab_body:
        body_block = enriched_data["body"]
        st.subheader("🌐 Global Body Summary")
        st.info(f"**Interpretation:** {body_block['global']['interpretation']}")
        with st.expander("ℹ️ What / Why"):
            st.write(f"**What:** {body_block['global']['what']}")
            st.write(f"**Why:** {body_block['global']['why']}")

        st.subheader("🧠 Body Metrics & Coaching")
        for name, metric in body_block["metrics"].items():
            render_metric_panel(name, metric)

        if "metrics_body.csv" in results_files:
            st.download_button("Download metrics_body.csv",
                results_files["metrics_body.csv"],
                "metrics_body.csv", "text/csv")

        if "debug_body.mp4" in results_files:
            st.video(results_files["debug_body.mp4"])
            st.download_button("Download debug_body.mp4",
                results_files["debug_body.mp4"],
                "debug_body.mp4", "video/mp4")

    # ---------------- FACE ----------------
    with tab_face:
        face_block = enriched_data["face"]
        st.subheader("🌐 Global Face Summary")
        st.info(f"**Interpretation:** {face_block['global']['interpretation']}")
        with st.expander("ℹ️ What / Why"):
            st.write(f"**What:** {face_block['global']['what']}")
            st.write(f"**Why:** {face_block['global']['why']}")

        st.subheader("🧠 Face Metrics & Coaching")
        for name, metric in face_block["metrics"].items():
            render_metric_panel(name, metric)

        if "metrics_face.csv" in results_files:
            st.download_button("Download metrics_face.csv",
                results_files["metrics_face.csv"],
                "metrics_face.csv", "text/csv")

        if "debug_face.mp4" in results_files:
            st.video(results_files["debug_face.mp4"])
            st.download_button("Download debug_face.mp4",
                results_files["debug_face.mp4"],
                "debug_face.mp4", "video/mp4")

    # Final download
    st.download_button(
        "📥 Download Full JSON",
        results_files["results_global_enriched.json"],
        "results_global_enriched.json",
        "application/json"
    )


# ============================================================
# PAGE ROUTING
# ============================================================
if st.session_state.page == "landing":
    landing_page()

elif st.session_state.page == "analyze":
    analysis_page()
