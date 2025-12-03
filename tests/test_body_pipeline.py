import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.body.pipeline import run_body_pipeline

def test_pipeline():
    video_path = "data/raw/myvideo.mp4"
    output_dir = "data/processed/test_run_body"

    # Clean up previous run
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)

    print(f"Testing body pipeline on {video_path}...")
    try:
        scores = run_body_pipeline(video_path, output_dir=output_dir)

        print("\n--- Pipeline Results ---")
        print(scores)

        # Verify outputs
        out_path = Path(output_dir)
        assert (out_path / "metrics_body.csv").exists(), "metrics_body.csv missing"
        assert (out_path / "results_body.json").exists(), "results_body.json missing"
        assert (out_path / "debug_pose.mp4").exists(), "debug_pose.mp4 missing"

        print("\n✅ Verification SUCCESS: All output files created.")

    except Exception as e:
        print(f"\n❌ Verification FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
