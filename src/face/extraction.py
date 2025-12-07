"""
Core extraction logic for the VERA Face Module.
Processes video frames using MediaPipe FaceMesh and extracts raw behavioral metrics.
"""

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from tqdm import tqdm

from src.face.geometry import (
    compute_head_center,
    compute_iris_centers,
    compute_face_center,
    compute_smile_activation,
    compute_inter_ocular_distance
)

def process_video(video_path):
    """
    Process a video file to extract face metrics frame by frame.

    Args:
        video_path (str): Path to the input video file.

    Returns:
        pd.DataFrame: DataFrame containing timestamped metrics:
                      - head_speed (IOD/sec, fps-normalized)
                      - gaze_dg (gaze direction change per sec, fps-normalized)
                      - smile (activation intensity, normalized by IOD)
    """
    # Initialize MediaPipe FaceMesh
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        refine_landmarks=True,
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"❌ Error loading video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0  # Fallback to 30fps if detection fails
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    features = []
    prev_head_center = None
    prev_gaze = None

    print(f"Processing video: {video_path}")

    for idx in tqdm(range(frame_count), desc="Face Analysis"):
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = idx / fps
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        head_speed = np.nan
        dg = np.nan
        smile = np.nan

        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark

            # ----- METRIC 0 : IOD (Normalization Factor) -----
            iod = compute_inter_ocular_distance(lm)

            # ----- HEAD STABILITY -----
            head_center = compute_head_center(lm)
            if prev_head_center is not None:
                raw_speed = np.linalg.norm(head_center - prev_head_center)

                # Normalize by IOD and convert to per-second units (fps-agnostic)
                if iod > 0:
                    head_speed = (raw_speed / iod) * fps  # IOD/sec
                else:
                    head_speed = 0.0
            prev_head_center = head_center

            # ----- GAZE CONSISTENCY -----
            iris_center = compute_iris_centers(lm)
            face_center = compute_face_center(lm)

            gaze_vec = iris_center - face_center
            gaze_vec = gaze_vec / (np.linalg.norm(gaze_vec) + 1e-6)

            if prev_gaze is not None:
                # Convert to per-second units (fps-agnostic)
                dg = np.linalg.norm(gaze_vec - prev_gaze) * fps  # per sec
            prev_gaze = gaze_vec

            # ----- SMILE ACTIVATION -----
            raw_smile = compute_smile_activation(lm)
            if iod > 0:
                smile = raw_smile / iod
            else:
                smile = 0.0

        # Append ALL features (even if NaN)
        features.append({
            "timestamp": timestamp,
            "head_speed": head_speed,
            "gaze_dg": dg,
            "smile": smile
        })

    cap.release()
    face_mesh.close()

    df = pd.DataFrame(features).set_index("timestamp")
    df["second"] = df.index.astype(int)

    return df
