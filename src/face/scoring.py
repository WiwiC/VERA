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
    INTERPRETATION_RANGES,
    CHANGE_THRESHOLDS
)
from src.utils.temporal import project_windows_to_seconds


def compute_change_labels(values, metric_id):
    """
    Compute window-to-window deltas and labels for temporal stability analysis.
    
    Args:
        values: Series or array of raw metric values per window
        metric_id: Metric name to look up thresholds
        
    Returns:
        tuple: (deltas array, labels list)
    """
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        return np.array([]), []
    
    deltas = np.abs(np.diff(values))
    thresholds = CHANGE_THRESHOLDS.get(metric_id, {"stable": 0.1, "shifting": 0.3})
    
    labels = []
    for d in deltas:
        if d <= thresholds["stable"]:
            labels.append("stable")
        elif d <= thresholds["shifting"]:
            labels.append("shifting")
        else:
            labels.append("erratic")
    
    return deltas, labels

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

    # Build 1-second raw timeline DataFrame (before windowing)
    raw_1s_df = pd.DataFrame({
        "second": head_speed_1s.index,
        "head_speed": head_speed_1s.values,
        "gaze_jitter": jitter_gaze_1s.values,
        "smile": smile_1s.values
    })

    # 2. Sliding Windows (5s)
    df_head_5s  = sliding_windows(head_speed_1s)
    df_gaze_5s  = sliding_windows(jitter_gaze_1s)
    df_smile_5s = sliding_windows(smile_1s)

    # If video is too short for windows, handle gracefully
    if df_head_5s.empty:
        return {
            "error": "Video too short for analysis (needs > 5 seconds)"
        }, pd.DataFrame(), pd.DataFrame(), raw_1s_df

    # 3. Scoring Logic

    # --- HEAD STABILITY ---
    head_val = df_head_5s["value"]
    # Absolute (Communication Score)
    head_comm_score = np.exp(-((head_val - BASELINE_HEAD_STABILITY_OPTIMAL)**2) / BASELINE_HEAD_STABILITY_VAR)
    df_head_5s["comm_score"] = head_comm_score

    # --- GAZE CONSISTENCY ---
    gaze_val = df_gaze_5s["value"]
    # Absolute (Communication Score) - Inverted logistic (lower jitter = higher score)
    gaze_comm_score = 1 / (1 + np.exp((gaze_val - BASELINE_GAZE_MIDPOINT) / BASELINE_GAZE_SCALE))
    df_gaze_5s["comm_score"] = gaze_comm_score

    # --- SMILE ACTIVATION ---
    smile_val = df_smile_5s["value"]
    # Absolute (Communication Score) - GAUSSIAN for optimal band
    smile_comm_score = np.exp(-((smile_val - BASELINE_SMILE_OPTIMAL)**2) / BASELINE_SMILE_VAR)
    df_smile_5s["comm_score"] = smile_comm_score

    # --- GLOBAL SCORE ---
    global_comm_score = (
        df_head_5s["comm_score"].mean() +
        df_gaze_5s["comm_score"].mean() +
        df_smile_5s["comm_score"].mean()
    ) / 3

    # --- WINDOW-TO-WINDOW DELTAS (for timeline stability analysis) ---
    head_deltas, head_labels = compute_change_labels(head_val.values, "head_stability")
    gaze_deltas, gaze_labels = compute_change_labels(gaze_val.values, "gaze_stability")
    smile_deltas, smile_labels = compute_change_labels(smile_val.values, "smile_activation")
    
    # Add deltas/labels to window_df (aligned to transition between windows)
    # Delta at index i represents change from window i to window i+1
    df_head_5s["delta"] = np.nan
    df_head_5s["change_label"] = ""
    if len(head_deltas) > 0:
        df_head_5s.iloc[:-1, df_head_5s.columns.get_loc("delta")] = head_deltas
        df_head_5s.iloc[:-1, df_head_5s.columns.get_loc("change_label")] = head_labels
    
    df_gaze_5s["delta"] = np.nan
    df_gaze_5s["change_label"] = ""
    if len(gaze_deltas) > 0:
        df_gaze_5s.iloc[:-1, df_gaze_5s.columns.get_loc("delta")] = gaze_deltas
        df_gaze_5s.iloc[:-1, df_gaze_5s.columns.get_loc("change_label")] = gaze_labels
    
    df_smile_5s["delta"] = np.nan
    df_smile_5s["change_label"] = ""
    if len(smile_deltas) > 0:
        df_smile_5s.iloc[:-1, df_smile_5s.columns.get_loc("delta")] = smile_deltas
        df_smile_5s.iloc[:-1, df_smile_5s.columns.get_loc("change_label")] = smile_labels

    # 4. Prepare Outputs

    # Merge window dataframes for export
    # Rename columns to be clear
    df_head_5s = df_head_5s.rename(columns={
        "value": "head_speed_val",
        "comm_score": "head_stability_comm_score",
        "delta": "head_stability_delta",
        "change_label": "head_stability_change_label"
    })
    df_gaze_5s = df_gaze_5s.rename(columns={
        "value": "gaze_jitter_val",
        "comm_score": "gaze_stability_comm_score",
        "delta": "gaze_stability_delta",
        "change_label": "gaze_stability_change_label"
    })
    df_smile_5s = df_smile_5s.rename(columns={
        "value": "smile_val",
        "comm_score": "smile_activation_comm_score",
        "delta": "smile_activation_delta",
        "change_label": "smile_activation_change_label"
    })

    # Merge on start_sec/end_sec
    window_df = df_head_5s.merge(df_gaze_5s, on=["start_sec", "end_sec"]).merge(df_smile_5s, on=["start_sec", "end_sec"])

    # Add Global Score to window_df (constant column)
    window_df["global_comm_score"] = global_comm_score

    # 5. Get Interpretations & Coaching

    # Communication Scores (Absolute)
    head_mean_comm = df_head_5s["head_stability_comm_score"].mean()
    gaze_mean_comm = df_gaze_5s["gaze_stability_comm_score"].mean()
    smile_mean_comm = df_smile_5s["smile_activation_comm_score"].mean()

    # Mean raw values for interpretation
    head_mean_val = df_head_5s["head_speed_val"].mean()
    gaze_mean_val = df_gaze_5s["gaze_jitter_val"].mean()
    smile_mean_val = df_smile_5s["smile_val"].mean()

    interp_head_comm, coach_head_comm = get_interpretation("head_stability", head_mean_val)
    interp_gaze_comm, coach_gaze_comm = get_interpretation("gaze_stability", gaze_mean_val)
    interp_smile_comm, coach_smile_comm = get_interpretation("smile_activation", smile_mean_val)

    scores = {
        "global_comm_score": float(global_comm_score),
        "face_global_interpretation": get_global_interpretation(global_comm_score),

        # Head Stability
        "head_stability_communication_score": float(head_mean_comm),
        "head_stability_communication_interpretation": interp_head_comm,
        "head_stability_communication_coaching": coach_head_comm,

        # Gaze Consistency
        "gaze_stability_communication_score": float(gaze_mean_comm),
        "gaze_stability_communication_interpretation": interp_gaze_comm,
        "gaze_stability_communication_coaching": coach_gaze_comm,

        # Smile Activation
        "smile_activation_communication_score": float(smile_mean_comm),
        "smile_activation_communication_interpretation": interp_smile_comm,
        "smile_activation_communication_coaching": coach_smile_comm,
    }

    # Project Raw Values (_val), Communication Scores (_comm_score), and deltas (numeric only)
    # Note: change_label columns are strings and cannot be projected via mean
    cols_to_project = [c for c in window_df.columns 
                       if "_val" in c or "_comm_score" in c or "_delta" in c]
    projection_input = window_df[["start_sec", "end_sec"] + cols_to_project]

    timeline_1s = project_windows_to_seconds(projection_input)

    return scores, window_df, timeline_1s, raw_1s_df
