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
    BASELINE_BODY_SWAY_SCALE,
    BASELINE_POSTURE_OPTIMAL,
    BASELINE_POSTURE_RANGE,
    INTERPRETATION_RANGES
)

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

def get_interpretation(score, metric_type, raw_value=None, baseline=None):
    """
    Get the text interpretation for a given score and metric type.
    Handles both list-based (ranges) and dict-based (directional) interpretations.
    """
    ranges = INTERPRETATION_RANGES.get(metric_type, [])

    # Handle Directional Interpretation (Gaussian)
    if isinstance(ranges, dict):
        if score >= 0.6:
            return ranges["optimal"]
        elif score >= 0.4:
            return ranges["good"]
        else:
            # Low score: check direction
            if raw_value is not None and baseline is not None:
                if raw_value < baseline:
                    return ranges["low"]
                else:
                    return ranges["high"]
            return ranges["low"] # Default fallback

    # Handle Range-based Interpretation (Sigmoid)
    for low, high, text in ranges:
        if low <= score <= high:
            return text
    return "Score out of range or undefined."

def compute_scores(raw_df):
    """
    Compute aggregated scores from raw frame data.

    Args:
        raw_df (pd.DataFrame): DataFrame with raw body metrics.

    Returns:
        tuple: (scores_dict, window_df)
    """
    # 1. Aggregate per second
    gesture_mag_1s    = raw_df.groupby("second")["gesture_magnitude"].mean().fillna(0)
    gesture_act_1s    = raw_df.groupby("second")["gesture_activity"].mean().fillna(0)
    gesture_jitter_1s = raw_df.groupby("second")["gesture_activity"].var().fillna(0)
    body_sway_1s      = raw_df.groupby("second")["body_sway"].var().fillna(0) # Note: Notebook used var() for sway aggregation?
    # Let's check notebook logic for sway aggregation.
    # Notebook: body_sway_1s = df.groupby("second")["body_sway"].var().fillna(0)
    # Wait, sway is speed. Variance of speed? Or mean speed?
    # Notebook cell 117: body_sway_1s = df.groupby("second")["body_sway"].var().fillna(0)
    # Okay, sticking to notebook logic.

    posture_open_1s   = raw_df.groupby("second")["posture_openness"].mean().fillna(0)

    # 2. Sliding Windows (5s)
    df_mag_5s    = sliding_windows(gesture_mag_1s)
    df_act_5s    = sliding_windows(gesture_act_1s)
    df_jitter_5s = sliding_windows(gesture_jitter_1s)
    df_sway_5s   = sliding_windows(body_sway_1s)
    df_open_5s   = sliding_windows(posture_open_1s)

    if df_mag_5s.empty:
        return {"error": "Video too short"}, pd.DataFrame()

    # 3. Scoring Logic

    # --- GESTURE MAGNITUDE ---
    z_mag = (df_mag_5s["value"] - df_mag_5s["value"].mean()) / (df_mag_5s["value"].std() + 1e-9)
    df_mag_5s["rel_score"] = 1 / (1 + np.exp(-z_mag))

    mag_abs = df_mag_5s["value"].mean()
    abs_mag_score = np.exp(-((mag_abs - BASELINE_GESTURE_MAG_OPTIMAL)**2) / BASELINE_GESTURE_MAG_VAR)

    score_mag = 0.5 * abs_mag_score + 0.5 * df_mag_5s["rel_score"].mean()

    # --- GESTURE ACTIVITY ---
    z_act = (df_act_5s["value"] - df_act_5s["value"].mean()) / (df_act_5s["value"].std() + 1e-9)
    df_act_5s["rel_score"] = 1 / (1 + np.exp(-z_act))

    act_abs = df_act_5s["value"].mean()
    abs_act_score = np.exp(-((act_abs - BASELINE_GESTURE_ACTIVITY_OPTIMAL)**2) / BASELINE_GESTURE_ACTIVITY_VAR)

    score_act = 0.5 * abs_act_score + 0.5 * df_act_5s["rel_score"].mean()

    # --- GESTURE JITTER ---
    z_jit = (df_jitter_5s["value"] - df_jitter_5s["value"].mean()) / (df_jitter_5s["value"].std() + 1e-9)
    df_jitter_5s["rel_score"] = 1 / (1 + np.exp(z_jit)) # Inverted

    jit_abs = df_jitter_5s["value"].mean()
    abs_jit_score = 1 / (1 + np.exp((jit_abs - BASELINE_GESTURE_JITTER_OPTIMAL) / BASELINE_GESTURE_JITTER_RANGE))

    score_jit = 0.5 * abs_jit_score + 0.5 * df_jitter_5s["rel_score"].mean()

    # --- BODY SWAY ---
    z_sway = (df_sway_5s["value"] - df_sway_5s["value"].mean()) / (df_sway_5s["value"].std() + 1e-9)
    df_sway_5s["rel_score"] = 1 / (1 + np.exp(z_sway)) # Inverted

    sway_abs = df_sway_5s["value"].mean()
    abs_sway_score = np.exp(-sway_abs * BASELINE_BODY_SWAY_SCALE)

    score_sway = 0.5 * abs_sway_score + 0.5 * df_sway_5s["rel_score"].mean()

    # --- POSTURE OPENNESS ---
    z_open = (df_open_5s["value"] - df_open_5s["value"].mean()) / (df_open_5s["value"].std() + 1e-9)
    df_open_5s["rel_score"] = 1 / (1 + np.exp(-z_open))

    open_abs = df_open_5s["value"].mean()
    abs_open_score = 1 / (1 + np.exp(-(open_abs - BASELINE_POSTURE_OPTIMAL) / BASELINE_POSTURE_RANGE))

    score_open = 0.5 * abs_open_score + 0.5 * df_open_5s["rel_score"].mean()

    # --- GLOBAL SCORE ---
    global_score = (score_mag + score_act + score_jit + score_sway + score_open) / 5

    # 4. Prepare Outputs
    df_mag_5s = df_mag_5s.rename(columns={"value": "gesture_magnitude_val", "rel_score": "gesture_magnitude_score"})
    df_act_5s = df_act_5s.rename(columns={"value": "gesture_activity_val", "rel_score": "gesture_activity_score"})
    df_jitter_5s = df_jitter_5s.rename(columns={"value": "gesture_jitter_val", "rel_score": "gesture_jitter_score"})
    df_sway_5s = df_sway_5s.rename(columns={"value": "body_sway_val", "rel_score": "body_sway_score"})
    df_open_5s = df_open_5s.rename(columns={"value": "posture_openness_val", "rel_score": "posture_openness_score"})

    window_df = df_mag_5s.merge(df_act_5s, on=["start_sec", "end_sec"])\
                         .merge(df_jitter_5s, on=["start_sec", "end_sec"])\
                         .merge(df_sway_5s, on=["start_sec", "end_sec"])\
                         .merge(df_open_5s, on=["start_sec", "end_sec"])

    scores = {
        "body_global_score": float(global_score),
        "body_global_interpretation": get_interpretation(global_score, "body_global_score"),

        "gesture_magnitude_score": float(score_mag),
        "gesture_magnitude_interpretation": get_interpretation(score_mag, "gesture_magnitude", mag_abs, BASELINE_GESTURE_MAG_OPTIMAL),

        "gesture_activity_score": float(score_act),
        "gesture_activity_interpretation": get_interpretation(score_act, "gesture_activity", act_abs, BASELINE_GESTURE_ACTIVITY_OPTIMAL),

        "gesture_jitter_score": float(score_jit),
        "gesture_jitter_interpretation": get_interpretation(score_jit, "gesture_jitter"),

        "body_sway_score": float(score_sway),
        "body_sway_interpretation": get_interpretation(score_sway, "body_sway"),

        "posture_openness_score": float(score_open),
        "posture_openness_interpretation": get_interpretation(score_open, "posture_openness")
    }

    return scores, window_df
