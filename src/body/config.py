"""
Configuration constants for the VERA Body Module.
Contains landmark indices, visualization colors, scoring baselines, and interpretation ranges.

FPS-NORMALIZED: All velocity metrics are now in per-second units.
Baselines are fps-agnostic and work with any video frame rate.

RECALIBRATED: Based on calibration audit (2025-01).
Baselines derived from human-labeled "optimal"/"stable"/"good" samples.
"""


# LANDMARK INDICES (MediaPipe Holistic/Pose)

POSE_POINTS = {
    "shoulders": [11, 12],
    "hips":      [23, 24],
    "wrists":    [15, 16],
}


# VISUALIZATION COLORS (BGR)

COLOR_SHOULDERS = (255, 0,   0)   # Blue
COLOR_HIPS      = (0,   255, 255) # Yellow
COLOR_WRISTS    = (0,   0,   255) # Red


# =========================================================
# SCORING BASELINES (Empirically Calibrated 2025-01)
# Derived from human-labeled calibration videos
# =========================================================

# Gesture Magnitude (SW units - NOT fps-dependent)
# RECALIBRATED: "optimal" samples = 2.49-2.89 SW, mean=2.69
# Previous optimal=2.0 was reasonable but variance too tight
BASELINE_GESTURE_MAG_OPTIMAL = 2.50   # SW (was 2.0)
BASELINE_GESTURE_MAG_VAR     = 0.64   # (0.8)² - widened for softer penalty

# Gesture Activity (SW/sec - fps-normalized)
# RECALIBRATED: "optimal" samples = 2.57-4.42 SW/sec, mean=3.49
# Previous optimal=2.4 was too low
BASELINE_GESTURE_ACTIVITY_OPTIMAL = 3.50   # SW/sec (was 2.4)
BASELINE_GESTURE_ACTIVITY_VAR     = 1.44   # (1.2)² for Gaussian scoring

# Gesture Stability (variance of per-second activity)
# RECALIBRATED: All data mean=11.6, std=9.8; "good" samples=0.78-14.71
# Previous midpoint=4.5 was too low (data 2x higher)
# Lower jitter = more stable, intentional gestures
BASELINE_GESTURE_JITTER_OPTIMAL = 10.0   # (was 4.5)
BASELINE_GESTURE_JITTER_RANGE   = 8.0    # (was 4.5) - widened scale

# Body Sway (SW/sec - fps-normalized)
# RECALIBRATED: "stable"/"optimal" samples = 0.58-1.01 SW/sec, mean=0.80
# Previous optimal=0.45 was too low (favored unnaturally still speakers)
BASELINE_BODY_SWAY_OPTIMAL = 0.75   # SW/sec (was 0.45)
BASELINE_BODY_SWAY_VAR     = 0.06   # (0.24)² - based on IQR/1.35
# Posture Openness (arms-based with midplane normalization)
# REFACTORED: Shoulder angle in raw output, but NOT used for scoring.
# Scoring based purely on arm position + wrist depth (midplane-normalized).

# --- Posture Openness Scoring (2-component, arms-based) ---
# State machine:
#   - "closed" = arms_close AND wrists_forward (defensive barrier)
#   - "neutral" = arms_close AND NOT wrists_forward (hands at rest/behind)
#   - "open" = NOT arms_close (gesturing)

# Component 1: Arms close to body
BASELINE_ARMS_CLOSE_THRESHOLD = 2.0   # SW units - gesture_mag < this = "close"

# Component 2: Wrist depth (midplane-normalized)
# NOTE: In MediaPipe, smaller Z = closer to camera, so NEGATIVE depth = forward
BASELINE_WRIST_FORWARD_DEPTH = -0.5   # depth < this = wrists forward (defensive)
BASELINE_WRIST_BEHIND_DEPTH = 0.3     # depth > this = wrists behind (confident)

# State scores
POSTURE_SCORE_OPEN = 1.0
POSTURE_SCORE_NEUTRAL = 0.6
POSTURE_SCORE_CLOSED = 0.2


# =========================================================
# CHANGE THRESHOLDS (MVP Heuristics for Timeline Labels)
# Used to label window-to-window changes as stable/shifting/erratic
# These are empirical, not ground truth — tune based on user feedback
# =========================================================

CHANGE_THRESHOLDS = {
    # gesture_magnitude (SW) - sweet spot metric
    # Typical range: 1.0 - 3.0, so changes of 0.3 are small
    "gesture_magnitude": {
        "stable": 0.30,
        "shifting": 0.80,
    },
    # gesture_activity (SW/sec) - sweet spot metric
    # Typical range: 0.6 - 9.0, so changes of 0.5 are small
    "gesture_activity": {
        "stable": 0.50,
        "shifting": 1.50,
    },
    # gesture_stability (variance) - lower is better
    # Typical range: 2.7 - 13.5, so changes of 1.5 are small
    "gesture_stability": {
        "stable": 1.50,
        "shifting": 4.00,
    },
    # body_sway (SW/sec) - sweet spot metric
    # Typical range: 0.15 - 1.50, so changes of 0.10 are small
    "body_sway": {
        "stable": 0.10,
        "shifting": 0.30,
    },
    # posture_openness (degrees) - sweet spot metric
    # Typical range: 40 - 56, so changes of 3° are small
    "posture_openness": {
        "stable": 3.0,
        "shifting": 8.0,
    },
}


# =========================================================
# INTERPRETATION RANGES (Recalibrated 2025-01)
# Aligned with empirical data from calibration videos
# =========================================================

INTERPRETATION_RANGES = {
    "gesture_magnitude": [
        # RECALIBRATED: "optimal" samples = 2.49-2.89 SW
        {"max": 1.2, "label": "very_low", "tier": (0.0, 0.4), "text": "Gestures too small (Weak). Hands glued to sides/lap.", "coaching": "Unlock your hands. Try to make at least one large gesture per sentence."},
        {"max": 2.0, "label": "low", "tier": (0.4, 0.6), "text": "Small, timid gestures.", "coaching": "Open up your posture. Imagine holding a beach ball, not a tennis ball."},
        {"max": 3.0, "label": "optimal", "tier": (0.8, 1.0), "text": "High gesture dynamics (Excellent). Confident, expansive gestures.", "coaching": "Excellent use of space. Your gestures command attention."},
        {"max": 3.5, "label": "high", "tier": (0.4, 0.6), "text": "Very large, theatrical gestures.", "coaching": "Great energy, but ensure your gestures don't block your face."},
        {"max": 999, "label": "very_high", "tier": (0.0, 0.4), "text": "Wild, flailing movements. Distracting.", "coaching": "Keep your gestures within the 'box' (shoulders to hips). You are flailing."}
    ],
    "gesture_activity": [
        # RECALIBRATED: "optimal" samples = 2.57-4.42 SW/sec
        {"max": 1.0, "label": "very_low", "tier": (0.0, 0.4), "text": "Statue-like. No movement.", "coaching": "Move your hands to emphasize key verbs. You look frozen."},
        {"max": 2.5, "label": "low", "tier": (0.4, 0.6), "text": "Too static (Weak). Slow, lethargic movement.", "coaching": "Add some snap to your gestures. Match the rhythm of your speech."},
        {"max": 5.0, "label": "optimal", "tier": (0.8, 1.0), "text": "Optimal gesture pace (Excellent). Dynamic, fluid movement.", "coaching": "Perfect gesture pacing. Your hands move naturally with your words."},
        {"max": 7.5, "label": "high", "tier": (0.4, 0.6), "text": "Fast, energetic movement.", "coaching": "High energy! Just be careful not to look frantic."},
        {"max": 999, "label": "very_high", "tier": (0.0, 0.4), "text": "Chaotic, frantic waving.", "coaching": "Slow down. Your hands are moving faster than your audience can follow."}
    ],
    "gesture_stability": [
        # RECALIBRATED: Data mean=11.6, "good" samples=0.78-14.71
        # INVERTED: Lower values = better (more stable)
        {"max": 5.0, "label": "optimal", "tier": (0.8, 1.0), "text": "Extremely stable gestures (Excellent). Smooth, intentional movement.", "coaching": "Excellent stability. You look very composed."},
        {"max": 12.0, "label": "good", "tier": (0.6, 0.8), "text": "Natural stability (Good). Healthy fluidity.", "coaching": "Good control. Your hands look steady."},
        {"max": 20.0, "label": "high", "tier": (0.4, 0.6), "text": "Mild instability (Weak). Occasional shaking.", "coaching": "Smooth out your movements. Try to be more deliberate."},
        {"max": 999, "label": "very_high", "tier": (0.0, 0.4), "text": "Strong jitter / instability (Poor). Fidgety hands.", "coaching": "Plant your hands when not gesturing. Avoid nervous ticks."}
    ],
    "body_sway": [
        # RECALIBRATED: "stable"/"optimal" samples = 0.58-1.01 SW/sec
        {"max": 0.30, "label": "rigid", "tier": (0.0, 0.4), "text": "Robotically still. Unnatural.", "coaching": "Relax your shoulders. It's okay to shift your weight slightly."},
        {"max": 0.55, "label": "stable", "tier": (0.6, 0.8), "text": "Grounded, controlled posture (Excellent). Very grounded.", "coaching": "Great stability. You look very grounded."},
        {"max": 1.00, "label": "optimal", "tier": (0.8, 1.0), "text": "Natural controlled movement (Good). Natural, relaxed posture.", "coaching": "Natural posture. You look comfortable and engaged."},
        {"max": 1.30, "label": "unstable", "tier": (0.4, 0.6), "text": "Restless torso movement (Weak). Noticeable swaying.", "coaching": "Plant your feet. You are starting to rock back and forth."},
        {"max": 999, "label": "distracting", "tier": (0.0, 0.4), "text": "Strong body sway (Poor). Sea-sickness inducing sway.", "coaching": "Stop moving your torso. Imagine a string pulling you up from the crown of your head."}
    ],
    "posture_openness": [
        # REFACTORED: Score-based buckets (3-state: 0.2/0.6/1.0)
        # Scoring done in scoring.py based on arms_close + wrist_depth
        {"max": 0.3, "label": "closed", "tier": (0.0, 0.4), "text": "Closed, defensive posture (Poor). Arms close to body with hands forward.", "coaching": "Open up your arms. You look guarded and defensive."},
        {"max": 0.7, "label": "neutral", "tier": (0.4, 0.6), "text": "Neutral posture (Ok). Arms at rest, hands at sides or behind.", "coaching": "Try using more hand gestures to engage your audience."},
        {"max": 999, "label": "open", "tier": (0.8, 1.0), "text": "Open, expressive posture (Excellent). Good use of gestures.", "coaching": "Great body language! You look confident and approachable."}
    ],
    "body_global_score": [
        (0.70, 1.00, "Excellent body language. High presence, energy, and control."),
        (0.50, 0.70, "Good body language. Balanced and effective."),
        (0.00, 0.50, "Needs improvement. Body signals may be distracting, weak, or closed-off.")
    ]
}
