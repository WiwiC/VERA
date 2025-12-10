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
    BASELINE_ARMS_CLOSE_THRESHOLD,
    BASELINE_WRIST_FORWARD_THRESHOLD,
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
        tuple: (scores_dict, window_df, timeline_1s)
    """
    # 1. Aggregate per second
    gesture_mag_1s    = raw_df.groupby("second")["gesture_magnitude"].mean().fillna(0)
    gesture_act_1s    = raw_df.groupby("second")["gesture_activity"].mean().fillna(0)
    gesture_stability_1s = raw_df.groupby("second")["gesture_activity"].var().fillna(0)
    body_sway_1s      = raw_df.groupby("second")["body_sway"].mean().fillna(0)
    posture_open_1s   = raw_df.groupby("second")["posture_openness"].mean().fillna(0)
    # wrist_depth_norm is aggregated in scoring section (internal use only)

    # Build 1-second raw timeline DataFrame (before windowing)
    # NOTE: wrist_depth_norm is NOT included - it's internal for posture scoring only
    raw_1s_df = pd.DataFrame({
        "second": gesture_mag_1s.index,
        "gesture_magnitude": gesture_mag_1s.values,
        "gesture_activity": gesture_act_1s.values,
        "gesture_stability": gesture_stability_1s.values,
        "body_sway": body_sway_1s.values,
        "posture_openness": posture_open_1s.values
    })

    # 2. Sliding Windows (5s)
    df_mag_5s    = sliding_windows(gesture_mag_1s)
    df_act_5s    = sliding_windows(gesture_act_1s)
    df_jitter_5s = sliding_windows(gesture_stability_1s)
    df_sway_5s   = sliding_windows(body_sway_1s)
    df_open_5s   = sliding_windows(posture_open_1s)

    if df_mag_5s.empty:
        return {"error": "Video too short"}, pd.DataFrame(), pd.DataFrame(), raw_1s_df

    # 3. Scoring Logic

    # --- GESTURE MAGNITUDE ---
    mag_val = df_mag_5s["value"]
    mag_comm_score = np.exp(-((mag_val - BASELINE_GESTURE_MAG_OPTIMAL)**2) / BASELINE_GESTURE_MAG_VAR)
    df_mag_5s["comm_score"] = mag_comm_score

    # --- GESTURE ACTIVITY ---
    act_val = df_act_5s["value"]
    act_comm_score = np.exp(-((act_val - BASELINE_GESTURE_ACTIVITY_OPTIMAL)**2) / BASELINE_GESTURE_ACTIVITY_VAR)
    df_act_5s["comm_score"] = act_comm_score

    # --- GESTURE JITTER ---
    jit_val = df_jitter_5s["value"]
    jit_comm_score = 1 / (1 + np.exp((jit_val - BASELINE_GESTURE_JITTER_OPTIMAL) / BASELINE_GESTURE_JITTER_RANGE))
    df_jitter_5s["comm_score"] = jit_comm_score

    # --- BODY SWAY ---
    sway_val = df_sway_5s["value"]
    sway_comm_score = np.exp(-((sway_val - BASELINE_BODY_SWAY_OPTIMAL)**2) / BASELINE_BODY_SWAY_VAR)
    df_sway_5s["comm_score"] = sway_comm_score

    # --- POSTURE OPENNESS (arms-based, 2-component) ---
    # No longer uses shoulder angle — proven to not discriminate well
    # Classification:
    #   - "closed" = arms_close AND wrists_forward (defensive barrier)
    #   - "neutral" = arms_close only (hands at rest)
    #   - "open" = arms expanded (gesturing)

    # Component A: Arm closeness (from gesture magnitude)
    arms_close = mag_val < BASELINE_ARMS_CLOSE_THRESHOLD  # < 1.0 SW

    # Component B: Wrist depth (raw normalized depth, not binary)
    wrist_depth_1s = raw_df.groupby("second")["wrist_depth_norm"].mean().fillna(0)
    df_wrist_depth_5s = sliding_windows(wrist_depth_1s)
    wrist_depth_val = df_wrist_depth_5s["value"]
    wrists_forward = wrist_depth_val < BASELINE_WRIST_FORWARD_THRESHOLD  # < -1.5 SW

    # Posture classification per window
    defensive_mask = arms_close & wrists_forward  # "closed"
    neutral_mask = arms_close & (~wrists_forward)  # "neutral"
    open_mask = ~arms_close  # "open"

    # Calculate ratios (for global interpretation)
    defensive_ratio = defensive_mask.sum() / len(defensive_mask) if len(defensive_mask) > 0 else 0
    neutral_ratio = neutral_mask.sum() / len(neutral_mask) if len(neutral_mask) > 0 else 0
    open_ratio = open_mask.sum() / len(open_mask) if len(open_mask) > 0 else 0

    # Arms-based posture score:
    # - closed = 0.0 to 0.3
    # - neutral = 0.5
    # - open = 0.7 to 1.0
    posture_comm_score = pd.Series(index=defensive_mask.index, dtype=float)
    posture_comm_score[open_mask] = 1.0
    posture_comm_score[neutral_mask] = 0.5
    posture_comm_score[defensive_mask] = 0.2
    df_open_5s["comm_score"] = posture_comm_score
    df_open_5s["value"] = mag_val  # Override: show gesture_mag as the "posture" value for timeline

    # --- GLOBAL SCORE ---
    global_comm_score = (
        df_mag_5s["comm_score"].mean() +
        df_act_5s["comm_score"].mean() +
        df_jitter_5s["comm_score"].mean() +
        df_sway_5s["comm_score"].mean() +
        df_open_5s["comm_score"].mean()
    ) / 5

    # --- WINDOW-TO-WINDOW DELTAS (for timeline stability analysis) ---
    mag_deltas, mag_labels = compute_change_labels(mag_val.values, "gesture_magnitude")
    act_deltas, act_labels = compute_change_labels(act_val.values, "gesture_activity")
    jit_deltas, jit_labels = compute_change_labels(jit_val.values, "gesture_stability")
    sway_deltas, sway_labels = compute_change_labels(sway_val.values, "body_sway")
    # Posture uses gesture_magnitude now (arms-based)
    open_deltas, open_labels = compute_change_labels(mag_val.values, "posture_openness")

    # Add deltas/labels to window dataframes
    for df, deltas, labels, prefix in [
        (df_mag_5s, mag_deltas, mag_labels, ""),
        (df_act_5s, act_deltas, act_labels, ""),
        (df_jitter_5s, jit_deltas, jit_labels, ""),
        (df_sway_5s, sway_deltas, sway_labels, ""),
        (df_open_5s, open_deltas, open_labels, ""),
    ]:
        df["delta"] = np.nan
        df["change_label"] = ""
        if len(deltas) > 0:
            df.iloc[:-1, df.columns.get_loc("delta")] = deltas
            df.iloc[:-1, df.columns.get_loc("change_label")] = labels

    # 4. Prepare Outputs
    # Rename columns for clarity in window_df
    df_mag_5s = df_mag_5s.rename(columns={
        "value": "gesture_magnitude_val",
        "comm_score": "gesture_magnitude_comm_score",
        "delta": "gesture_magnitude_delta",
        "change_label": "gesture_magnitude_change_label"
    })
    df_act_5s = df_act_5s.rename(columns={
        "value": "gesture_activity_val",
        "comm_score": "gesture_activity_comm_score",
        "delta": "gesture_activity_delta",
        "change_label": "gesture_activity_change_label"
    })
    df_jitter_5s = df_jitter_5s.rename(columns={
        "value": "gesture_stability_val",
        "comm_score": "gesture_stability_comm_score",
        "delta": "gesture_stability_delta",
        "change_label": "gesture_stability_change_label"
    })
    df_sway_5s = df_sway_5s.rename(columns={
        "value": "body_sway_val",
        "comm_score": "body_sway_comm_score",
        "delta": "body_sway_delta",
        "change_label": "body_sway_change_label"
    })
    df_open_5s = df_open_5s.rename(columns={
        "value": "posture_openness_val",
        "comm_score": "posture_openness_comm_score",
        "delta": "posture_openness_delta",
        "change_label": "posture_openness_change_label"
    })

    window_df = df_mag_5s.merge(df_act_5s, on=["start_sec", "end_sec"])\
                         .merge(df_jitter_5s, on=["start_sec", "end_sec"])\
                         .merge(df_sway_5s, on=["start_sec", "end_sec"])\
                         .merge(df_open_5s, on=["start_sec", "end_sec"])

    # Add Global Score to window_df (constant column)
    window_df["global_comm_score"] = global_comm_score

    # 5. Get Interpretations & Coaching

    # Communication Scores (Absolute)
    mag_mean_comm = df_mag_5s["gesture_magnitude_comm_score"].mean()
    act_mean_comm = df_act_5s["gesture_activity_comm_score"].mean()
    jit_mean_comm = df_jitter_5s["gesture_stability_comm_score"].mean()
    sway_mean_comm = df_sway_5s["body_sway_comm_score"].mean()
    open_mean_comm = df_open_5s["posture_openness_comm_score"].mean()

    # Mean raw values for interpretation
    mag_mean_val = df_mag_5s["gesture_magnitude_val"].mean()
    act_mean_val = df_act_5s["gesture_activity_val"].mean()
    jit_mean_val = df_jitter_5s["gesture_stability_val"].mean()
    sway_mean_val = df_sway_5s["body_sway_val"].mean()
    open_mean_val = df_open_5s["posture_openness_val"].mean()

    interp_mag_comm, coach_mag_comm = get_interpretation("gesture_magnitude", mag_mean_val)
    interp_act_comm, coach_act_comm = get_interpretation("gesture_activity", act_mean_val)
    interp_jit_comm, coach_jit_comm = get_interpretation("gesture_stability", jit_mean_val)
    interp_sway_comm, coach_sway_comm = get_interpretation("body_sway", sway_mean_val)

    # Arms-based posture interpretation (replaces angle-based buckets)
    if defensive_ratio > 0.5:
        interp_open_comm = "Closed, defensive posture (Poor). Arms close to body with hands in front."
        coach_open_comm = "Open up your arms. You look guarded and defensive."
    elif neutral_ratio > 0.5:
        interp_open_comm = "Neutral posture (Ok). Arms at rest but not gesturing."
        coach_open_comm = "Try using more hand gestures to engage your audience."
    else:
        interp_open_comm = "Open, expressive posture (Excellent). Good use of gestures."
        coach_open_comm = "Great body language! You look confident and approachable."

    scores = {
        "global_comm_score": float(global_comm_score),
        "body_global_interpretation": get_global_interpretation(global_comm_score),

        # Gesture Magnitude
        "gesture_magnitude_communication_score": float(mag_mean_comm),
        "gesture_magnitude_communication_interpretation": interp_mag_comm,
        "gesture_magnitude_communication_coaching": coach_mag_comm,

        # Gesture Activity
        "gesture_activity_communication_score": float(act_mean_comm),
        "gesture_activity_communication_interpretation": interp_act_comm,
        "gesture_activity_communication_coaching": coach_act_comm,

        # Gesture Jitter
        "gesture_stability_communication_score": float(jit_mean_comm),
        "gesture_stability_communication_interpretation": interp_jit_comm,
        "gesture_stability_communication_coaching": coach_jit_comm,

        # Body Sway
        "body_sway_communication_score": float(sway_mean_comm),
        "body_sway_communication_interpretation": interp_sway_comm,
        "body_sway_communication_coaching": coach_sway_comm,

        # Posture Openness
        "posture_openness_communication_score": float(open_mean_comm),
        "posture_openness_communication_interpretation": interp_open_comm,
        "posture_openness_communication_coaching": coach_open_comm,
    }

    # 6. Generate Timeline (1Hz)
    # Project Raw Values (_val), Communication Scores (_comm_score), and deltas (numeric only)
    # Note: change_label columns are strings and cannot be projected via mean
    cols_to_project = [c for c in window_df.columns
                       if "_val" in c or "_comm_score" in c or "_delta" in c]
    projection_input = window_df[["start_sec", "end_sec"] + cols_to_project]

    timeline_1s = project_windows_to_seconds(projection_input)

    return scores, window_df, timeline_1s, raw_1s_df
