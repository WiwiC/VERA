"""
Main pipeline orchestration for the VERA Audio Module.
"""

import os
import json
import pandas as pd
from pathlib import Path
from src.audio.extraction import process_audio
from src.audio.scoring import compute_scores

def run_audio_pipeline(video_path, output_dir):
    """
    Run the full audio analysis pipeline.

    Args:
        video_path (str): Path to input video.
        output_dir (str): Directory to save results.

    Returns:
        dict: Final scores and interpretations.
    """
    print(f"🚀 Starting Audio Pipeline for: {Path(video_path).name}")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Extraction
    print("--- Step 1: Extraction ---")

    raw_metrics = process_audio(video_path, output_dir)

    if not raw_metrics:
        print("❌ Audio extraction failed.")
        return {}

    # Rename generated audio file to debug_audio.mp3 for consistency
    generated_audio = Path(output_dir) / f"{Path(video_path).stem}.mp3"
    debug_audio_path = Path(output_dir) / "debug_audio.mp3"
    if generated_audio.exists():
        if debug_audio_path.exists():
            debug_audio_path.unlink()
        generated_audio.rename(debug_audio_path)
        print(f"✅ Saved debug audio to: {debug_audio_path}")

    # 2. Scoring
    print("--- Step 2: Scoring ---")
    scores = compute_scores(raw_metrics)

    # 3. Saving Results
    print("--- Step 3: Saving Results ---")

    # Save Raw Metrics (CSV)
    # Convert scalar dict to 1-row DataFrame
    df_metrics = pd.DataFrame([raw_metrics])
    metrics_path = Path(output_dir) / "metrics_audio.csv"
    df_metrics.to_csv(metrics_path, index=False)
    print(f"✅ Saved metrics to: {metrics_path}")

    # Save Scores (JSON)
    results_path = Path(output_dir) / "results_audio.json"
    with open(results_path, "w") as f:
        json.dump(scores, f, indent=4)
    print(f"✅ Saved scores to: {results_path}")

    print("🎉 Audio Pipeline completed successfully!")
    print("\n--- Pipeline Results ---")
    print(scores)

    return scores
