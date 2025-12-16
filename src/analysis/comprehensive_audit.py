import os
import json
import pandas as pd
import subprocess
from pathlib import Path
import sys

# Configuration
VIDEOS = ["18", "24", "60", "61", "63", "67"]
MANIFEST_PATH = "data/raw/updated_calibration_manifest_V3.csv"
OLD_RESULTS_DIR = "data/processed"
NEW_RESULTS_DIR = "data/processed"

# Metric Mapping (CSV Column -> JSON Metric ID)
METRIC_MAP = {
    "head_stability": "head_stability",
    "gaze_stability": "gaze_stability",
    "smile_activation": "smile_activation",
    "head_down_ratio": "head_down_ratio",
    "gesture_magnitude": "gesture_magnitude",
    "gesture_activity": "gesture_activity",
    "gesture_stability": "gesture_stability",
    "body_sway": "body_sway",
    "posture_openess": "posture_openness", # Note CSV typo
    "speech_rate": "speech_rate",
    "pause_ratio": "pause_ratio",
    "pitch_dynamic": "pitch_dynamic",
    "volume_dynamic": "volume_dynamic",
    "vocal_punch": "vocal_punch"
}

def run_pipeline(video_id):
    video_path = f"data/raw/{video_id}.mp4"
    print(f"🚀 Running pipeline for Video {video_id}...")
    # Clean output dir first
    subprocess.run(f"rm -rf data/processed/{video_id}", shell=True)

    cmd = f"source VERA-env/bin/activate && python src/main.py {video_path}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error running pipeline for {video_id}:\n{result.stderr}")
        return False
    return True

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def get_metric_result(data, metric_id):
    # Search in all modules
    for module in ["face", "body", "audio"]:
        if module in data and "metrics" in data[module]:
            if metric_id in data[module]["metrics"]:
                return data[module]["metrics"][metric_id]
    return None

def main():
    # 1. Load Manifest
    try:
        manifest = pd.read_csv(MANIFEST_PATH, sep=";")
        manifest["file_video_name"] = manifest["file_video_name"].astype(str)
    except Exception as e:
        print(f"❌ Error loading manifest: {e}")
        return

    report_lines = []
    report_lines.append("# Comprehensive Calibration Audit Report")
    report_lines.append(f"**Date:** {pd.Timestamp.now()}")
    report_lines.append("")

    for vid in VIDEOS:
        print(f"\n--- Processing Video {vid} ---")

        # 2. Run Pipeline
        if not run_pipeline(vid):
            continue

        # 3. Load Results
        new_path = f"{NEW_RESULTS_DIR}/{vid}/results_global_enriched.json"
        old_path = f"{OLD_RESULTS_DIR}/results_global_enriched_old_{vid}.json"

        new_data = load_json(new_path)
        old_data = load_json(old_path)

        if not new_data:
            print(f"❌ New results not found for {vid}")
            continue

        report_lines.append(f"## Video {vid}")

        # --- Cluster Verification ---
        cluster = new_data.get("clustering", {})
        cluster_name = cluster.get("name", "N/A")
        cluster_traits = cluster.get("traits", [])
        report_lines.append(f"**Cluster:** {cluster_name}")
        report_lines.append(f"**Traits:** {', '.join(cluster_traits)}")

        # Verify traits against metrics (Simple heuristic check)
        # e.g. if "Low pitchd" in traits, check if pitch_dynamic score is low
        # Or check if raw value is low

        report_lines.append("")
        report_lines.append("| Metric | Manifest Label | New Label | New Score | Old Score | Delta | Match? |")
        report_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        row = manifest[manifest["file_video_name"] == vid]
        if row.empty:
            print(f"⚠️ Video {vid} not found in manifest")
            continue

        row = row.iloc[0]

        for csv_col, metric_id in METRIC_MAP.items():
            manifest_label = str(row.get(csv_col, "N/A")).strip().lower()

            # Get New Result
            new_res = get_metric_result(new_data, metric_id)
            new_label = new_res.get("label", "N/A").lower() if new_res else "N/A"
            new_score = new_res.get("score", 0) if new_res else 0

            # Get Old Result
            old_res = get_metric_result(old_data, metric_id) if old_data else None
            old_score = old_res.get("score", 0) if old_res else 0

            delta = new_score - old_score

            # Match Check (Loose string matching)
            # Handle "optimal" vs "good" etc
            match = "✅" if manifest_label in new_label or new_label in manifest_label else "❌"
            if manifest_label == "nan" or manifest_label == "n/a":
                match = "⚪"

            report_lines.append(f"| {metric_id} | {manifest_label} | {new_label} | {new_score} | {old_score} | {delta:+d} | {match} |")

        report_lines.append("")

        # Global Scores Comparison
        report_lines.append("### Global Scores Comparison")
        report_lines.append("| Module | New Score | Old Score | Delta |")
        report_lines.append("| :--- | :--- | :--- | :--- |")

        for mod in ["body", "face", "audio"]:
            new_g = new_data.get(mod, {}).get("global", {}).get("score", 0)
            old_g = old_data.get(mod, {}).get("global", {}).get("score", 0) if old_data else 0
            report_lines.append(f"| {mod.capitalize()} | {new_g} | {old_g} | {new_g - old_g:+d} |")

        report_lines.append("")

    # Save Report
    with open("calibration_audit_report.md", "w") as f:
        f.write("\n".join(report_lines))

    print("\n✅ Audit Complete. Report saved to calibration_audit_report.md")
    print(f"Content preview:\n")
    print("\n".join(report_lines[:20]))

if __name__ == "__main__":
    main()
