"""
Scoring and interpretation logic for the VERA Body Module.
Aggregates metrics, applies sliding windows, computes scores, and generates text interpretations.
"""

import numpy as np
import pandas as pd
from src.body.config import (
    BASELINE_GESTURE_MAG_OPTIMAL,
    BASELINE_GESTURE_MAG_VAR,
    BASELINE_GESTURE_ACTIVITY_OPTIMAL,
    BASELINE_GESTURE_ACTIVITY_VAR,
    BASELINE_GESTURE_JITTER_OPTIMAL,
    BASELINE_GESTURE_JITTER_RANGE,
    BASELINE_BODY_SWAY_OPTIMAL,
    BASELINE_BODY_SWAY_VAR,
    BASELINE_POSTURE_OPTIMAL,
    BASELINE_POSTURE_VAR,
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
    ranges = INTERPRETATION_RANGES.get("body_global_score", [])
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
        raw_df (pd.DataFrame): DataFrame with raw body metrics.

    Returns:
        tuple: (scores_dict, window_df, timeline_1s)
    """
    # 1. Aggregate per second
    gesture_mag_1s    = raw_df.groupby("second")["gesture_magnitude"].mean().fillna(0)
    gesture_act_1s    = raw_df.groupby("second")["gesture_activity"].mean().fillna(0)
    gesture_jitter_1s = raw_df.groupby("second")["gesture_activity"].var().fillna(0)
    body_sway_1s      = raw_df.groupby("second")["body_sway"].mean().fillna(0)
    posture_open_1s   = raw_df.groupby("second")["posture_openness"].mean().fillna(0)

    # 2. Sliding Windows (5s)
    df_mag_5s    = sliding_windows(gesture_mag_1s)
    df_act_5s    = sliding_windows(gesture_act_1s)
    df_jitter_5s = sliding_windows(gesture_jitter_1s)
    df_sway_5s   = sliding_windows(body_sway_1s)
    df_open_5s   = sliding_windows(posture_open_1s)

    if df_mag_5s.empty:
        return {"error": "Video too short"}, pd.DataFrame(), pd.DataFrame()

    # 3. Scoring Logic

    # --- GESTURE MAGNITUDE ---
    # Absolute Score (Communication)
    mag_val = df_mag_5s["value"]
    mag_comm_score = np.exp(-((mag_val - BASELINE_GESTURE_MAG_OPTIMAL)**2) / BASELINE_GESTURE_MAG_VAR)

    # Relative Score (Consistency)
    z_mag = (mag_val - mag_val.mean()) / (mag_val.std() + 1e-9)
    mag_cons_score = np.exp(-z_mag**2)

    df_mag_5s["comm_score"] = mag_comm_score
    df_mag_5s["cons_score"] = mag_cons_score

    # --- GESTURE ACTIVITY ---
    act_val = df_act_5s["value"]
    act_comm_score = np.exp(-((act_val - BASELINE_GESTURE_ACTIVITY_OPTIMAL)**2) / BASELINE_GESTURE_ACTIVITY_VAR)

    z_act = (act_val - act_val.mean()) / (act_val.std() + 1e-9)
    act_cons_score = np.exp(-z_act**2)

    df_act_5s["comm_score"] = act_comm_score
    df_act_5s["cons_score"] = act_cons_score

    # --- GESTURE JITTER ---
    jit_val = df_jitter_5s["value"]
    # Absolute Score (Communication)
    jit_comm_score = 1 / (1 + np.exp((jit_val - BASELINE_GESTURE_JITTER_OPTIMAL) / BASELINE_GESTURE_JITTER_RANGE))

    # Relative Score (Consistency)
    z_jit = (jit_val - jit_val.mean()) / (jit_val.std() + 1e-9)
    jit_cons_score = 1 / (1 + np.exp(z_jit)) # Inverted relative score (lower jitter relative to self is better?)

    df_jitter_5s["comm_score"] = jit_comm_score
    df_jitter_5s["cons_score"] = jit_cons_score

    # --- BODY SWAY ---
    sway_val = df_sway_5s["value"]
    # Absolute Score (Communication)
    sway_comm_score = np.exp(-((sway_val - BASELINE_BODY_SWAY_OPTIMAL)**2) / BASELINE_BODY_SWAY_VAR)

    # Relative Score (Consistency)
    z_sway = (sway_val - sway_val.mean()) / (sway_val.std() + 1e-9)
    sway_cons_score = 1 / (1 + np.exp(z_sway))

    df_sway_5s["comm_score"] = sway_comm_score
    df_sway_5s["cons_score"] = sway_cons_score

    # --- POSTURE OPENNESS ---
    open_val = df_open_5s["value"]
    # Absolute Score (Communication) - GAUSSIAN for optimal band
    open_comm_score = np.exp(-((open_val - BASELINE_POSTURE_OPTIMAL)**2) / BASELINE_POSTURE_VAR)

    # Relative Score (Consistency)
    z_open = (open_val - open_val.mean()) / (open_val.std() + 1e-9)
    open_cons_score = 1 / (1 + np.exp(-z_open))

    df_open_5s["comm_score"] = open_comm_score
    df_open_5s["cons_score"] = open_cons_score

    # --- GLOBAL SCORES ---
    # Global Communication Score (Mean of Absolute Scores)
    global_comm_score = (
        df_mag_5s["comm_score"].mean() +
        df_act_5s["comm_score"].mean() +
        df_jitter_5s["comm_score"].mean() +
        df_sway_5s["comm_score"].mean() +
        df_open_5s["comm_score"].mean()
    ) / 5

    # Global Consistency Score (Mean of Relative Scores)
    global_consistency_score = (
        df_mag_5s["cons_score"].mean() +
        df_act_5s["cons_score"].mean() +
        df_jitter_5s["cons_score"].mean() +
        df_sway_5s["cons_score"].mean() +
        df_open_5s["cons_score"].mean()
    ) / 5

    # 4. Prepare Outputs
    # Rename columns for clarity in window_df
    df_mag_5s = df_mag_5s.rename(columns={"value": "gesture_magnitude_val", "comm_score": "gesture_magnitude_comm_score", "cons_score": "gesture_magnitude_cons_score"})
    df_act_5s = df_act_5s.rename(columns={"value": "gesture_activity_val", "comm_score": "gesture_activity_comm_score", "cons_score": "gesture_activity_cons_score"})
    df_jitter_5s = df_jitter_5s.rename(columns={"value": "gesture_jitter_val", "comm_score": "gesture_jitter_comm_score", "cons_score": "gesture_jitter_cons_score"})
    df_sway_5s = df_sway_5s.rename(columns={"value": "body_sway_val", "comm_score": "body_sway_comm_score", "cons_score": "body_sway_cons_score"})
    df_open_5s = df_open_5s.rename(columns={"value": "posture_openness_val", "comm_score": "posture_openness_comm_score", "cons_score": "posture_openness_cons_score"})

    window_df = df_mag_5s.merge(df_act_5s, on=["start_sec", "end_sec"])\
                         .merge(df_jitter_5s, on=["start_sec", "end_sec"])\
                         .merge(df_sway_5s, on=["start_sec", "end_sec"])\
                         .merge(df_open_5s, on=["start_sec", "end_sec"])

    # Add Global Scores to window_df (constant columns) as requested
    window_df["global_comm_score"] = global_comm_score
    window_df["global_consistency_score"] = global_consistency_score

    # 5. Get Interpretations & Coaching

    # Communication Scores (Absolute)
    mag_mean_comm = df_mag_5s["gesture_magnitude_comm_score"].mean()
    act_mean_comm = df_act_5s["gesture_activity_comm_score"].mean()
    jit_mean_comm = df_jitter_5s["gesture_jitter_comm_score"].mean()
    sway_mean_comm = df_sway_5s["body_sway_comm_score"].mean()
    open_mean_comm = df_open_5s["posture_openness_comm_score"].mean()

    # Consistency Scores (Relative)
    mag_mean_cons = df_mag_5s["gesture_magnitude_cons_score"].mean()
    act_mean_cons = df_act_5s["gesture_activity_cons_score"].mean()
    jit_mean_cons = df_jitter_5s["gesture_jitter_cons_score"].mean()
    sway_mean_cons = df_sway_5s["body_sway_cons_score"].mean()
    open_mean_cons = df_open_5s["posture_openness_cons_score"].mean()

    # Interpretations
    # Use MEAN RAW VALUE for Communication Interpretation (buckets are based on values)
    mag_mean_val = df_mag_5s["gesture_magnitude_val"].mean()
    act_mean_val = df_act_5s["gesture_activity_val"].mean()
    jit_mean_val = df_jitter_5s["gesture_jitter_val"].mean()
    sway_mean_val = df_sway_5s["body_sway_val"].mean()
    open_mean_val = df_open_5s["posture_openness_val"].mean()

    interp_mag_comm, coach_mag_comm = get_interpretation("gesture_magnitude", mag_mean_val)
    interp_act_comm, coach_act_comm = get_interpretation("gesture_activity", act_mean_val)
    interp_jit_comm, coach_jit_comm = get_interpretation("gesture_jitter", jit_mean_val)
    interp_sway_comm, coach_sway_comm = get_interpretation("body_sway", sway_mean_val)
    interp_open_comm, coach_open_comm = get_interpretation("posture_openness", open_mean_val)

    # Consistency Interpretations
    interp_mag_cons, coach_mag_cons = get_consistency_interpretation(mag_mean_cons)
    interp_act_cons, coach_act_cons = get_consistency_interpretation(act_mean_cons)
    interp_jit_cons, coach_jit_cons = get_consistency_interpretation(jit_mean_cons)
    interp_sway_cons, coach_sway_cons = get_consistency_interpretation(sway_mean_cons)
    interp_open_cons, coach_open_cons = get_consistency_interpretation(open_mean_cons)

    scores = {
        "global_comm_score": float(global_comm_score),
        "global_consistency_score": float(global_consistency_score),
        "body_global_interpretation": get_global_interpretation(global_comm_score),

        # Gesture Magnitude
        "gesture_magnitude_communication_score": float(mag_mean_comm),
        "gesture_magnitude_communication_interpretation": interp_mag_comm,
        "gesture_magnitude_communication_coaching": coach_mag_comm,

        "gesture_magnitude_consistency_score": float(mag_mean_cons),
        "gesture_magnitude_consistency_interpretation": interp_mag_cons,
        "gesture_magnitude_consistency_coaching": coach_mag_cons,

        # Gesture Activity
        "gesture_activity_communication_score": float(act_mean_comm),
        "gesture_activity_communication_interpretation": interp_act_comm,
        "gesture_activity_communication_coaching": coach_act_comm,

        "gesture_activity_consistency_score": float(act_mean_cons),
        "gesture_activity_consistency_interpretation": interp_act_cons,
        "gesture_activity_consistency_coaching": coach_act_cons,

        # Gesture Jitter
        "gesture_jitter_communication_score": float(jit_mean_comm),
        "gesture_jitter_communication_interpretation": interp_jit_comm,
        "gesture_jitter_communication_coaching": coach_jit_comm,

        "gesture_jitter_consistency_score": float(jit_mean_cons),
        "gesture_jitter_consistency_interpretation": interp_jit_cons,
        "gesture_jitter_consistency_coaching": coach_jit_cons,

        # Body Sway
        "body_sway_communication_score": float(sway_mean_comm),
        "body_sway_communication_interpretation": interp_sway_comm,
        "body_sway_communication_coaching": coach_sway_comm,

        "body_sway_consistency_score": float(sway_mean_cons),
        "body_sway_consistency_interpretation": interp_sway_cons,
        "body_sway_consistency_coaching": coach_sway_cons,

        # Posture Openness
        "posture_openness_communication_score": float(open_mean_comm),
        "posture_openness_communication_interpretation": interp_open_comm,
        "posture_openness_communication_coaching": coach_open_comm,

        "posture_openness_consistency_score": float(open_mean_cons),
        "posture_openness_consistency_interpretation": interp_open_cons,
        "posture_openness_consistency_coaching": coach_open_cons
    }

    # 6. Generate Timeline (1Hz)
    # Project Raw Values (_val) and Communication Scores (_comm_score)
    cols_to_project = [c for c in window_df.columns if "_val" in c or "_comm_score" in c or "_cons_score" in c]
    projection_input = window_df[["start_sec", "end_sec"] + cols_to_project]

    timeline_1s = project_windows_to_seconds(projection_input)

    return scores, window_df, timeline_1s
