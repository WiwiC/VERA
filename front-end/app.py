import streamlit as st
import time
import json
import base64
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.main import run_pipelines_iterator

# ==============================================================================
# 0. CONFIG & CONSTANTS
# ==============================================================================
st.set_page_config(page_title="VERA - AI Communication Coach", page_icon="🎙️", layout="wide")

# Directory setup
UPLOAD_DIR = Path("front-end/uploaded")
PROCESSED_DIR = Path("front-end/processed")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Initialize session state (Navigation)
# Use query params for source of truth to allow link-based navigation
query_params = st.query_params
if "page" in query_params:
    st.session_state.current_page = query_params["page"]

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

if "video_uploaded" not in st.session_state:
    st.session_state.video_uploaded = False
if "processing" not in st.session_state:
    st.session_state.processing = False
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "video_path" not in st.session_state:
    st.session_state.video_path = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None


# ==============================================================================
# 1. GLOBAL CSS (from globals.css)
# ==============================================================================
st.markdown("""
<style>
    /* Import Inter Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global Variables */
    :root {
        --background: #ffffff;
        --foreground: #030213;
        --card: #ffffff;
        --border: rgba(0, 0, 0, 0.1);
        --muted: #ececf0;
        --muted-foreground: #717182;
    }

    /* Prevent horizontal scroll from banner */
    div[data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
    }

    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: var(--background);
        color: var(--foreground);
    }

    .stApp {
        background: linear-gradient(to bottom right, #f8fafc, #e2e8f0);
    }

    /* Hide Streamlit branding - But keep Header visible for MainMenu */
    #MainMenu {visibility: visible;}
    footer {visibility: hidden;}
    header {visibility: visible;}

    /* Remove top padding from main container */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 20px;
        padding-left: 5rem;
        padding-right: 5rem;
        max-width: 100%;
    }

    /* --- NAVIGATION MENU (Injected into Header) --- */
    .nav-menu {
        position: fixed;
        top: 14px; /* Align vertically in standard header (approx 60px height) */
        left: 50%;
        transform: translateX(-50%);
        z-index: 999999; /* Above Streamlit header elements */
        display: flex;
        gap: 3rem;
        background: transparent;
    }

    .nav-link {
        color: #31333f !important; /* Black (Darker for white header) */
        text-decoration: none !important;
        font-weight: 400;
        font-size: 1rem;
        padding: 4px 0;
        border-bottom: none;
        transition: all 0.2s;
    }

    .nav-link:hover {
        color: #31333f !important; /* Gray-900 */
        text-decoration: none !important;
    }

    .nav-link-active {
        color: #31333f !important; /* Black */
        font-weight: 600;
        border-bottom: 2px solid #31333f;
        text-decoration: none !important;
    }

    /* Remove default link styles override */
    a.nav-link:hover, a.nav-link-active:hover {
        text-decoration: none;
    }

    /* --- PRIMARY BUTTON OVERRIDE --- */
    div.stButton > button[kind="primary"] {
        background-color: #245EDF !important;
        border-color: #245EDF !important;
        color: white !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1a4bbd !important;
        border-color: #1a4bbd !important;
        color: white !important;
    }
    div.stButton > button[kind="primary"]:focus:not(:active) {
        border-color: #245EDF !important;
        color: white !important;
    }

    /* --- HERO BANNER --- */
    .banner {
        width: 100vw;
        height: 250px;
        position: absolute;
        top: 40px; /* Standard header height */
        left: 50%;
        transform: translateX(-50%);
        overflow: hidden;
        z-index: 0;
        margin: 0;
        padding: 0;
    }

    .banner img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .banner-overlay {
        position: absolute;
        inset: 0;
        background: linear-gradient(to right, rgba(30,58,138,0.85), rgba(88,28,135,0.85));
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* Main Content Spacer */
    .content-spacer {
        margin-top: 300px; /* 60px header + 300px banner */
    }

    /* Metrics and other components */
    .upload-box {
        border: 2px dashed #93c5fd;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        background: white;
    }

    .metric-card {
        background: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }

    .metric-card:hover {
        background: #f9fafb;
    }

    /* Chevron Animation */
    details > summary .chevron-icon {
        transition: transform 0.2s ease-in-out;
        display: inline-block;
    }
    details[open] > summary .chevron-icon {
        transform: rotate(180deg);
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# Helper Function: Render Metric Column
# ==============================================================================
def render_metrics_column(title, icon, color, data, media_path=None):
    color_map = {
        "blue": {"bg": "#eff6ff", "border": "#bfdbfe", "text": "#1e40af", "score_bg": "#2563eb", "badge_bg": "#dbeafe", "badge_text": "#1e40af"},
        "purple": {"bg": "#f3e8ff", "border": "#d8b4fe", "text": "#6b21a8", "score_bg": "#7c3aed", "badge_bg": "#f3e8ff", "badge_text": "#6b21a8"},
        "green": {"bg": "#d1fae5", "border": "#a7f3d0", "text": "#065f46", "score_bg": "#059669", "badge_bg": "#dcfce7", "badge_text": "#166534"}
    }
    colors = color_map[color]

    metrics_html = ""
    for metric in data["metrics"]:
        score = metric["score"]
        pill_color = "#d1fae5" if score >= 70 else "#fef3c7" if score >= 40 else "#fee2e2"
        pill_text = "#065f46" if score >= 70 else "#92400e" if score >= 40 else "#991b1b"

        metrics_html += f"""<details style="background: white; border-radius: 0.5rem; margin-bottom: 0.75rem; border: 1px solid rgba(0,0,0,0.05); overflow: hidden;"><summary style="padding: 1rem; cursor: pointer; display: flex; align-items: center; justify-content: space-between; list-style: none; background: white; border-radius: 0.5rem; transaction: 0.2s;"><div style="display:flex; align-items:center; width:100%; justify-content:space-between;"><span style="font-weight: 500; color: #1f2937;">{metric['name']}</span><div style="display:flex; align-items:center; gap:8px;"><span style="background: {pill_color}; color: {pill_text}; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600;">{score}/100</span><span class="chevron-icon" style="color: #9ca3af; font-size: 0.8rem;">▼</span></div></div></summary><div style="padding: 1rem; border-top: 1px solid #f3f4f6; background: #fdfdfd; font-size: 0.9rem; color: #4b5563;"><div style="margin-bottom: 0.5rem;"><strong>Interpretation:</strong> {metric['interpretation']}</div><div style="margin-bottom: 1rem;"><strong>Coaching:</strong> {metric['coaching']}</div><div style="font-size: 0.8rem; background: #f9fafb; padding: 0.75rem; border-radius: 0.375rem; border: 1px solid #e5e7eb;"><div style="font-weight: 600; margin-bottom: 0.25rem; color: #374151;">Metrics understanding</div><div style="margin-bottom: 0.25rem;"><strong>What:</strong> {metric.get('what', 'N/A')}</div><div style="margin-bottom: 0.25rem;"><strong>How:</strong> {metric.get('how', 'N/A')}</div><div><strong>Why:</strong> {metric.get('why', 'N/A')}</div></div></div></details>"""

    # Add spacer if only 4 metrics (to align height with Body which has 5)
    if len(data["metrics"]) == 4:
        metrics_html += '<div style="height: 74.5px;"></div>'

    # Media Embedding Logic
    media_html = ""
    if media_path:
        path_obj = Path(media_path)
        if path_obj.exists():
            try:
                with open(path_obj, "rb") as f:
                    media_bytes = f.read()
                media_b64 = base64.b64encode(media_bytes).decode()

                # Determine MIME type
                if path_obj.suffix.lower() == ".mp3":
                    mime_type = "audio/mpeg"
                    media_tag = f'<audio controls style="width: 100%; margin-top: 10px; border-radius: 8px;"><source src="data:{mime_type};base64,{media_b64}" type="{mime_type}">Your browser does not support the audio element.</audio>'
                elif path_obj.suffix.lower() == ".mp4":
                    mime_type = "video/mp4"
                    media_tag = f'<video controls style="width: 100%; margin-top: 10px; border-radius: 8px;"><source src="data:{mime_type};base64,{media_b64}" type="{mime_type}">Your browser does not support the video element.</video>'
                else:
                    media_tag = ""

                if media_tag:
                    media_html = f"""
<div style="margin-top: auto; padding-top: 1rem; border-top: 1px solid {colors['border']};">
<div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 8px; color: {colors['text']};">Debug Media</div>
{media_tag}
</div>"""
            except Exception as e:
                print(f"Error loading media {media_path}: {e}")

    st.markdown(f"""
<div style="background: {colors['bg']}; border: 1px solid {colors['border']}; border-radius: 1rem; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); height: 100%; min-height: 600px; display: flex; flex-direction: column;">
<div style="text-align: center; margin-bottom: 2rem;">
<div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
<h3 style="color: {colors['text']}; font-size: 1.25rem; font-weight: 600; margin-bottom: 1.5rem;">{title}</h3>
<div style="background: {colors['score_bg']}; color: white; width: 120px; height: 120px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0 auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
<div style="font-size: 2.25rem; font-weight: 700; line-height: 1;">{data['globalScore']}</div>
<div style="font-size: 0.75rem; opacity: 0.9; margin-top: 4px;">Global Score</div>
</div>
</div>
<div style="flex-grow: 1;">
{metrics_html}
</div>
{media_html}
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# GLOBAL HEADER (ABSOLUTE TEXTURE) + NAVIGATION (ON TOP)
# ==============================================================================

# Determines active class
dash_class = "nav-link-active" if st.session_state.current_page == "Dashboard" else "nav-link"
hist_class = "nav-link-active" if st.session_state.current_page == "History" else "nav-link"

# Markdown HTML for Header + Nav Links
st.markdown(f"""
<!-- Top Navigation Bar -->
<div class="top-nav">
<div class="nav-menu">
<a href="?page=Dashboard" class="{dash_class}" target="_self">Dashboard</a>
<a href="?page=History" class="{hist_class}" target="_self">History</a>
</div>
</div>

<!-- Main Banner -->
<div class="banner">
<img src="https://images.unsplash.com/photo-1552664730-d307ca884978?w=1600&q=80" alt="VERA Banner">
<div class="banner-overlay">
<div style="text-align: center; color: white;">
<h1 style="font-size: 3rem; margin-bottom: 0.1rem; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">VERA - Voice, Expression & Reaction Analyzer</h1>
<p style="font-size: 1.5rem; opacity: 0.9; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">Non-verbal Communication Coach</p>
</div>
</div>
</div>
""", unsafe_allow_html=True)

# 3. Content Spacer to push page down
st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)


# ==============================================================================
# PAGE: HISTORY
# ==============================================================================
def render_history():
    st.markdown("## History Analysis") # Removed Icon
    st.markdown("Revisit your past coaching sessions.")
    st.markdown("---")

    processed_folders = [f for f in PROCESSED_DIR.iterdir() if f.is_dir()]
    processed_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    if not processed_folders:
        st.info("No analysis history found. Go to Dashboard to start your first analysis!")
        return

    for folder in processed_folders:
        json_path = folder / "results_global_enriched.json"

        if json_path.exists():
            try:
                with open(json_path) as f:
                    data = json.load(f)

                audio_score = data.get("audio", {}).get("global", {}).get("score", "N/A")
                face_score = data.get("face", {}).get("global", {}).get("score", "N/A")
                body_score = data.get("body", {}).get("global", {}).get("score", "N/A")

                # Check for Video for Thumbnail
                potential_video_path = UPLOAD_DIR / f"{folder.name}.mp4"

                with st.container():
                    col_thumb, col_info, col_scores, col_action = st.columns([2, 3, 3, 2])

                    with col_thumb:
                        if potential_video_path.exists():
                             # Show video as thumbnail (user request)
                             st.video(str(potential_video_path))
                        else:
                             st.markdown("<div style='font-size: 3rem; text-align: center;'>🎥</div>", unsafe_allow_html=True)

                    with col_info:
                        st.markdown(f"### {folder.name}")
                        st.caption(f"Processed: {time.ctime(folder.stat().st_mtime)}")

                    with col_scores:
                        st.markdown(f"""
<div style="display: flex; gap: 12px; align-items: center; margin-top: 10px;">
<div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
<div style="background: #2563eb; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
{audio_score}
</div>
<span style="font-size: 0.75rem; color: #1e40af; font-weight: 500;">Audio</span>
</div>
<div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
<div style="background: #7c3aed; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
{face_score}
</div>
<span style="font-size: 0.75rem; color: #6b21a8; font-weight: 500;">Face</span>
</div>
<div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
<div style="background: #059669; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
{body_score}
</div>
<span style="font-size: 0.75rem; color: #065f46; font-weight: 500;">Body</span>
</div>
</div>
""", unsafe_allow_html=True)

                    with col_action:
                        st.write("") # Spacer
                        if st.button("See Details ➡️", key=f"details_{folder.name}"):
                            st.session_state.analysis_results = data
                            st.session_state.video_path = str(potential_video_path) if potential_video_path.exists() else None
                            st.session_state.uploaded_file = None
                            st.session_state.video_uploaded = potential_video_path.exists()
                            st.session_state.show_results = True
                            st.session_state.processing = False
                            st.session_state.current_page = "Dashboard"
                            st.query_params["page"] = "Dashboard"
                            st.rerun()

                    st.markdown("---")
            except Exception as e:
                st.error(f"Error loading {folder.name}: {e}")


# ==============================================================================
# PAGE: DASHBOARD
# ==============================================================================
def render_dashboard():
    # Removed Local Banner (Now Global)

    # 3. VIDEO UPLOADER SECTION (Grid: 1/3 Upload, 2/3 Preview)
    with st.container():

        col1, col2 = st.columns([1, 1])

        # Left: What is VERA section
        with col1:
            st.markdown("## What is VERA ?")
            st.markdown("""
            <div style="color: #4b5563; line-height: 1.6; margin-bottom: 0.5rem;">
                <b>VERA</b> is an advanced multi-modal AI pipeline designed to analyze communication performance by leveraging computer vision and audio signal processing.
                <br>
                It evaluates user's:
                <br>
                <b>- Face</b> (micro-expressions, gaze, head down ratio...),
                <br>
                <b>- Body language</b> (posture, gestures, stability...),
                <br>
                <b>- Audio</b> (speech rate, pause ratio, pitch dynamics...),
                <br>
                and provides data-driven feedback to help users improve their communication skills.
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### Upload your video")
            uploaded_file = st.file_uploader(
                "Drag & Drop your video here or click to browse",
                type=["mp4", "mov"],
                label_visibility="collapsed"
            )
            st.markdown("<p style='font-size: 0.9rem; color: #6b7280; margin-top: 0.5rem;'>* <b>Recommended:</b> 1:00 - 2:00 min video max! Make sure your body is visible from the hips to the head.</p>", unsafe_allow_html=True)

            if uploaded_file:
                # Save file locally
                video_path = UPLOAD_DIR / uploaded_file.name
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.session_state.video_uploaded = True
                st.session_state.uploaded_file = uploaded_file
                st.session_state.video_path = str(video_path)
                st.success(f"✓ {uploaded_file.name}")

        # Right: Video Preview (2/3)
        with col2:
            st.markdown("## Preview")

            # Handle both FileUploader object AND string path (from History redirect)
            preview_source = st.session_state.uploaded_file if st.session_state.uploaded_file else st.session_state.video_path

            if st.session_state.video_uploaded and preview_source:
                # Display video
                st.video(preview_source)

                if st.button("▶️ Start Analysis", key="start_btn", disabled=st.session_state.processing, use_container_width=True, type="primary"):
                    st.session_state.processing = True
                    st.session_state.show_results = False
                    st.rerun()

            else:
                st.markdown("""
                <div style="background: white; border-radius: 0.5rem; height: 315px; display: flex; align-items: center; justify-content: center; color: #9ca3af; border: 1px dashed #e5e7eb;">
                    <div style="text-align: center;">
                        <div style="font-size: 3rem; margin-bottom: 0.5rem; opacity: 0.5;">No Video</div>
                        <p>Upload a video to get started</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # 4. PROCESSING SECTION (Full Width)
    if st.session_state.processing:
        # Processing State: Disabled Button + Inline Progress
        st.markdown("""
            <button style="
                width: 100%;
                padding: 0.75rem 2rem;
                background-color: #f3f4f6;
                color: #9ca3af;
                border: 1px solid #e5e7eb;
                border-radius: 0.5rem;
                cursor: not-allowed;
                font-weight: 600;
                margin-bottom: 20px;
            ">
                ⏳ Analysis in Progress...
            </button>
            """, unsafe_allow_html=True)

        # Status placeholders (Full Width Container)
        with st.container():
            progress_bar = st.progress(0, text="Initializing analysis engine...")
            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

            status_placeholder = st.empty()
            audio_status = st.empty()
            face_status = st.empty()
            body_status = st.empty()

            # Helper for inline status
            def show_inline_status(name, state, custom_text=None):
                colors = {
                    "waiting": "#94a3b8",
                    "processing": "#3b82f6",
                    "done": "#10b981",
                    "error": "#ef4444"
                }
                icons = {
                    "waiting": "⏳",
                    "processing": "🔄",
                    "done": "✅",
                    "error": "❌"
                }
                display_text = custom_text if custom_text else state

                return f"""
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 16px;
                    background-color: white;
                    border: 1px solid #e2e8f0;
                    border-left: 4px solid {colors.get(state, "#94a3b8")};
                    border-radius: 8px;
                    transition: all 0.3s ease;
                    margin-bottom: 8px;
                ">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size: 1.1em;">{icons.get(state, "ℹ️")}</span>
                        <span style="font-weight: 500; color: #334155;">{name}</span>
                    </div>
                    <span style="color: {colors.get(state, "#334155")}; font-weight: 600; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px;">
                        {display_text}
                    </span>
                </div>
                """

            # Initialize Statuses
            audio_status.markdown(show_inline_status("Audio Pipeline", "waiting"), unsafe_allow_html=True)
            face_status.markdown(show_inline_status("Face Pipeline", "waiting"), unsafe_allow_html=True)
            body_status.markdown(show_inline_status("Body Pipeline", "waiting"), unsafe_allow_html=True)

            # Run Backend Pipeline
            def update_bar(p, status_text=None):
                # Clamp to 0-100
                val = max(0, min(100, int(p * 100)))
                progress_bar.progress(val, text=f"Analyzing... {val}%")

                # Update status cards based on progress phase (heuristic) or explicit status
                if status_text:
                    if p <= 0.05:
                         audio_status.markdown(show_inline_status("Audio Pipeline", "processing", custom_text=status_text), unsafe_allow_html=True)
                    elif p < 0.60:
                        # Audio done, Face processing
                        audio_status.markdown(show_inline_status("Audio Pipeline", "done"), unsafe_allow_html=True)
                        face_status.markdown(show_inline_status("Face Pipeline", "processing", custom_text=status_text), unsafe_allow_html=True)
                    else:
                        # Face done, Body processing
                        face_status.markdown(show_inline_status("Face Pipeline", "done"), unsafe_allow_html=True)
                        body_status.markdown(show_inline_status("Body Pipeline", "processing", custom_text=status_text), unsafe_allow_html=True)

            iterator = run_pipelines_iterator(st.session_state.video_path, output_base_dir=str(PROCESSED_DIR), progress_callback=update_bar)
            final_results = {}
            output_dir = None

            for event_type, *args in iterator:
                if event_type == "start":
                    output_dir = args[0]
                    # progress_bar handled by callback

                elif event_type == "progress":
                    module, _ = args
                    if module == "audio":
                        audio_status.markdown(show_inline_status("Audio Pipeline", "done"), unsafe_allow_html=True)
                        # Start Face (implied next)
                        face_status.markdown(show_inline_status("Face Pipeline", "processing"), unsafe_allow_html=True)

                    elif module == "face":
                        face_status.markdown(show_inline_status("Face Pipeline", "done"), unsafe_allow_html=True)
                        # Start Body (implied next)
                        body_status.markdown(show_inline_status("Body Pipeline", "processing"), unsafe_allow_html=True)

                    elif module == "body":
                        body_status.markdown(show_inline_status("Body Pipeline", "done"), unsafe_allow_html=True)

                elif event_type == "error":
                    module, err = args
                    st.error(f"Error in {module}: {err}")

                elif event_type == "final":
                    output_dir, final_results = args
                    progress_bar.progress(100, text="All Analysis Complete!")

            # Load Enriched Results (JSON)
            if output_dir:
                json_path = output_dir / "results_global_enriched.json"
                if json_path.exists():
                    with open(json_path) as f:
                        st.session_state.analysis_results = json.load(f)
                else:
                    st.error("Results file not found!")

            time.sleep(1.0)
            st.session_state.processing = False
            st.session_state.show_results = True
            st.rerun()

    # 5. RESULTS SECTION (3 Columns: Audio, Face, Body)
    if st.session_state.show_results:
        #st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid rgba(49, 51, 63, 0.2);' />", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-top: 12px; margin-bottom: 20px; font-weight: 600; color: #111827;'>Detailed analysis</h2>", unsafe_allow_html=True)

        analysis_data = st.session_state.analysis_results

        # Calculate Debug Media Paths
        processed_folder = None
        if st.session_state.video_path:
            video_stem = Path(st.session_state.video_path).stem
            processed_folder = PROCESSED_DIR / video_stem

        debug_audio = processed_folder / "debug_audio.mp3" if processed_folder else None
        debug_face = processed_folder / "debug_face.mp4" if processed_folder else None
        debug_body = processed_folder / "debug_pose.mp4" if processed_folder else None

        # 3-Column Layout
        col_audio, col_face, col_body = st.columns(3)

        with col_audio:
            if "audio" in analysis_data:
                # Re-mapping to match render_metrics_column expectation:
                # Expected: data['globalScore'], data['metrics'] list
                audio_data = {
                    "globalScore": analysis_data["audio"]["global"]["score"],
                    "metrics": list(analysis_data["audio"]["metrics"].values())
                }
                render_metrics_column("Audio", "🎤", "blue", audio_data, media_path=debug_audio)

        with col_face:
            if "face" in analysis_data:
                face_data = {
                    "globalScore": analysis_data["face"]["global"]["score"],
                    "metrics": list(analysis_data["face"]["metrics"].values())
                }
                render_metrics_column("Face Expression", "😊", "purple", face_data, media_path=debug_face)

        with col_body:
            if "body" in analysis_data:
                body_data = {
                    "globalScore": analysis_data["body"]["global"]["score"],
                    "metrics": list(analysis_data["body"]["metrics"].values())
                }
                render_metrics_column("Body Language", "🤸", "green", body_data, media_path=debug_body)

        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# PAGE ROUTER
# ==============================================================================
if st.session_state.current_page == "Dashboard":
    render_dashboard()
elif st.session_state.current_page == "History":
    render_history()
