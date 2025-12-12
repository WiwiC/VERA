"""
Visualization module for the VERA Body Module.
Generates a debug video with MediaPipe Pose skeleton and custom colored keypoints.
"""

import cv2
import mediapipe as mp
import os
import subprocess
import imageio_ffmpeg
from tqdm import tqdm
from src.body.config import (
    POSE_POINTS,
    COLOR_SHOULDERS,
    COLOR_HIPS,
    COLOR_WRISTS
)

def create_debug_video(video_path, output_path):
    """
    Process the video again to draw pose landmarks and save a debug video.

    Args:
        video_path (str): Path to the input video.
        output_path (str): Path to save the output video.
    """
    print(f"Generating debug video: {output_path}")

    mp_holistic = mp.solutions.holistic
    mp_drawing = mp.solutions.drawing_utils

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
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Video writer
    out = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*'mp4v'),
        fps,
        (width, height)
    )

    for _ in tqdm(range(frame_count), desc="Generating Video"):
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(rgb)

        annotated = frame.copy()
        h, w, _ = frame.shape

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark

            # ---- Custom colored keypoints ----
            for i in POSE_POINTS["shoulders"]:
                cv2.circle(annotated, (int(lm[i].x*w), int(lm[i].y*h)), 5, COLOR_SHOULDERS, -1)
            for i in POSE_POINTS["hips"]:
                cv2.circle(annotated, (int(lm[i].x*w), int(lm[i].y*h)), 5, COLOR_HIPS, -1)
            for i in POSE_POINTS["wrists"]:
                cv2.circle(annotated, (int(lm[i].x*w), int(lm[i].y*h)), 6, COLOR_WRISTS, -1)

            # ---- Full body skeleton (NO face) ----
            mp_drawing.draw_landmarks(
                annotated,
                results.pose_landmarks,
                mp_holistic.POSE_CONNECTIONS
            )

        out.write(annotated)

    cap.release()
    out.release()
    holistic.close()

    # Convert to H.264 for browser compatibility
    print("🔄 Converting to H.264...")
    temp_output = output_path + ".temp.mp4"
    if os.path.exists(output_path):
        os.rename(output_path, temp_output)

        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            subprocess.run([
                ffmpeg_exe, "-y", "-i", temp_output,
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "23",
                output_path
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            os.remove(temp_output)
            print("✅ Converted to H.264.")
        except Exception as e:
            print(f"⚠️ Failed to convert to H.264: {e}")
            # Restore original if conversion fails
            if os.path.exists(temp_output):
                os.rename(temp_output, output_path)

    print("✅ Debug video saved.")
