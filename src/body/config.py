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
BASELINE_GESTURE_MAG_MEAN = 0.20
BASELINE_GESTURE_MAG_RANGE = 0.10

# Gesture Activity
BASELINE_GESTURE_ACTIVITY_OPTIMAL = 0.02
BASELINE_GESTURE_ACTIVITY_VAR = 0.0004

# Gesture Jitter
BASELINE_GESTURE_JITTER_OPTIMAL = 0.0005
BASELINE_GESTURE_JITTER_RANGE = 0.0004

# Body Sway
BASELINE_BODY_SWAY_SCALE = 3000

# Posture Openness
BASELINE_POSTURE_OPTIMAL = 120
BASELINE_POSTURE_RANGE = 15

# =========================================================
# INTERPRETATION RANGES
# =========================================================
INTERPRETATION_RANGES = {
    "gesture_magnitude": [
        (0.55, 1.00, "High gesture dynamics (Excellent). Energetic, lively hand activity that enhances expression."),
        (0.45, 0.55, "Balanced movement (Good). Hands move naturally and fluidly."),
        (0.30, 0.45, "Slow or hesitant activity (Weak). Hands move, but inconsistently or too little."),
        (0.00, 0.30, "Almost no gesture activity (Poor). Hands passive — low energy, low presence.")
    ],
    "gesture_activity": [
        (0.55, 1.00, "Optimal gesture pace (Excellent). Movements are well-timed and energetic."),
        (0.45, 0.55, "Good gesture pace (Good). Natural flow of movement."),
        (0.30, 0.45, "Irregular gesture pace (Weak). Too fast or too slow at times."),
        (0.00, 0.30, "Poor gesture pace (Poor). Distracting or non-existent movement.")
    ],
    "gesture_jitter": [
        (0.55, 1.00, "Extremely stable gestures (Excellent). Smooth, intentional movement without fidgeting."),
        (0.45, 0.55, "Natural stability (Good). Healthy fluidity — no distracting instability."),
        (0.30, 0.45, "Mild instability (Weak). Occasional shaking or unintentional flicks."),
        (0.00, 0.30, "Strong jitter / instability (Poor). Fidgety, shaky, restless hands.")
    ],
    "body_sway": [
        (0.55, 1.00, "Grounded, controlled posture (Excellent). Torso remains stable and solid."),
        (0.45, 0.55, "Natural controlled movement (Good). Small natural shifts, nothing distracting."),
        (0.30, 0.45, "Restless torso movement (Weak). Slight swaying, shifting, or rocking."),
        (0.00, 0.30, "Strong body sway (Poor). Frequent rocking or shifting weight.")
    ],
    "posture_openness": [
        (0.55, 1.00, "Open, expansive posture (Excellent). Strong, confident posture — welcoming and authoritative."),
        (0.45, 0.55, "Healthy neutral openness (Good). Comfortably open posture — approachable and relaxed."),
        (0.30, 0.45, "Closed or slightly constricted posture (Weak). Shoulders turning inward — slight defensiveness."),
        (0.00, 0.30, "Closed, collapsed posture (Poor). Strong inward rotation of shoulders.")
    ],
    "body_global_score": [
        (0.60, 1.00, "Excellent body language. High presence, energy, and control."),
        (0.40, 0.60, "Good body language. Balanced and effective."),
        (0.00, 0.40, "Needs improvement. Body signals may be distracting, weak, or closed-off.")
    ]
}
