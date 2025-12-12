import json
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.body.config import (
    BASELINE_BODY_SWAY_OPTIMAL,
    BASELINE_BODY_SWAY_VAR,
    INTERPRETATION_RANGES as BODY_RANGES
)
from src.face.config import INTERPRETATION_RANGES as FACE_RANGES
from src.audio.config import INTERPRETATION_RANGES as AUDIO_RANGES

DATA_DIR = Path("data/processed")

def check_score_alignment(metric, score, label):
    """
    Check if score aligns with label.
    """
    if label == "optimal" and score < 60:
        return "LOW_SCORE_FOR_OPTIMAL"
    if label == "good" and score < 40:
        return "LOW_SCORE_FOR_GOOD"
    if label in ["poor", "distracting", "rigid", "very_low", "very_high"] and score > 60:
        return "HIGH_SCORE_FOR_POOR"
    return "OK"

def check_coaching_alignment(metric, label, coaching, ranges):
    """
    Check if coaching text matches the config for the given label.
    """
    buckets = ranges.get(metric, [])
    for bucket in buckets:
        if bucket["label"] == label:
            expected = bucket["coaching"]
            if coaching != expected:
                return f"MISMATCH: Expected '{expected[:30]}...', Got '{coaching[:30]}...'"
            return "OK"
    return "LABEL_NOT_FOUND_IN_CONFIG"

def audit_video(video_dir):
    json_path = video_dir / "results_global_enriched.json"
    if not json_path.exists():
        return []

    try:
        with open(json_path) as f:
            data = json.load(f)
    except Exception as e:
        return [f"Error reading {json_path}: {e}"]

    issues = []
    video_name = video_dir.name

    # Flatten metrics
    metrics = []

    # Body
    if "body" in data and "metrics" in data["body"]:
        for m in ["body_sway", "gesture_magnitude", "gesture_activity", "gesture_stability", "posture_openness"]:
            if m in data["body"]["metrics"]:
                item = data["body"]["metrics"][m]
                metrics.append(("body", m, item, BODY_RANGES))

    # Face
    if "face" in data and "metrics" in data["face"]:
        for m in ["head_stability", "gaze_stability", "smile_activation", "head_down_ratio"]:
            if m in data["face"]["metrics"]:
                item = data["face"]["metrics"][m]
                metrics.append(("face", m, item, FACE_RANGES))

    # Audio
    if "audio" in data and "metrics" in data["audio"]:
        for m in ["speech_rate", "pause_ratio", "pitch_dynamic", "volume_dynamic", "vocal_punch"]:
            if m in data["audio"]["metrics"]:
                item = data["audio"]["metrics"][m]
                metrics.append(("audio", m, item, AUDIO_RANGES))

    for module, metric, item, ranges in metrics:
        score = item.get("score", 0)
        raw = item.get("raw_value", 0)
        label = item.get("label", "unknown")
        coaching = item.get("coaching", "")

        # DEBUG for Video 63 Body Sway
        if video_name == "63" and metric == "body_sway":
            print(f"DEBUG [63] body_sway: Score={score}, Label={label}, Raw={raw}")

        # 1. Score Alignment
        align_status = check_score_alignment(metric, score, label)
        if align_status != "OK":
            issues.append({
                "video": video_name,
                "metric": metric,
                "issue": align_status,
                "details": f"Score: {score}, Label: {label}, Raw: {raw:.3f}"
            })

        # 2. Coaching Alignment
        coach_status = check_coaching_alignment(metric, label, coaching, ranges)
        if coach_status != "OK":
            issues.append({
                "video": video_name,
                "metric": metric,
                "issue": "COACHING_MISMATCH",
                "details": coach_status
            })

    return issues

def main():
    print("--- Configuration Check ---")
    print(f"BASELINE_BODY_SWAY_OPTIMAL: {BASELINE_BODY_SWAY_OPTIMAL}")
    print(f"BASELINE_BODY_SWAY_VAR: {BASELINE_BODY_SWAY_VAR}")

    # Test Calculation for 0.558
    val = 0.558257
    calc_score = np.exp(-((val - BASELINE_BODY_SWAY_OPTIMAL)**2) / BASELINE_BODY_SWAY_VAR)
    print(f"Test Calc for 0.558: {calc_score:.4f} (Expected ~0.28 based on user report)")
    print("-" * 30)

    all_issues = []
    for video_dir in sorted(DATA_DIR.iterdir()):
        if video_dir.is_dir():
            if video_dir.name == "63":
                print(f"\n--- DEBUG VIDEO 63 ---")
                issues = audit_video(video_dir)
                for i in issues:
                    print(f"ISSUE FOUND: {i}")
                all_issues.extend(issues)
            else:
                all_issues.extend(audit_video(video_dir))

    # Group by Issue Type
    print(f"\nFound {len(all_issues)} issues.")

    print("\n--- Score vs Label Discrepancies ---")
    score_issues = [i for i in all_issues if "SCORE" in i["issue"]]
    for i in score_issues[:20]: # Show top 20
        print(f"[{i['video']}] {i['metric']}: {i['issue']} ({i['details']})")
    if len(score_issues) > 20:
        print(f"... and {len(score_issues) - 20} more.")

    print("\n--- Coaching Mismatches ---")
    coach_issues = [i for i in all_issues if "COACHING" in i["issue"]]
    for i in coach_issues[:20]:
        print(f"[{i['video']}] {i['metric']}: {i['details']}")
    if len(coach_issues) > 20:
        print(f"... and {len(coach_issues) - 20} more.")

if __name__ == "__main__":
    main()
