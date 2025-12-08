"""
Configuration constants for the VERA Body Module.
Contains landmark indices, visualization colors, scoring baselines, and interpretation ranges.

FPS-NORMALIZED: All velocity metrics are now in per-second units.
Baselines are fps-agnostic and work with any video frame rate.
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
# SCORING BASELINES (FPS-NORMALIZED)
# Velocity metrics are in per-second units
# Position/angle metrics are NOT fps-dependent
# =========================================================

# Gesture Magnitude (SW units - NOT fps-dependent)
# Observed data: mean 2.10, median 2.14, range 0.8-3.8 SW
# Optimal band: 1.5 - 2.5 SW (confident, expansive gestures)
BASELINE_GESTURE_MAG_OPTIMAL = 2.0
BASELINE_GESTURE_MAG_VAR     = 0.36  # (0.6)²

# Gesture Activity (SW/sec - fps-normalized)
# Observed data at 30fps: mean 0.088 SW/frame → 2.64 SW/sec
# Optimal band: 1.5 - 4.5 SW/sec (dynamic, fluid movement)
BASELINE_GESTURE_ACTIVITY_OPTIMAL = 2.4   # SW/sec
BASELINE_GESTURE_ACTIVITY_VAR     = 1.44  # (1.2)² for Gaussian scoring

# Gesture Jitter (variance of per-second activity - scales by fps²)
# Lower jitter = more stable, intentional gestures
# Observed data: ~0.005 per-frame variance → 4.5 at 30fps scale
BASELINE_GESTURE_JITTER_OPTIMAL = 4.5
BASELINE_GESTURE_JITTER_RANGE   = 4.5

# Body Sway (SW/sec - fps-normalized)
# Observed data at 30fps: mean 0.019 SW/frame → 0.57 SW/sec
# Optimal band: 0.30 - 0.90 SW/sec (natural engagement without distraction)
BASELINE_BODY_SWAY_OPTIMAL = 0.45   # SW/sec
BASELINE_BODY_SWAY_VAR     = 0.09   # (0.3)² for Gaussian scoring

# Posture Openness (degrees - NOT fps-dependent)
# Angle at sternum (Left Shoulder - Sternum - Right Shoulder)
# Observed data: mean 47°, std 6.7°, range 40-75°
# Optimal band: Gaussian
BASELINE_POSTURE_OPTIMAL = 48
BASELINE_POSTURE_VAR     = 100  # (10)² for Gaussian scoring


# =========================================================
# INTERPRETATION RANGES (FPS-NORMALIZED)
# Velocity thresholds scaled to per-second units (×30)
# Variance thresholds scaled by ×900 (fps²)
# =========================================================

INTERPRETATION_RANGES = {
    "gesture_magnitude": [
        # Buckets on magnitude (SW) - NOT fps-dependent
        {"max": 1.0, "label": "very_low", "text": "Gestures too small (Weak). Hands glued to sides/lap.", "coaching": "Unlock your hands. Try to make at least one large gesture per sentence."},
        {"max": 1.5, "label": "low", "text": "Small, timid gestures.", "coaching": "Open up your posture. Imagine holding a beach ball, not a tennis ball."},
        {"max": 2.5, "label": "optimal", "text": "High gesture dynamics (Excellent). Confident, expansive gestures.", "coaching": "Excellent use of space. Your gestures command attention."},
        {"max": 3.0, "label": "high", "text": "Very large, theatrical gestures.", "coaching": "Great energy, but ensure your gestures don't block your face."},
        {"max": 999, "label": "very_high", "text": "Wild, flailing movements. Distracting.", "coaching": "Keep your gestures within the 'box' (shoulders to hips). You are flailing."}
    ],
    "gesture_activity": [
        # Buckets on activity (SW/sec) - scaled ×30 from per-frame
        {"max": 0.6, "label": "very_low", "text": "Statue-like. No movement.", "coaching": "Move your hands to emphasize key verbs. You look frozen."},
        {"max": 1.5, "label": "low", "text": "Too static (Weak). Slow, lethargic movement.", "coaching": "Add some snap to your gestures. Match the rhythm of your speech."},
        {"max": 4.5, "label": "optimal", "text": "Optimal gesture pace (Excellent). Dynamic, fluid movement.", "coaching": "Perfect gesture pacing. Your hands move naturally with your words."},
        {"max": 9.0, "label": "high", "text": "Fast, energetic movement.", "coaching": "High energy! Just be careful not to look frantic."},
        {"max": 999, "label": "very_high", "text": "Chaotic, frantic waving.", "coaching": "Slow down. Your hands are moving faster than your audience can follow."}
    ],
    "gesture_jitter": [
        # Buckets on jitter (variance of activity/sec) - scaled ×900 from per-frame
        # INVERTED: Lower values = better (more stable)
        {"max": 2.7, "label": "optimal", "text": "Extremely stable gestures (Excellent). Smooth, intentional movement.", "coaching": "Excellent stability. You look very composed."},
        {"max": 7.2, "label": "good", "text": "Natural stability (Good). Healthy fluidity.", "coaching": "Good control. Your hands look steady."},
        {"max": 13.5, "label": "high", "text": "Mild instability (Weak). Occasional shaking.", "coaching": "Smooth out your movements. Try to be more deliberate."},
        {"max": 999, "label": "very_high", "text": "Strong jitter / instability (Poor). Fidgety hands.", "coaching": "Plant your hands when not gesturing. Avoid nervous ticks."}
    ],
    "body_sway": [
        # Buckets on sway (SW/sec) - scaled ×30 from per-frame
        {"max": 0.15, "label": "rigid", "text": "Robotically still. Unnatural.", "coaching": "Relax your shoulders. It's okay to shift your weight slightly."},
        {"max": 0.30, "label": "stable", "text": "Grounded, controlled posture (Excellent). Very grounded.", "coaching": "Great stability. You look very grounded."},
        {"max": 0.90, "label": "optimal", "text": "Natural controlled movement (Good). Natural, relaxed posture.", "coaching": "Natural posture. You look comfortable and engaged."},
        {"max": 1.50, "label": "unstable", "text": "Restless torso movement (Weak). Noticeable swaying.", "coaching": "Plant your feet. You are starting to rock back and forth."},
        {"max": 999, "label": "distracting", "text": "Strong body sway (Poor). Sea-sickness inducing sway.", "coaching": "Stop moving your torso. Imagine a string pulling you up from the crown of your head."}
    ],
    "posture_openness": [
        # Buckets on degrees (angle at sternum) - NOT fps-dependent
        # ALIGNED with Gaussian scoring (peak at 48°, variance 100)
        # Score thresholds: 42°=0.70, 48°=1.0, 54°=0.70, 40°=0.53, 56°=0.53
        {"max": 40, "label": "closed", "text": "Closed, collapsed posture (Poor). Strong inward rotation.", "coaching": "Roll your shoulders back. You look defensive."},
        {"max": 42, "label": "constricted", "text": "Slightly constricted posture (Weak). Shoulders rolled forward.", "coaching": "Open your chest. Let your arms hang naturally."},
        {"max": 54, "label": "optimal", "text": "Optimal posture (Excellent). Confident and approachable.", "coaching": "Perfect posture. You look confident and open."},
        {"max": 56, "label": "good", "text": "Open posture (Good). Slightly expansive.", "coaching": "Good openness. You look approachable."},
        {"max": 999, "label": "exaggerated", "text": "Exaggerated openness (Weak). May look unnatural or stiff.", "coaching": "Relax your shoulders slightly. You look overly rigid."}
    ],
    "body_global_score": [
        (0.70, 1.00, "Excellent body language. High presence, energy, and control."),
        (0.50, 0.70, "Good body language. Balanced and effective."),
        (0.00, 0.50, "Needs improvement. Body signals may be distracting, weak, or closed-off.")
    ]
}
