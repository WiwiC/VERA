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
    body_sway_1s      = raw_df.groupby("second")["body_sway"].mean().fillna(0)
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
    df_mag_5s["rel_score"] = np.exp(-z_mag**2) # Gaussian: Reward consistency (close to mean), penalize outliers

    mag_abs = df_mag_5s["value"].mean()
    abs_mag_score = np.exp(-((mag_abs - BASELINE_GESTURE_MAG_OPTIMAL)**2) / BASELINE_GESTURE_MAG_VAR)

    score_mag = 0.5 * abs_mag_score + 0.5 * df_mag_5s["rel_score"].mean()

    # --- GESTURE ACTIVITY ---
    z_act = (df_act_5s["value"] - df_act_5s["value"].mean()) / (df_act_5s["value"].std() + 1e-9)
    df_act_5s["rel_score"] = np.exp(-z_act**2) # Gaussian: Reward consistency

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

    # 5. Get Interpretations & Coaching
    interp_mag, coach_mag = get_interpretation("gesture_magnitude", mag_abs)
    interp_act, coach_act = get_interpretation("gesture_activity", act_abs)

    # Jitter is variance of activity. The buckets in config are 0.2, 0.4...
    # jit_abs is mean variance.
    interp_jit, coach_jit = get_interpretation("gesture_jitter", jit_abs)

    # Sway is variance of position. Buckets 0.05, 0.1...
    interp_sway, coach_sway = get_interpretation("body_sway", sway_abs)

    interp_open, coach_open = get_interpretation("posture_openness", open_abs)

    scores = {
        "body_global_score": float(global_score),
        "body_global_interpretation": get_global_interpretation(global_score),

        "gesture_magnitude_score": float(score_mag),
        "gesture_magnitude_interpretation": interp_mag,
        "gesture_magnitude_coaching": coach_mag,

        "gesture_activity_score": float(score_act),
        "gesture_activity_interpretation": interp_act,
        "gesture_activity_coaching": coach_act,

        "gesture_jitter_score": float(score_jit),
        "gesture_jitter_interpretation": interp_jit,
        "gesture_jitter_coaching": coach_jit,

        "body_sway_score": float(score_sway),
        "body_sway_interpretation": interp_sway,
        "body_sway_coaching": coach_sway,

        "posture_openness_score": float(score_open),
        "posture_openness_interpretation": interp_open,
        "posture_openness_coaching": coach_open
    }

    return scores, window_df
