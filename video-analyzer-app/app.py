import streamlit as st
import os
import tempfile
import json
from pathlib import Path
import sys
import base64

# ----------------------------------------------------------
# COLOR SCORES
# ----------------------------------------------------------
def score_color(score):
    if score > 70:
        return "#7DCE82"   # green
    elif score >= 40:
        return "#E8E810"   # orange
    else:
        return "#F25F5C"   # red

# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------
st.set_page_config(
    page_title="VERA Analyzer",
    page_icon="🎥",
    layout="wide"
)

# ----------------------------------------------------------
# PROJECT IMPORTS
# ----------------------------------------------------------
current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.main import run_pipelines, run_pipelines_iterator


# ----------------------------------------------------------
# UTILITY: Read results
# ----------------------------------------------------------
def load_results_from_dir(output_dir):
    output_dir = Path(output_dir)
    outputs = {}

    enriched = output_dir / "results_global_enriched.json"
    if enriched.exists():
        outputs["results_global_enriched.json"] = enriched.read_text()

    debug_files = {
        "audio": "debug_audio.mp3",
        "body": "debug_pose.mp4",
        "face": "debug_face.mp4",
    }

    for module in ["audio", "body", "face"]:
        csv_path = output_dir / f"metrics_{module}.csv"
        if csv_path.exists():
            outputs[f"metrics_{module}.csv"] = csv_path.read_text()

        debug_path = output_dir / debug_files[module]
        if debug_path.exists():
            outputs[debug_files[module]] = debug_path.read_bytes()

    return outputs


# ----------------------------------------------------------
# SESSION STATE INITIALIZATION
# ----------------------------------------------------------
if "page" not in st.session_state:
    video_param = st.query_params.get("video")
    if video_param:
        folder = Path("data/processed") / video_param
        if folder.exists():
            st.session_state.results_files = load_results_from_dir(folder)
            st.session_state.page = "analyze"
            st.session_state.current_video_name = video_param
        else:
            st.session_state.page = "landing"
    else:
        st.session_state.page = "landing"

if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None


# ----------------------------------------------------------
# UNIVERSAL SIMPLE CSS (minimal & clean)
# ----------------------------------------------------------
st.markdown("""
<style>
    body { background-color: #ECECFF !important; }

    .vera-card {
        background: white;
        #padding: 22px;
        border-radius: 14px;
        #box-shadow: 0 3px 12px rgba(0,0,0,0.07);
        margin-bottom: 18px;
    }

    .vera-section-title {
        font-size: 26px;
        font-weight: 700;
        color: #2A2B7A;
        margin-bottom: 14px;
        margin-top: 6px;
    }

    .vera-subtitle {
        font-size: 18px;
        font-weight: 600;
        color: #2A2B7A;
    }

    .metric-row {
        display: flex;
        justify-content: flex-start;
        align-items: center;
        gap: 12px;
        margin-bottom: 6px;
    }

    .metric-title-text {
        font-size: 18px;
        font-weight: 600;
        color: #2A2B7A;
    }

    .metric-score-pill {
        background: #E6DEFF;
        padding: 6px 14px;
        border-radius: 12px;
        font-size: 18px;
        font-weight: 700;
        color: #1A2080;
    }

    /* Global Score Cards */
    .score-grid {
        display: flex;
        flex-direction: column;
        gap: 14px;
    }
    .score-item {
        flex: 1;
        text-align: center;
        background: #ECECFF;
        border-radius: 14px;
        padding: 20px;
    }
    .score-value {
        font-size: 34px;
        font-weight: 800;
        color: #1A2080;
        margin-top: -4px;
    }
</style>
""", unsafe_allow_html=True)



# ----------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------
with st.sidebar:
    logo_path = current_dir / "logoVERA.png"
    if logo_path.exists():
        st.image(str(logo_path), width=80)

    st.title("VERA Analyzer")

    if st.button("🏡 New Analysis", use_container_width=True):
        st.session_state.page = "landing"
        st.session_state.uploaded_video = None
        st.session_state.results_files = None
        st.query_params.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("📜 History")

    processed_dir = Path("data/processed")
    videos = []
    if processed_dir.exists():
        for d in processed_dir.iterdir():
            if d.is_dir() and (d / "results_global_enriched.json").exists():
                videos.append(d.name)

    videos.sort(reverse=True)

    if videos:
        def on_select():
            sel = st.session_state.history_selector
            folder = processed_dir / sel
            st.session_state.results_files = load_results_from_dir(folder)
            st.session_state.current_video_name = sel
            st.session_state.page = "analyze"
            st.query_params["video"] = sel

        current = st.session_state.get("current_video_name")
        default_idx = videos.index(current) if current in videos else None

        st.radio(
            "Select a past analysis:",
            options=videos,
            index=default_idx,
            key="history_selector",
            on_change=on_select,
        )
    else:
        st.info("No history found.")



# ----------------------------------------------------------
# VIDEO PROCESSING
# ----------------------------------------------------------
def process_video(video_path):
    progress = st.progress(0)
    status_box = st.container()

    # Create placeholders for each processing step
    audio_msg = status_box.empty()
    face_msg = status_box.empty()
    body_msg = status_box.empty()

    iterator = run_pipelines_iterator(video_path)
    completed = 0
    total = 3  # audio, face, body

    steps_ui = {
        "audio": audio_msg,
        "face": face_msg,
        "body": body_msg,
    }

    # Initialize UI
    audio_msg.info("🎤 Audio: processing…")
    face_msg.info("🙂 Face: waiting…")
    body_msg.info("🕺 Body: waiting…")

    outdir = None

    for event_type, *args in iterator:
        if event_type == "progress":
            module, _ = args

            # Update progress bar
            completed += 1
            progress.progress(completed / total)

            # Update visual step indicator
            steps_ui[module].success(f"✔ {module.capitalize()}: done!")

        elif event_type == "final":
            outdir, results = args

    progress.progress(1.0)

    return load_results_from_dir(outdir)

# ----------------------------------------------------------
# LANDING PAGE
# ----------------------------------------------------------
def landing_page():
    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Logo
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        logo_path = current_dir / "logoVERA.png"
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)

    st.markdown("<h1 style='text-align:center;'>VERA Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;font-size:18px;color:#303082;'>Analyze your communication performance in pitches, interviews, or presentations.</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            with st.container(border=True):
                uploaded = st.file_uploader("Upload your video:", type=["mp4", "mov", "avi"])
                if uploaded:
                    st.session_state.uploaded_video = uploaded
                    st.success("Uploaded!")

    st.markdown("<br>", unsafe_allow_html=True)

    colA, colB, colC = st.columns([1, 2, 1])
    with colB:
        if st.button("🚀 Start Analyzer", use_container_width=True):
            if st.session_state.uploaded_video is None:
                st.error("Please upload a video first.")
                return

            file = st.session_state.uploaded_video
            temp_path = f"/tmp/{Path(file.name).name}"
            open(temp_path, "wb").write(file.read())

            st.session_state.results_files = process_video(temp_path)
            st.session_state.page = "analyze"
            st.session_state.current_video_name = Path(file.name).stem
            st.query_params["video"] = Path(file.name).stem
            st.rerun()



# ----------------------------------------------------------
# ANALYZER PAGE
# ----------------------------------------------------------
def analysis_page():

    results = st.session_state.results_files
    if not results:
        st.error("No results found.")
        return

    enriched = json.loads(results["results_global_enriched.json"])

    # -------------------------
    # VIDEO + GLOBAL SCORES ROW
    # -------------------------
    st.markdown("<div class='vera-section-title'>VERA COACHING</div>", unsafe_allow_html=True)

    col_video, col_scores = st.columns([2, 1.3])

    with col_video:
        st.markdown("<div class='vera-card'>", unsafe_allow_html=True)
        st.subheader("Your Video")
        st.video(st.session_state.uploaded_video)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_scores:
        st.markdown("<div class='vera-card'>", unsafe_allow_html=True)
        st.subheader("Global Scores")

        def get_score(m):
            return int(enriched.get(m, {}).get("global", {}).get("score", 0))

        st.markdown("""
            <div class="score-grid">
                <div class="score-item">
                    <div>🎤 Audio</div>
                    <div class="score-value">""" + str(get_score("audio")) + """</div>
                </div>
                <div class="score-item">
                    <div>🕺 Body</div>
                    <div class="score-value">""" + str(get_score("body")) + """</div>
                </div>
                <div class="score-item">
                    <div>🙂 Face</div>
                    <div class="score-value">""" + str(get_score("face")) + """</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


    # -------------------------
    # DETAILED METRICS SECTION
    # -------------------------
    st.markdown("<div class='vera-section-title'>Detailed Analysis</div>", unsafe_allow_html=True)

    tabs = st.tabs(["🎧 Audio", "🕺 Body", "🙂 Face"])
    modules = ["audio", "body", "face"]

    for tab, module in zip(tabs, modules):
        with tab:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='vera-card'>", unsafe_allow_html=True)

            metrics = enriched[module]["metrics"]
            for name, metric in metrics.items():
                title = name.replace("_"," ").title()
                score = int(metric.get("score", 0))

                st.markdown(f"""
                <div class="metric-row">
                    <div class="metric-title-text">{title}</div>
                    <div class="metric-score-pill" style="background:{score_color(score)}; color:white;">{score}</div>
                </div>
                """, unsafe_allow_html=True)

                interpretation = (
                    metric.get("interpretation")
                        or metric.get("communication_interpretation")
                )

                if interpretation:
                    st.markdown(f"""
                    <div style="
                        background-color:#F5F2FF;
                        border-left: 4px solid #A18CFF;
                        padding: 12px 14px;
                        border-radius: 6px;
                        margin: 10px 0 14px 0;
                        font-size: 15px;
                        color: #2A2B7A;
                        line-height: 1.45;
                    ">
                    <b>Analysis:</b> {interpretation}
                    </div>
                    """, unsafe_allow_html=True)

                coaching = metric.get("coaching")
                if coaching:
                    st.markdown(f"""
                    <div style="
                        background-color:#E9E4FF;
                        border-left: 6px solid #6A4CFF;
                        padding: 14px 16px;
                        border-radius: 8px;
                        margin: 10px 0;
                    ">
                    <b style="color:#2A2B7A;">Coaching:</b> {coaching}
                    </div>
                    """, unsafe_allow_html=True)

                with st.expander("Info"):
                    what = metric.get("what", "N/A")
                    how = metric.get("how", "N/A")
                    why = metric.get("why", "N/A")

                    st.markdown(f"""
                    <div style="margin-bottom:10px;">
                        <p><b>What do we measure? </b> {what}</p>
                        <p><b>How do we measure? </b> {how}</p>
                        <p><b>Why do we measure this? </b> {why}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

            # -------------------------
            # DEBUG FILE DOWNLOAD LINK
            # -------------------------
            debug_key = {
                "audio": "debug_audio.mp3",
                "body": "debug_pose.mp4",
                "face": "debug_face.mp4",
            }[module]

            if debug_key in results:
                st.markdown("###### Debug File (Download Required)")

                file_bytes = results[debug_key]
                file_name = debug_key

                st.download_button(
                    label=f"⬇️ Download {file_name}",
                    data=file_bytes,
                    file_name=file_name,
                    mime="audio/mpeg" if file_name.endswith(".mp3") else "video/mp4",
                    use_container_width=True
                )
            else:
                st.info("No debug file available for this module.")

            st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------
# ROUTING
# ----------------------------------------------------------
if st.session_state.page == "landing":
    landing_page()
else:
    analysis_page()
