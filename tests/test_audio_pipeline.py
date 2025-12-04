import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.audio.pipeline import run_audio_pipeline

def test_pipeline():
    video_path = "data/raw/myvideo.mp4"
    output_dir = "data/processed/test_run_audio_myvideo"

    # Clean up previous run
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)

    # Run Pipeline
    scores = run_audio_pipeline(video_path, output_dir)

    # Verify Outputs
    assert os.path.exists(f"{output_dir}/metrics_audio.csv"), "Metrics CSV not created"
    assert os.path.exists(f"{output_dir}/results_audio.json"), "Results JSON not created"

    # Verify Scores
    assert "audio_global_score" in scores, "Global score missing"
    assert 0.0 <= scores["audio_global_score"] <= 1.0, "Global score out of range"

    print("\n✅ Verification SUCCESS: All output files created.")

if __name__ == "__main__":
    test_pipeline()
