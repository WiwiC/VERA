import json
import csv
import sys
from pathlib import Path
from collections import defaultdict

MANIFEST_PATH = "data/raw/updated_calibration_manifest_V2.csv"
RESULTS_DIR = Path("data/processed")

# Metric Mapping (Manifest Column -> JSON Metric Key)
METRIC_MAP = {
    "head_stability": "head_stability",
    "gaze_stability": "gaze_stability",
    "smile_activation": "smile_activation",
    "head_down_ratio": "head_down_ratio",
    "gesture_magnitude": "gesture_magnitude",
    "gesture_activity": "gesture_activity",
    "gesture_stability": "gesture_stability",
    "body_sway": "body_sway",
    "posture_openess": "posture_openness", # Note spelling in CSV
    "speech_rate": "speech_rate",
    "pause_ratio": "pause_ratio",
    "pitch_dynamic": "pitch_dynamic",
    "volume_dynamic": "volume_dynamic",
    "vocal_punch": "vocal_punch"
}

# Module Mapping
MODULE_MAP = {
    "head_stability": "face",
    "gaze_stability": "face",
    "smile_activation": "face",
    "head_down_ratio": "face",
    "gesture_magnitude": "body",
    "gesture_activity": "body",
    "gesture_stability": "body",
    "body_sway": "body",
    "posture_openness": "body",
    "speech_rate": "audio",
    "pause_ratio": "audio",
    "pitch_dynamic": "audio",
    "volume_dynamic": "audio",
    "vocal_punch": "audio"
}

# Opposite Definitions (for "Low Opposites" ranking)
# If (Manifest, Actual) pair is in this set (order independent), it's an Opposite Error.
OPPOSITES = {
    frozenset(["very_low", "very_high"]),
    frozenset(["very_low", "high"]),
    frozenset(["low", "very_high"]),
    frozenset(["low", "high"]),
    frozenset(["rigid", "distracting"]),
    frozenset(["rigid", "unstable"]),
    frozenset(["closed", "open"]),
    frozenset(["monotone", "expressive"]),
    frozenset(["flat", "expressive"]),
    frozenset(["muffled", "strong"]),
    frozenset(["soft", "strong"]),
    frozenset(["slow", "fast"]),
    frozenset(["very_slow", "fast"]),
    frozenset(["very_slow", "very_fast"]),
    frozenset(["no_pauses", "high_pauses"]), # Assuming high_pauses exists? Or disjointed?
    frozenset(["no_pauses", "disjointed"]),
}

def is_opposite(label1, label2):
    if not label1 or not label2:
        return False
    l1 = label1.lower().strip()
    l2 = label2.lower().strip()
    if l1 == l2:
        return False
    return frozenset([l1, l2]) in OPPOSITES

def load_manifest():
    videos = {}
    with open(MANIFEST_PATH, "r") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            vid = row["file_video_name"].strip()
            videos[vid] = row
    return videos

def get_actual_label(video_id, metric_key):
    # Handle CSV spelling mismatch
    json_metric_key = metric_key
    if metric_key == "posture_openess":
        json_metric_key = "posture_openness"

    module = MODULE_MAP.get(json_metric_key)
    if not module:
        return None

    path = RESULTS_DIR / video_id / "results_global_enriched.json"
    if not path.exists():
        return None

    try:
        with open(path) as f:
            data = json.load(f)

        # Navigate: module -> metrics -> metric_key -> label
        return data.get(module, {}).get("metrics", {}).get(json_metric_key, {}).get("label")
    except:
        return None

def main():
    manifest_videos = load_manifest()
    results = []

    print(f"Analyzing {len(manifest_videos)} videos from manifest...")

    for vid, manifest_data in manifest_videos.items():
        matches = 0
        opposites = 0
        total_metrics = 0
        details = []

        for csv_col, json_key in METRIC_MAP.items():
            # FILTER: Skip Audio metrics for Visual Demo search
            if MODULE_MAP.get(json_key) == "audio":
                continue

            expected = manifest_data.get(csv_col, "").strip().lower()
            if not expected:
                continue

            actual = get_actual_label(vid, json_key)
            if actual:
                actual = actual.strip().lower()
                total_metrics += 1

                if actual == expected:
                    matches += 1
                elif is_opposite(expected, actual):
                    opposites += 1
                    details.append(f"{json_key}: {expected} vs {actual} (OPPOSITE)")
                else:
                    details.append(f"{json_key}: {expected} vs {actual}")

        if total_metrics > 0:
            score = matches / total_metrics
            results.append({
                "video": vid,
                "matches": matches,
                "opposites": opposites,
                "total": total_metrics,
                "score": score,
                "details": details
            })

    # Sort by Matches (Descending)
    results.sort(key=lambda x: x["matches"], reverse=True)

    print("\n" + "="*50)
    print("🏆 BEST VIDEO FOR DEMO (Highest Exact Matches)")
    print("="*50)
    if results:
        best = results[0]
        print(f"Video: {best['video']}")
        print(f"Matches: {best['matches']}/{best['total']} ({best['score']:.1%})")
        print(f"Opposites: {best['opposites']}")
        print("Mismatches:")
        for d in best['details']:
            print(f"  - {d}")

    print("\n" + "="*50)
    print("TOP 5 BEST MATCHING VIDEOS")
    print("="*50)
    for i, res in enumerate(results[:5]):
        print(f"{i+1}. Video {res['video']}: {res['matches']} matches, {res['opposites']} opposites")

    # Sort by Opposites (Ascending) -> "Low Opposites"
    # Secondary sort by Matches (Descending)
    results_low_opp = sorted(results, key=lambda x: (x["opposites"], -x["matches"]))

    print("\n" + "="*50)
    print("TOP 3 VIDEOS WITH LOWEST OPPOSITE ERRORS")
    print("="*50)
    for i, res in enumerate(results_low_opp[:3]):
        print(f"{i+1}. Video {res['video']}: {res['opposites']} opposites, {res['matches']} matches")

    print("\n" + "="*50)
    print("REQUESTED ANALYSIS: VIDEOS 60 & 66")
    print("="*50)
    for target in ["60", "66"]:
        res = next((r for r in results if r["video"] == target), None)
        if res:
            print(f"\nVideo {target}:")
            print(f"Matches: {res['matches']}/{res['total']} ({res['score']:.1%})")
            print(f"Opposites: {res['opposites']}")
            print("Mismatches:")
            for d in res['details']:
                print(f"  - {d}")
        else:
            print(f"\nVideo {target}: Not found in results.")

if __name__ == "__main__":
    main()
