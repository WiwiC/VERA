import streamlit as st
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
                width: 420px;
                margin-left: auto;
                margin-right: auto;
                box-shadow: 0px 4px 18px rgba(0,0,0,0.12);
            }

            .start-button-container {
                max-width: 420px;
                margin: 20px auto 0 auto;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='landing-container'>", unsafe_allow_html=True)

    # Logo
    logo_path = Path(__file__).parent / "logoVERA.png"
    if logo_path.exists():
        st.image(str(logo_path), width=180)

    # Tagline
    st.markdown("""
        <p class="tagline">
            <b>VERA (Vocal, Expressive & Relational Analyzer)</b><br>
            evaluates how you communicate during pitches, interviews, or presentations.
        </p>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Upload card
    st.markdown("<div class='upload-card'>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload your video:", type=["mp4", "mov", "avi", "mkv"])
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded:
        st.session_state.uploaded_video = uploaded
        st.success("Video uploaded successfully!")

    # Start Analyzer button
    st.markdown("<div class='start-button-container'>", unsafe_allow_html=True)

    if st.button("🚀 Start Analyzer", use_container_width=True):

        if "uploaded_video" not in st.session_state or st.session_state.uploaded_video is None:
            st.error("Please upload a video first.")
        else:
            uploaded_video = st.session_state.uploaded_video

            # PROCESSING HAPPENS HERE
            with st.spinner("🔄 Processing your video… This may take a moment ⏳"):

                # Save temp file
                suffix = Path(uploaded_video.name).suffix or ".mp4"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_video.read())
                    temp_path = tmp.name

                # Run pipeline ONCE
                st.session_state.results_files = process_video(temp_path)

            # When finished → go to analyzer page
            st.session_state.page = "analyze"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)



# ============================================================
# ANALYZER PAGE
# ============================================================
def analysis_page():

    # 💜 Full purple background
    st.markdown("""
        <style>
            .stApp {
                background-color: #E7E7FF !important;
            }
            .block-container {
                background-color: transparent !important;
                padding-top: 20px;
            }

            .dashboard-card {
                background: white;
                border-radius: 18px;
                padding: 25px;
                box-shadow: 0px 4px 18px rgba(0,0,0,0.12);
                margin-bottom: 35px;
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

    # ============================================================
    # GET UPLOADED VIDEO + RESULTS
    # ============================================================
    uploaded_video = st.session_state.uploaded_video

    results_files = st.session_state.get("results_files", None)
    if results_files is None:
        st.error("No analysis results found. Please upload and analyze a video first.")
        return

    enriched_data = json.loads(results_files["results_global_enriched.json"])

    # ============================================================
    # TOP: VIDEO LEFT + SCORES RIGHT
    # ============================================================
    col_left, col_right = st.columns([1.2, 1])

    # -------------------------
    # VIDEO CARD
    # -------------------------
    with col_left:
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown("## 🎥 Video Preview")
        st.video(uploaded_video)
        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------
    # GLOBAL SCORES CARD
    # -------------------------
    with col_right:
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>⭐ Global Scores</div>", unsafe_allow_html=True)

        def get_global(module):
            block = enriched_data.get(module, {}).get("global", {})
            if module == "audio":
                return float(block.get("score", 0))
            return float(block.get("communication_score", 0))

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

        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # METRIC EXPLORATION SECTION
    # ============================================================
    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Detailed Analysis</div>", unsafe_allow_html=True)

    selected = st.segmented_control(
        "Select Module",
        options=["Audio", "Body", "Face"],
        default="Audio"
    )

    # Pick which module's metrics to show
    module_key = selected.lower()
    module_metrics = enriched_data[module_key]["metrics"]

    # ------------------------------------------------------------
    # METRIC CARD COMPONENT
    # ------------------------------------------------------------
    def show_metric(name, metric):

        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)

        st.markdown(
            f"<div class='metric-name'>{name.replace('_', ' ').title()}</div>",
            unsafe_allow_html=True,
        )

        # Score
        score = metric.get("score") or metric.get("communication_score")
        if score is not None:
            st.markdown(
                f"<div class='metric-score'>Score: {score:.2f}</div>",
                unsafe_allow_html=True
            )

        # Coaching
        coaching = metric.get("coaching") or metric.get("communication_coaching")
        if coaching:
            st.markdown(
                f"<div class='metric-coaching'><b>Coaching:</b> {coaching}</div>",
                unsafe_allow_html=True
            )

        # Details expander
        with st.expander("More Details"):
            interp = metric.get("interpretation") or metric.get("communication_interpretation")
            if interp:
                st.write(f"**Interpretation:** {interp}")

            st.write(f"**What:** {metric.get('what', 'N/A')}")
            st.write(f"**How:** {metric.get('how', 'N/A')}")
            st.write(f"**Why:** {metric.get('why', 'N/A')}")

            if "score_semantics" in metric:
                st.json(metric["score_semantics"])

        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------------------------
    # TWO-COLUMN METRIC GRID
    # ------------------------------------------------------------
    colA, colB = st.columns(2)

    for i, (name, metric) in enumerate(module_metrics.items()):
        target_col = colA if i % 2 == 0 else colB
        with target_col:
            show_metric(name, metric)

    st.markdown("</div>", unsafe_allow_html=True)

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
