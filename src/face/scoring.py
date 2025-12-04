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
    df_head_5s["rel_score"] = 1 / (1 + np.exp(z_head)) # Inverted: lower jitter is better (consistency)

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
    df_head_5s = df_head_5s.rename(columns={"value": "head_jitter_val", "rel_score": "head_score"})
    df_gaze_5s = df_gaze_5s.rename(columns={"value": "gaze_jitter_val", "rel_score": "gaze_score"})
    df_smile_5s = df_smile_5s.rename(columns={"value": "smile_val", "rel_score": "smile_score"})

    # Merge on start_sec/end_sec
    window_df = df_head_5s.merge(df_gaze_5s, on=["start_sec", "end_sec"]).merge(df_smile_5s, on=["start_sec", "end_sec"])

    # 5. Get Interpretations & Coaching
    # Note: Head Stability bucket is based on IOD/sec (speed), but head_abs is variance of speed?
    # Let's check compute_scores aggregation:
    # jitter_head_1s = raw_df.groupby("second")["head_speed"].var()
    # So head_abs is mean variance of speed.
    # But my config buckets are for "head_stability" in IOD/sec (speed).
    # Wait, the config says: "Optimal: 0.2 - 0.5 IOD/sec (Natural nodding)".
    # If I am measuring variance, the units are (IOD/sec)^2.
    # This is a mismatch.
    # If the config buckets are for SPEED, I should use mean speed, not variance.
    # But "Stability" implies low variance.
    # Let's look at the config again.
    # "Unstable head movement (Poor). Bobblehead effect." -> High speed or high variance?
    # Usually high speed means moving a lot. High variance means changing speed a lot.
    # Given the buckets (0.2, 0.5...), these look like Speed values.
    # Variance would be much smaller (e.g. 0.01).
    # I should probably use MEAN SPEED for the interpretation bucket check, even if I score on variance?
    # Or change aggregation to mean?
    # In body/scoring, I used mean for magnitude/activity, but variance for jitter/sway.
    # Here, head_stability seems to be treated like jitter (variance).
    # But the config values (0.35) are definitely speed-scale (0.35 * 6cm = 2cm/sec).
    # Variance of 0.35 would be huge.
    # So I suspect I should be aggregating MEAN speed for the interpretation check.

    # Let's calculate mean speed for interpretation purposes
    # I don't have it in the window df (which has variance).
    # I can't easily get it without re-aggregating.
    # However, for now, I will use head_abs (variance) and assume the user meant variance in config?
    # No, 0.35 variance is impossible for head stability.
    # The config comment says "Optimal: 0.2 - 0.5 IOD/sec". That is SPEED.
    # So I should change the aggregation to use MEAN for interpretation?
    # Or just accept that my scoring uses variance but my interpretation uses speed?
    # I will calculate mean speed from raw_df just for interpretation if possible.
    # But compute_scores takes raw_df.

    mean_head_speed = raw_df["head_speed"].mean()
    mean_gaze_dg = raw_df["gaze_dg"].mean() # Gaze consistency is also variance-based in scoring?
    # jitter_gaze_1s = var().
    # Config: "Optimal > 0.8 (Score)". Wait, Gaze interpretation is based on SCORE in the assessment.
    # But in the config file I wrote: "max: 0.4, 0.7...". These look like scores (0-1).
    # So for Gaze and Smile, I can use the SCORE.
    # For Head Stability, the buckets are 0.1, 0.2... which are raw values.
    # So for Head, I need the raw mean speed.

    interp_head, coach_head = get_interpretation("head_stability", mean_head_speed)

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

    return scores, window_df
