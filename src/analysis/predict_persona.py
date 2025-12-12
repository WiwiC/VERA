"""
Persona Prediction Module for VERA.

Loads the pre-trained clustering model (Scaler + KMeans) and assigns a persona
to a new video based on its extracted features.
"""

import joblib
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Paths
MODELS_DIR = Path("data/models")
SCALER_PATH = MODELS_DIR / "scaler.pkl"
KMEANS_PATH = MODELS_DIR / "kmeans_k3.pkl"
PERSONAS_PATH = MODELS_DIR / "personas_k3.json"

# Feature Mapping: Model Feature Name -> (Module, Result Key)
FEATURE_MAPPING = {
    "body_gesture_activity_mean": ("body", "gesture_activity_val"),
    "body_posture_openness_mean": ("body", "posture_openness_val"),
    "body_body_sway_mean": ("body", "body_sway_val"),
    "audio_wpm": ("audio", "speech_rate_val"),
    "face_head_speed_mean": ("face", "head_stability_val"),
    "face_smile_mean": ("face", "smile_activation_val"),
    "audio_pitch_std_st": ("audio", "pitch_dynamic_val")
}

# Ordered list of features expected by the model (MUST MATCH TRAINING ORDER)
MODEL_FEATURES = [
    "body_gesture_activity_mean",
    "body_posture_openness_mean",
    "body_body_sway_mean",
    "audio_wpm",
    "face_head_speed_mean",
    "face_smile_mean",
    "audio_pitch_std_st"
]

_model_cache = {}

def load_models():
    """Load and cache models."""
    global _model_cache
    if not _model_cache:
        print("Loading clustering models...")
        try:
            _model_cache["scaler"] = joblib.load(SCALER_PATH)
            _model_cache["kmeans"] = joblib.load(KMEANS_PATH)
            with open(PERSONAS_PATH) as f:
                _model_cache["personas"] = json.load(f)
        except FileNotFoundError as e:
            print(f"❌ Model file not found: {e}")
            return None
    return _model_cache

def predict_persona(global_results):
    """
    Predict the communication persona for a video.

    Args:
        global_results (dict): The flat results dictionary from main.py.

    Returns:
        dict: The predicted persona (name, description, traits) or None if error.
    """
    models = load_models()
    if not models:
        return None

    # 1. Extract Features
    feature_vector = []
    for feat_name in MODEL_FEATURES:
        module, key = FEATURE_MAPPING[feat_name]

        # Safe extraction
        val = global_results.get(module, {}).get(key)

        if val is None:
            print(f"⚠️ Missing feature for prediction: {module}.{key}")
            # Fallback: Use 0 or mean?
            # Since we use StandardScaler, 0 is the mean of the training set.
            # So 0 is a safe neutral fallback.
            val = 0.0

        feature_vector.append(float(val))

    # 2. Normalize
    X = np.array([feature_vector]) # Shape (1, 7)
    X_scaled = models["scaler"].transform(X)

    # 3. Predict Cluster
    cluster_id = models["kmeans"].predict(X_scaled)[0]

    # 4. Get Persona Info
    # JSON keys are strings, convert cluster_id to string
    persona = models["personas"].get(str(cluster_id))

    if not persona:
        print(f"❌ Persona not found for cluster {cluster_id}")
        return None

    return {
        "cluster_id": int(cluster_id),
        "name": persona["name"],
        "description": persona["description"],
        "traits": persona["traits"]
    }
