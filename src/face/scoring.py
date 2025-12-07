"""
Scoring and interpretation logic for the VERA Face Module.
Aggregates metrics, applies sliding windows, computes scores, and generates text interpretations.
"""

import numpy as np
import pandas as pd
from src.face.config import (
    BASELINE_HEAD_STABILITY_OPTIMAL,
    BASELINE_HEAD_STABILITY_VAR,
    BASELINE_GAZE_OPTIMAL,
    BASELINE_GAZE_VAR,
    BASELINE_SMILE_OPTIMAL,
    BASELINE_SMILE_RANGE,
    INTERPRETATION_RANGES
)
from src.utils.temporal import project_windows_to_seconds

def sliding_windows(series, window=5):
    """
    Apply a sliding window to a pandas Series.
    Returns a DataFrame with start_sec, end_sec, and mean value for the window.
    """
    rows = []
    seconds = series.index.values

    for start in seconds:
        end = start + window

        win = series.loc[start:end]

        if len(win) == window + 1:
            rows.append({
                "start_sec": start,
                "end_sec": end,
                "value": win.mean()
            })

    return pd.DataFrame(rows)

def get_interpretation(metric_type, raw_value):
    """
    Get text interpretation and coaching based on raw value and buckets.
    """
    buckets = INTERPRETATION_RANGES.get(metric_type, [])

    # Iterate through buckets to find the matching range
    for bucket in buckets:
        if raw_value <= bucket["max"]:
            return bucket["text"], bucket["coaching"]

    # Fallback (should not happen with max=999)
    return "Value out of range", "Check your settings."

def get_global_interpretation(score):
    """
    Get interpretation for the global score (Range-based).
    """
    ranges = INTERPRETATION_RANGES.get("face_global_score", [])
    for low, high, text in ranges:
        if low <= score <= high:
            return text
    return "Score out of range"

def compute_scores(raw_df):
    """
    Compute aggregated scores from raw frame data.

    Args:
        raw_df (pd.DataFrame): DataFrame with 'head_speed', 'gaze_dg', 'smile', 'second'.

    Returns:
        tuple: (scores_dict, window_df)
               scores_dict contains global scores and interpretations.
               window_df contains the 5-second window metrics.
    """
    # 1. Aggregate per second
    # Head Stability: Use MEAN speed (IOD/sec) to match baseline (0.35 IOD/sec)
    head_speed_1s  = raw_df.groupby("second")["head_speed"].mean().fillna(0)
    jitter_gaze_1s = raw_df.groupby("second")["gaze_dg"].var().fillna(0)
    smile_1s       = raw_df.groupby("second")["smile"].mean().fillna(0)

    # 2. Sliding Windows (5s)
    df_head_5s  = sliding_windows(head_speed_1s)
    df_gaze_5s  = sliding_windows(jitter_gaze_1s)
    df_smile_5s = sliding_windows(smile_1s)

    # If video is too short for windows, handle gracefully
    if df_head_5s.empty:
        return {
            "error": "Video too short for analysis (needs > 5 seconds)"
        }, pd.DataFrame()

    # 3. Scoring Logic

    # --- HEAD STABILITY ---
    # Relative
    z_head = (df_head_5s["value"] - df_head_5s["value"].mean()) / (df_head_5s["value"].std() + 1e-9)
    df_head_5s["rel_score"] = 1 / (1 + np.exp(z_head)) # Inverted: Lower speed (relative to mean) is better for stability

    # Absolute (Gaussian: Optimal range)
    head_abs = df_head_5s["value"].mean()
    abs_head_score = np.exp(-((head_abs - BASELINE_HEAD_STABILITY_OPTIMAL)**2) / BASELINE_HEAD_STABILITY_VAR)

    # Final
    score_head = 0.5 * abs_head_score + 0.5 * df_head_5s["rel_score"].mean()

    # --- GAZE CONSISTENCY ---
    # Relative
    z_gaze = (df_gaze_5s["value"] - df_gaze_5s["value"].mean()) / (df_gaze_5s["value"].std() + 1e-9)
    df_gaze_5s["rel_score"] = 1 / (1 + np.exp(z_gaze)) # Inverted

    # Absolute
    gaze_abs = df_gaze_5s["value"].mean()
    abs_gaze_score = 1 / (1 + np.exp((gaze_abs - BASELINE_GAZE_OPTIMAL) / BASELINE_GAZE_VAR))

    # Final
    score_gaze = 0.5 * abs_gaze_score + 0.5 * df_gaze_5s["rel_score"].mean()

    # --- SMILE ACTIVATION ---
    # Relative
    z_smile = (df_smile_5s["value"] - df_smile_5s["value"].mean()) / (df_smile_5s["value"].std() + 1e-9)
    df_smile_5s["rel_score"] = 1 / (1 + np.exp(-z_smile)) # Normal: higher is better

    # Absolute
    smile_abs = df_smile_5s["value"].mean()
    abs_smile_score = 1 / (1 + np.exp(-(smile_abs - BASELINE_SMILE_OPTIMAL) / BASELINE_SMILE_RANGE))

    # Final
    score_smile = 0.5 * abs_smile_score + 0.5 * df_smile_5s["rel_score"].mean()

    # --- GLOBAL SCORE ---
    global_score = (score_head + score_gaze + score_smile) / 3

    # 4. Prepare Outputs

    # Merge window dataframes for export
    # Rename columns to be clear
    df_head_5s = df_head_5s.rename(columns={"value": "head_speed_val", "rel_score": "head_score"})
    df_gaze_5s = df_gaze_5s.rename(columns={"value": "gaze_jitter_val", "rel_score": "gaze_score"})
    df_smile_5s = df_smile_5s.rename(columns={"value": "smile_val", "rel_score": "smile_score"})

    # Merge on start_sec/end_sec
    window_df = df_head_5s.merge(df_gaze_5s, on=["start_sec", "end_sec"]).merge(df_smile_5s, on=["start_sec", "end_sec"])


    mean_head_speed = raw_df["head_speed"].mean()
    mean_gaze_dg = raw_df["gaze_dg"].mean()

    # Use SCORE for interpretation (standardization)
    interp_head, coach_head = get_interpretation("head_stability", score_head)

    # Gaze and Smile use SCORE for buckets (0-1)
    interp_gaze, coach_gaze = get_interpretation("gaze_consistency", score_gaze)
    interp_smile, coach_smile = get_interpretation("smile_activation", score_smile)

    scores = {
        "face_global_score": float(global_score),
        "face_global_interpretation": get_global_interpretation(global_score),

        "head_stability_score": float(score_head),
        "head_stability_interpretation": interp_head,
        "head_stability_coaching": coach_head,

        "gaze_consistency_score": float(score_gaze),
        "gaze_consistency_interpretation": interp_gaze,
        "gaze_consistency_coaching": coach_gaze,

        "smile_activation_score": float(score_smile),
        "smile_activation_interpretation": interp_smile,
        "smile_activation_coaching": coach_smile
    }

    # 5. Generate Timeline (1Hz -> 5s)
    cols_to_project = [c for c in window_df.columns if "_score" in c]
    projection_input = window_df[["start_sec", "end_sec"] + cols_to_project]

    timeline_1s = project_windows_to_seconds(projection_input)

    return scores, window_df, timeline_1s
