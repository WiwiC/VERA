"""
Visualization module for the VERA Face Module.
Generates a debug video with facial landmarks overlaid.
"""

import cv2
import mediapipe as mp
import os
import subprocess
import imageio_ffmpeg
from tqdm import tqdm
from src.face.config import (
    HEAD_POINTS,
    GAZE_POINTS,
    EXPRESS_POINTS,
    SMILE_POINTS,
    COLOR_HEAD,
    COLOR_GAZE,
    COLOR_EXP,
    COLOR_SMILE
)

def create_debug_video(video_path, output_path):
    """
    Process the video again to draw landmarks and save a debug video.

    Args:
        video_path (str): Path to the input video.
        output_path (str): Path to save the output video.
    """
    print(f"Generating debug video: {output_path}")

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
        results = face_mesh.process(rgb)

        annotated = frame.copy()
        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark
            h, w, _ = frame.shape

            # Head landmarks
            for i in HEAD_POINTS:
                cv2.circle(annotated, (int(lm[i].x*w), int(lm[i].y*h)), 3, COLOR_HEAD, -1)

            # Gaze landmarks
            for i in GAZE_POINTS:
                cv2.circle(annotated, (int(lm[i].x*w), int(lm[i].y*h)), 3, COLOR_GAZE, -1)

            # Expressiveness landmarks
            for i in EXPRESS_POINTS:
                cv2.circle(annotated, (int(lm[i].x*w), int(lm[i].y*h)), 3, COLOR_EXP, -1)

            # Smile landmarks
            for i in SMILE_POINTS:
                cv2.circle(annotated, (int(lm[i].x*w), int(lm[i].y*h)), 4, COLOR_SMILE, -1)

        out.write(annotated)

    cap.release()
    out.release()
    face_mesh.close()

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
