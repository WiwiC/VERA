# VERA Metrics Reference Guide

This document describes all 14 metrics analyzed by VERA, their measurement methodology, and the interpretation labels you can use when manually labeling videos.

---

## SCORING METHODOLOGY (New: Tiered Parabolic Scoring)

VERA uses a **Tiered Parabolic Scoring** system to ensure that numerical scores (0-100%) always align with the assigned label.

1.  **Buckets & Tiers:** Each metric is divided into "buckets" (e.g., `low`, `optimal`, `high`). Each bucket is assigned a fixed **Score Tier** (e.g., `optimal` is always 80-100%).
2.  **Parabolic Interpolation:** Within the "Optimal" bucket, we use a parabolic curve. This means you get a higher score (closer to 100%) if you are in the *center* of the optimal range, and a slightly lower score (closer to 80%) if you are at the edges.
3.  **Linear Interpolation:** For non-optimal buckets, scores are distributed linearly.

This ensures that if you receive an "Optimal" label, your score is guaranteed to be high (80%+).

---

## FACE MODULE

### 1. Head Stability
| Property | Value |
|----------|-------|
| **What it measures** | How steady your head is while you speak. Captures natural nodding and tilting that signal engagement, versus being frozen or excessively bobbing. |
| **How it's measured** | Tracks how much your head position changes between video frames, normalized to your face size and converted to movement per second. |
| **Unit** | IOD/sec (Inter-Ocular Distance per second) |
| **Ideal range** | 1.00 - 2.00 |

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `rigid` | < 0.60 | 0% - 40% | Stiff neck. Frozen. |
| `stable` | 0.60 - 1.00 | 60% - 80% | Very controlled. Serious but attentive. |
| `optimal` | 1.00 - 2.00 | 80% - 100% | Natural head engagement. Good nodding and tilting. |
| `high` | 2.00 - 3.00 | 40% - 60% | Active head movement. Engaged but energetic. |
| `distracting` | > 3.00 | 0% - 40% | Excessive head movement. Bobblehead effect. |

---

### 2. Gaze Stability
| Property | Value |
|----------|-------|
| **What it measures** | How stable and focused your eye contact is. Captures whether you maintain a confident, locked-in gaze versus darting or scanning nervously. |
| **How it's measured** | Measures how much your gaze direction changes each second by tracking iris positions relative to your face. |
| **Unit** | Variance of gaze change per second |
| **Ideal range** | 0 - 0.08 (lower is better) |

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `optimal` | < 0.08 | 80% - 100% | Highly controlled gaze. Locked-in, confident gaze. |
| `good` | 0.08 - 0.15 | 60% - 80% | Natural gaze behavior. Natural eye contact. |
| `weak` | 0.15 - 0.22 | 40% - 60% | Slightly unstable gaze. Occasional scanning. |
| `poor` | > 0.22 | 0% - 40% | Unsteady or nervous gaze. Frequent darting. |

---

### 3. Smile Activation
| Property | Value |
|----------|-------|
| **What it measures** | How much you smile during your presentation. Captures warmth and approachability through facial expression. |
| **How it's measured** | Measures the width of your mouth (lip corners distance) relative to the distance between your eyes. |
| **Unit** | Ratio (lip width / inter-ocular distance) |
| **Ideal range** | 0.76 - 0.80 |

> **Calibration Update (Numbing Pass):**
> *   **Change:** Raised `SMILE_PROBABILITY_THRESHOLD` from `0.5` to `0.75`.
> *   **Reason:** The model was detecting "ghost smiles" in neutral faces (prob ~0.3). Now requires a distinct smile to register.

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `flat` | < 0.74 | 0% - 40% | Flat or absent smile. Serious, poker face. |
| `neutral` | 0.74 - 0.76 | 40% - 60% | Low smile activation. Professional but reserved. |
| `optimal` | 0.76 - 0.80 | 80% - 100% | Balanced, natural smile. Warm and approachable. |
| `expressive` | > 0.80 | 60% - 80% | Very high smile (Good). Highly radiant. |

---

### 4. Head Down Ratio
| Property | Value |
|----------|-------|
| **What it measures** | How much time your head is tilted downward (reading notes/avoiding audience). |
| **How it's measured** | Percentage of time where head pitch angle exceeds the threshold. |
| **Unit** | Ratio (0-1) |
| **Ideal range** | 0 - 0.10 (lower is better) |

> **Calibration Update (Numbing Pass):**
> *   **Change:** Raised `HEAD_DOWN_ANGLE_THRESHOLD` from `14.0°` to `17.0°`.
> *   **Reason:** The model was flagging natural nodding (10-15°) as "looking down". This relaxes the sensitivity.

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `forward` | < 0.10 | 80% - 100% | Excellent posture. Head facing audience. |
| `occasional_down` | 0.10 - 0.25 | 60% - 80% | Good posture with occasional glances down. |
| `frequent_down` | 0.25 - 0.40 | 40% - 60% | Head often tilted down. |
| `mostly_down` | > 0.40 | 0% - 40% | Head mostly facing down. Avoids audience. |

---

## BODY MODULE

### 5. Gesture Magnitude
| Property | Value |
|----------|-------|
| **What it measures** | How large and expansive your hand gestures are. Captures whether you use confident, space-claiming gestures or keep your hands close to your body. |
| **How it's measured** | Measures how far your wrists are from your torso center, normalized to your shoulder width. |
| **Unit** | SW (Shoulder Widths) |
| **Ideal range** | 1.8 - 3.0 |

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `very_low` | < 1.2 | 0% - 40% | Gestures too small. Hands glued to sides/lap. |
| `low` | 1.2 - 1.8 | 40% - 60% | Small, timid gestures. |
| `optimal` | 1.8 - 3.0 | 80% - 100% | High gesture dynamics. Confident, expansive gestures. |
| `high` | 3.0 - 3.5 | 40% - 60% | Very large, theatrical gestures. |
| `very_high` | > 3.5 | 0% - 40% | Wild, flailing movements. Distracting. |

---

### 6. Gesture Activity
| Property | Value |
|----------|-------|
| **What it measures** | How dynamic and fluid your hand movements are. Captures the speed and energy of your gestures throughout the presentation. |
| **How it's measured** | Tracks how fast your wrists move over time, normalized to your shoulder width and converted to movement per second. |
| **Unit** | SW/sec (Shoulder Widths per second) |
| **Ideal range** | 2.0 - 5.0 |

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `very_low` | < 1.0 | 0% - 40% | Statue-like. No movement. |
| `low` | 1.0 - 2.0 | 40% - 60% | Too static. Slow, lethargic movement. |
| `optimal` | 2.0 - 5.0 | 80% - 100% | Optimal gesture pace. Dynamic, fluid movement. |
| `high` | 5.0 - 7.5 | 40% - 60% | Fast, energetic movement. |
| `very_high` | > 7.5 | 0% - 40% | Chaotic, frantic waving. |

---

### 7. Gesture Stability
| Property | Value |
|----------|-------|
| **What it measures** | How smooth and intentional your gestures are. Captures whether your hand movements are controlled and deliberate versus shaky or fidgety. |
| **How it's measured** | Measures the variance in your gesture speed each second — lower variance means smoother, more intentional movements. |
| **Unit** | Variance of gesture activity per second |
| **Ideal range** | 0 - 5.0 (lower is better) |

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `optimal` | < 5.0 | 80% - 100% | Extremely stable gestures. Smooth, intentional movement. |
| `good` | 5.0 - 12.0 | 60% - 80% | Natural stability. Healthy fluidity. |
| `high` | 12.0 - 20.0 | 40% - 60% | Mild instability. Occasional shaking. |
| `very_high` | > 20.0 | 0% - 40% | Strong jitter / instability. Fidgety hands. |

---

### 8. Body Sway
| Property | Value |
|----------|-------|
| **What it measures** | How much your torso moves side-to-side or back-and-forth. Captures whether you have a grounded, stable presence versus restless rocking. |
| **How it's measured** | Tracks how much your torso center moves over time, normalized to your shoulder width and converted to movement per second. |
| **Unit** | SW/sec (Shoulder Widths per second) |
| **Ideal range** | 0.55 - 1.00 |

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `rigid` | < 0.30 | 0% - 40% | Robotically still. Unnatural. |
| `stable` | 0.30 - 0.55 | 60% - 80% | Grounded, controlled posture. Very grounded. |
| `optimal` | 0.55 - 1.00 | 80% - 100% | Natural controlled movement. Natural, relaxed posture. |
| `unstable` | 1.00 - 1.30 | 40% - 60% | Restless torso movement. Noticeable swaying. |
| `distracting` | > 1.30 | 0% - 40% | Strong body sway. Sea-sickness inducing sway. |

---

### 9. Posture Openness

| Property | Value |
|----------|-------|
| **What it measures** | How open and confident your posture is. This captures whether your arms are open and natural versus closed and defensive. |
| **How it's measured** | A composite score based on arm position and wrist depth. We detect "barrier postures" (arms crossed or close to body with hands forward) vs. open, expressive postures. |
| **Unit** | State (Score 0.2, 0.6, or 1.0) |
| **Ideal range** | Open (Score 1.0) |

**Labels (in order):**
| Label | Score | Description |
|-------|-------|-------------|
| `closed` | 0.2 | Closed, defensive posture. Arms close to body with hands forward. |
| `neutral` | 0.6 | Neutral posture. Arms at rest, hands at sides or behind. |
| `open` | 1.0 | Open, expressive posture. Good use of gestures. |

---

## AUDIO MODULE

### 10. Speech Rate
| Property | Value |
|----------|-------|
| **What it measures** | How fast you speak, measured in words per minute. Captures your pacing and whether it's easy for the audience to follow. |
| **How it's measured** | Transcribes your speech and counts the words, then divides by the speaking time. |
| **Unit** | WPM (Words Per Minute) |
| **Ideal range** | 120 - 170 WPM |

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `very_slow` | < 100 | 0% - 40% | Very slow pace. Can feel heavy or overly deliberate. |
| `slow` | 100 - 120 | 40% - 60% | Slower than typical. Very clear but may lack energy. |
| `optimal` | 120 - 170 | 80% - 100% | Optimal pace. Easy to follow and engaging. |
| `fast` | 170 - 190 | 60% - 80% | Energetic and lively. Good for excitement. |
| `rushed` | 190 - 210 | 40% - 60% | Very fast. Listeners might miss details. |
| `overwhelming` | > 210 | 0% - 40% | Too rapid. Cognitive overload for listeners. |

---

### 11. Pause Ratio
| Property | Value |
|----------|-------|
| **What it measures** | How much silence you use relative to speaking time. Captures your rhythm and use of pauses for emphasis. |
| **How it's measured** | Detects speech versus silence and calculates the percentage of time that is silent. |
| **Unit** | Ratio (0-1) |
| **Ideal range** | 0.04 - 0.08 |

> **Calibration Update (Numbing Pass):**
> *   **Change:** Raised `PAUSE_MIN_DURATION` from `0.5s` to `0.75s`.
> *   **Reason:** The system was counting breaths as pauses. This forces it to only count intentional silence.

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `no_pauses` | < 0.02 | 0% - 40% | Machine-gun delivery. No breathing room. |
| `low_pauses` | 0.02 - 0.04 | 60% - 80% | Fast-flowing speech. Good energy but dense. |
| `optimal` | 0.04 - 0.08 | 80% - 100% | Perfect rhythm. Natural flow with good pacing. |
| `frequent_pauses` | 0.08 - 0.12 | 60% - 80% | Deliberate style. Clear but may lose momentum. |
| `disjointed` | 0.12 - 0.18 | 40% - 60% | Too many pauses. Breaks the flow. |
| `fragmented` | > 0.18 | 0% - 40% | Excessive silence. Sounds hesitant or unprepared. |

---

### 12. Pitch Dynamic
| Property | Value |
|----------|-------|
| **What it measures** | How much your voice pitch varies during your presentation. Captures vocal expressiveness and melodic quality. |
| **How it's measured** | Analyzes your voice frequency and measures how much it rises and falls, expressed in semitones (musical half-steps). |
| **Unit** | Semitones (ST) |
| **Ideal range** | 3.0 - 5.0 ST |

> **Calibration Update (Numbing Pass):**
> *   **Change:** Widened "Monotone" bucket from `< 1.5` to `< 3.0`.
> *   **Reason:** The model was hallucinating expressiveness in robotic voices. We now require significantly more variation to be considered "Neutral" or "Expressive".

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `monotone` | < 3.0 | 0% - 40% | Completely monotone. Hard to listen to. |
| `neutral` | 3.0 - 5.0 | 60% - 80% | Reserved and controlled, but lacks emotion. |
| `expressive` | 5.0 - 7.5 | 80% - 100% | Good expressiveness. Engaging vocal melody. |
| `exaggerated` | > 7.5 | 40% - 60% | Rollercoaster pitch. Can be distracting. |

---

### 13. Volume Dynamic
| Property | Value |
|----------|-------|
| **What it measures** | How much your volume varies during your presentation. Captures emotional texture and emphasis in your delivery. |
| **How it's measured** | Measures the variation in your voice loudness over time, expressed as a coefficient of variation. |
| **Unit** | CV (Coefficient of Variation) |
| **Ideal range** | 0.55 - 0.80 |

> **Calibration Update (Numbing Pass):**
> *   **Change:** Drastically raised the floor for all buckets.
> *   **Old Optimal:** 0.40 - 0.90
> *   **New Optimal:** 0.55 - 0.80
> *   **Reason:** The model treated micro-variations as "Expressive". We now require real dynamic range.

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `flat` | < 0.35 | 0% - 40% | Flat volume. No emotional emphasis. |
| `low` | 0.35 - 0.55 | 40% - 60% | Controlled volume. Polite but could be more dynamic. |
| `optimal` | 0.55 - 0.80 | 80% - 100% | Dynamic delivery. Good emotional texture. |
| `expressive` | 0.80 - 1.20 | 60% - 80% | Highly dynamic. Strong emotional variation. |
| `unstable` | > 1.20 | 0% - 40% | Extreme volume swings. Can be jarring. |

---

### 14. Vocal Punch
| Property | Value |
|----------|-------|
| **What it measures** | How much energy and attack your voice has. Captures the clarity and power of your articulation. |
| **How it's measured** | Measures the ratio between your voice peaks and overall loudness, expressed in decibels (crest factor). |
| **Unit** | dB (Decibels) |
| **Ideal range** | 17.0 - 21.0 dB |

**Labels (in order):**
| Label | Raw Range | Score Tier | Description |
|-------|-----------|------------|-------------|
| `muffled` | < 14.0 | 0% - 40% | Muffled/Flat. Lacks energy and attack. |
| `soft` | 14.0 - 17.0 | 40% - 60% | Gentle delivery. Good for intimacy, bad for power. |
| `optimal` | 17.0 - 21.0 | 80% - 100% | Strong vocal energy. Clear, punchy articulation. |
| `strong` | 21.0 - 24.0 | 60% - 80% | Very punchy. High energy and presence. |
| `aggressive` | > 24.0 | 0% - 40% | Aggressive. Too punchy or shouting. |

---

## Quick Reference: All Labels

| Module | Metric | Labels (ordered worst → best → worst) |
|--------|--------|---------------------------------------|
| Face | head_stability | `rigid` → `stable` → `optimal` → `high` → `distracting` |
| Face | gaze_stability | `optimal` → `good` → `weak` → `poor` |
| Face | smile_activation | `flat` → `neutral` → `optimal` → `excessive` |
| Face | head_down_ratio | `forward` → `occasional_down` → `frequent_down` → `mostly_down` |
| Body | gesture_magnitude | `very_low` → `low` → `optimal` → `high` → `very_high` |
| Body | gesture_activity | `very_low` → `low` → `optimal` → `high` → `very_high` |
| Body | gesture_stability | `optimal` → `good` → `high` → `very_high` |
| Body | body_sway | `rigid` → `stable` → `optimal` → `unstable` → `distracting` |
| Body | posture_openness | `closed` → `constricted` → `optimal` → `good` → `exaggerated` |
| Audio | speech_rate | `very_slow` → `slow` → `optimal` → `fast` → `rushed` → `overwhelming` |
| Audio | pause_ratio | `no_pauses` → `low_pauses` → `optimal` → `frequent_pauses` → `disjointed` → `fragmented` |
| Audio | pitch_dynamic | `monotone` → `neutral` → `expressive` → `exaggerated` |
| Audio | volume_dynamic | `flat` → `low` → `optimal` → `expressive` → `unstable` |
| Audio | vocal_punch | `muffled` → `soft` → `optimal` → `strong` → `aggressive` |
