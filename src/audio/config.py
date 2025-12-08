"""
Configuration parameters for the VERA Audio Module.
Includes baselines for scoring and interpretation text ranges.

RECALIBRATED: Based on empirical data analysis (2024-12).
Variances adjusted to provide meaningful discrimination.
"""

# =========================================================
# SCORING BASELINES (Plateau Ranges)
# =========================================================

# 1. Speech Rate (WPM)
# 140-160 is ideal.
# Plateau: 130 - 160 WPM (Score 1.0)
BASELINE_WPM_RANGE = (130, 160)
BASELINE_WPM_VAR   = 225  # (15)² - unchanged, works correctly

# 2. Pause Ratio
# 10-25% is natural.
# Plateau: 0.10 - 0.25 (Score 1.0)
BASELINE_PAUSE_RANGE = (0.10, 0.25)
BASELINE_PAUSE_VAR   = 0.0004  # (0.02)² - proper penalty for deviations

# 3. Pitch Dynamic (Expressiveness)
# 3.5-6.0 ST is lively.
# Plateau: 3.5 - 6.0 Semitones (Score 1.0)
BASELINE_PITCH_STD_RANGE = (3.5, 6.0)
BASELINE_PITCH_STD_VAR   = 0.05  # (0.22)² - proper penalty for deviations

# 4. Volume Dynamic (Emotionality)
# High var = High arousal.
# Plateau: 0.40 - 0.90 CV (Score 1.0)
BASELINE_VOLUME_CV_RANGE = (0.40, 0.90)
BASELINE_VOLUME_CV_VAR   = 0.0625  # (0.25)² - unchanged, works correctly

# 5. Vocal Punch (Energy)
# Plateau: 13.0 - 20.0 dB (Score 1.0)
BASELINE_CREST_RANGE = (13.0, 20.0)
BASELINE_CREST_VAR   = 12.25  # (3.5)² - unchanged, works correctly


# =========================================================
# INTERPRETATION RANGES + Directional Feedback
# =========================================================

INTERPRETATION_RANGES = {
    "speech_rate": [
        {"max": 100, "label": "very_slow", "text": "Very slow pace; can feel heavy or overly deliberate.", "coaching": "Increase your tempo on less critical details to add energy."},
        {"max": 130, "label": "slow", "text": "Slower than typical; very clear but may lack energy.", "coaching": "Speed up slightly to keep the flow engaging, while keeping clarity."},
        {"max": 160, "label": "optimal", "text": "Optimal pace. Easy to follow and engaging.", "coaching": "Excellent pace! You are easy to follow and engaging."},
        {"max": 180, "label": "fast", "text": "Energetic and lively. Good for excitement.", "coaching": "Great energy. Just ensure you pause enough to let points land."},
        {"max": 200, "label": "rushed", "text": "Very fast; listeners might miss details.", "coaching": "Slow down slightly. You risk losing the audience's comprehension."},
        {"max": 999, "label": "overwhelming", "text": "Too rapid; cognitive overload for listeners.", "coaching": "Deliberately slow down. Force yourself to take a breath between sentences."}
    ],
    "pause_ratio": [
        {"max": 0.05, "label": "no_pauses", "text": "Rushed, dense, and breathless.", "coaching": "Force yourself to pause for 1 second after every key point."},
        {"max": 0.10, "label": "low_pauses", "text": "Continuous flow; risks sounding run-on.", "coaching": "Use silence to your advantage. Let your audience digest your ideas."},
        {"max": 0.25, "label": "optimal", "text": "Perfect rhythm. Great use of silence for emphasis.", "coaching": "Perfect use of silence. It makes you sound confident and thoughtful."},
        {"max": 0.40, "label": "frequent_pauses", "text": "Very distinct, deliberate speaking style.", "coaching": "Good clarity, but ensure the flow doesn't feel choppy."},
        {"max": 0.50, "label": "disjointed", "text": "Too much silence; breaks the momentum.", "coaching": "Connect your ideas more smoothly. Reduce the length of your pauses."},
        {"max": 999, "label": "fragmented", "text": "Excessive silence; sounds hesitant or unprepared.", "coaching": "Try to keep your train of thought moving. Avoid long gaps."}
    ],
    "pitch_dynamic": [
        {"max": 1.5, "label": "robotic", "text": "Completely monotone. Hard to listen to.", "coaching": "You need to vary your pitch. Try emphasizing one word in every sentence."},
        {"max": 3.5, "label": "flat", "text": "Reserved and controlled, but lacks emotion.", "coaching": "Try to 'color' your words more. Don't be afraid to go higher or lower."},
        {"max": 6.0, "label": "optimal", "text": "Highly expressive. Captivating vocal melody.", "coaching": "Fantastic intonation! Your voice is melodic and captivating."},
        {"max": 8.0, "label": "theatrical", "text": "Very expressive; high emotional engagement.", "coaching": "Very lively! Great for storytelling, but ensure it fits the context."},
        {"max": 999, "label": "exaggerated", "text": "Rollercoaster pitch; can be distracting.", "coaching": "Tone it down slightly. Too much variation can sound insincere."}
    ],
    "volume_dynamic": [
        {"max": 0.20, "label": "monotone", "text": "Robotic volume. No emotional emphasis.", "coaching": "Punch your key words! Make important ideas louder than the rest."},
        {"max": 0.40, "label": "reserved", "text": "Controlled volume. Polite but safe.", "coaching": "Don't be afraid to whisper or project. Use volume to tell the story."},
        {"max": 0.90, "label": "optimal", "text": "Dynamic delivery. Great emotional texture.", "coaching": "Great dynamic range. You use volume effectively to convey emotion."},
        {"max": 999, "label": "unstable", "text": "Extreme volume swings.", "coaching": "Be careful of sudden shouts or drops. Keep the baseline steady."}
    ],
    "vocal_punch": [
        {"max": 10.0, "label": "muffled", "text": "Muffled/Flat (Weak). Lacks energy and attack.", "coaching": "Articulate more clearly. Hit your consonants harder."},
        {"max": 13.0, "label": "soft", "text": "Gentle delivery. Good for intimacy, bad for power.", "coaching": "Project your voice more. Imagine reaching the back of the room."},
        {"max": 20.0, "label": "optimal", "text": "Strong vocal energy. Clear, punchy articulation.", "coaching": "Strong vocal presence. Your voice cuts through clearly."},
        {"max": 999, "label": "aggressive", "text": "Aggressive (Distracting). Too punchy or shouting.", "coaching": "Soften your attack slightly. You don't need to shout to be heard."}
    ],
    "audio_global_score": [
        (0.70, 1.00, "Excellent vocal presence. Engaging, clear, and dynamic."),
        (0.50, 0.70, "Good vocal presence. Balanced and effective."),
        (0.00, 0.50, "Needs improvement. Voice may be monotone, rushed, or flat.")
    ]
}
