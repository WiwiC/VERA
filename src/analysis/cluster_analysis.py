"""
Unsupervised Clustering Analysis for VERA (Small-N Strategy)

This script performs clustering on the VERA master vector dataset to identify
communication style personas. It is tailored for small sample sizes (N=23).

Strategy:
1. Feature Selection: 7 high-signal features (Face, Body, Audio).
2. Preprocessing: Z-score outlier removal (>3), StandardScaler.
3. Safety Checks: Correlation (>0.7) and PCA Dominance (>0.45).
4. Clustering: KMeans (K=3, 4) with n_init=50.
5. Validation: Bootstrap Stability (Jaccard Similarity).
6. Output: Personas and Visualizations.
7. Production: Saves trained models (Scaler, KMeans, Personas) to data/models/.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import jaccard_score
from scipy.stats import zscore
from pathlib import Path
import warnings
import joblib
import json

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# =========================================================
# Configuration
# =========================================================

DATA_PATH = Path("data/clustering_dataset/master_vector_data_set.csv")
OUTPUT_DIR = Path("data/clustering_results")
MODELS_DIR = Path("data/models")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# The "Rich Semantic" Set - 7 Features
FEATURES = [
    "body_gesture_activity_mean",   # Energy
    "body_posture_openness_mean",   # Confidence
    "body_body_sway_mean",          # Stability
    "audio_wpm",                    # Pacing
    "face_head_speed_mean",         # Engagement
    "face_smile_mean",              # Warmth
    "audio_pitch_std_st"            # Expressiveness
]

# Safety Thresholds
CORRELATION_THRESHOLD = 0.7
PCA_DOMINANCE_THRESHOLD = 0.45
OUTLIER_Z_THRESHOLD = 3.0

# Clustering Settings
K_VALUES = [3, 4]
N_INIT = 50
BOOTSTRAP_ITERATIONS = 30
BOOTSTRAP_SAMPLE_RATIO = 0.8

# =========================================================
# Helper Functions
# =========================================================

def load_and_preprocess(data_path):
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)

    # Select features
    missing_features = [f for f in FEATURES if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing features in dataset: {missing_features}")

    X = df[FEATURES].copy()
    video_ids = df["video_name"].astype(str)

    # Impute missing values with mean
    if X.isnull().sum().sum() > 0:
        print("⚠️ Imputing missing values with column means.")
        X = X.fillna(X.mean())

    # Outlier Removal (Z-score > 3)
    z_scores = np.abs(zscore(X))
    outliers = (z_scores > OUTLIER_Z_THRESHOLD).any(axis=1)
    if outliers.sum() > 0:
        print(f"⚠️ Removing {outliers.sum()} outliers with Z-score > {OUTLIER_Z_THRESHOLD}")
        X = X[~outliers]
        video_ids = video_ids[~outliers]

    return X, video_ids

def check_safety(X, X_scaled):
    print("\n--- Safety Checks ---")

    # 1. Correlation Check
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    high_corr = [column for column in upper.columns if any(upper[column] > CORRELATION_THRESHOLD)]

    if high_corr:
        print(f"⚠️ High Correlation Detected (> {CORRELATION_THRESHOLD}):")
        for col in high_corr:
            correlated_with = upper.index[upper[col] > CORRELATION_THRESHOLD].tolist()
            print(f"  - {col} correlates with {correlated_with}")
        print("  -> Recommendation: Consider dropping one if stability is low.")
    else:
        print("✅ Correlation Check Passed.")

    # 2. PCA Dominance Check
    pca = PCA(n_components=2)
    pca.fit(X_scaled)

    pc1_loadings = np.abs(pca.components_[0])
    dominant_features = np.where(pc1_loadings > PCA_DOMINANCE_THRESHOLD)[0]

    if len(dominant_features) > 0:
        print(f"⚠️ PCA Dominance Detected (Loading > {PCA_DOMINANCE_THRESHOLD} on PC1):")
        for idx in dominant_features:
            print(f"  - {FEATURES[idx]} (Loading: {pc1_loadings[idx]:.2f})")
        print("  -> Risk: This feature may be driving the entire clustering.")
    else:
        print("✅ PCA Dominance Check Passed.")

def bootstrap_stability(X_scaled, k):
    """
    Compute stability score using Jaccard similarity of cluster assignments
    across bootstrap subsamples.
    """
    n_samples = X_scaled.shape[0]
    n_subsample = int(n_samples * BOOTSTRAP_SAMPLE_RATIO)

    scores = []

    # Base clustering
    kmeans_base = KMeans(n_clusters=k, n_init=N_INIT, random_state=42)
    labels_base = kmeans_base.fit_predict(X_scaled)

    for i in range(BOOTSTRAP_ITERATIONS):
        # Bootstrap indices
        indices = np.random.choice(n_samples, n_subsample, replace=False)
        X_sub = X_scaled[indices]

        # Cluster subsample
        kmeans_sub = KMeans(n_clusters=k, n_init=N_INIT, random_state=i)
        labels_sub = kmeans_sub.fit_predict(X_sub)

        # Compare with base labels (restricted to subsample indices)
        labels_base_sub = labels_base[indices]

        # Jaccard requires matching labels. Since KMeans labels are arbitrary permutations,
        # we can't directly compare.
        # Let's use Adjusted Rand Index (ARI) which is permutation invariant.
        from sklearn.metrics import adjusted_rand_score
        score = adjusted_rand_score(labels_base_sub, labels_sub)
        scores.append(score)

    return np.mean(scores)

def generate_personas(df_original, labels, k):
    """
    Generate persona descriptions based on feature deviations.
    """
    df_labeled = df_original.copy()
    df_labeled['cluster'] = labels

    centroids = df_labeled.groupby('cluster').mean()
    global_mean = df_original.mean()
    global_std = df_original.std()

    personas = {}

    print(f"\n--- Personas (K={k}) ---")
    for cluster_id in range(k):
        centroid = centroids.loc[cluster_id]
        z_scores = (centroid - global_mean) / global_std

        # Find top 2 distinguishing features (highest absolute Z-scores)
        top_features = z_scores.abs().sort_values(ascending=False).head(3)

        desc_parts = []
        for feat in top_features.index:
            z = z_scores[feat]
            direction = "High" if z > 0 else "Low"
            # Clean feature name
            name = feat.replace("body_", "").replace("face_", "").replace("audio_", "").replace("_mean", "").replace("_st", "")
            desc_parts.append(f"{direction} {name}")

        persona_name = ", ".join(desc_parts[:2])
        count = (labels == cluster_id).sum()

        print(f"Cluster {cluster_id} ({count} videos): \"{persona_name}\"")
        print(f"  Key Traits: {', '.join(desc_parts)}")

        # Structure for JSON export
        personas[cluster_id] = {
            "name": persona_name,
            "traits": desc_parts,
            "description": f"Characterized by {', '.join(desc_parts)}."
        }

    return personas

def visualize_clusters(X_scaled, labels, video_ids, k, personas, output_path):
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    explained_var = pca.explained_variance_ratio_.sum()

    plt.figure(figsize=(12, 8))

    # Scatter plot
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=labels, cmap='viridis', s=100, alpha=0.8)

    # Annotate points
    for i, vid in enumerate(video_ids):
        plt.annotate(vid, (X_pca[i, 0], X_pca[i, 1]), xytext=(5, 5), textcoords='offset points', fontsize=8)

    # Annotate centroids (approximate)
    for cluster_id in range(k):
        center = X_pca[labels == cluster_id].mean(axis=0)
        p_name = personas[cluster_id]["name"]
        plt.text(center[0], center[1], f"C{cluster_id}\n{p_name}",
                 fontsize=10, fontweight='bold', ha='center', va='center',
                 bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

    plt.title(f"Cluster Analysis (K={k})\nPCA Explained Variance: {explained_var:.1%}")
    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
    plt.grid(True, alpha=0.3)

    plt.savefig(output_path)
    print(f"✅ Saved plot to {output_path}")
    plt.close()

def save_models(scaler, kmeans, personas, k):
    """Save trained models and artifacts."""
    print(f"\n💾 Saving models for K={k}...")

    # Save Scaler (Global)
    scaler_path = MODELS_DIR / "scaler.pkl"
    joblib.dump(scaler, scaler_path)
    print(f"  - Scaler: {scaler_path}")

    # Save KMeans
    kmeans_path = MODELS_DIR / f"kmeans_k{k}.pkl"
    joblib.dump(kmeans, kmeans_path)
    print(f"  - KMeans: {kmeans_path}")

    # Save Personas
    personas_path = MODELS_DIR / f"personas_k{k}.json"
    # Convert integer keys to strings for JSON compatibility if needed,
    # but json.dump handles int keys by converting to string usually.
    with open(personas_path, "w") as f:
        json.dump(personas, f, indent=4)
    print(f"  - Personas: {personas_path}")

# =========================================================
# Main Execution
# =========================================================

def main():
    print("🚀 Starting Small-N Cluster Analysis...")

    # 1. Load & Preprocess
    X, video_ids = load_and_preprocess(DATA_PATH)
    print(f"Data Loaded: {X.shape[0]} samples, {X.shape[1]} features")

    # Fit Scaler (Global)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 2. Safety Checks
    check_safety(X, X_scaled)

    # 3. Clustering Loop
    for k in K_VALUES:
        print(f"\n--- Analyzing K={k} ---")

        # Fit KMeans
        kmeans = KMeans(n_clusters=k, n_init=N_INIT, random_state=42)
        labels = kmeans.fit_predict(X_scaled)

        # Validation
        stability_score = bootstrap_stability(X_scaled, k)
        print(f"Stability Score (ARI): {stability_score:.2f}")

        if stability_score < 0.6:
            print("⚠️ Warning: Cluster stability is low (< 0.6). Interpret with caution.")

        # Generate Personas
        personas = generate_personas(X, labels, k)

        # Visualize
        output_file = OUTPUT_DIR / f"clusters_k{k}.png"
        visualize_clusters(X_scaled, labels, video_ids, k, personas, output_file)

        # Save Models
        save_models(scaler, kmeans, personas, k)

    print("\n✅ Analysis Complete.")

if __name__ == "__main__":
    main()
