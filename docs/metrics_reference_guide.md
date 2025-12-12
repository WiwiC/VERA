# VERA Metrics Reference Guide

This document describes all 14 metrics analyzed by VERA, their measurement methodology, and the interpretation labels you can use when manually labeling videos.

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
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `rigid` | < 0.60 | Stiff neck. Frozen. |
| `stable` | 0.60 - 1.00 | Very controlled. Serious but attentive. |
| `optimal` | 1.00 - 2.00 | Natural head engagement. Good nodding and tilting. |
| `high` | 2.00 - 3.00 | Active head movement. Engaged but energetic. |
| `distracting` | > 3.00 | Excessive head movement. Bobblehead effect. |

---

### 2. Gaze Stability
| Property | Value |
|----------|-------|
| **What it measures** | How stable and focused your eye contact is. Captures whether you maintain a confident, locked-in gaze versus darting or scanning nervously. |
| **How it's measured** | Measures how much your gaze direction changes each second by tracking iris positions relative to your face. |
| **Unit** | Variance of gaze change per second |
| **Ideal range** | 0 - 0.08 (lower is better) |

**Labels (in order):**
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `optimal` | < 0.08 | Highly controlled gaze. Locked-in, confident gaze. |
| `good` | 0.08 - 0.15 | Natural gaze behavior. Natural eye contact. |
| `weak` | 0.15 - 0.22 | Slightly unstable gaze. Occasional scanning. |
| `poor` | > 0.22 | Unsteady or nervous gaze. Frequent darting. |

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
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `flat` | < 0.74 | Flat or absent smile. Serious, poker face. |
| `neutral` | 0.74 - 0.76 | Low smile activation. Professional but reserved. |
| `optimal` | 0.76 - 0.80 | Balanced, natural smile. Warm and approachable. |
| `expressive` | > 0.80 | Very high smile (Good). Highly radiant. |

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
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `forward` | < 0.10 | Excellent posture. Head facing audience. |
| `occasional_down` | 0.10 - 0.25 | Good posture with occasional glances down. |
| `frequent_down` | 0.25 - 0.40 | Head often tilted down. |
| `mostly_down` | > 0.40 | Head mostly facing down. Avoids audience. |

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
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `very_low` | < 1.2 | Gestures too small. Hands glued to sides/lap. |
| `low` | 1.2 - 1.8 | Small, timid gestures. |
| `optimal` | 1.8 - 3.0 | High gesture dynamics. Confident, expansive gestures. |
| `high` | 3.0 - 3.5 | Very large, theatrical gestures. |
| `very_high` | > 3.5 | Wild, flailing movements. Distracting. |

---

### 6. Gesture Activity
| Property | Value |
|----------|-------|
| **What it measures** | How dynamic and fluid your hand movements are. Captures the speed and energy of your gestures throughout the presentation. |
| **How it's measured** | Tracks how fast your wrists move over time, normalized to your shoulder width and converted to movement per second. |
| **Unit** | SW/sec (Shoulder Widths per second) |
| **Ideal range** | 2.0 - 5.0 |

**Labels (in order):**
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `very_low` | < 1.0 | Statue-like. No movement. |
| `low` | 1.0 - 2.0 | Too static. Slow, lethargic movement. |
| `optimal` | 2.0 - 5.0 | Optimal gesture pace. Dynamic, fluid movement. |
| `high` | 5.0 - 7.5 | Fast, energetic movement. |
| `very_high` | > 7.5 | Chaotic, frantic waving. |

---

### 7. Gesture Stability
| Property | Value |
|----------|-------|
| **What it measures** | How smooth and intentional your gestures are. Captures whether your hand movements are controlled and deliberate versus shaky or fidgety. |
| **How it's measured** | Measures the variance in your gesture speed each second — lower variance means smoother, more intentional movements. |
| **Unit** | Variance of gesture activity per second |
| **Ideal range** | 0 - 5.0 (lower is better) |

**Labels (in order):**
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `optimal` | < 5.0 | Extremely stable gestures. Smooth, intentional movement. |
| `good` | 5.0 - 12.0 | Natural stability. Healthy fluidity. |
| `high` | 12.0 - 20.0 | Mild instability. Occasional shaking. |
| `very_high` | > 20.0 | Strong jitter / instability. Fidgety hands. |

---

### 8. Body Sway
| Property | Value |
|----------|-------|
| **What it measures** | How much your torso moves side-to-side or back-and-forth. Captures whether you have a grounded, stable presence versus restless rocking. |
| **How it's measured** | Tracks how much your torso center moves over time, normalized to your shoulder width and converted to movement per second. |
| **Unit** | SW/sec (Shoulder Widths per second) |
| **Ideal range** | 0.55 - 1.00 |

**Labels (in order):**
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `rigid` | < 0.30 | Robotically still. Unnatural. |
| `stable` | 0.30 - 0.55 | Grounded, controlled posture. Very grounded. |
| `optimal` | 0.55 - 1.00 | Natural controlled movement. Natural, relaxed posture. |
| `unstable` | 1.00 - 1.30 | Restless torso movement. Noticeable swaying. |
| `distracting` | > 1.30 | Strong body sway. Sea-sickness inducing sway. |

---

### 9. Posture Openness
| Property | Value |
|----------|-------|
| **What it measures** | How open and confident your posture is. Captures whether your shoulders are rolled back and open versus hunched forward and closed. |
| **How it's measured** | Measures the angle formed by your shoulders relative to your chest — a wider angle means a more open posture. |
| **Unit** | Degrees |
| **Ideal range** | 50° - 58° |

**Labels (in order):**
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `closed` | < 46° | Closed, collapsed posture. Strong inward rotation. |
| `constricted` | 46° - 50° | Slightly constricted posture. Shoulders rolled forward. |
| `optimal` | 50° - 58° | Optimal posture. Confident and approachable. |
| `good` | 58° - 65° | Open posture. Slightly expansive. |
| `exaggerated` | > 65° | Exaggerated openness. May look unnatural or stiff. |

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
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `very_slow` | < 100 | Very slow pace. Can feel heavy or overly deliberate. |
| `slow` | 100 - 120 | Slower than typical. Very clear but may lack energy. |
| `optimal` | 120 - 170 | Optimal pace. Easy to follow and engaging. |
| `fast` | 170 - 190 | Energetic and lively. Good for excitement. |
| `rushed` | 190 - 210 | Very fast. Listeners might miss details. |
| `overwhelming` | > 210 | Too rapid. Cognitive overload for listeners. |

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
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `no_pauses` | < 0.02 | Machine-gun delivery. No breathing room. |
| `low_pauses` | 0.02 - 0.04 | Fast-flowing speech. Good energy but dense. |
| `optimal` | 0.04 - 0.08 | Perfect rhythm. Natural flow with good pacing. |
| `frequent_pauses` | 0.08 - 0.12 | Deliberate style. Clear but may lose momentum. |
| `disjointed` | 0.12 - 0.18 | Too many pauses. Breaks the flow. |
| `fragmented` | > 0.18 | Excessive silence. Sounds hesitant or unprepared. |

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
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `monotone` | < 3.0 | Completely monotone. Hard to listen to. |
| `neutral` | 3.0 - 5.0 | Reserved and controlled, but lacks emotion. |
| `expressive` | 5.0 - 7.5 | Good expressiveness. Engaging vocal melody. |
| `exaggerated` | > 7.5 | Rollercoaster pitch. Can be distracting. |

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
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `flat` | < 0.35 | Flat volume. No emotional emphasis. |
| `low` | 0.35 - 0.55 | Controlled volume. Polite but could be more dynamic. |
| `optimal` | 0.55 - 0.80 | Dynamic delivery. Good emotional texture. |
| `expressive` | 0.80 - 1.20 | Highly dynamic. Strong emotional variation. |
| `unstable` | > 1.20 | Extreme volume swings. Can be jarring. |

---

### 14. Vocal Punch
| Property | Value |
|----------|-------|
| **What it measures** | How much energy and attack your voice has. Captures the clarity and power of your articulation. |
| **How it's measured** | Measures the ratio between your voice peaks and overall loudness, expressed in decibels (crest factor). |
| **Unit** | dB (Decibels) |
| **Ideal range** | 17.0 - 21.0 dB |

**Labels (in order):**
| Label | Raw Range | Description |
|-------|-----------|-------------|
| `muffled` | < 14.0 | Muffled/Flat. Lacks energy and attack. |
| `soft` | 14.0 - 17.0 | Gentle delivery. Good for intimacy, bad for power. |
| `optimal` | 17.0 - 21.0 | Strong vocal energy. Clear, punchy articulation. |
| `strong` | 21.0 - 24.0 | Very punchy. High energy and presence. |
| `aggressive` | > 24.0 | Aggressive. Too punchy or shouting. |

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
