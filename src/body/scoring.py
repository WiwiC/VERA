"""
Scoring logic for the VERA Body Module.
Converts raw metrics into 0-1 scores using Tiered Parabolic Scoring.
Aggregates metrics, applies sliding windows, computes scores, and generates text interpretations.

REFACTORED (2025-01):
- Uses compute_tiered_score to ensure scores align with labels.
- Restored windowing and timeline generation logic.
"""

import numpy as np
import pandas as pd
import sys
import os

# Add project root to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.body.config import (
    INTERPRETATION_RANGES,
    CHANGE_THRESHOLDS
)
from src.utils.temporal import project_windows_to_seconds
from src.utils.scoring_utils import compute_tiered_score

def compute_change_labels(values, metric_id):
    """
    Compute window-to-window deltas and labels for temporal stability analysis.
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
    Get text interpretation, coaching, and label based on raw value and buckets.
    """
    buckets = INTERPRETATION_RANGES.get(metric_type, [])
    for bucket in buckets:
        if raw_value <= bucket["max"]:
            return bucket["text"], bucket["coaching"], bucket["label"]
    return "Value out of range", "Check your settings.", "unknown"

def get_global_interpretation(score):
    ranges = INTERPRETATION_RANGES.get("body_global_score", [])
    for low, high, text in ranges:
        if low <= score <= high:
            return text
    return "Score out of range"

def compute_scores(raw_df):
    """
    Compute aggregated scores from raw frame data.

    Args:
        raw_df (pd.DataFrame): DataFrame with 'gesture_magnitude', 'gesture_activity', 'body_sway', 'posture_openness', 'second'.

    Returns:
        tuple: (scores_dict, window_df, timeline_1s, raw_1s_df)
    """
    # 1. Aggregate per second
    mag_1s = raw_df.groupby("second")["gesture_magnitude"].mean().fillna(0)
    act_1s = raw_df.groupby("second")["gesture_activity"].mean().fillna(0)
    sway_1s = raw_df.groupby("second")["body_sway"].mean().fillna(0)
    posture_1s = raw_df.groupby("second")["posture_openness"].mean().fillna(0.6)

    # Gesture Stability: Variance of activity within the second?
    # Or variance of activity across frames?
    # raw_df has frame-level data.
    # So we calculate variance of 'gesture_activity' for each second group.
    stab_1s = raw_df.groupby("second")["gesture_activity"].var().fillna(0)

    # Build 1-second raw timeline DataFrame
    raw_1s_df = pd.DataFrame({
        "second": mag_1s.index,
        "gesture_magnitude": mag_1s.values,
        "gesture_activity": act_1s.values,
        "gesture_stability": stab_1s.values,
        "body_sway": sway_1s.values,
        "posture_openness": posture_1s.values
    })

    # 2. Sliding Windows (5s)
    df_mag_5s = sliding_windows(mag_1s)
    df_act_5s = sliding_windows(act_1s)
    df_stab_5s = sliding_windows(stab_1s)
    df_sway_5s = sliding_windows(sway_1s)
    df_posture_5s = sliding_windows(posture_1s)

    # Handle short videos
    if df_mag_5s.empty:
        return {
            "error": "Video too short for analysis (needs > 5 seconds)"
        }, pd.DataFrame(), pd.DataFrame(), raw_1s_df

    # 3. Scoring Logic (Tiered Parabolic)

    # Gesture Magnitude
    df_mag_5s["comm_score"] = df_mag_5s["value"].apply(
        lambda x: compute_tiered_score(x, INTERPRETATION_RANGES["gesture_magnitude"])
    )

    # Gesture Activity
    df_act_5s["comm_score"] = df_act_5s["value"].apply(
        lambda x: compute_tiered_score(x, INTERPRETATION_RANGES["gesture_activity"])
    )

    # Gesture Stability
    df_stab_5s["comm_score"] = df_stab_5s["value"].apply(
        lambda x: compute_tiered_score(x, INTERPRETATION_RANGES["gesture_stability"])
    )

    # Body Sway
    df_sway_5s["comm_score"] = df_sway_5s["value"].apply(
        lambda x: compute_tiered_score(x, INTERPRETATION_RANGES["body_sway"])
    )

    # Posture Openness
    # Posture score is already 0.2/0.6/1.0.
    # But we still want to map it to the tiers in case of averaging (e.g. 0.8).
    # The config has buckets for 0.3, 0.7, 999.
    df_posture_5s["comm_score"] = df_posture_5s["value"].apply(
        lambda x: compute_tiered_score(x, INTERPRETATION_RANGES["posture_openness"])
    )

    # 4. Global Score
    global_score = (
        df_mag_5s["comm_score"].mean() +
        df_act_5s["comm_score"].mean() +
        df_stab_5s["comm_score"].mean() +
        df_sway_5s["comm_score"].mean() +
        df_posture_5s["comm_score"].mean()
    ) / 5.0

    # 5. Window Deltas
    for df, metric in [
        (df_mag_5s, "gesture_magnitude"),
        (df_act_5s, "gesture_activity"),
        (df_stab_5s, "gesture_stability"),
        (df_sway_5s, "body_sway"),
        (df_posture_5s, "posture_openness")
    ]:
        deltas, labels = compute_change_labels(df["value"].values, metric)
        df["delta"] = np.nan
        df["change_label"] = ""
        if len(deltas) > 0:
            df.iloc[:-1, df.columns.get_loc("delta")] = deltas
            df.iloc[:-1, df.columns.get_loc("change_label")] = labels

    # 6. Prepare Outputs

    # Rename columns
    df_mag_5s = df_mag_5s.rename(columns={"value": "gesture_magnitude_val", "comm_score": "gesture_magnitude_score", "delta": "gesture_magnitude_delta", "change_label": "gesture_magnitude_change_label"})
    df_act_5s = df_act_5s.rename(columns={"value": "gesture_activity_val", "comm_score": "gesture_activity_score", "delta": "gesture_activity_delta", "change_label": "gesture_activity_change_label"})
    df_stab_5s = df_stab_5s.rename(columns={"value": "gesture_stability_val", "comm_score": "gesture_stability_score", "delta": "gesture_stability_delta", "change_label": "gesture_stability_change_label"})
    df_sway_5s = df_sway_5s.rename(columns={"value": "body_sway_val", "comm_score": "body_sway_score", "delta": "body_sway_delta", "change_label": "body_sway_change_label"})
    df_posture_5s = df_posture_5s.rename(columns={"value": "posture_openness_val", "comm_score": "posture_openness_score", "delta": "posture_openness_delta", "change_label": "posture_openness_change_label"})

    # Merge
    window_df = df_mag_5s.merge(df_act_5s, on=["start_sec", "end_sec"])\
                         .merge(df_stab_5s, on=["start_sec", "end_sec"])\
                         .merge(df_sway_5s, on=["start_sec", "end_sec"])\
                         .merge(df_posture_5s, on=["start_sec", "end_sec"])

    window_df["body_global_score"] = global_score

    # 7. Global Interpretations
    mag_mean = df_mag_5s["gesture_magnitude_val"].mean()
    act_mean = df_act_5s["gesture_activity_val"].mean()
    stab_mean = df_stab_5s["gesture_stability_val"].mean()
    sway_mean = df_sway_5s["body_sway_val"].mean()
    posture_mean = df_posture_5s["posture_openness_val"].mean()

    # Scores (mean of window scores)
    mag_score = df_mag_5s["gesture_magnitude_score"].mean()
    act_score = df_act_5s["gesture_activity_score"].mean()
    stab_score = df_stab_5s["gesture_stability_score"].mean()
    sway_score = df_sway_5s["body_sway_score"].mean()
    posture_score = df_posture_5s["posture_openness_score"].mean()

    interp_mag, coach_mag, label_mag = get_interpretation("gesture_magnitude", mag_mean)
    interp_act, coach_act, label_act = get_interpretation("gesture_activity", act_mean)
    interp_stab, coach_stab, label_stab = get_interpretation("gesture_stability", stab_mean)
    interp_sway, coach_sway, label_sway = get_interpretation("body_sway", sway_mean)
    interp_posture, coach_posture, label_posture = get_interpretation("posture_openness", posture_mean)

    scores = {
        "global_comm_score": float(global_score),
        "body_global_interpretation": get_global_interpretation(global_score),

        "gesture_magnitude_score": float(mag_score),
        "gesture_magnitude_val": float(mag_mean),
        "gesture_magnitude_interpretation": interp_mag,
        "gesture_magnitude_coaching": coach_mag,
        "gesture_magnitude_label": label_mag,

        "gesture_activity_score": float(act_score),
        "gesture_activity_val": float(act_mean),
        "gesture_activity_interpretation": interp_act,
        "gesture_activity_coaching": coach_act,
        "gesture_activity_label": label_act,

        "gesture_stability_score": float(stab_score),
        "gesture_stability_val": float(stab_mean),
        "gesture_stability_interpretation": interp_stab,
        "gesture_stability_coaching": coach_stab,
        "gesture_stability_label": label_stab,

        "body_sway_score": float(sway_score),
        "body_sway_val": float(sway_mean),
        "body_sway_interpretation": interp_sway,
        "body_sway_coaching": coach_sway,
        "body_sway_label": label_sway,

        "posture_openness_score": float(posture_score),
        "posture_openness_val": float(posture_mean),
        "posture_openness_interpretation": interp_posture,
        "posture_openness_coaching": coach_posture,
        "posture_openness_label": label_posture
    }

    # Project Timeline
    cols_to_project = [c for c in window_df.columns if "_val" in c or "_score" in c or "_delta" in c]
    projection_input = window_df[["start_sec", "end_sec"] + cols_to_project]
    timeline_1s = project_windows_to_seconds(projection_input)

    return scores, window_df, timeline_1s, raw_1s_df
