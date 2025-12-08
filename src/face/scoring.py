"""
Scoring and interpretation logic for the VERA Face Module.
Aggregates metrics, applies sliding windows, computes scores, and generates text interpretations.
"""

import numpy as np
import pandas as pd
from src.face.config import (
    BASELINE_HEAD_STABILITY_OPTIMAL,
    BASELINE_HEAD_STABILITY_VAR,
    BASELINE_GAZE_MIDPOINT,
    BASELINE_GAZE_SCALE,
    BASELINE_SMILE_OPTIMAL,
    BASELINE_SMILE_VAR,
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

def get_consistency_interpretation(score):
    """
    Get generic interpretation for consistency scores (0-1).
    """
    if score >= 0.7:
        return "High consistency. Very stable behavior.", "Excellent stability. Keep it up."
    elif score >= 0.4:
        return "Moderate consistency. Some variations.", "Good balance, but try to be more consistent."
    else:
        return "Low consistency. Highly variable.", "Try to maintain a more steady behavior."

def compute_scores(raw_df):
    """
    Compute aggregated scores from raw frame data.

    Args:
        raw_df (pd.DataFrame): DataFrame with 'head_speed', 'gaze_dg', 'smile', 'second'.

    Returns:
        tuple: (scores_dict, window_df, timeline_1s)
               scores_dict contains global scores and interpretations.
               window_df contains the 5-second window metrics.
               timeline_1s contains the 1Hz timeline with values and scores.
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
        }, pd.DataFrame(), pd.DataFrame()

    # 3. Scoring Logic

    # --- HEAD STABILITY ---
    head_val = df_head_5s["value"]
    # Absolute (Communication Score)
    head_comm_score = np.exp(-((head_val - BASELINE_HEAD_STABILITY_OPTIMAL)**2) / BASELINE_HEAD_STABILITY_VAR)

    # Relative (Consistency Score)
    z_head = (head_val - head_val.mean()) / (head_val.std() + 1e-9)
    head_cons_score = 1 / (1 + np.exp(z_head))

    df_head_5s["comm_score"] = head_comm_score
    df_head_5s["cons_score"] = head_cons_score

    # --- GAZE CONSISTENCY ---
    gaze_val = df_gaze_5s["value"]
    # Absolute (Communication Score) - Inverted logistic (lower jitter = higher score)
    # MIDPOINT is the logistic center; optimal values are below this (≤0.08)
    gaze_comm_score = 1 / (1 + np.exp((gaze_val - BASELINE_GAZE_MIDPOINT) / BASELINE_GAZE_SCALE))

    # Relative (Consistency Score)
    z_gaze = (gaze_val - gaze_val.mean()) / (gaze_val.std() + 1e-9)
    gaze_cons_score = 1 / (1 + np.exp(z_gaze))

    df_gaze_5s["comm_score"] = gaze_comm_score
    df_gaze_5s["cons_score"] = gaze_cons_score

    # --- SMILE ACTIVATION ---
    smile_val = df_smile_5s["value"]
    # Absolute (Communication Score) - GAUSSIAN for optimal band
    smile_comm_score = np.exp(-((smile_val - BASELINE_SMILE_OPTIMAL)**2) / BASELINE_SMILE_VAR)

    # Relative (Consistency Score)
    z_smile = (smile_val - smile_val.mean()) / (smile_val.std() + 1e-9)
    smile_cons_score = 1 / (1 + np.exp(-z_smile))

    df_smile_5s["comm_score"] = smile_comm_score
    df_smile_5s["cons_score"] = smile_cons_score

    # --- GLOBAL SCORES ---
    # Global Communication Score (Mean of Absolute Scores)
    global_comm_score = (
        df_head_5s["comm_score"].mean() +
        df_gaze_5s["comm_score"].mean() +
        df_smile_5s["comm_score"].mean()
    ) / 3

    # Global Consistency Score (Mean of Relative Scores)
    global_consistency_score = (
        df_head_5s["cons_score"].mean() +
        df_gaze_5s["cons_score"].mean() +
        df_smile_5s["cons_score"].mean()
    ) / 3

    # 4. Prepare Outputs

    # Merge window dataframes for export
    # Rename columns to be clear
    df_head_5s = df_head_5s.rename(columns={"value": "head_speed_val", "comm_score": "head_stability_comm_score", "cons_score": "head_stability_cons_score"})
    df_gaze_5s = df_gaze_5s.rename(columns={"value": "gaze_jitter_val", "comm_score": "gaze_consistency_comm_score", "cons_score": "gaze_consistency_cons_score"})
    df_smile_5s = df_smile_5s.rename(columns={"value": "smile_val", "comm_score": "smile_activation_comm_score", "cons_score": "smile_activation_cons_score"})

    # Merge on start_sec/end_sec
    window_df = df_head_5s.merge(df_gaze_5s, on=["start_sec", "end_sec"]).merge(df_smile_5s, on=["start_sec", "end_sec"])

    # Add Global Scores to window_df (constant columns)
    window_df["global_comm_score"] = global_comm_score
    window_df["global_consistency_score"] = global_consistency_score

    # 5. Get Interpretations & Coaching

    # Communication Scores (Absolute)
    head_mean_comm = df_head_5s["head_stability_comm_score"].mean()
    gaze_mean_comm = df_gaze_5s["gaze_consistency_comm_score"].mean()
    smile_mean_comm = df_smile_5s["smile_activation_comm_score"].mean()

    # Consistency Scores (Relative)
    head_mean_cons = df_head_5s["head_stability_cons_score"].mean()
    gaze_mean_cons = df_gaze_5s["gaze_consistency_cons_score"].mean()
    smile_mean_cons = df_smile_5s["smile_activation_cons_score"].mean()

    # Interpretations
    # We must pass the MEAN RAW VALUE to get the correct communication interpretation.

    head_mean_val = df_head_5s["head_speed_val"].mean()
    gaze_mean_val = df_gaze_5s["gaze_jitter_val"].mean()
    smile_mean_val = df_smile_5s["smile_val"].mean()

    interp_head_comm, coach_head_comm = get_interpretation("head_stability", head_mean_val)
    interp_gaze_comm, coach_gaze_comm = get_interpretation("gaze_consistency", gaze_mean_val)
    interp_smile_comm, coach_smile_comm = get_interpretation("smile_activation", smile_mean_val)

    # Consistency Interpretations
    interp_head_cons, coach_head_cons = get_consistency_interpretation(head_mean_cons)
    interp_gaze_cons, coach_gaze_cons = get_consistency_interpretation(gaze_mean_cons)
    interp_smile_cons, coach_smile_cons = get_consistency_interpretation(smile_mean_cons)

    scores = {
        "global_comm_score": float(global_comm_score),
        "global_consistency_score": float(global_consistency_score),
        "face_global_interpretation": get_global_interpretation(global_comm_score),

        # Head Stability
        "head_stability_communication_score": float(head_mean_comm),
        "head_stability_communication_interpretation": interp_head_comm,
        "head_stability_communication_coaching": coach_head_comm,

        "head_stability_consistency_score": float(head_mean_cons),
        "head_stability_consistency_interpretation": interp_head_cons,
        "head_stability_consistency_coaching": coach_head_cons,

        # Gaze Consistency
        "gaze_consistency_communication_score": float(gaze_mean_comm),
        "gaze_consistency_communication_interpretation": interp_gaze_comm,
        "gaze_consistency_communication_coaching": coach_gaze_comm,

        "gaze_consistency_consistency_score": float(gaze_mean_cons),
        "gaze_consistency_consistency_interpretation": interp_gaze_cons,
        "gaze_consistency_consistency_coaching": coach_gaze_cons,

        # Smile Activation
        "smile_activation_communication_score": float(smile_mean_comm),
        "smile_activation_communication_interpretation": interp_smile_comm,
        "smile_activation_communication_coaching": coach_smile_comm,

        "smile_activation_consistency_score": float(smile_mean_cons),
        "smile_activation_consistency_interpretation": interp_smile_cons,
        "smile_activation_consistency_coaching": coach_smile_cons
    }

    # Project Raw Values (_val) and Communication Scores (_comm_score)
    # Comm Score is what we want to see on timeline.
    cols_to_project = [c for c in window_df.columns if "_val" in c or "_comm_score" in c or "_cons_score" in c]
    projection_input = window_df[["start_sec", "end_sec"] + cols_to_project]

    timeline_1s = project_windows_to_seconds(projection_input)

    return scores, window_df, timeline_1s
