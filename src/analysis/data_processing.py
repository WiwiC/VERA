"""
Clustering Data Processing Module.

This module handles the transformation of raw extraction outputs (Audio, Body, Face)
into a single feature vector for clustering analysis. It updates a master dataset
CSV with the new vector.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path

MASTER_DATASET_PATH = Path("data/clustering_dataset/master_vector_data_set.csv")

def update_master_dataset(video_name, processed_dir):
    """
    Process raw data for a video and update the master clustering dataset.

    Args:
        video_name (str): Name of the video (used as identifier).
        processed_dir (str or Path): Directory containing the raw CSV files.
    """
    processed_dir = Path(processed_dir)
    print(f"📊 Processing data for clustering: {video_name}")

    # 1. Load Raw Data
    # Body: Use 1s timeline (contains computed scores like Posture Openness)
    body_path = processed_dir / "1s_raw_timeline_body.csv"
    face_path = processed_dir / "df_Face_raw_data.csv"
    audio_path = processed_dir / "df_Audio_raw_data.csv"

    if not (body_path.exists() and face_path.exists() and audio_path.exists()):
        print(f"⚠️ Missing data files in {processed_dir}. Skipping clustering update.")
        return

    try:
        df_body = pd.read_csv(body_path)
        df_face = pd.read_csv(face_path)
        df_audio = pd.read_csv(audio_path)
    except Exception as e:
        print(f"❌ Error reading CSV files: {e}")
        return

    # 2. Clean Data
    # Drop first row (often empty/initialization artifacts)
    # Note: 1s timeline doesn't have initialization artifacts usually, but safe to keep check
    if len(df_face) > 1:
        df_face = df_face.iloc[1:].reset_index(drop=True)

    # Drop non-feature columns
    cols_to_drop = ["timestamp", "second"]
    df_body = df_body.drop(columns=[c for c in cols_to_drop if c in df_body.columns], errors='ignore')
    df_face = df_face.drop(columns=[c for c in cols_to_drop if c in df_face.columns], errors='ignore')

    # 3. Feature Extraction (Mean & Variance)
    features = {"video_name": video_name}

    # Body Features
    for col in df_body.columns:
        # Check if column is numeric
        if pd.api.types.is_numeric_dtype(df_body[col]):
            features[f"body_{col}_mean"] = df_body[col].mean()
            features[f"body_{col}_var"] = df_body[col].var()

    # Face Features
    for col in df_face.columns:
        if pd.api.types.is_numeric_dtype(df_face[col]):
            features[f"face_{col}_mean"] = df_face[col].mean()
            features[f"face_{col}_var"] = df_face[col].var()

    # Audio Features (Direct copy)
    for col in df_audio.columns:
        if pd.api.types.is_numeric_dtype(df_audio[col]):
             features[f"audio_{col}"] = df_audio[col].iloc[0]

    # 4. Update Master Dataset
    # Ensure directory exists
    MASTER_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)

    if MASTER_DATASET_PATH.exists():
        try:
            master_df = pd.read_csv(MASTER_DATASET_PATH)
        except pd.errors.EmptyDataError:
            print(f"⚠️ Master dataset at {MASTER_DATASET_PATH} is empty. Creating new one.")
            master_df = pd.DataFrame()
    else:
        master_df = pd.DataFrame()

    # Remove existing entry for this video if it exists (to overwrite)
    if "video_name" in master_df.columns:
        # Convert to string for consistent comparison (CSV may store as int)
        master_df["video_name"] = master_df["video_name"].astype(str)
        master_df = master_df[master_df["video_name"] != str(video_name)]

    # Append new row
    row_df = pd.DataFrame([features])
    master_df = pd.concat([master_df, row_df], ignore_index=True)

    # Save
    master_df.to_csv(MASTER_DATASET_PATH, index=False)
    print(f"✅ Master dataset updated: {MASTER_DATASET_PATH}")
    print(f"   Total samples: {len(master_df)}")

if __name__ == "__main__":
    # Test run
    import sys
    if len(sys.argv) > 2:
        update_master_dataset(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python src/analysis/data_processing.py <video_name> <processed_dir>")
