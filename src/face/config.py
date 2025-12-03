"""
Configuration constants for the VERA Face Module.
Contains landmark indices, visualization colors, scoring baselines, and interpretation ranges.
"""

# =========================================================
# LANDMARK INDICES (MediaPipe FaceMesh)
# =========================================================
HEAD_POINTS = [234, 454, 1]    # ears + nose
GAZE_POINTS = [468, 473, 1]    # iris + nose
EXPRESS_POINTS = [
    55, 65, 52, 285, 295, 282,
    159, 145, 386, 374,
    13, 14, 61, 291, 234, 454
]
SMILE_POINTS = [61, 291]       # lip corners

# =========================================================
# VISUALIZATION COLORS (BGR)
# =========================================================
COLOR_HEAD   = (255, 0,   0)   # Blue
COLOR_GAZE   = (0,   255, 255) # Yellow
COLOR_EXP    = (0,   255, 0)   # Green
COLOR_SMILE  = (0,   0,   255) # Red

# =========================================================
# SCORING BASELINES
# =========================================================
# Head Stability
BASELINE_JITTER_OPTIMAL = 0.0001
BASELINE_JITTER_RANGE = 0.0003

#Gaze Consistency
BASELINE_GAZE_OPTIMAL = 0.0035   # "natural" gaze micro-movement
BASELINE_GAZE_VAR     = 0.00002  # tolerance

# Smile Activation
BASELINE_SMILE_OPTIMAL = 0.02
BASELINE_SMILE_RANGE = 0.01

# =========================================================
# INTERPRETATION RANGES
# =========================================================
INTERPRETATION_RANGES = {
    "head_stability": [
        (0.55, 1.00, "Highly stable head posture (Excellent). Controlled, confident, composed delivery."),
        (0.45, 0.55, "Natural and healthy stability (Good). Balanced movement: expressive but steady."),
        (0.30, 0.45, "Mild instability (Weak). Subtle micro-fidgeting or restlessness."),
        (0.00, 0.30, "Unstable head movement (Poor). Distracting, restless, or shaky posture.")
    ],
    "gaze_consistency": [
        (0.55, 1.00, "Highly controlled gaze (Excellent). Calm, intentional, confident eye behavior."),
        (0.45, 0.55, "Natural gaze behavior (Good). Healthy balance between expressiveness and control."),
        (0.30, 0.45, "Slightly unstable gaze (Weak). Occasional darting or scanning behavior."),
        (0.00, 0.30, "Unsteady or nervous gaze (Poor). Frequent darting eye movements.")
    ],
    "smile_activation": [
        (0.55, 1.00, "Expressive, warm, approachable (Excellent). Strong, natural smile."),
        (0.45, 0.55, "Balanced, natural smile (Good). Occasional or moderate smiling."),
        (0.30, 0.45, "Low smile activation (Weak). Neutral or minimally expressive."),
        (0.00, 0.30, "Flat or absent smile (Poor). No visible smiling, can feel closed-off.")
    ],
    "face_global_score": [
        (0.60, 1.00, "Excellent facial communication. High presence, warmth, and control."),
        (0.40, 0.60, "Good facial communication. Balanced and effective."),
        (0.00, 0.40, "Needs improvement. Facial signals may be distracting or weak.")
    ]
}
