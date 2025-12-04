# Your core video processing logic

import os
import json
from google.cloud import storage
import subprocess # Needed for robust audio extraction
import shutil # Needed for file operations

# --- IMPORT YOUR EXISTING PIPELINES ---
try:
    # Ensure these files are in the same 'cloud_worker' directory!
    from tests import test_face_pipeline
    from tests import test_body_pipeline
    from tests import test_audio_pipeline
except ImportError as e:
    print(f"CRITICAL: Failed to import local pipeline files. Check file names and structure: {e}")
    # Re-raise the error; the Cloud Run worker should fail immediately if the code isn't loaded.
    raise

# --- Initialization & Constants ---
storage_client = storage.Client()
TEMP_VIDEO_FILE = "/tmp/input_video.mp4"
TEMP_AUDIO_FILE = "/tmp/input_audio.wav"
TEMP_PROCESSED_VIDEO = "/tmp/processed_output.mp4"

# NOTE: Cloud Run needs ffmpeg for audio extraction. Ensure it's installed in your Dockerfile.
def extract_audio(video_path, audio_path):
    """Extracts audio stream from video using ffmpeg."""
    command = [
        'ffmpeg', '-i', video_path,
        '-ab', '160k',
        '-ac', '2',
        '-ar', '44100',
        '-vn', audio_path
    ]
    subprocess.run(command, check=True)
    print(f"Audio extracted to {audio_path}")


def run_all_analysis(local_video_path):
    """
    Executes all three pipelines (Face, Body, Audio) and merges results.
    """

    # 1. Run Face Analysis
    print("Executing Face Pipeline...")
    # ACTION: Replace 'run_face_analysis_function' with the actual function name in test_face_pipeline.py
    # Ensure this function accepts the local video path and returns a dictionary.
    face_results = test_face_pipeline.test_pipeline(local_video_path)

    # 2. Run Body Analysis
    print("Executing Body Pipeline...")
    # ACTION: Replace 'run_body_analysis_function' with the actual function name in test_body_pipeline.py
    body_results = test_body_pipeline.test_pipeline(local_video_path)

    # 3. Audio Extraction and Analysis
    print("Preparing and executing Audio Pipeline...")
    extract_audio(local_video_path, TEMP_AUDIO_FILE)
    # ACTION: Replace 'run_audio_function' with the actual function name in audio.py
    audio_results = test_audio_pipeline.test_pipeline(TEMP_AUDIO_FILE)

    # 4. Merge Results
    final_results = {}
    final_results.update(face_results)
    final_results.update(body_results)
    final_results.update(audio_results)

    return final_results


def create_processed_video(local_video_path, output_path):
    """
    Runs video rendering logic and saves the final output locally.
    """
    # ACTION: Place your video rendering code here. It must:
    # 1. Read the local_video_path
    # 2. Add overlays (bounding boxes, text, etc.)
    # 3. Save the resulting video file to the 'output_path' (/tmp/processed_output.mp4)

    print("Running video rendering logic...")
    # Placeholder: Copy the input video to the output path if no processing is done yet
    shutil.copyfile(local_video_path, output_path)
    # If you run actual video processing, remove the line above and insert your code here.

    return output_path


# --- Main Entry Point (Called by main.py) ---
def run_video_analysis(job_data):
    """
    Handles the end-to-end video processing lifecycle (Download, Run, Upload, Cleanup).
    """

    video_id = job_data['video_id']
    raw_bucket = job_data['raw_bucket']
    processed_bucket = job_data['processed_bucket']
    input_path = job_data['input_path']

    # 1. Download Video
    try:
        input_blob = storage_client.bucket(raw_bucket).blob(input_path)
        input_blob.download_to_filename(TEMP_VIDEO_FILE)
        print(f"Video downloaded for {video_id}.")

        # 2. Run All Analysis
        final_results = run_all_analysis(TEMP_VIDEO_FILE)

        # 3. Create Processed Video
        local_processed_video_path = create_processed_video(TEMP_VIDEO_FILE, TEMP_PROCESSED_VIDEO)

        # 4. Upload Results (JSON)
        results_json_string = json.dumps(final_results, indent=2)
        json_gcs_path = f"results/{video_id}_output.json"
        json_blob = storage_client.bucket(processed_bucket).blob(json_gcs_path)
        json_blob.upload_from_string(results_json_string, content_type='application/json')

        # 5. Upload Processed Video
        video_gcs_path = f"results/{video_id}_processed.mp4"
        video_blob = storage_client.bucket(processed_bucket).blob(video_gcs_path)
        video_blob.upload_from_filename(local_processed_video_path, content_type='video/mp4')

        print(f"--- Analysis SUCCESS for video {video_id} ---")

    except Exception as e:
        print(f"--- Analysis FAILED for video {video_id}: {e} ---")
        raise # Critical: Re-raise the error so main.py returns 500 and Pub/Sub retries the job.

    finally:
        # 6. Cleanup local temporary files (CRUCIAL for Cloud Run disk space)
        for f in [TEMP_VIDEO_FILE, TEMP_AUDIO_FILE, TEMP_PROCESSED_VIDEO]:
            if os.path.exists(f):
                os.remove(f)
        print("Local cleanup complete.")
