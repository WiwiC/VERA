"""
Configuration constants for the VERA Body Module.
Contains landmark indices, visualization colors, scoring baselines, and interpretation ranges.
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

# SCORING BASELINES
# Gesture Magnitude

# Normalized by Shoulder Width (SW)
# Optimal: 1.0 - 2.5 SW (Hands moving freely)
BASELINE_GESTURE_MAG_OPTIMAL = 1.5
BASELINE_GESTURE_MAG_VAR     = 0.5

# Gesture Activity
# Normalized by Shoulder Width (SW/sec)
# Optimal: 0.5 - 1.5 SW/sec
BASELINE_GESTURE_ACTIVITY_OPTIMAL = 1.0
BASELINE_GESTURE_ACTIVITY_VAR = 0.25

# Gesture Jitter
# Normalized by Shoulder Width
BASELINE_GESTURE_JITTER_OPTIMAL = 0.5
BASELINE_GESTURE_JITTER_RANGE = 0.5

# Body Sway
# Normalized by Shoulder Width
# Scale factor for exp(-sway * scale). Target < 0.2 SW.
# If sway=0.5 (Distracting), Score ~0.08 (exp(-0.5 * 5))
BASELINE_BODY_SWAY_SCALE = 5.0

# Posture Openness
BASELINE_POSTURE_OPTIMAL = 150
BASELINE_POSTURE_RANGE = 15


# INTERPRETATION RANGES

INTERPRETATION_RANGES = {
    "gesture_magnitude": [
        {"max": 0.5, "label": "very_low", "text": "Gestures too small (Weak). Hands glued to sides/lap.", "coaching": "Unlock your hands. Try to make at least one large gesture per sentence."},
        {"max": 1.0, "label": "low", "text": "Small, timid gestures.", "coaching": "Open up your posture. Imagine holding a beach ball, not a tennis ball."},
        {"max": 2.5, "label": "optimal", "text": "High gesture dynamics (Excellent). Confident, expansive gestures.", "coaching": "Excellent use of space. Your gestures command attention."},
        {"max": 3.5, "label": "high", "text": "Very large, theatrical gestures.", "coaching": "Great energy, but ensure your gestures don't block your face."},
        {"max": 999, "label": "very_high", "text": "Wild, flailing movements. Distracting.", "coaching": "Keep your gestures within the 'box' (shoulders to hips). You are flailing."}
    ],
    "gesture_activity": [
        {"max": 0.2, "label": "very_low", "text": "Statue-like. No movement.", "coaching": "Move your hands to emphasize key verbs. You look frozen."},
        {"max": 0.5, "label": "low", "text": "Too static (Weak). Slow, lethargic movement.", "coaching": "Add some snap to your gestures. Match the rhythm of your speech."},
        {"max": 1.5, "label": "optimal", "text": "Optimal gesture pace (Excellent). Dynamic, fluid movement.", "coaching": "Perfect gesture pacing. Your hands move naturally with your words."},
        {"max": 2.5, "label": "high", "text": "Fast, energetic movement.", "coaching": "High energy! Just be careful not to look frantic."},
        {"max": 999, "label": "very_high", "text": "Chaotic, frantic waving.", "coaching": "Slow down. Your hands are moving faster than your audience can follow."}
    ],
    "gesture_jitter": [
        {"max": 0.20, "label": "optimal", "text": "Extremely stable gestures (Excellent). Smooth, intentional movement without fidgeting.", "coaching": "Excellent stability. You look very composed."},
        {"max": 0.40, "label": "good", "text": "Natural stability (Good). Healthy fluidity — no distracting instability.", "coaching": "Good control. Your hands look steady."},
        {"max": 0.60, "label": "high", "text": "Mild instability (Weak). Occasional shaking or unintentional flicks.", "coaching": "Smooth out your movements. Try to be more deliberate."},
        {"max": 999, "label": "very_high", "text": "Strong jitter / instability (Poor). Fidgety, shaky, restless hands.", "coaching": "Plant your hands when not gesturing. Avoid nervous ticks."}
    ],
    "body_sway": [
        {"max": 0.05, "label": "rigid", "text": "Robotically still. Unnatural.", "coaching": "Relax your shoulders. It's okay to shift your weight slightly."},
        {"max": 0.10, "label": "stable", "text": "Grounded, controlled posture (Excellent). Very grounded.", "coaching": "Great stability. You look very grounded."},
        {"max": 0.30, "label": "optimal", "text": "Natural controlled movement (Good). Natural, relaxed posture.", "coaching": "Natural posture. You look comfortable and engaged."},
        {"max": 0.50, "label": "unstable", "text": "Restless torso movement (Weak). Noticeable swaying.", "coaching": "Plant your feet. You are starting to rock back and forth."},
        {"max": 999, "label": "distracting", "text": "Strong body sway (Poor). Sea-sickness inducing sway.", "coaching": "Stop moving your torso. Imagine a string pulling you up from the crown of your head."}
    ],
    "posture_openness": [
        {"max": 20, "label": "closed", "text": "Closed, collapsed posture (Poor). Strong inward rotation.", "coaching": "Roll your shoulders back. You look defensive."},
        {"max": 40, "label": "constricted", "text": "Closed or slightly constricted posture (Weak). Slight defensiveness.", "coaching": "Open your chest. Let your arms hang naturally."},
        {"max": 60, "label": "good", "text": "Healthy neutral openness (Good). Approachable and relaxed.", "coaching": "Good posture. You look approachable."},
        {"max": 999, "label": "optimal", "text": "Open, expansive posture (Excellent). Strong, confident posture.", "coaching": "Excellent command of space. You look authoritative."}
    ],
    "body_global_score": [
        (0.70, 1.00, "Excellent body language. High presence, energy, and control."),
        (0.50, 0.70, "Good body language. Balanced and effective."),
        (0.00, 0.50, "Needs improvement. Body signals may be distracting, weak, or closed-off.")
    ]
}
