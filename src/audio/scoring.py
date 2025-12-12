"""
Scoring logic for the VERA Audio Module.
Converts raw metrics into 0-1 scores using Tiered Parabolic Scoring.

REFACTORED (2025-01):
- Uses compute_tiered_score to ensure scores align with labels.
- Replaces mixed Gaussian/Plateau logic with unified tiered logic.
"""

import numpy as np
import sys
import os

# Add project root to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.audio.config import (
    BASELINE_WPM_RANGE,
    BASELINE_PAUSE_OPTIMAL,
    BASELINE_PITCH_STD_RANGE,
    BASELINE_VOLUME_CV_OPTIMAL,
    BASELINE_CREST_RANGE,
    INTERPRETATION_RANGES
)
from src.utils.scoring_utils import compute_tiered_score

def get_interpretation(metric_type, raw_value):
    """
    Get text interpretation, coaching, and label based on raw value and buckets.
    """
    buckets = INTERPRETATION_RANGES.get(metric_type, [])

    # Iterate through buckets to find the matching range
    for bucket in buckets:
        if raw_value <= bucket["max"]:
            return bucket["text"], bucket["coaching"], bucket["label"]

    # Fallback (should not happen with max=999)
    return "Value out of range", "Check your settings.", "unknown"

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
    Compute 0-1 scores for all performance metrics using Tiered Parabolic Scoring.
    """
    # 1. Extract Raw Values
    wpm = raw_metrics.get("wpm", 0)
    pause = raw_metrics.get("pause_ratio", 0)
    pitch_st = raw_metrics.get("pitch_std_st", 0)
    vol_cv = raw_metrics.get("volume_cv", 0)
    crest = raw_metrics.get("crest_factor_db", 0)

    # 2. Calculate Scores (Tiered Parabolic)
    score_wpm = compute_tiered_score(wpm, INTERPRETATION_RANGES["speech_rate"])
    score_pause = compute_tiered_score(pause, INTERPRETATION_RANGES["pause_ratio"])
    score_pitch = compute_tiered_score(pitch_st, INTERPRETATION_RANGES["pitch_dynamic"])
    score_vol = compute_tiered_score(vol_cv, INTERPRETATION_RANGES["volume_dynamic"])
    score_crest = compute_tiered_score(crest, INTERPRETATION_RANGES["vocal_punch"])

    # 3. Calculate Global Score (Average)
    global_score = (score_wpm + score_pause + score_pitch + score_vol + score_crest) / 5.0

    # 4. Get Interpretations & Coaching & Labels
    interp_wpm, coach_wpm, label_wpm = get_interpretation("speech_rate", wpm)
    interp_pause, coach_pause, label_pause = get_interpretation("pause_ratio", pause)
    interp_pitch, coach_pitch, label_pitch = get_interpretation("pitch_dynamic", pitch_st)
    interp_vol, coach_vol, label_vol = get_interpretation("volume_dynamic", vol_cv)
    interp_crest, coach_crest, label_crest = get_interpretation("vocal_punch", crest)

    # 5. Generate Result Dictionary
    scores = {
        "audio_global_score": float(global_score),
        "audio_global_interpretation": get_global_interpretation(global_score),

        "speech_rate_score": float(score_wpm),
        "speech_rate_val": float(wpm),
        "speech_rate_interpretation": interp_wpm,
        "speech_rate_coaching": coach_wpm,
        "speech_rate_label": label_wpm,

        "pause_ratio_score": float(score_pause),
        "pause_ratio_val": float(pause),
        "pause_ratio_interpretation": interp_pause,
        "pause_ratio_coaching": coach_pause,
        "pause_ratio_label": label_pause,

        "pitch_dynamic_score": float(score_pitch),
        "pitch_dynamic_val": float(pitch_st),
        "pitch_dynamic_interpretation": interp_pitch,
        "pitch_dynamic_coaching": coach_pitch,
        "pitch_dynamic_label": label_pitch,

        "volume_dynamic_score": float(score_vol),
        "volume_dynamic_val": float(vol_cv),
        "volume_dynamic_interpretation": interp_vol,
        "volume_dynamic_coaching": coach_vol,
        "volume_dynamic_label": label_vol,

        "vocal_punch_score": float(score_crest),
        "vocal_punch_val": float(crest),
        "vocal_punch_interpretation": interp_crest,
        "vocal_punch_coaching": coach_crest,
        "vocal_punch_label": label_crest
    }

    return scores
