"""
Configuration parameters for the VERA Audio Module.
Includes baselines for scoring and interpretation text ranges.

RECALIBRATED: Based on calibration audit (2025-01).
Baselines derived from human-labeled "optimal" samples.
"""

# =========================================================
# SCORING BASELINES (Empirically Calibrated)
# =========================================================

# 1. Speech Rate (WPM)
# Calibration data: optimal samples = 122-167 WPM
# Plateau: 120 - 170 WPM (Score 1.0)
BASELINE_WPM_RANGE = (120, 170)
BASELINE_WPM_VAR   = 400  # (20)² - balanced sensitivity

# 2. Pause Ratio
# CRITICAL FIX: Original plateau (0.10-0.25) was inverted vs data (0.01-0.08)
# Calibration data: "optimal" samples = 0.01-0.04, all data = 0.01-0.18
# WIDER Gaussian to accommodate Video 63 (0.01) and Video 67 (0.04)
BASELINE_PAUSE_OPTIMAL = 0.04   # Center of "optimal" labeled samples
BASELINE_PAUSE_VAR     = 0.002  # (0.045)² - wider to accommodate 0.01-0.08 range

# 3. Pitch Dynamic (Expressiveness)
# Calibration data: mean=2.87 ST, range=2.0-5.1 ST
# Original plateau (3.5-6.0) was too high for this data
# Plateau: 2.0 - 4.5 Semitones (Score 1.0)
BASELINE_PITCH_STD_RANGE = (2.0, 4.5)
BASELINE_PITCH_STD_VAR   = 0.25  # (0.5)² - gentler falloff

# 4. Volume Dynamic (Emotionality)
# CRITICAL FIX: Original plateau (0.40-0.90) gave all videos score=1.0
# Calibration data: mean=0.706, std=0.05, range=0.63-0.80
# Using Gaussian scoring for discrimination
BASELINE_VOLUME_CV_OPTIMAL = 0.70   # Calibration median
BASELINE_VOLUME_CV_VAR     = 0.003  # (0.055)² - discriminates within data range

# 5. Vocal Punch (Energy)
# Calibration data: mean=19.4 dB, range=17.5-24.6
# Narrowed plateau for better discrimination
# Plateau: 17.0 - 21.0 dB (Score 1.0)
BASELINE_CREST_RANGE = (17.0, 21.0)
BASELINE_CREST_VAR   = 4.0  # (2.0)² - tighter falloff


# =========================================================
# INTERPRETATION RANGES (Recalibrated 2025-01)
# Aligned with empirical data distributions
# =========================================================

INTERPRETATION_RANGES = {
    "speech_rate": [
        # Calibration data: range 81-201 WPM, optimal ~120-170
        {"max": 100, "label": "very_slow", "text": "Very slow pace; can feel heavy or overly deliberate.", "coaching": "Increase your tempo on less critical details to add energy."},
        {"max": 120, "label": "slow", "text": "Slower than typical; very clear but may lack energy.", "coaching": "Speed up slightly to keep the flow engaging, while keeping clarity."},
        {"max": 170, "label": "optimal", "text": "Optimal pace. Easy to follow and engaging.", "coaching": "Excellent pace! You are easy to follow and engaging."},
        {"max": 190, "label": "fast", "text": "Energetic and lively. Good for excitement.", "coaching": "Great energy. Just ensure you pause enough to let points land."},
        {"max": 210, "label": "rushed", "text": "Very fast; listeners might miss details.", "coaching": "Slow down slightly. You risk losing the audience's comprehension."},
        {"max": 999, "label": "overwhelming", "text": "Too rapid; cognitive overload for listeners.", "coaching": "Deliberately slow down. Force yourself to take a breath between sentences."}
    ],
    "pause_ratio": [
        # RECALIBRATED: Data range 0.01-0.18, optimal ~0.02-0.08
        {"max": 0.02, "label": "no_pauses", "text": "Machine-gun delivery. No breathing room.", "coaching": "Force yourself to pause for 1 second after every key point."},
        {"max": 0.04, "label": "low_pauses", "text": "Fast-flowing speech. Good energy but dense.", "coaching": "Add micro-pauses to let key points land."},
        {"max": 0.08, "label": "optimal", "text": "Perfect rhythm. Natural flow with good pacing.", "coaching": "Great pacing! You sound confident and natural."},
        {"max": 0.12, "label": "frequent_pauses", "text": "Deliberate style. Clear but may lose momentum.", "coaching": "Good clarity, but keep the energy up between pauses."},
        {"max": 0.18, "label": "disjointed", "text": "Too many pauses. Breaks the flow.", "coaching": "Connect your ideas more smoothly. Reduce pause length."},
        {"max": 999, "label": "fragmented", "text": "Excessive silence; sounds hesitant or unprepared.", "coaching": "Try to keep your train of thought moving. Avoid long gaps."}
    ],
    "pitch_dynamic": [
        # RECALIBRATED: Data range 2.0-5.1 ST, mean 2.87
        {"max": 1.5, "label": "robotic", "text": "Completely monotone. Hard to listen to.", "coaching": "You need to vary your pitch. Try emphasizing one word in every sentence."},
        {"max": 2.0, "label": "flat", "text": "Reserved and controlled, but lacks emotion.", "coaching": "Try to 'color' your words more. Don't be afraid to go higher or lower."},
        {"max": 4.5, "label": "optimal", "text": "Good expressiveness. Engaging vocal melody.", "coaching": "Good intonation! Your voice carries emotion well."},
        {"max": 6.0, "label": "theatrical", "text": "Very expressive; high emotional engagement.", "coaching": "Very lively! Great for storytelling, but ensure it fits the context."},
        {"max": 999, "label": "exaggerated", "text": "Rollercoaster pitch; can be distracting.", "coaching": "Tone it down slightly. Too much variation can sound insincere."}
    ],
    "volume_dynamic": [
        # RECALIBRATED: Data range 0.63-0.80, mean 0.706
        {"max": 0.55, "label": "monotone", "text": "Flat volume. No emotional emphasis.", "coaching": "Punch your key words! Make important ideas louder than the rest."},
        {"max": 0.65, "label": "reserved", "text": "Controlled volume. Polite but could be more dynamic.", "coaching": "Don't be afraid to whisper or project. Use volume to tell the story."},
        {"max": 0.75, "label": "optimal", "text": "Dynamic delivery. Good emotional texture.", "coaching": "Great dynamic range. You use volume effectively to convey emotion."},
        {"max": 0.85, "label": "expressive", "text": "Highly dynamic. Strong emotional variation.", "coaching": "Very expressive! Just ensure consistency in calmer moments."},
        {"max": 999, "label": "unstable", "text": "Extreme volume swings. Can be jarring.", "coaching": "Be careful of sudden shouts or drops. Keep the baseline steady."}
    ],
    "vocal_punch": [
        # RECALIBRATED: Data range 17.5-24.6 dB, mean 19.4
        {"max": 14.0, "label": "muffled", "text": "Muffled/Flat (Weak). Lacks energy and attack.", "coaching": "Articulate more clearly. Hit your consonants harder."},
        {"max": 17.0, "label": "soft", "text": "Gentle delivery. Good for intimacy, bad for power.", "coaching": "Project your voice more. Imagine reaching the back of the room."},
        {"max": 21.0, "label": "optimal", "text": "Strong vocal energy. Clear, punchy articulation.", "coaching": "Strong vocal presence. Your voice cuts through clearly."},
        {"max": 24.0, "label": "strong", "text": "Very punchy. High energy and presence.", "coaching": "Great presence! Just be mindful of the context."},
        {"max": 999, "label": "aggressive", "text": "Aggressive (Distracting). Too punchy or shouting.", "coaching": "Soften your attack slightly. You don't need to shout to be heard."}
    ],
    "audio_global_score": [
        (0.70, 1.00, "Excellent vocal presence. Engaging, clear, and dynamic."),
        (0.50, 0.70, "Good vocal presence. Balanced and effective."),
        (0.00, 0.50, "Needs improvement. Voice may be monotone, rushed, or flat.")
    ]
}
