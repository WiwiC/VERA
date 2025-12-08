"""
Configuration constants for the VERA Face Module.
Contains landmark indices, visualization colors, scoring baselines, and interpretation ranges.

FPS-NORMALIZED: All velocity metrics are now in per-second units.
Baselines are fps-agnostic and work with any video frame rate.

RECALIBRATED: Based on empirical data analysis (2024-12).
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
# SCORING BASELINES (FPS-NORMALIZED & RECALIBRATED)
# All velocity metrics are in per-second units
# =========================================================

# Head Stability (IOD/sec)
# Observed data: mean 0.89, median 0.74, IQR 0.50
# Optimal band: 0.75 - 1.35 IOD/sec (matches interpretation buckets)
BASELINE_HEAD_STABILITY_OPTIMAL = 0.90   # IOD/sec
BASELINE_HEAD_STABILITY_VAR     = 0.27   # (0.52)² for Gaussian scoring

# Gaze Consistency (variance of per-second gaze changes)
# Observed data: mean 0.108, Q25 0.09, Q75 0.12
# Lower jitter = better (inverted logistic)
# Note: MIDPOINT is the logistic center, NOT the optimal value (optimal is ≤0.08)
BASELINE_GAZE_MIDPOINT = 0.10   # Logistic inflection point (lower values score higher)
BASELINE_GAZE_SCALE    = 0.03   # Logistic scale parameter

# Smile Activation (normalized by IOD - NOT fps-dependent)
# Observed data: mean 0.82, std 0.05, range 0.62-1.01
# Uses GAUSSIAN scoring (optimal band, not "more is better")
BASELINE_SMILE_OPTIMAL = 0.82
BASELINE_SMILE_VAR     = 0.0064  # (0.08)² for Gaussian scoring


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
# INTERPRETATION RANGES (FPS-NORMALIZED & RECALIBRATED)
# Thresholds aligned with observed data distributions
# =========================================================

INTERPRETATION_RANGES = {
    "head_stability": [
        # Buckets on head_speed (IOD/sec)
        # Data: Q25=0.46, median=0.74, Q75=1.02
        {"max": 0.45, "label": "rigid", "text": "Stiff neck. Frozen.", "coaching": "Nod slightly to show agreement or emphasis. You look stiff."},
        {"max": 0.75, "label": "stable", "text": "Very controlled. Serious.", "coaching": "Good control. A bit more movement could make you look warmer."},
        {"max": 1.35, "label": "optimal", "text": "Natural head engagement (Excellent). Good nodding and tilting.", "coaching": "Perfect head engagement. Your nods make you look like an active listener."},
        {"max": 1.80, "label": "high", "text": "Active head movement.", "coaching": "High energy. Ensure your head movements are intentional, not random."},
        {"max": 999, "label": "distracting", "text": "Excessive head movement (Poor). Bobblehead effect.", "coaching": "Keep your head steady. Excessive nodding undermines your authority."}
    ],
    "gaze_stability": [
        # Buckets on gaze_jitter (variance of gaze_dg/sec)
        # RECALIBRATED: Data mean 0.108, Q25 0.09, Q75 0.12
        # INVERTED: Lower values = better (more stable gaze)
        {"max": 0.08, "label": "optimal", "text": "Highly controlled gaze (Excellent). Locked-in, confident gaze.", "coaching": "Excellent focus. You connect strongly with the viewer."},
        {"max": 0.11, "label": "good", "text": "Natural gaze behavior (Good). Natural eye contact.", "coaching": "Good eye contact. You feel present."},
        {"max": 0.14, "label": "weak", "text": "Slightly unstable gaze (Weak). Occasional scanning.", "coaching": "Hold your gaze for longer. Stop scanning the room."},
        {"max": 999, "label": "poor", "text": "Unsteady or nervous gaze (Poor). Frequent darting.", "coaching": "Look at the camera lens, not your screen. You seem disengaged."}
    ],
    "smile_activation": [
        # Buckets on smile_val (lip distance / IOD)
        # Data: mean 0.82, Q25 0.79, Q75 0.85
        {"max": 0.75, "label": "flat", "text": "Flat or absent smile (Poor). Serious, poker face.", "coaching": "Smile with your eyes. You look a bit severe."},
        {"max": 0.80, "label": "neutral", "text": "Low smile activation (Weak). Professional but reserved.", "coaching": "Try to smile at the start and end of your sentences."},
        {"max": 0.88, "label": "optimal", "text": "Balanced, natural smile (Excellent). Warm and approachable.", "coaching": "Nice warmth. Your expression is welcoming."},
        {"max": 999, "label": "excessive", "text": "Very high smile (Good). Highly radiant, possibly over-expressive.", "coaching": "Great energy! Just ensure your smile matches the content."}
    ],
    "face_global_score": [
        (0.70, 1.00, "Excellent facial communication. High presence, warmth, and control."),
        (0.50, 0.70, "Good facial communication. Balanced and effective."),
        (0.00, 0.50, "Needs improvement. Facial signals may be distracting or weak.")
    ]
}
