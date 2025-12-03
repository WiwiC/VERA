Here is the **entire README.md as a single, clean, ready-to-paste Markdown file** — no code fences, no fragmentation, no separation.

You can paste **exactly this** into your `README.md`.

---

# **VERA — Multimodal Communication Analysis (MVP: Face Module)**

**VERA** (Vocal, Expressive & Relational Analyzer) is an AI system that evaluates how a person communicates during a pitch, interview, or presentation.
This MVP implements the **facial analysis pipeline**, using Mediapipe FaceMesh to extract objective behavioral metrics and compute scientifically grounded communication scores.

Future modules (audio & body language) will integrate into the same architecture.

---

## 🚀 Project Goal

The objective of VERA is to build a **multimodal communication analytics system** that:

* Extracts **objective, measurable** behavioral signals
* Computes **temporal metrics** linked to communication quality
* Produces **interpretable communication scores**
* Enables **clustering** of communication styles
* Serves as the foundation for an **LLM-based coaching agent**

No emotion decoding.
No psychological inference.
Only **geometric, reproducible, explainable data.**

This project is developed as part of a **Le Wagon Data Science & AI Bootcamp** final sprint.

---

## 📦 Current Status (MVP)

### ✔ Face Module — Complete

* Mediapipe landmark extraction (20 stable points)
* Head Stability (jitter)
* Gaze Consistency (eye vector jitter)
* Smile Activation (lip corner distance)
* 1-second and 5-second sliding window aggregation
* z-score + sigmoid scoring
* Global facial communication score
* Debug video overlay
* Exported **face feature vector** (for ML + clustering)

### 🚧 In Progress

* Audio analysis
* Body language analysis
* Multimodal fusion
* Dataset-level normalization
* Clustering + communication archetypes
* LLM coaching agent

---

## 📁 Project Structure

```
VERA/
│
├── data/
│   ├── raw/                # input videos
│   └── processed/          # debug videos, metrics, vectors
│
├── notebooks/
│   └── 01_facemesh_extraction.ipynb  # testing notebook
│
├── src/
│   ├── face/
│   │   ├── extraction.py         # landmark extraction + raw features
│   │   ├── landmarks.py          # landmark IDs + utilities
│   │   ├── metrics.py            # jitter, windows, z-normalization
│   │   ├── scoring.py            # scoring formulas
│   │   ├── pipeline.py           # full face pipeline
│   │   └── visualization.py      # facemesh overlay video
│   │
│   ├── audio/                    # placeholder
│   └── body/                     # placeholder
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🧠 Methodology

### 1) Landmark Extraction (Mediapipe FaceMesh)

We use only ~20 stable points to reduce noise:

* **Head stability** → ears (234, 454)
* **Gaze consistency** → irises (468, 473) + nose (1)
* **Smile activation** → lip corners (61, 291)

This improves robustness and simplifies the pipeline.

---

### 2) Frame-Level Feature Extraction

| Feature              | What It Measures          | Formula |   |                         |   |   |
| -------------------- | ------------------------- | ------- | - | ----------------------- | - | - |
| **Head Stability**   | micro-instability         | `       |   | center[t] - center[t-1] |   | ` |
| **Gaze Consistency** | smoothness of gaze vector | `       |   | gaze[t] - gaze[t-1]     |   | ` |
| **Smile Activation** | smile intensity           | `       |   | lip_left - lip_right    |   | ` |

Each frame is appended into a DataFrame with timestamps.

---

### 3) 1-Second Aggregation

Frames are grouped into 1-second bins using:

```
df["second"] = df.index.astype(int)
```

Then:

* Head Stability → variance of head speed
* Gaze Consistency → variance of gaze change vector
* Smile Activation → mean smile intensity

---

### 4) 5-Second Sliding Windows

We use sliding windows:

* 0–5
* 1–6
* 2–7
* …

This stabilizes noise and reflects communication rhythm.

Each window produces:

* `jitter_5s`
* `smile_5s`

---

### 5) Scoring (z-normalization + sigmoid)

Metric normalization:

```
z = (x - mean) / std
score = sigmoid(z)
```

For stability metrics → lower jitter = higher score:

```
score = 1 / (1 + sigmoid(z))
```

This ensures all metrics are comparable.

---

### 6) Global Face Score (equal weights for MVP)

Because we do not yet have a dataset to learn real weights:

```
Face Score = (Head + Gaze + Smile) / 3
```

The score is returned as:

* `scores`
* `face_vector`
* `face_vector_array` (compact numeric list)

---

## 📤 Pipeline Outputs

Running the pipeline returns:

```
{
  "scores": {
      "head_stability": 0.xx,
      "gaze_consistency": 0.xx,
      "smile_activation": 0.xx,
      "face_global_score": 0.xx
  },
  "face_vector": {
      "head_stability": ...,
      "gaze_consistency": ...,
      "smile_activation": ...,
      "face_global_score": ...
  },
  "face_vector_array": [0.xx, 0.xx, 0.xx, 0.xx],
  "head_jitter_5s": ...,
  "gaze_jitter_5s": ...,
  "smile_5s": ...,
  "raw_frames": df
}
```

A facemesh debug video is also generated:

```
data/processed/debug_facemesh.mp4
```

---

## ▶️ How to Run the Face Pipeline

### 1. Add your video

```
data/raw/myvideo.mp4
```

### 2. Activate environment

```
source VERA-env/bin/activate
```

### 3. Run analysis

```
from src.face.pipeline import run_face_pipeline

result = run_face_pipeline("data/raw/myvideo.mp4")

print(result["scores"])
result["face_vector"]
```

### 4. Generate facemesh overlay

```
from src.face.visualization import draw_facemesh_video

draw_facemesh_video(
    "data/raw/myvideo.mp4",
    "data/processed/debug.mp4"
)
```

---

## 📊 Roadmap

### 🟦 Audio Module

* Speech rate (WPM)
* Pause ratio
* Pitch variation (F0)
* Volume stability (RMS)

### 🟩 Body Module

* Gesture magnitude
* Gesture activity rate
* Body sway
* Posture openness

### 🟧 Multimodal Fusion

Merge:

```
face_vector + audio_vector + body_vector
```

### 🟥 Clustering

KMeans clustering to identify communication archetypes:

* Controlled & Clear
* Engaging & Dynamic
* Restless
* Low-Energy / Monotone

### 🟪 Coaching Agent

LLM-based interpretation:

* Style analysis
* Strengths & weaknesses
* Actionable recommendations

---

## 🤝 Authors

Developed by a team of three Data Science students at **Le Wagon**,
as part of the 10-day final project sprint.

---

## 📄 License

MIT License.

---

If you want, I can also generate:

* A GitHub banner
* An architecture diagram (SVG)
* A dataset schema for clustering
* Badges (Python, Mediapipe, License, etc.)
