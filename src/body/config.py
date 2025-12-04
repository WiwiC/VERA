"""
Configuration constants for the VERA Body Module.
Contains landmark indices, visualization colors, scoring baselines, and interpretation ranges.
"""

# =========================================================
# LANDMARK INDICES (MediaPipe Holistic/Pose)
# =========================================================
POSE_POINTS = {
    "shoulders": [11, 12],
    "hips":      [23, 24],
    "wrists":    [15, 16],
}

# =========================================================
# VISUALIZATION COLORS (BGR)
# =========================================================
COLOR_SHOULDERS = (255, 0,   0)   # Blue
COLOR_HIPS      = (0,   255, 255) # Yellow
COLOR_WRISTS    = (0,   0,   255) # Red

# =========================================================
# SCORING BASELINES
# =========================================================
# Gesture Magnitude
# Gesture Magnitude
BASELINE_GESTURE_MAG_OPTIMAL = 0.45  # "Open" gestures (not too small, not too big)
BASELINE_GESTURE_MAG_VAR     = 0.03  # Tolerance width

# Gesture Activity
BASELINE_GESTURE_ACTIVITY_OPTIMAL = 0.02
BASELINE_GESTURE_ACTIVITY_VAR = 0.0004

# Gesture Jitter
BASELINE_GESTURE_JITTER_OPTIMAL = 0.0005
BASELINE_GESTURE_JITTER_RANGE = 0.0004

# Body Sway
BASELINE_BODY_SWAY_SCALE = 3000

# Posture Openness
BASELINE_POSTURE_OPTIMAL = 150
BASELINE_POSTURE_RANGE = 15

# =========================================================
# INTERPRETATION RANGES
# =========================================================
INTERPRETATION_RANGES = {
    "gesture_magnitude": {
        "optimal": "High gesture dynamics (Excellent). Energetic, lively hand activity that enhances expression.",
        "good": "Balanced movement (Good). Hands move naturally and fluidly.",
        "low": "Gestures too small (Weak). Try to open up your arms and use more space.",
        "high": "Gestures too large (Distracting). Try to keep your hands within the 'box' (shoulders to hips)."
    },
    "gesture_activity": {
        "optimal": "Optimal gesture pace (Excellent). Movements are well-timed and energetic.",
        "good": "Good gesture pace (Good). Natural flow of movement.",
        "low": "Too static (Weak). Try to move your hands more to engage the audience.",
        "high": "Too fast/chaotic (Distracting). Try to slow down your movements."
    },
    "gesture_jitter": [
        (0.60, 1.00, "Extremely stable gestures (Excellent). Smooth, intentional movement without fidgeting."),
        (0.40, 0.60, "Natural stability (Good). Healthy fluidity — no distracting instability."),
        (0.20, 0.40, "Mild instability (Weak). Occasional shaking or unintentional flicks."),
        (0.00, 0.20, "Strong jitter / instability (Poor). Fidgety, shaky, restless hands.")
    ],
    "body_sway": [
        (0.60, 1.00, "Grounded, controlled posture (Excellent). Torso remains stable and solid."),
        (0.40, 0.60, "Natural controlled movement (Good). Small natural shifts, nothing distracting."),
        (0.20, 0.40, "Restless torso movement (Weak). Slight swaying, shifting, or rocking."),
        (0.00, 0.20, "Strong body sway (Poor). Frequent rocking or shifting weight.")
    ],
    "posture_openness": [
        (0.60, 1.00, "Open, expansive posture (Excellent). Strong, confident posture — welcoming and authoritative."),
        (0.40, 0.60, "Healthy neutral openness (Good). Comfortably open posture — approachable and relaxed."),
        (0.20, 0.40, "Closed or slightly constricted posture (Weak). Shoulders turning inward — slight defensiveness."),
        (0.00, 0.20, "Closed, collapsed posture (Poor). Strong inward rotation of shoulders.")
    ],
    "body_global_score": [
        (0.70, 1.00, "Excellent body language. High presence, energy, and control."),
        (0.50, 0.70, "Good body language. Balanced and effective."),
        (0.00, 0.50, "Needs improvement. Body signals may be distracting, weak, or closed-off.")
    ]
}
