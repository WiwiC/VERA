import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.face.pipeline import run_face_pipeline

def test_pipeline():
    video_path = "data/raw/myvideo.mp4"
    output_dir = "data/processed/test_run_face_myvideo"

    # Clean up previous run
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)

    print(f"Testing pipeline on {video_path}...")
    try:
        scores = run_face_pipeline(video_path, output_dir=output_dir)

        print("\n--- Pipeline Results ---")
        print(scores)

        # Verify outputs
        # Verify outputs
        out_path = Path(output_dir)
        assert (out_path / "metrics_face.csv").exists(), "metrics_face.csv missing"
        assert (out_path / "results_face.json").exists(), "results_face.json missing"
        assert (out_path / "debug_face.mp4").exists(), "debug_face.mp4 missing"

        print("\n✅ Verification SUCCESS: All output files created.")

    except Exception as e:
        print(f"\n❌ Verification FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
