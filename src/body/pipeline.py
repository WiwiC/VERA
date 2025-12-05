"""
Main pipeline orchestration for the VERA Body Module.
Runs extraction, scoring, and visualization, saving results to a structured output directory.
"""

import os
import json
import pandas as pd
from pathlib import Path

from src.body.extraction import process_video
from src.body.scoring import compute_scores
from src.body.visualization import create_debug_video

def run_body_pipeline(video_path, output_dir=None):
    """
    Run the full body analysis pipeline on a video.

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
        output_dir = Path("data/processed") / video_path.stem
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"🚀 Starting Body Pipeline for: {video_path.name}")
    print(f"📂 Output directory: {output_dir}")

    # 1. Extraction
    print("--- Step 1: Extraction ---")
    raw_df = process_video(str(video_path))

    # 2. Scoring
    print("--- Step 2: Scoring ---")
    scores, window_df = compute_scores(raw_df)

    # 3. Save Results
    print("--- Step 3: Saving Results ---")

    # 3. Save Metrics
    print("--- Step 3: Saving Results ---")

    # Save Raw Data (Frame-by-Frame)
    raw_data_path = output_dir / "df_Body_raw_data.csv"
    raw_df.to_csv(raw_data_path)
    print(f"✅ Saved raw data to: {raw_data_path}")

    # Save Processed Metrics (Windowed/Smoothed)
    metrics_path = output_dir / "metrics_body.csv"
    window_df.to_csv(metrics_path, index=False)
    print(f"✅ Saved processed metrics to: {metrics_path}")

    # Save results JSON (results_body.json)
    results_path = output_dir / "results_body.json"
    with open(results_path, "w") as f:
        json.dump(scores, f, indent=4)
    print(f"✅ Saved scores to: {results_path}")

    # 4. Visualization
    print("--- Step 4: Visualization ---")
    debug_video_path = output_dir / "debug_pose.mp4"
    create_debug_video(str(video_path), str(debug_video_path))
    print(f"✅ Saved debug video to: {debug_video_path}")

    print("🎉 Body Pipeline completed successfully!")
    return scores

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run_body_pipeline(sys.argv[1])
    else:
        print("Usage: python -m src.body.pipeline <video_path>")
