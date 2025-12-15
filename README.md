# VERA (Vocal - Expression & Reaction Analysis)

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

**VERA** is an advanced multi-modal AI pipeline designed to analyze communication performance. It processes video input to evaluate **Face** (micro-expressions, gaze), **Body** (posture, gestures), and **Audio** (tonality, pacing) metrics. By leveraging computer vision and audio signal processing, VERA provides objective, data-driven feedback to help users improve their communication skills.

---

## 🚀 Key Features

*   **Multi-Modal Analysis:** Parallel processing of visual signals (using MediaPipe) and auditory signals (using Librosa) for a holistic view of performance.
*   **14 Core Metrics:** Comprehensive tracking of engagement indicators across three dimensions:
    *   **Face:** Head Stability, Gaze Stability, Smile Activation, Head Down Ratio.
    *   **Body:** Gesture Magnitude, Gesture Activity, Gesture Stability, Body Sway, Posture Openness.
    *   **Audio:** Speech Rate, Pause Ratio, Pitch Dynamic, Volume Dynamic, Vocal Punch.
*   **Persona K-means Clustering:** Automatically assigns a "Communication Persona" based on high-dimensional metric clusters (Unsupervised ML)
*   **Rich Visualization:** Generates debug videos with skeletal overlays and facial landmarks to visualize exactly what the AI sees.

---

## ⚙️ How It Works

The VERA pipeline follows a rigorous scientific approach to analysis:

1.  **Extraction:** The video is processed frame-by-frame to extract raw landmarks (x, y, z coordinates) and audio features.
2.  **Aggregation:** Raw data is aggregated into 1-second chunks and smoothed using a 5-second sliding window to identify trends.
3.  **Scoring:** Aggregated values are compared against empirically calibrated baselines using a **Tiered Parabolic Scoring** system.
4.  **Enrichment:** Scores are merged with coaching text and interpretation labels from the `metrics_spec.json` schema to generate human-readable insights.

---

## 🛠️ Installation

### Prerequisites
*   Python 3.10+
*   `ffmpeg` (required for audio processing)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/vera.git
cd vera

# Create a virtual environment
python -m venv VERA-env
source VERA-env/bin/activate  # or VERA-env\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 Usage

### Run Analysis (CLI)
To analyze a single video file:

```bash
python src/main.py path/to/video.mp4
```

The output will be generated in `data/processed/<video_name>/`.

### Run Dashboard (UI)
To visualize the results in an interactive dashboard:

```bash
streamlit run video-analyzer-app/app.py
```

### Run API (FastAPI)
To start the backend API server:

```bash
uvicorn src.api.fast:app --reload
```
The API will be available at `http://localhost:8000`.


---

## 📊 Metrics Guide

| Module | Metric | Description | Ideal Range |
| :--- | :--- | :--- | :--- |
| **Face** | `head_stability` | Measures how steady the head is (nodding vs. frozen). |
| **Face** | `gaze_stability` | Tracks focus and eye contact stability. |
| **Face** | `smile_activation` | Measures the width/presence of smiles. |
| **Face** | `head_down_ratio` | Percentage of time looking down (reading notes). |
| **Body** | `gesture_magnitude` | Measures how expansive/large gestures are. |
| **Body** | `gesture_activity` | Measures the speed and frequency of gestures. |
| **Body** | `gesture_stability` | Measures the smoothness of hand movements. |
| **Body** | `body_sway` | Tracks torso movement (rocking vs. grounded). |
| **Body** | `posture_openness` | Measures how open the chest/shoulders are. |
| **Audio** | `speech_rate` | Words per minute (WPM). |
| **Audio** | `pause_ratio` | Ratio of silence to speech. |
| **Audio** | `pitch_dynamic` | Variation in voice pitch (semitones). |
| **Audio** | `volume_dynamic` | Variation in voice loudness. |
| **Audio** | `vocal_punch` | Ratio of peak volume to average (clarity). |

---

## 🔧 Configuration

VERA is designed to be highly configurable:

*   **`src/schemas/metrics_spec.json`**: The **Source of Truth**. Edit this file to change metric display names, coaching tips, or interpretation text. Changes here automatically reflect in the UI.
*   **`src/*/config.py`**: Edit these files (e.g., `src/audio/config.py`) to adjust the numerical baselines, scoring tiers, and thresholds.

## 📂 Output Format

*   **`results_global_enriched.json`**: The primary output file. Contains nested JSON with scores, raw values, labels, and coaching tips for every metric.
*   **`metrics_*.csv`**: Detailed time-series data for deep-dive analysis.
*   **`debug_*.mp4`**: Video files with visual overlays showing the AI's tracking performance.
