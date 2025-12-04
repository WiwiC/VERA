# The Streamlit UI code (Frontend)

# Imports: python libraries and google cloud libraries
import streamlit as st
from google.cloud import storage, pubsub
import json, uuid, time, datetime

# --- CONFIGURATION (Replace with your actual IDs) ---
PROJECT_ID = "vera-480211"
RAW_BUCKET_NAME = "pitch-raw-videos-lewagon"
PROCESSED_BUCKET_NAME = "pitch-processed-videos-lewagon"
PUB_SUB_TOPIC_NAME = "video-analysis-jobs"

# Initialize clients (Must be authenticated via service account/ADC in deployed env)
storage_client = storage.Client(project=PROJECT_ID)
pubsub_publisher = pubsub.PublisherClient()
pubsub_topic_path = pubsub_publisher.topic_path(PROJECT_ID, PUB_SUB_TOPIC_NAME)

# --- STREAMLIT UI & STATE MANAGEMENT ---
if 'video_id' not in st.session_state: st.session_state['video_id'] = None
if 'gcs_path' not in st.session_state: st.session_state['gcs_path'] = None
if 'job_started' not in st.session_state: st.session_state['job_started'] = False

st.title("🎤 AI Pitch Analyzer")

# --- STEP 1: UPLOAD VIDEO ---
st.header("Step 1: Upload Video")
uploaded_file = st.file_uploader("Select your pitch video (.mp4, .mov)", type=['mp4', 'mov'])

if uploaded_file and st.button("Upload Video to Cloud (1/2)", disabled=st.session_state['job_started']):
    with st.spinner('Transferring video to Google Cloud Storage...'):
        st.session_state['video_id'] = str(uuid.uuid4())
        gcs_raw_path = f"raw/{st.session_state['video_id']}.mp4"

        # 1. Upload file to GCS
        storage_client.bucket(RAW_BUCKET_NAME).blob(gcs_raw_path).upload_from_file(
            uploaded_file, content_type=uploaded_file.type
        )
        st.session_state['gcs_path'] = gcs_raw_path
        st.success(f"Video uploaded successfully! ID: {st.session_state['video_id']}")
        st.experimental_rerun()


# --- STEP 2: START PROCESSING ---
if st.session_state['gcs_path'] is not None and not st.session_state['job_started']:
    st.header("Step 2: Start Analysis")
    st.info(f"Video ready at: {st.session_state['gcs_path']}")

    if st.button("Start Processing/Analyzing (2/2)"):
        with st.spinner('Sending job request to the Cloud Run worker...'):
            # 1. Create the job payload
            job_payload = {
                "video_id": st.session_state['video_id'],
                "input_path": st.session_state['gcs_path'],
                "raw_bucket": RAW_BUCKET_NAME,
                "processed_bucket": PROCESSED_BUCKET_NAME
            }

            # 2. Publish message to Pub/Sub
            pubsub_publisher.publish(
                pubsub_topic_path,
                json.dumps(job_payload).encode("utf-8")
            )

            st.session_state['job_started'] = True
            st.success("Processing job initialized! Waiting for results...")
            st.experimental_rerun()

# --- STEP 3: POLLING AND RESULTS DISPLAY ---
if st.session_state['job_started']:
    st.header("Step 3: Check Results")
    video_id = st.session_state['video_id']

    # Paths for result files
    json_path = f"results/{video_id}_output.json"
    video_path = f"results/{video_id}_processed.mp4"

    # Check if the JSON result exists in the processed bucket
    result_blob = storage_client.bucket(PROCESSED_BUCKET_NAME).blob(json_path)

    if result_blob.exists():
        # --- RESULTS READY ---
        st.success("✅ Analysis Complete! Pitch Analysis Report:")

        # Load JSON data (assuming your worker merges the face and body data into one JSON object)
        analysis_output = json.loads(result_blob.download_as_text())

        # --- 1. GLOBAL SCORES AND INTERPRETATION ---
        st.subheader("⭐ Overall Nonverbal Summary")

        # Display the main scores and interpretations
        col_face_g, col_body_g = st.columns(2)

        with col_face_g:
            st.metric("Face Global Score", f"{round(analysis_output.get('face_global_score', 0) * 100)}%")
            st.markdown(f"**Interpretation:** *{analysis_output.get('face_global_interpretation', 'N/A')}*")

        with col_body_g:
            st.metric("Body Global Score", f"{round(analysis_output.get('body_global_score', 0) * 100)}%")
            st.markdown(f"**Interpretation:** *{analysis_output.get('body_global_interpretation', 'N/A')}*")

        st.divider()

        # --- 2. DETAILED FACIAL ANALYSIS ---
        st.subheader("👤 Facial Gesture Deep Dive")
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            st.metric("Head Stability Score", f"{round(analysis_output.get('head_stability_score', 0) * 100)}%")
            st.markdown(f"**Interpretation:** {analysis_output.get('head_stability_interpretation', 'N/A')}")

        with col_f2:
            st.metric("Gaze Consistency Score", f"{round(analysis_output.get('gaze_consistency_score', 0) * 100)}%")
            st.markdown(f"**Interpretation:** {analysis_output.get('gaze_consistency_interpretation', 'N/A')}")

        st.metric("Smile Activation Score", f"{round(analysis_output.get('smile_activation_score', 0) * 100)}%")
        st.markdown(f"**Interpretation:** {analysis_output.get('smile_activation_interpretation', 'N/A')}")

        st.divider()

        # --- 3. DETAILED BODY ANALYSIS ---
        st.subheader("🧍 Body & Posture Deep Dive")
        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.metric("Gesture Magnitude Score", f"{round(analysis_output.get('gesture_magnitude_score', 0) * 100)}%")
            st.markdown(f"**Interpretation:** {analysis_output.get('gesture_magnitude_interpretation', 'N/A')}")

            st.metric("Body Sway Score", f"{round(analysis_output.get('body_sway_score', 0) * 100)}%")
            st.markdown(f"**Interpretation:** {analysis_output.get('body_sway_interpretation', 'N/A')}")

        with col_b2:
            st.metric("Gesture Activity Score", f"{round(analysis_output.get('gesture_activity_score', 0) * 100)}%")
            st.markdown(f"**Interpretation:** {analysis_output.get('gesture_activity_interpretation', 'N/A')}")

            st.metric("Posture Openness Score", f"{round(analysis_output.get('posture_openness_score', 0) * 100)}%")
            st.markdown(f"**Interpretation:** {analysis_output.get('posture_openness_interpretation', 'N/A')}")

            st.metric("Gesture Jitter Score", f"{round(analysis_output.get('gesture_jitter_score', 0) * 100)}%")
            st.markdown(f"**Interpretation:** {analysis_output.get('gesture_jitter_interpretation', 'N/A')}")

        st.divider()

        # --- 4. VIDEO LINK DISPLAY ---
        st.subheader("🔗 Processed Video Playback")

        # Generate time-limited link for processed video (CRITICAL SECURITY STEP)
        video_blob = storage_client.bucket(PROCESSED_BUCKET_NAME).blob(video_path)
        video_url = video_blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=10), # Link valid for 10 minutes
            method="GET"
        )

        st.video(video_url)
        st.markdown(f"**Download Link (10 min expiration):** [Click here to download the processed video]({video_url})")

        # Clean up session state for a fresh run
        st.session_state['job_started'] = False
        st.session_state['gcs_path'] = None
        st.session_state['video_id'] = None

    else:
        # --- POLLING ---
        st.info("⏳ Processing in progress... Checking again in 5 seconds.")
        time.sleep(5)
        st.experimental_rerun()
