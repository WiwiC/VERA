# **VERA — Multimodal Communication Analysis**

**VERA** (Vocal, Expressive & Relational Analyzer) is an AI system that evaluates how a person communicates during a pitch, interview, or presentation.

VERA is built on the core philosophy that effective communication consists of **three equally important dimensions**:

1.  **🗣️ Voice (Audio)**: *How* you say it (tone, pace, volume).
2.  **👤 Face (Expression)**: Your facial engagement and stability.
3.  **🧍 Body (Non-Verbal)**: Your posture, gestures, and presence.

By analyzing these three dimensions in parallel, VERA extracts objective, measurable behavioral metrics to produce interpretable scores and actionable feedback without psychological inference.

---

## 🚀 Project Goal

The objective of VERA is to build a **multimodal communication analytics system** that:

*   Extracts **objective behavioral signals** from video input across all three dimensions.
*   Computes **temporal metrics** linked to communication quality.
*   Aggregates data into a **Master Feature Vector** for clustering and style analysis.
*   Serves as the foundation for an **LLM-based coaching agent**.

---

## 📦 The 3 Dimensions of Analysis

VERA analyzes communication through three dedicated, parallel pipelines. Each module contains its own extraction and scoring logic:

### 1. 🗣️ Voice (Audio Module)
*Located in `src/audio/`*
Analyzes speech patterns and vocal delivery.
*   **Speech Rate**: Words Per Minute (WPM) using `faster_whisper`.
*   **Pauses**: Silence duration and ratio using `webrtcvad`.
*   **Pitch**: Mean frequency (Hz) and variation (semitones) using `librosa`.
*   **Volume**: Loudness (LUFS) and stability (CV).

### 2. 👤 Face (Face Module)
*Located in `src/face/`*
Analyzes facial expressions and engagement.
*   **Tech**: Mediapipe FaceMesh (468 landmarks).
*   **Head Stability**: Micro-movements and jitter.
*   **Gaze Consistency**: Eye contact stability.
*   **Smile Activation**: Intensity and frequency of smiles.

### 3. 🧍 Body (Body Module)
*Located in `src/body/`*
Analyzes non-verbal body language and posture.
*   **Tech**: Mediapipe Holistic.
*   **Gesture Magnitude**: Expansiveness of hand movements.
*   **Gesture Activity**: Speed and frequency of gestures.
*   **Body Sway**: Torso stability and movement.
*   **Posture Openness**: Shoulder and chest expansion.

---

## ⚙️ Architecture

The system is designed for performance and modularity:

1.  **Orchestrator (`src/main.py`)**:
    *   Runs the Audio, Body, and Face pipelines in **parallel** using `ProcessPoolExecutor`.
    *   Ensures efficient utilization of system resources.

2.  **Aggregation Layer (`src/analysis`)**:
    *   Runs *after* the three modules have finished.
    *   Aggregates frame-by-frame metrics from all three modules.
    *   Computes statistical features (mean, variance).
    *   Updates a **Master Dataset** (`data/clustering_dataset/master_vector_data_set.csv`) for downstream machine learning tasks.

---

## 📁 Project Structure

The codebase is organized into three parallel analysis modules and one aggregation layer:

```
VERA/
│
├── data/
│   ├── raw/                # Input videos
│   ├── processed/          # Output results (JSON, CSV, Debug Videos)
│   └── clustering_dataset/ # Aggregated feature vectors
│
├── src/
│   │   # --- The 3 Analysis Modules ---
│   ├── audio/              # Audio extraction & scoring
│   ├── body/               # Body language extraction & scoring
│   ├── face/               # Face extraction & scoring
│   │
│   │   # --- Aggregation Layer ---
│   ├── analysis/           # Combines results from all 3 modules
│   │
│   └── main.py             # Orchestrator (Runs modules in parallel)
│
├── requirements.txt
└── README.md
```

---

## ▶️ How to Run

### 1. Setup Environment
```bash
pip install -r requirements.txt
```

### 2. Run Analysis
You can run the full multimodal pipeline on a video file:

```bash
python src/main.py path/to/your/video.mp4
```

### 3. Check Results
Results are saved in `data/processed/<video_name>/`:
*   `results_global.json`: Summary of all scores.
*   `debug_facemesh.mp4`: Video with facial landmarks.
*   `debug_pose.mp4`: Video with body skeletal tracking.
*   `metrics_*.csv`: Detailed frame-by-frame data.

---

## 📊 Outputs

Running the pipeline returns a global JSON object:

```json
{
  "meta": {
    "duration_sec": 12.5
  },
  "audio": {
    "wpm": 145.2,
    "pitch_mean_hz": 120.5,
    "volume_lufs": -14.2
  },
  "face": {
    "head_stability": 0.85,
    "gaze_stability": 0.92,
    "smile_activation": 0.45
  },
  "body": {
    "gesture_magnitude": 1.2,
    "posture_openness": 0.88
  }
}
```

---

## 🤝 Authors:
