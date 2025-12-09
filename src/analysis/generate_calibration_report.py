"""
Calibration Report Generator for VERA.

This script compares human-labeled ground truth from calibration_manifest.csv
against model outputs in results_global.json, measuring bucket distance.

Usage:
    python -m src.analysis.generate_calibration_report

Output:
    data/calibration_report.csv
"""

import json
import pandas as pd
from pathlib import Path


# =========================================================
# Configuration
# =========================================================

MANIFEST_PATH = Path("data/raw/calibration_manifest.csv")
PROCESSED_DIR = Path("data/processed")
METRICS_SPEC_PATH = Path("src/schemas/metrics_spec.json")
OUTPUT_PATH = Path("data/calibration_report.csv")

# Mapping from manifest column names to metrics_spec metric_id and JSON path
METRIC_MAPPING = {
    # Body metrics
    "gesture_magnitude": ("body", "gesture_magnitude_communication_score", "gesture_magnitude"),
    "gesture_activity": ("body", "gesture_activity_communication_score", "gesture_activity"),
    "gesture_stability": ("body", "gesture_stability_communication_score", "gesture_stability"),
    "body_sway": ("body", "body_sway_communication_score", "body_sway"),
    "posture_openess": ("body", "posture_openness_communication_score", "posture_openness"),  # Note: typo in manifest

    # Face metrics
    "head_stability": ("face", "head_stability_communication_score", "head_stability"),
    "gaze_stability": ("face", "gaze_stability_communication_score", "gaze_stability"),
    "smile_activation": ("face", "smile_activation_communication_score", "smile_activation"),

    # Audio metrics
    "speech_rate": ("audio", "speech_rate_score", "speech_rate"),
    "pause_ratio": ("audio", "pause_ratio_score", "pause_ratio"),
    "pitch_dynamic": ("audio", "pitch_dynamic_score", "pitch_dynamic"),
    "volume_dynamic": ("audio", "volume_dynamic_score", "volume_dynamic"),
    "vocal_punch": ("audio", "vocal_punch_score", "vocal_punch"),
}


# =========================================================
# Bucket Distance Calculation
# =========================================================

def load_bucket_order(metrics_spec: dict) -> dict:
    """
    Extract the ordered list of labels for each metric from metrics_spec.json.
    Returns: {metric_id: [label1, label2, ...]} in order from first bucket to last.
    """
    bucket_order = {}

    for metric in metrics_spec.get("metrics", []):
        metric_id = metric.get("metric_id")
        buckets = metric.get("interpretation_buckets", [])

        if buckets:
            # Extract labels in order
            labels = [b.get("label") for b in buckets if b.get("label")]
            bucket_order[metric_id] = labels

    return bucket_order


def get_bucket_distance(human_label: str, model_label: str, bucket_labels: list) -> int:
    """
    Calculate the bucket distance between two labels.
    Returns the absolute difference in bucket positions, or -1 if label not found.
    """
    if not human_label or not model_label:
        return None

    # Normalize labels (lowercase, strip whitespace)
    human_label = human_label.strip().lower()
    model_label = model_label.strip().lower()

    # Find positions
    try:
        human_idx = bucket_labels.index(human_label)
    except ValueError:
        return None  # Human label not in bucket list

    try:
        model_idx = bucket_labels.index(model_label)
    except ValueError:
        return None  # Model label not in bucket list

    return abs(human_idx - model_idx)


def get_model_label_from_score(score: float, metric_id: str, metrics_spec: dict) -> str:
    """
    Given a score (0-1), determine which interpretation bucket it falls into.
    This requires understanding the scoring function and reversing it.

    For simplicity, we'll use the interpretation from results_global.json directly.
    """
    # This is a placeholder - we'll extract the label from the JSON interpretation text
    pass


# =========================================================
# Main Report Generation
# =========================================================

def load_results(video_id: str) -> dict:
    """Load results_global.json for a video."""
    results_path = PROCESSED_DIR / video_id / "results_global.json"

    if not results_path.exists():
        return None

    with open(results_path) as f:
        return json.load(f)


def extract_model_label(interpretation_text: str, bucket_labels: list) -> str:
    """
    Extract the bucket label from the interpretation text.
    The interpretation text contains patterns like "(Excellent)" or "(Weak)" or label keywords.
    """
    if not interpretation_text:
        return None

    interpretation_lower = interpretation_text.lower()

    # Check if any bucket label appears in the interpretation
    for label in bucket_labels:
        if label.lower() in interpretation_lower:
            return label.lower()

    return None


def generate_report():
    """Generate the calibration report CSV."""

    # Load metrics spec for bucket definitions
    with open(METRICS_SPEC_PATH) as f:
        metrics_spec = json.load(f)

    bucket_order = load_bucket_order(metrics_spec)

    # Load manifest
    manifest = pd.read_csv(MANIFEST_PATH, sep=";")

    # Prepare report rows
    report_rows = []

    for _, row in manifest.iterrows():
        video_id = str(row["file_video_name"]).strip()
        notes = row.get("notes", "")

        # Load model results
        results = load_results(video_id)

        if results is None:
            print(f"Warning: No results found for video {video_id}")
            continue

        # Process each metric
        for manifest_col, (module, score_key, spec_metric_id) in METRIC_MAPPING.items():
            human_label = row.get(manifest_col)

            if pd.isna(human_label) or human_label == "":
                continue  # Skip unlabeled metrics

            human_label = str(human_label).strip().lower()

            # Get model data
            module_data = results.get(module, {})
            model_score = module_data.get(score_key)

            # Get interpretation text to extract model label
            interp_key = score_key.replace("_score", "_interpretation")
            interpretation = module_data.get(interp_key, "")

            # Get bucket labels for this metric
            buckets = bucket_order.get(spec_metric_id, [])

            # Extract model label from interpretation
            model_label = extract_model_label(interpretation, buckets)

            # Calculate bucket distance
            distance = get_bucket_distance(human_label, model_label, buckets)

            # Determine match status
            if distance is None:
                match_status = "unknown"
            elif distance == 0:
                match_status = "exact_match"
            elif distance == 1:
                match_status = "off_by_1"
            else:
                match_status = f"off_by_{distance}"

            report_rows.append({
                "video_id": video_id,
                "metric": spec_metric_id,
                "human_label": human_label,
                "model_label": model_label,
                "model_score": round(model_score, 4) if model_score is not None else None,
                "bucket_distance": distance,
                "match_status": match_status,
                "interpretation": interpretation[:80] + "..." if len(str(interpretation)) > 80 else interpretation,
                "notes": notes if manifest_col == list(METRIC_MAPPING.keys())[0] else ""  # Only show notes once per video
            })

    # Check if we have any data
    if not report_rows:
        print("\n⚠️  No processed videos found!")
        print("Run the VERA pipeline on your calibration videos first:")
        print("  python -m src.main data/raw/<video>.mp4 --output data/processed/<video_id>")
        return None

    # Create DataFrame and save
    report_df = pd.DataFrame(report_rows)

    # Sort by video_id, then by metric
    report_df = report_df.sort_values(["video_id", "metric"])

    # Save to CSV
    report_df.to_csv(OUTPUT_PATH, index=False)

    print(f"\n{'='*60}")
    print(f"Calibration Report Generated: {OUTPUT_PATH}")
    print(f"{'='*60}")
    print(f"Total entries: {len(report_df)}")
    print(f"Videos processed: {report_df['video_id'].nunique()}")

    # Summary statistics
    print(f"\n--- Match Summary ---")
    match_counts = report_df["match_status"].value_counts()
    for status, count in match_counts.items():
        pct = count / len(report_df) * 100
        print(f"  {status}: {count} ({pct:.1f}%)")

    # Per-metric summary
    print(f"\n--- Per-Metric Accuracy ---")
    for metric in report_df["metric"].unique():
        metric_df = report_df[report_df["metric"] == metric]
        exact_matches = (metric_df["bucket_distance"] == 0).sum()
        total = len(metric_df)
        pct = exact_matches / total * 100 if total > 0 else 0
        avg_distance = metric_df["bucket_distance"].mean()
        print(f"  {metric}: {exact_matches}/{total} exact ({pct:.0f}%), avg distance: {avg_distance:.2f}")

    # Outliers (distance >= 2)
    outliers = report_df[report_df["bucket_distance"] >= 2]
    if len(outliers) > 0:
        print(f"\n--- Outliers (distance >= 2) ---")
        for _, row in outliers.iterrows():
            print(f"  Video {row['video_id']}: {row['metric']} - Human: {row['human_label']}, Model: {row['model_label']} (dist={row['bucket_distance']})")

    return report_df


if __name__ == "__main__":
    generate_report()
