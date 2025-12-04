# The Flask/FastAPI app that receives Pub/Sub jobs
import json
import base64
import os
import time
from flask import Flask, request

# Import necessary Google Cloud libraries for GCS access
from google.cloud import storage

# Import your core analysis function from a local file
from analysis import run_video_analysis

app = Flask(__name__)
storage_client = storage.Client()

# --- 1. The Pub/Sub Listener Endpoint ---
# Cloud Run is configured to expose the application on the root path '/'.
# This endpoint receives the job message from Pub/Sub.
@app.route('/', methods=['POST'])
def pubsub_receiver():

    # Pub/Sub sends the message data base64-encoded inside a JSON wrapper (the envelope)
    envelope = request.get_json()
    if not envelope or 'message' not in envelope or 'data' not in envelope['message']:
        print("Error: No valid Pub/Sub message received.")
        return 'Invalid message', 400

    try:
        # Decode the job payload sent from the Streamlit app
        message_data = envelope['message']['data']
        job_payload_json = base64.b64decode(message_data).decode('utf-8')
        job_payload = json.loads(job_payload_json)

        print(f"Received job for video ID: {job_payload['video_id']}")

        # --- 2. Dispatch Work ---
        # Call your actual analysis function here. It handles the I/O with GCS.
        # We pass the job data which contains all GCS paths.
        run_video_analysis(job_payload)

        # CRITICAL: Return 200 OK immediately. This tells Pub/Sub the message was
        # successfully processed, preventing it from retrying the job.
        return '', 200

    except Exception as e:
        # Log the error for debugging in Cloud Logging
        print(f"Error processing message for video {job_payload.get('video_id', 'Unknown')}: {e}")

        # Return 500 status code to tell Pub/Sub to retry the message later (important for resilience)
        return f'Error: {e}', 500

# --- 3. Run the Server ---
if __name__ == '__main__':
    # Cloud Run automatically sets the PORT environment variable.
    # We must listen on 0.0.0.0 and use the port specified by the environment.
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
