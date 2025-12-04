"""
Scoring logic for the VERA Audio Module.
Converts raw metrics into 0-1 scores using Gaussian functions.
"""

import numpy as np
from src.audio.config import (
    BASELINE_WPM_RANGE, BASELINE_WPM_VAR,
    BASELINE_PAUSE_RANGE, BASELINE_PAUSE_VAR,
    BASELINE_PITCH_STD_RANGE, BASELINE_PITCH_STD_VAR,
    BASELINE_VOLUME_CV_RANGE, BASELINE_VOLUME_CV_VAR,
    BASELINE_CREST_RANGE, BASELINE_CREST_VAR,
    INTERPRETATION_RANGES
)

def plateau_score(value, range_min, range_max, variance):
    """
    Calculate Plateau (Trapezoidal) score.
    - If value is within [range_min, range_max], score is 1.0.
    - If value < range_min, Gaussian decay from range_min.
    - If value > range_max, Gaussian decay from range_max.
    """
    if range_min <= value <= range_max:
        return 1.0
    elif value < range_min:
        return np.exp(-((value - range_min)**2) / variance)
    else: # value > range_max
        return np.exp(-((value - range_max)**2) / variance)

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
    ranges = INTERPRETATION_RANGES.get("audio_global_score", [])
    for low, high, text in ranges:
        if low <= score <= high:
            return text
    return "Score out of range"

def compute_scores(raw_metrics):
    """
    Compute 0-1 scores for all performance metrics.
    """
    # 1. Extract Raw Values
    wpm = raw_metrics.get("wpm", 0)
    pause = raw_metrics.get("pause_ratio", 0)
    pitch_st = raw_metrics.get("pitch_std_st", 0)
    vol_cv = raw_metrics.get("volume_cv", 0)
    crest = raw_metrics.get("crest_factor_db", 0)

    # 2. Calculate Plateau Scores
    score_wpm = plateau_score(wpm, BASELINE_WPM_RANGE[0], BASELINE_WPM_RANGE[1], BASELINE_WPM_VAR)
    score_pause = plateau_score(pause, BASELINE_PAUSE_RANGE[0], BASELINE_PAUSE_RANGE[1], BASELINE_PAUSE_VAR)
    score_pitch = plateau_score(pitch_st, BASELINE_PITCH_STD_RANGE[0], BASELINE_PITCH_STD_RANGE[1], BASELINE_PITCH_STD_VAR)
    score_vol = plateau_score(vol_cv, BASELINE_VOLUME_CV_RANGE[0], BASELINE_VOLUME_CV_RANGE[1], BASELINE_VOLUME_CV_VAR)
    score_crest = plateau_score(crest, BASELINE_CREST_RANGE[0], BASELINE_CREST_RANGE[1], BASELINE_CREST_VAR)

    # 3. Calculate Global Score (Average)
    global_score = (score_wpm + score_pause + score_pitch + score_vol + score_crest) / 5.0

    # 4. Get Interpretations & Coaching
    interp_wpm, coach_wpm = get_interpretation("speech_rate", wpm)
    interp_pause, coach_pause = get_interpretation("pause_ratio", pause)
    interp_pitch, coach_pitch = get_interpretation("pitch_dynamic", pitch_st)
    interp_vol, coach_vol = get_interpretation("volume_dynamic", vol_cv)
    interp_crest, coach_crest = get_interpretation("vocal_punch", crest)

    # 5. Generate Result Dictionary
    scores = {
        "audio_global_score": float(global_score),
        "audio_global_interpretation": get_global_interpretation(global_score),

        "speech_rate_score": float(score_wpm),
        "speech_rate_interpretation": interp_wpm,
        "speech_rate_coaching": coach_wpm,

        "pause_ratio_score": float(score_pause),
        "pause_ratio_interpretation": interp_pause,
        "pause_ratio_coaching": coach_pause,

        "pitch_dynamic_score": float(score_pitch),
        "pitch_dynamic_interpretation": interp_pitch,
        "pitch_dynamic_coaching": coach_pitch,

        "volume_dynamic_score": float(score_vol),
        "volume_dynamic_interpretation": interp_vol,
        "volume_dynamic_coaching": coach_vol,

        "vocal_punch_score": float(score_crest),
        "vocal_punch_interpretation": interp_crest,
        "vocal_punch_coaching": coach_crest
    }

    return scores
