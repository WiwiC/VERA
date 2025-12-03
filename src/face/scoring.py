"""
Scoring and interpretation logic for the VERA Face Module.
Aggregates metrics, applies sliding windows, computes scores, and generates text interpretations.
"""

import numpy as np
import pandas as pd
from src.face.config import (
    BASELINE_JITTER_OPTIMAL,
    BASELINE_JITTER_RANGE,
    BASELINE_GAZE_OPTIMAL,
    BASELINE_GAZE_VAR,
    BASELINE_SMILE_OPTIMAL,
    BASELINE_SMILE_RANGE,
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
        # We need to ensure we have data for the full window
        # But for simplicity, we'll take whatever falls in [start, end]
        # The notebook logic was: if len(win) == window + 1: rows.append(...)
        # Let's stick to the notebook logic for fidelity
        win = series.loc[start:end]

        # Assuming 1 data point per second, window+1 means we cover start to end inclusive?
        # Actually, if window=5, we want [t, t+5]. That's 6 points if inclusive.
        # Let's check notebook logic: "if len(win) == window + 1"
        if len(win) == window + 1:
            rows.append({
                "start_sec": start,
                "end_sec": end,
                "value": win.mean()
            })

    return pd.DataFrame(rows)

def get_interpretation(score, metric_type):
    """
    Get the text interpretation for a given score and metric type.
    """
    ranges = INTERPRETATION_RANGES.get(metric_type, [])
    for low, high, text in ranges:
        if low <= score <= high:
            return text
    return "Score out of range or undefined."

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
    jitter_head_1s = raw_df.groupby("second")["head_speed"].var().fillna(0)
    jitter_gaze_1s = raw_df.groupby("second")["gaze_dg"].var().fillna(0)
    smile_1s       = raw_df.groupby("second")["smile"].mean().fillna(0)

    # 2. Sliding Windows (5s)
    df_head_5s  = sliding_windows(jitter_head_1s)
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
    df_head_5s["rel_score"] = 1 / (1 + np.exp(z_head)) # Inverted: lower jitter is better

    # Absolute
    head_abs = df_head_5s["value"].mean()
    abs_head_score = 1 / (1 + np.exp((head_abs - BASELINE_JITTER_OPTIMAL) / BASELINE_JITTER_RANGE))

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
    df_head_5s = df_head_5s.rename(columns={"value": "head_jitter_val", "rel_score": "head_score"})
    df_gaze_5s = df_gaze_5s.rename(columns={"value": "gaze_jitter_val", "rel_score": "gaze_score"})
    df_smile_5s = df_smile_5s.rename(columns={"value": "smile_val", "rel_score": "smile_score"})

    # Merge on start_sec/end_sec
    window_df = df_head_5s.merge(df_gaze_5s, on=["start_sec", "end_sec"]).merge(df_smile_5s, on=["start_sec", "end_sec"])

    scores = {
        "face_global_score": float(global_score),
        "face_global_interpretation": get_interpretation(global_score, "face_global_score"),

        "head_stability_score": float(score_head),
        "head_stability_interpretation": get_interpretation(score_head, "head_stability"),

        "gaze_consistency_score": float(score_gaze),
        "gaze_consistency_interpretation": get_interpretation(score_gaze, "gaze_consistency"),

        "smile_activation_score": float(score_smile),
        "smile_activation_interpretation": get_interpretation(score_smile, "smile_activation")
    }

    return scores, window_df
