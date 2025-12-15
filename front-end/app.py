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

    /* Custom Components */
    .banner {
        position: relative;
        height: 256px;
        width: 100%;
        overflow: hidden;
        border-radius: 0;
        margin-bottom: 3rem;
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
    st.markdown('<div style="background: white; border-radius: 0.75rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); padding: 2rem; margin-bottom: 2rem;">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    # Left: Upload Box (1/3)
    with col1:
        st.markdown("## Upload Your Video")
        uploaded_file = st.file_uploader(
            "Drag & Drop your video here or click to browse",
            type=["mp4", "mov", "avi"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            st.session_state.video_uploaded = True
            st.session_state.uploaded_file = uploaded_file
            st.success(f"✓ {uploaded_file.name}")
        else:
            st.markdown("""
            <div class="upload-box">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📁</div>
                <p style="color: #6b7280; margin-bottom: 0.5rem;">Drag & Drop your video here</p>
                <p style="color: #9ca3af; font-size: 0.875rem;">or click to browse</p>
            </div>
            """, unsafe_allow_html=True)

    # Right: Video Preview (2/3)
    with col2:
        st.markdown("## Preview")

        if st.session_state.video_uploaded and st.session_state.uploaded_file:
            # Create centered column for video (80% width)
            _, col_video_centered, _ = st.columns([1, 8, 1])

            with col_video_centered:
                # Display video
                st.video(st.session_state.uploaded_file)

                st.markdown("<br>", unsafe_allow_html=True)

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
            <div style="background: #f3f4f6; border-radius: 0.5rem; height: 16rem; display: flex; align-items: center; justify-content: center; color: #9ca3af;">
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem; opacity: 0.5;">Upload Video</div>
                    <p>No video uploaded</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 5. RESULTS SECTION (3 Columns: Audio, Face, Body)
# ==============================================================================
if st.session_state.show_results:
    st.markdown("---")

    # Helper function for metric column
    def render_metrics_column(title, icon, color, data):
        color_map = {
            "blue": {"bg": "#eff6ff", "border": "#bfdbfe", "text": "#1e40af", "score_bg": "#2563eb"},
            "purple": {"bg": "#f3e8ff", "border": "#d8b4fe", "text": "#6b21a8", "score_bg": "#7c3aed"},
            "green": {"bg": "#d1fae5", "border": "#a7f3d0", "text": "#065f46", "score_bg": "#059669"}
        }
        colors = color_map[color]

        st.markdown(f"""
        <div style="background: {colors['bg']}; border: 1px solid {colors['border']}; border-radius: 0.75rem; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
                <h3 style="color: {colors['text']}; font-size: 1.25rem; margin-bottom: 1rem;">{title}</h3>
                <div style="background: {colors['score_bg']}; color: white; border-radius: 9999px; padding: 1rem 1.5rem; display: inline-block;">
                    <div style="font-size: 1.875rem; font-weight: 700;">{data['globalScore']}</div>
                    <div style="font-size: 0.875rem; opacity: 0.9;">Global Score</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)

        for metric in data["metrics"]:
            score = metric["score"]
            score_class = "score-green" if score >= 70 else "score-yellow" if score >= 40 else "score-red"

            with st.expander(f"**{metric['name']}** - {score}/100", expanded=False):
                st.markdown(f"**Interpretation:** {metric['interpretation']}")
                st.markdown(f"**Coaching:** {metric['coaching']}")

        st.markdown("</div>", unsafe_allow_html=True)

    # 3-Column Layout
    col_audio, col_face, col_body = st.columns(3)

    with col_audio:
        render_metrics_column("Audio", "🎤", "blue", MOCK_DATA["audio"])

    with col_face:
        render_metrics_column("Face Expression", "😊", "purple", MOCK_DATA["face"])

    with col_body:
        render_metrics_column("Body Language", "🤸", "green", MOCK_DATA["body"])
