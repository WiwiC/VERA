import streamlit as st
import time
from pathlib import Path

# ==============================================================================
# 0. PAGE CONFIG & SESSION STATE
# ==============================================================================
st.set_page_config(
    page_title="VERA - AI Communication Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "video_uploaded" not in st.session_state:
    st.session_state.video_uploaded = False
if "processing" not in st.session_state:
    st.session_state.processing = False
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

# Mock data (from mockData.ts)
MOCK_DATA = {
    "audio": {
        "globalScore": 78,
        "metrics": [
            {
                "name": "Speech Rate",
                "score": 85,
                "interpretation": "Optimal pacing - clear and engaging",
                "coaching": "Maintain this natural rhythm in future presentations"
            },
            {
                "name": "Pause Ratio",
                "score": 72,
                "interpretation": "Good use of pauses for emphasis",
                "coaching": "Consider adding slightly longer pauses before key points"
            },
            {
                "name": "Pitch Dynamics",
                "score": 68,
                "interpretation": "Moderate vocal variety",
                "coaching": "Expand your pitch range to add more emotional color"
            },
            {
                "name": "Volume Dynamics",
                "score": 80,
                "interpretation": "Strong volume control and projection",
                "coaching": "Excellent energy - keep leveraging volume for emphasis"
            },
            {
                "name": "Vocal Punch",
                "score": 82,
                "interpretation": "High energy and conviction",
                "coaching": "Your vocal intensity effectively captures attention"
            }
        ]
    },
    "face": {
        "globalScore": 71,
        "metrics": [
            {
                "name": "Head Stability",
                "score": 76,
                "interpretation": "Steady and confident posture",
                "coaching": "Good control - avoid excessive nodding"
            },
            {
                "name": "Gaze Stability",
                "score": 65,
                "interpretation": "Moderate eye contact",
                "coaching": "Hold gaze 3-5 seconds per person to build connection"
            },
            {
                "name": "Smile Activation",
                "score": 70,
                "interpretation": "Warm and approachable expression",
                "coaching": "Authentic smiles detected - continue being genuine"
            },
            {
                "name": "Head Down Ratio",
                "score": 74,
                "interpretation": "Minimal downward gaze",
                "coaching": "Keep chin level to project confidence and authority"
            }
        ]
    },
    "body": {
        "globalScore": 83,
        "metrics": [
            {
                "name": "Gesture Magnitude",
                "score": 88,
                "interpretation": "Dynamic and expressive movements",
                "coaching": "Strong gestures amplify your message effectively"
            },
            {
                "name": "Gesture Activity",
                "score": 82,
                "interpretation": "Well-timed hand movements",
                "coaching": "Good balance - gestures align with speech rhythm"
            },
            {
                "name": "Gesture Stability",
                "score": 79,
                "interpretation": "Controlled and purposeful",
                "coaching": "Minimize fidgeting during pauses for added gravitas"
            },
            {
                "name": "Body Sway",
                "score": 85,
                "interpretation": "Natural weight shifts and movement",
                "coaching": "Your movement keeps the audience engaged"
            },
            {
                "name": "Posture Openness",
                "score": 81,
                "interpretation": "Open and welcoming stance",
                "coaching": "Excellent - avoid crossing arms to maintain accessibility"
            }
        ]
    }
}


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

    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: var(--background);
        color: var(--foreground);
    }

    .stApp {
        background: linear-gradient(to bottom right, #f8fafc, #e2e8f0);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Remove top padding from main container */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 20px;
        padding-left: 5rem;
        padding-right: 5rem;
        max-width: 100%;
    }

    /* Custom Components */
    /* Custom Components */
    .banner {
        width: 100vw;
        position: relative;
        left: 50%;
        margin-left: -50vw;
        height: 256px;
        overflow: hidden;
        border-radius: 0;
        margin-bottom: 3rem;
        margin-top: 0;
    }

    .banner img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .banner-overlay {
        position: absolute;
        inset: 0;
        background: linear-gradient(to right, rgba(30,58,138,0.8), rgba(88,28,135,0.8));
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
    }

    .upload-box {
        border: 2px dashed #93c5fd;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        background: white;
    }

    .upload-box:hover {
        border-color: #3b82f6;
        background: #eff6ff;
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

    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
    }

    .score-green {
        background: #d1fae5;
        color: #065f46;
    }

    .score-yellow {
        background: #fef3c7;
        color: #92400e;
    }

    .score-red {
        background: #fee2e2;
        color: #991b1b;
    }

    /* Button Styles */
    .stButton button {
        background: #2563eb;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 0.5rem;
        font-weight: 600;
        transition: background 0.2s;
    }

    .stButton button:hover {
        background: #1d4ed8;
    }

    /* Processing Modal */
    .modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }

    .modal-content {
        background: white;
        border-radius: 1rem;
        padding: 2rem;
        max-width: 28rem;
        width: 90%;
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
    }

    .pipeline-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
    }

    .progress-bar {
        width: 100%;
        height: 0.5rem;
        background: #e5e7eb;
        border-radius: 9999px;
        overflow: hidden;
        margin-top: 2rem;
    }

    .progress-fill {
        height: 100%;
        background: #2563eb;
        transition: width 0.3s ease-linear;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. HEADER BANNER
# ==============================================================================
st.markdown("""
<div class="banner">
    <img src="https://images.unsplash.com/photo-1552664730-d307ca884978?w=1600&q=80" alt="VERA Banner">
    <div class="banner-overlay">
        <div style="text-align: center;">
            <h1 style="font-size: 3rem; margin-bottom: 1rem;">VERA</h1>
            <p style="font-size: 1.25rem; opacity: 0.9;">Advanced Multi-Modal AI Communication Analysis</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 3. VIDEO UPLOADER SECTION (Grid: 1/3 Upload, 2/3 Preview)
# ==============================================================================
with st.container():

    col1, col2 = st.columns([1, 1])

    # Left: What is VERA section
    with col1:
        st.markdown("## What is VERA ?")
        st.markdown("""
        <div style="color: #4b5563; line-height: 1.6; margin-bottom: 2rem;">
            <b>VERA</b> is an advanced multi-modal pipeline designed to analyze communication performance by leveraging computer vision and audio signal processing.
            <br><br>
            It evaluates user's <b>Face</b> (micro-expressions, gaze...) <b>Body language</b> (posture, gestures...), and <b>Audio</b> (tonality, pacing..), and provides data-driven feedback to help users improve their communication skills.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Upload your video")
        uploaded_file = st.file_uploader(
            "Drag & Drop your video here or click to browse",
            type=["mp4", "mov", "avi"],
            label_visibility="collapsed"
        )
        st.markdown("<p style='font-size: 0.8rem; color: #6b7280; margin-top: 0.5rem;'>* Make sure your body is visible from the hips to the head</p>", unsafe_allow_html=True)

        if uploaded_file:
            st.session_state.video_uploaded = True
            st.session_state.uploaded_file = uploaded_file
            st.success(f"✓ {uploaded_file.name}")

    # Right: Video Preview (2/3)
    with col2:
        st.markdown("## Preview")

        if st.session_state.video_uploaded and st.session_state.uploaded_file:
            # Display video
            st.video(st.session_state.uploaded_file)



            if not st.session_state.processing:
                # Normal State: Start Button
                if st.button("▶️ Start Analysis", key="start_btn", use_container_width=True):
                    st.session_state.processing = True
                    st.session_state.show_results = False
                    st.rerun()
            else:
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

                # Status placeholders
                progress_bar = st.progress(0, text="Starting analysis...")
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

                audio_status = st.empty()
                face_status = st.empty()
                body_status = st.empty()

                # Helper for inline status
                def show_inline_status(name, state):
                    icons = {"waiting": "⏳", "processing": "🔄", "done": "✅"}
                    colors = {"waiting": "#94a3b8", "processing": "#3b82f6", "done": "#10b981"}
                    bg_colors = {"waiting": "#f8fafc", "processing": "#eff6ff", "done": "#f0fdf4"}
                    border_colors = {"waiting": "#e2e8f0", "processing": "#bfdbfe", "done": "#bbf7d0"}

                    return f"""
                    <div style="
                        display: flex; align-items: center; justify-content: space-between;
                        padding: 10px 14px; margin-bottom: 8px;
                        background-color: {bg_colors[state]};
                        border: 1px solid {border_colors[state]};
                        border-radius: 8px;
                        transition: all 0.3s ease;
                    ">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-size: 1.1em;">{icons[state]}</span>
                            <span style="font-weight: 500; color: #334155;">{name}</span>
                        </div>
                        <span style="color: {colors[state]}; font-weight: 600; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px;">
                            {state}
                        </span>
                    </div>
                    """

                time.sleep(0.8)

                # Audio
                audio_status.markdown(show_inline_status("Audio Pipeline", "processing"), unsafe_allow_html=True)
                progress_bar.progress(33, text="Analyzing Audio...")
                time.sleep(1.5)
                audio_status.markdown(show_inline_status("Audio Pipeline", "done"), unsafe_allow_html=True)

                # Face
                face_status.markdown(show_inline_status("Face Pipeline", "processing"), unsafe_allow_html=True)
                progress_bar.progress(66, text="Analyzing Facial Expressions...")
                time.sleep(1.5)
                face_status.markdown(show_inline_status("Face Pipeline", "done"), unsafe_allow_html=True)

                # Body
                body_status.markdown(show_inline_status("Body Pipeline", "processing"), unsafe_allow_html=True)
                progress_bar.progress(90, text="Analyzing Body Language...")
                time.sleep(1.5)
                body_status.markdown(show_inline_status("Body Pipeline", "done"), unsafe_allow_html=True)

                progress_bar.progress(100, text="Analysis Complete!")
                time.sleep(0.5)

                st.session_state.processing = False
                st.session_state.show_results = True
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




# ==============================================================================
# 5. RESULTS SECTION (3 Columns: Audio, Face, Body)
# ==============================================================================
if st.session_state.show_results:
    st.markdown("---")

    # Helper function for metric column
    def render_metrics_column(title, icon, color, data):
        color_map = {
            "blue": {"bg": "#eff6ff", "border": "#bfdbfe", "text": "#1e40af", "score_bg": "#2563eb", "badge_bg": "#dbeafe", "badge_text": "#1e40af"},
            "purple": {"bg": "#f3e8ff", "border": "#d8b4fe", "text": "#6b21a8", "score_bg": "#7c3aed", "badge_bg": "#f3e8ff", "badge_text": "#6b21a8"},
            "green": {"bg": "#d1fae5", "border": "#a7f3d0", "text": "#065f46", "score_bg": "#059669", "badge_bg": "#dcfce7", "badge_text": "#166534"}
        }
        colors = color_map[color]

        # Generate HTML for indicators
        metrics_html = ""
        for metric in data["metrics"]:
            score = metric["score"]
            badge_class = "score-green" if score >= 70 else "score-yellow" if score >= 40 else "score-red"

            # Badge Color Logic for the pill inside the row
            pill_color = "#d1fae5" if score >= 70 else "#fef3c7" if score >= 40 else "#fee2e2"
            pill_text = "#065f46" if score >= 70 else "#92400e" if score >= 40 else "#991b1b"

            metrics_html += f"""<details style="background: white; border-radius: 0.5rem; margin-bottom: 0.75rem; border: 1px solid rgba(0,0,0,0.05); overflow: hidden;"><summary style="padding: 1rem; cursor: pointer; display: flex; align-items: center; justify-content: space-between; list-style: none; background: white; border-radius: 0.5rem; transaction: 0.2s;"><span style="font-weight: 500; color: #1f2937;">{metric['name']}</span><span style="background: {pill_color}; color: {pill_text}; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600;">{score}/100</span></summary><div style="padding: 1rem; border-top: 1px solid #f3f4f6; background: #fdfdfd; font-size: 0.9rem; color: #4b5563;"><div style="margin-bottom: 0.5rem;"><strong>Interpretation:</strong> {metric['interpretation']}</div><div><strong>Coaching:</strong> {metric['coaching']}</div></div></details>"""

        # Main Card HTML
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
</div>
""", unsafe_allow_html=True)

    # 3-Column Layout
    col_audio, col_face, col_body = st.columns(3)

    with col_audio:
        render_metrics_column("Audio", "🎤", "blue", MOCK_DATA["audio"])

    with col_face:
        render_metrics_column("Face Expression", "😊", "purple", MOCK_DATA["face"])

    with col_body:
        render_metrics_column("Body Language", "🤸", "green", MOCK_DATA["body"])

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
