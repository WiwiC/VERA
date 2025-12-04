"""
Core extraction logic for the VERA Body Module.
Processes video frames using MediaPipe Holistic and extracts raw behavioral metrics.
"""

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from tqdm import tqdm

from src.body.geometry import (
    compute_torso_center,
    compute_gesture_magnitude,
    compute_posture_openness,
    compute_shoulder_width
)

def process_video(video_path):
    """
    Process a video file to extract body metrics frame by frame.

    Args:
        video_path (str): Path to the input video file.

    Returns:
        pd.DataFrame: DataFrame containing timestamped metrics:
                      - gesture_magnitude
                      - gesture_activity
                      - body_sway
                      - posture_openness
    """
    # Initialize MediaPipe Holistic
    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        refine_face_landmarks=False
    )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"❌ Error loading video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    features = []

    prev_L_wr = None
    prev_R_wr = None
    prev_torso = None

    print(f"Processing video: {video_path}")

    for idx in tqdm(range(frame_count), desc="Body Analysis"):
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = idx / fps
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(rgb)

        gesture_magnitude = np.nan
        gesture_activity = np.nan
        body_sway = np.nan
        posture_openness = np.nan

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark

            # ----- METRIC 0 : Shoulder Width (Normalization Factor) -----
            shoulder_width = compute_shoulder_width(lm)

            # ----- METRIC 1 : Gesture Magnitude -----
            # Now returns "Shoulder Width Units" (e.g. 1.5 SW)
            gesture_magnitude = compute_gesture_magnitude(lm, shoulder_width)

            # ----- METRIC 2 : Gesture Activity -----
            L_wr = np.array([lm[15].x, lm[15].y, lm[15].z])
            R_wr = np.array([lm[16].x, lm[16].y, lm[16].z])

            if prev_L_wr is not None:
                speed_L = np.linalg.norm(L_wr - prev_L_wr)
                speed_R = np.linalg.norm(R_wr - prev_R_wr)
                raw_activity = np.nanmean([speed_L, speed_R])

                # Normalize by shoulder width if valid
                if shoulder_width > 0:
                    gesture_activity = raw_activity / shoulder_width
                else:
                    gesture_activity = 0.0

            prev_L_wr = L_wr
            prev_R_wr = R_wr

            # ----- METRIC 3 : Body Sway -----
            torso = compute_torso_center(lm)
            if prev_torso is not None:
                raw_sway = np.linalg.norm(torso - prev_torso)

                # Normalize by shoulder width if valid
                if shoulder_width > 0:
                    body_sway = raw_sway / shoulder_width
                else:
                    body_sway = 0.0
            prev_torso = torso

            # ----- METRIC 4 : Posture Openness -----
            posture_openness = compute_posture_openness(lm)

        features.append({
            "timestamp": timestamp,
            "gesture_magnitude": gesture_magnitude,
            "gesture_activity": gesture_activity,
            "body_sway": body_sway,
            "posture_openness": posture_openness
        })

    cap.release()
    holistic.close()

    df = pd.DataFrame(features).set_index("timestamp")
    df["second"] = df.index.astype(int)

    return df
