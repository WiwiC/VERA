import streamlit as st
import os
import tempfile
import json
from pathlib import Path
import sys
import base64

st.set_page_config(
    page_title="VERA Analyzer",
    layout="wide",
)

# ============================================================
# PROJECT IMPORTS
# ============================================================
current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.main import run_pipelines, run_pipelines_iterator  # Your parallel pipeline runner


def load_results_from_dir(output_dir):
    """Loads results from an existing directory."""
    output_dir = Path(output_dir)
    outputs = {}

    enriched = output_dir / "results_global_enriched.json"
    if enriched.exists():
        outputs["results_global_enriched.json"] = enriched.read_text()

    expected_debug_files = {
        "audio": "debug_audio.mp3",
        "body": "debug_pose.mp4",
        "face": "debug_face.mp4"
    }

    for module in ["audio", "body", "face"]:
        csv_path = output_dir / f"metrics_{module}.csv"
        if csv_path.exists():
            outputs[f"metrics_{module}.csv"] = csv_path.read_text()

        debug_filename = expected_debug_files.get(module)
        debug_path = output_dir / debug_filename
        if debug_path.exists():
            outputs[debug_filename] = debug_path.read_bytes()

    return outputs


# ============================================================
# PAGE STATE CONTROLLER
# ============================================================

# 1. Handle Query Params (Persistent State)
if "page" not in st.session_state:
    # Check if a video is specified in URL
    video_param = st.query_params.get("video")
    if video_param:
        # Try to load it
        target_dir = Path("data/processed") / video_param
        if target_dir.exists():
            st.session_state.results_files = load_results_from_dir(target_dir)
            st.session_state.page = "analyze"
            st.session_state.current_video_name = video_param
        else:
            st.session_state.page = "landing"
    else:
        st.session_state.page = "landing"

if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
with st.sidebar:
    st.title("VERA Analyzer")

    if st.button("🏠 New Analysis", use_container_width=True):
        st.session_state.page = "landing"
        st.session_state.uploaded_video = None
        st.session_state.results_files = None
        st.query_params.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("📜 History")

    # List processed videos
    processed_dir = Path("data/processed")
    if processed_dir.exists():
        # Find directories that contain results
        videos = []
        for d in processed_dir.iterdir():
            if d.is_dir() and (d / "results_global_enriched.json").exists():
                videos.append(d.name)

        videos.sort(reverse=True) # Show newest first (if named by timestamp, otherwise alphabetical)

        if videos:
            def load_selected_video_from_sidebar():
                selected = st.session_state.history_selector
                if selected:
                    target_dir = processed_dir / selected
                    st.session_state.results_files = load_results_from_dir(target_dir)
                    st.session_state.page = "analyze"
                    st.session_state.current_video_name = selected
                    st.query_params["video"] = selected

            # Determine index of current video to keep radio in sync
            current_video = st.session_state.get("current_video_name")
            try:
                default_index = videos.index(current_video)
            except (ValueError, TypeError):
                default_index = None

            st.radio(
                "Select a past analysis:",
                options=videos,
                index=default_index,
                key="history_selector",
                on_change=load_selected_video_from_sidebar
            )
        else:
            st.info("No history found yet.")


# ============================================================
# CUSTOM METRIC UI PANEL
# ============================================================
def render_metric_panel(metric_name: str, metric_data: dict):
    """Renders a metric with score, interpretation, coaching, what/how/why, semantics."""
    nice_name = metric_name.replace("_", " ").title()

    st.markdown("---")
    st.markdown(f"### 🧩 **{nice_name}**")

    # Extract scores
    main_score = metric_data.get("score")
    comm_score = metric_data.get("communication_score")
    cons_score = metric_data.get("consistency_score")

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

    interpretation = (
        metric_data.get("interpretation")
        or metric_data.get("communication_interpretation")
    )
    if interpretation:
        st.info(f"**Interpretation:** {interpretation}")

    coaching = (
        metric_data.get("coaching")
        or metric_data.get("communication_coaching")
    )
    if coaching:
        st.warning(f"**Coaching:** {coaching}")

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

    with st.expander("ℹ️ What / How / Why"):
        st.write(f"**What:** {metric_data.get('what', 'N/A')}")
        st.write(f"**How:** {metric_data.get('how', 'N/A')}")
        st.write(f"**Why:** {metric_data.get('why', 'N/A')}")

    if "score_semantics" in metric_data:
        with st.expander("📘 Score Meaning"):
            st.json(metric_data["score_semantics"])


# ============================================================
# VIDEO PROCESSING
# ============================================================
def process_video(video_path):

    with st.status("🔄 Running VERA analysis...", expanded=True) as status:

        iterator = run_pipelines_iterator(video_path)
        output_dir = None
        results = {}

        completed_modules = 0
        total_modules = 3 # Audio, Body, Face

        for event_type, *args in iterator:
            if event_type == "start":
                output_dir = args[0]
                st.write("📂 Output directory created.")

            elif event_type == "progress":
                module, res = args
                completed_modules += 1
                st.write(f"✅ **{module.capitalize()}** analysis complete.")

            elif event_type == "error":
                module, err = args
                completed_modules += 1
                st.error(f"❌ **{module.capitalize()}** failed: {err}")

            elif event_type == "final":
                output_dir, results = args

        status.update(label="🎉 All pipelines complete!", state="complete")

    outputs = {}

    enriched = Path(output_dir) / "results_global_enriched.json"
    if enriched.exists():
        outputs["results_global_enriched.json"] = enriched.read_text()

    expected_debug_files = {
        "audio": "debug_audio.mp3",
        "body": "debug_pose.mp4",
        "face": "debug_face.mp4"
    }

    for module in ["audio", "body", "face"]:
        csv_path = Path(output_dir) / f"metrics_{module}.csv"
        if csv_path.exists():
            outputs[f"metrics_{module}.csv"] = csv_path.read_text()

        debug_filename = expected_debug_files.get(module)
        debug_path = Path(output_dir) / debug_filename
        if debug_path.exists():
            outputs[debug_filename] = debug_path.read_bytes()

    return outputs




# ============================================================
# LANDING PAGE
# ============================================================
def landing_page():

    st.markdown("""
        <style>
            .stApp { background-color: #E7E7FF !important; }

            .landing-container {
                text-align: center;
                padding-top: 80px;
            }

            .tagline {
                font-size: 22px;
                color: #2B3A8B;
                margin-top: 10px;
                margin-bottom: 30px;
                font-weight: 600;
            }

            .upload-card {
                background: white;
                padding: 30px;
                border-radius: 18px;
                width: 480px;
                margin-left: auto;
                margin-right: auto;
                box-shadow: 0px 4px 18px rgba(0,0,0,0.12);
            }

            .start-button-container {
                margin-top: 25px;
                width: 480px;
                margin-left: auto;
                margin-right: auto;
            }

            /* Target the bordered container to look like a card */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background-color: white;
                border-radius: 18px;
                padding: 20px;
                box-shadow: 0px 4px 18px rgba(0,0,0,0.12);
                border: none; /* Remove default gray border */
            }
        </style>
    """, unsafe_allow_html=True)

    # --------------------------
    # HERO SECTION
    # --------------------------

    # Helper to encode image
    def get_base64_image(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    # Logo (Centered via HTML/Flexbox)
    logo_path = Path(__file__).parent / "logoVERA.png"
    if logo_path.exists():
        img_base64 = get_base64_image(logo_path)
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                <img src="data:image/png;base64,{img_base64}" width="200">
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. Tagline (Centered via CSS class)
    st.markdown("""
        <div style="text-align: center;">
            <p class="tagline">
                <b>VERA (Vocal, Expressive & Relational Analyzer)</b><br>
                evaluates how you communicate during pitches, interviews, or presentations.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --------------------------
    # UPLOAD CARD
    # --------------------------
    # --------------------------
    # UPLOAD CARD
    # --------------------------
    # Use columns to center the card (width approx 50%)
    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        with st.container(border=True):
            uploaded = st.file_uploader(
                "Upload your video:",
                type=["mp4", "mov", "avi", "mkv"]
            )

        if uploaded:
            st.session_state.uploaded_video = uploaded
            st.success("Video uploaded successfully!")

    # --------------------------
    # START BUTTON (NO EMPTY WHITE BAR)
    # --------------------------
    st.markdown("<div class='start-button-container'>", unsafe_allow_html=True)

    # center the button nicely
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        if st.button("🚀 Start Analyzer", use_container_width=True):

            if st.session_state.uploaded_video is None:
                st.error("Please upload a video first.")
            else:
                # Save uploaded file temporarily
                uploaded_video = st.session_state.uploaded_video
                suffix = Path(uploaded_video.name).suffix or ".mp4"

                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_video.read())
                    temp_path = tmp.name

                # Run pipeline once
                # Removed st.spinner to avoid double-spinner look, relying on st.status inside process_video
                st.session_state.results_files = process_video(temp_path)

                # Navigate to analysis page
                st.session_state.page = "analyze"

                # Set query param for persistence
                video_name = Path(temp_path).stem
                st.query_params["video"] = video_name
                st.session_state.current_video_name = video_name

                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# ANALYZER PAGE
# ============================================================
def analysis_page():

    # 💜 Full purple background
    st.markdown("""
        <style>
            .stApp { background-color: #E7E7FF !important; }
            .block-container {
                background-color: transparent !important;
                padding-top: 20px;
            }


            .score-card {
                background: #F4F4FF;
                border-radius: 16px;
                padding: 18px;
                text-align: center;
                box-shadow: 0px 2px 10px rgba(0,0,0,0.08);
            }

            .score-title {
                font-size: 18px;
                font-weight: 600;
                color: #2B3A8B;
            }

            .score-value {
                font-size: 32px;
                font-weight: 700;
                color: #1A237E;
                margin-top: -5px;
            }

            .section-title {
                font-size: 22px;
                font-weight: 700;
                color: #2B3A8B;
                margin-bottom: 15px;
            }

            .metric-card {
                background: #FFFFFF;
                padding: 18px;
                border-radius: 14px;
                box-shadow: 0px 2px 10px rgba(0,0,0,0.06);
                margin-bottom: 18px;
            }

            .metric-name {
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 6px;
            }

            .metric-score {
                font-size: 16px;
                font-weight: 500;
                color: #303F9F;
                margin-bottom: 5px;
            }

            .metric-coaching {
                font-size: 14px;
                color: #555;
                margin-bottom: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    uploaded_video = st.session_state.uploaded_video
    results_files = st.session_state.get("results_files", None)

    if results_files is None:
        st.error("No analysis results found. Please upload and analyze a video first.")
        return

    enriched_data = json.loads(results_files["results_global_enriched.json"])

    # ============================================================
    # TOP: VIDEO + GLOBAL SCORES
    # ============================================================
    col_left, col_right = st.columns([1.2, 1])

    # -------------------------
    # VIDEO CARD
    # -------------------------
    with col_left:
        with st.container(border=True):
            st.markdown("## 🎥 Video Preview")
            st.video(uploaded_video)

    # -------------------------
    # GLOBAL SCORES CARD
    # -------------------------
    with col_right:
        with st.container(border=True):
            st.markdown("<div class='section-title'>⭐ Global Scores</div>", unsafe_allow_html=True)

            def get_global(module):
                block = enriched_data.get(module, {}).get("global", {})
                # enrich.py normalizes the key to "score" for all modules
                return float(block.get("score", 0))

            g1, g2, g3 = st.columns(3)

            with g1:
                st.markdown(
                    f"""
                    <div class="score-card">
                        <div class="score-title">🎤 Audio</div>
                        <div class="score-value">{get_global('audio'):.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with g2:
                st.markdown(
                    f"""
                    <div class="score-card">
                        <div class="score-title">🕺 Body</div>
                        <div class="score-value">{get_global('body'):.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with g3:
                st.markdown(
                    f"""
                    <div class="score-card">
                        <div class="score-title">🙂 Face</div>
                        <div class="score-value">{get_global('face'):.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ============================================================
    # DETAILED ANALYSIS SECTION (FIXED)
    # ============================================================
    with st.container(border=True):
        st.markdown("<div class='section-title'>Detailed Analysis</div>", unsafe_allow_html=True)

        selected = st.segmented_control(
            "Select Module",
            options=["Audio", "Body", "Face"],
            default="Audio"
        )

        module_key = selected.lower()
        module_metrics = enriched_data[module_key]["metrics"]

        # Metric rendering component
        def show_metric(name, metric):

            with st.container(border=True):
                st.markdown(
                    f"<div class='metric-name'>{name.replace('_', ' ').title()}</div>",
                    unsafe_allow_html=True,
                )

                score = metric.get("score") or metric.get("communication_score")
                if score is not None:
                    st.markdown(
                        f"<div class='metric-score'>Score: {score:.2f}</div>",
                        unsafe_allow_html=True
                    )

                coaching = metric.get("coaching") or metric.get("communication_coaching")
                if coaching:
                    st.markdown(
                        f"<div class='metric-coaching'><b>Coaching:</b> {coaching}</div>",
                        unsafe_allow_html=True
                    )

                with st.expander("More Details"):
                    interp = metric.get("interpretation") or metric.get("communication_interpretation")
                    if interp:
                        st.write(f"**Interpretation:** {interp}")

                    st.write(f"**What:** {metric.get('what', 'N/A')}")
                    st.write(f"**How:** {metric.get('how', 'N/A')}")
                    st.write(f"**Why:** {metric.get('why', 'N/A')}")

                    if "score_semantics" in metric:
                        st.json(metric["score_semantics"])

        # Two column layout
        colA, colB = st.columns(2)

        for i, (name, metric) in enumerate(module_metrics.items()):
            target_col = colA if i % 2 == 0 else colB
            with target_col:
                show_metric(name, metric)

    # ============================================================
    # DOWNLOAD JSON
    # ============================================================
    st.download_button(
        "📥 Download Full JSON Report",
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
