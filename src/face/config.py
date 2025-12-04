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
# Head Stability
# Normalized by IOD (Inter-Ocular Distance)
# Optimal: 0.2 - 0.5 IOD/sec (Natural nodding)
BASELINE_HEAD_STABILITY_OPTIMAL = 0.35
BASELINE_HEAD_STABILITY_VAR     = 0.1

#Gaze Consistency
BASELINE_GAZE_OPTIMAL = 0.00075   # "natural" gaze micro-movement
BASELINE_GAZE_VAR     = 0.00002  # tolerance

# Smile Activation
BASELINE_SMILE_OPTIMAL = 0.02
BASELINE_SMILE_RANGE = 0.01

# =========================================================
# INTERPRETATION RANGES
# =========================================================
INTERPRETATION_RANGES = {
    "head_stability": [
        {"max": 0.1, "label": "rigid", "text": "Stiff neck. Frozen.", "coaching": "Nod slightly to show agreement or emphasis. You look stiff."},
        {"max": 0.2, "label": "stable", "text": "Very controlled. Serious.", "coaching": "Good control. A bit more movement could make you look warmer."},
        {"max": 0.5, "label": "optimal", "text": "Highly stable head posture (Excellent). Natural nodding and tilting.", "coaching": "Perfect head engagement. Your nods make you look like an active listener."},
        {"max": 1.0, "label": "high", "text": "Very active head movement.", "coaching": "High energy. Ensure your head movements are intentional, not random."},
        {"max": 999, "label": "distracting", "text": "Unstable head movement (Poor). Bobblehead effect.", "coaching": "Keep your head steady. Excessive nodding undermines your authority."}
    ],
    "gaze_consistency": [
        {"max": 0.4, "label": "poor", "text": "Unsteady or nervous gaze (Poor). Avoidant or distracted.", "coaching": "Look at the camera lens, not your screen. You seem disengaged."},
        {"max": 0.7, "label": "weak", "text": "Slightly unstable gaze (Weak). Frequent scanning/darting.", "coaching": "Hold your gaze for longer. Stop scanning the room."},
        {"max": 0.9, "label": "good", "text": "Natural gaze behavior (Good). Natural eye contact.", "coaching": "Good eye contact. You feel present."},
        {"max": 999, "label": "optimal", "text": "Highly controlled gaze (Excellent). Locked-in, confident gaze.", "coaching": "Excellent focus. You connect strongly with the viewer."}
    ],
    "smile_activation": [
        {"max": 0.2, "label": "flat", "text": "Flat or absent smile (Poor). Serious, poker face.", "coaching": "Smile with your eyes. You look a bit severe."},
        {"max": 0.5, "label": "neutral", "text": "Low smile activation (Weak). Professional but reserved.", "coaching": "Try to smile at the start and end of your sentences."},
        {"max": 0.8, "label": "good", "text": "Balanced, natural smile (Good). Warm and approachable.", "coaching": "Nice warmth. Your expression is welcoming."},
        {"max": 999, "label": "optimal", "text": "Expressive, warm, approachable (Excellent). Highly radiant and positive.", "coaching": "Fantastic energy! Your smile is contagious."}
    ],
    "face_global_score": [
        (0.70, 1.00, "Excellent facial communication. High presence, warmth, and control."),
        (0.50, 0.70, "Good facial communication. Balanced and effective."),
        (0.00, 0.50, "Needs improvement. Facial signals may be distracting or weak.")
    ]
}
