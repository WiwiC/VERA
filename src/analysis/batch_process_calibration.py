"""
Batch processing script for VERA calibration.
Reads the calibration manifest, runs the pipeline for each video, and generates the final report.
"""

import pandas as pd
import subprocess
import sys
from pathlib import Path
import time

MANIFEST_PATH = Path("data/raw/calibration_manifest.csv")
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

def run_pipeline(video_id):
    video_path = RAW_DIR / f"{video_id}.mp4"
    output_dir = PROCESSED_DIR / str(video_id)

    if not video_path.exists():
        print(f"⚠️ Video not found: {video_path}")
        return False

    print(f"\n{'='*60}")
    print(f"Processing Video: {video_id}")
    print(f"{'='*60}")

    cmd = [
        "python", "-m", "src.main",
        str(video_path),
        "--output", str(output_dir)
    ]

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error processing {video_id}: {e}")
        return False

def main():
    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest not found: {MANIFEST_PATH}")
        sys.exit(1)

    print(f"Reading manifest: {MANIFEST_PATH}")
    df = pd.read_csv(MANIFEST_PATH, sep=";")

    # Get list of video IDs
    video_ids = df["file_video_name"].astype(str).str.strip().unique()

    print(f"Found {len(video_ids)} videos to process: {video_ids}")

    successful = []
    failed = []

    start_time = time.time()

    for vid in video_ids:
        if run_pipeline(vid):
            successful.append(vid)
        else:
            failed.append(vid)

    end_time = time.time()
    duration = end_time - start_time

    print(f"\n{'='*60}")
    print(f"Batch Processing Complete in {duration:.1f}s")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print(f"Failed videos: {failed}")

    # Run Calibration Report
    print(f"\n{'='*60}")
    print("Generating Calibration Report...")
    print(f"{'='*60}")

    report_cmd = [
        "python", "src/analysis/generate_calibration_report.py",
        str(MANIFEST_PATH)
    ]

    try:
        subprocess.run(report_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating report: {e}")

if __name__ == "__main__":
    main()
