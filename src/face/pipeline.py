"""
Main pipeline orchestration for the VERA Face Module.
Runs extraction, scoring, and visualization, saving results to a structured output directory.
"""

import os
import json
import pandas as pd
from pathlib import Path

from src.face.extraction import process_video
from src.face.scoring import compute_scores
from src.face.visualization import create_debug_video

def run_face_pipeline(video_path, output_dir=None):
    """
    Run the full face analysis pipeline on a video.

    Args:
        video_path (str): Path to the input video.
        output_dir (str, optional): Directory to save results.
                                    If None, defaults to 'data/processed/<video_name>'.

    Returns:
        dict: The final scores dictionary.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Determine output directory
    if output_dir is None:
        # Default: data/processed/<video_stem>
        # Assuming project root is 2 levels up from src/face/pipeline.py?
        # Safer to just use relative path from CWD or absolute path provided.
        # Let's assume CWD is project root.
        output_dir = Path("data/processed") / video_path.stem
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"🚀 Starting Face Pipeline for: {video_path.name}")
    print(f"📂 Output directory: {output_dir}")

    # 1. Extraction
    print("--- Step 1: Extraction ---")
    raw_df = process_video(str(video_path))

    # 2. Scoring
    print("--- Step 2: Scoring ---")
    scores, window_df = compute_scores(raw_df)

    # 3. Save Results
    print("--- Step 3: Saving Results ---")

    # Save Raw Data (Frame-by-Frame)
    raw_data_path = output_dir / "df_Face_raw_data.csv"
    raw_df.to_csv(raw_data_path)
    print(f"✅ Saved raw data to: {raw_data_path}")

    # Save Processed Metrics (Windowed/Smoothed)
    metrics_path = output_dir / "metrics_face.csv"
    window_df.to_csv(metrics_path, index=False)
    print(f"✅ Saved processed metrics to: {metrics_path}")

    # Save results JSON
    results_path = output_dir / "results_face.json"
    with open(results_path, "w") as f:
        json.dump(scores, f, indent=4)
    print(f"✅ Saved scores to: {results_path}")

    # 4. Visualization
    print("--- Step 4: Visualization ---")
    debug_video_path = output_dir / "debug_face.mp4"
    create_debug_video(str(video_path), str(debug_video_path))
    print(f"✅ Saved debug video to: {debug_video_path}")

    print("🎉 Pipeline completed successfully!")
    return scores

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        run_face_pipeline(sys.argv[1])
    else:
        print("Usage: python -m src.face.pipeline <video_path>")
