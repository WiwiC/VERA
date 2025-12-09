"""
Configuration constants for the VERA Face Module.
Contains landmark indices, visualization colors, scoring baselines, and interpretation ranges.

FPS-NORMALIZED: All velocity metrics are now in per-second units.
Baselines are fps-agnostic and work with any video frame rate.

RECALIBRATED: Based on calibration audit (2025-01).
Baselines derived from human-labeled "optimal"/"stable"/"good" samples.
"""


# LANDMARK INDICES (MediaPipe FaceMesh)

HEAD_POINTS = [234, 454, 1]    # ears + nose
GAZE_POINTS = [468, 473, 1]    # iris + nose
EXPRESS_POINTS = [
    55, 65, 52, 285, 295, 282,
    159, 145, 386, 374,
    13, 14, 61, 291, 234, 454
]
SMILE_POINTS = [61, 291]       # lip corners


# VISUALIZATION COLORS (BGR)

COLOR_HEAD   = (255, 0,   0)   # Blue
COLOR_GAZE   = (0,   255, 255) # Yellow
COLOR_EXP    = (0,   255, 0)   # Green
COLOR_SMILE  = (0,   0,   255) # Red


# =========================================================
# SCORING BASELINES (Empirically Calibrated 2025-01)
# Derived from human-labeled calibration videos
# =========================================================

# Head Stability (IOD/sec)
# RECALIBRATED: Previous optimal=0.90 was too low (data median=1.89)
# Calibration data: "stable"/"optimal" samples = 0.72-2.02 (WIDE RANGE!)
# Video 63 (optimal)=0.72, Video 67 (optimal)=2.02 → need VERY wide variance
BASELINE_HEAD_STABILITY_OPTIMAL = 1.30   # IOD/sec (center of range)
BASELINE_HEAD_STABILITY_VAR     = 1.00   # (1.0)² - very wide to accommodate range

# Gaze Stability (variance of per-second gaze changes)
# RECALIBRATED: Previous midpoint=0.10 was too low (data median=0.133)
# Calibration data: "good"/"optimal" samples = 0.05-0.17, mean=0.10
# All data: mean=0.174, std=0.12
# Lower jitter = better (inverted logistic)
BASELINE_GAZE_MIDPOINT = 0.15   # Logistic inflection point (was 0.10)
BASELINE_GAZE_SCALE    = 0.08   # Logistic scale - widened from 0.03 for softer transition

# Smile Activation (normalized by IOD - NOT fps-dependent)
# RECALIBRATED: Data range is narrow (0.74-0.82), need wider variance
# Calibration data: all samples mean=0.769, std=0.022
# Previous variance=0.0064 was too tight for this narrow range
BASELINE_SMILE_OPTIMAL = 0.77   # (was 0.82)
BASELINE_SMILE_VAR     = 0.001  # (0.032)² - widened significantly


# =========================================================
# CHANGE THRESHOLDS (MVP Heuristics for Timeline Labels)
# Used to label window-to-window changes as stable/shifting/erratic
# These are empirical, not ground truth — tune based on user feedback
# =========================================================

CHANGE_THRESHOLDS = {
    # head_speed (IOD/sec) - sweet spot metric
    # Typical range: 0.45 - 1.80, so changes of 0.15 are small
    "head_stability": {
        "stable": 0.15,    # |delta| <= 0.15 → stable
        "shifting": 0.40,  # 0.15 < |delta| <= 0.40 → shifting
        # > 0.40 → erratic
    },
    # gaze_jitter (variance) - lower is better
    # Typical range: 0.08 - 0.14, so changes of 0.02 are small
    "gaze_stability": {
        "stable": 0.02,
        "shifting": 0.05,
    },
    # smile (ratio) - sweet spot metric
    # Typical range: 0.75 - 0.88, so changes of 0.03 are small
    "smile_activation": {
        "stable": 0.03,
        "shifting": 0.08,
    },
}


# =========================================================
# INTERPRETATION RANGES (Recalibrated 2025-01)
# Aligned with empirical data from calibration videos
# =========================================================

INTERPRETATION_RANGES = {
    "head_stability": [
        # RECALIBRATED: Calibration data median=1.89, "optimal" samples=0.72-2.02
        # Previous buckets were too low - "optimal" videos scored poorly
        {"max": 0.60, "label": "rigid", "text": "Stiff neck. Frozen.", "coaching": "Nod slightly to show agreement or emphasis. You look stiff."},
        {"max": 1.00, "label": "stable", "text": "Very controlled. Serious but attentive.", "coaching": "Good control. A bit more movement could make you look warmer."},
        {"max": 2.00, "label": "optimal", "text": "Natural head engagement (Excellent). Good nodding and tilting.", "coaching": "Perfect head engagement. Your nods make you look like an active listener."},
        {"max": 3.00, "label": "high", "text": "Active head movement. Engaged but energetic.", "coaching": "High energy. Ensure your head movements are intentional, not random."},
        {"max": 999, "label": "distracting", "text": "Excessive head movement (Poor). Bobblehead effect.", "coaching": "Keep your head steady. Excessive nodding undermines your authority."}
    ],
    "gaze_stability": [
        # RECALIBRATED: Calibration data mean=0.174, "good" samples=0.05-0.17
        # INVERTED: Lower values = better (more stable gaze)
        {"max": 0.08, "label": "optimal", "text": "Highly controlled gaze (Excellent). Locked-in, confident gaze.", "coaching": "Excellent focus. You connect strongly with the viewer."},
        {"max": 0.15, "label": "good", "text": "Natural gaze behavior (Good). Natural eye contact.", "coaching": "Good eye contact. You feel present."},
        {"max": 0.22, "label": "weak", "text": "Slightly unstable gaze (Weak). Occasional scanning.", "coaching": "Hold your gaze for longer. Stop scanning the room."},
        {"max": 999, "label": "poor", "text": "Unsteady or nervous gaze (Poor). Frequent darting.", "coaching": "Look at the camera lens, not your screen. You seem disengaged."}
    ],
    "smile_activation": [
        # RECALIBRATED: Calibration data range=0.74-0.82, mean=0.77
        # Narrow range - buckets adjusted accordingly
        {"max": 0.74, "label": "flat", "text": "Flat or absent smile (Poor). Serious, poker face.", "coaching": "Smile with your eyes. You look a bit severe."},
        {"max": 0.76, "label": "neutral", "text": "Low smile activation (Weak). Professional but reserved.", "coaching": "Try to smile at the start and end of your sentences."},
        {"max": 0.80, "label": "optimal", "text": "Balanced, natural smile (Excellent). Warm and approachable.", "coaching": "Nice warmth. Your expression is welcoming."},
        {"max": 999, "label": "excessive", "text": "Very high smile (Good). Highly radiant, possibly over-expressive.", "coaching": "Great energy! Just ensure your smile matches the content."}
    ],
    "face_global_score": [
        (0.70, 1.00, "Excellent facial communication. High presence, warmth, and control."),
        (0.50, 0.70, "Good facial communication. Balanced and effective."),
        (0.00, 0.50, "Needs improvement. Facial signals may be distracting or weak.")
    ]
}
