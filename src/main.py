"""
VERA Main Orchestrator
Runs Audio, Body, and Face pipelines in parallel for a given video
"""

import sys
import os
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.audio.pipeline import run_audio_pipeline
from src.body.pipeline import run_body_pipeline
from src.face.pipeline import run_face_pipeline

def run_wrapper(pipeline_func, video_path, output_dir):
    """
    Wrapper to run a pipeline function and catch errors.
    """
    try:
        return pipeline_func(video_path, output_dir)
    except Exception as e:
        print(f"❌ Error in {pipeline_func.__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    if len(sys.argv) < 2:
        print("Usage: python src/main.py <video_path>")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        sys.exit(1)

    # Create output directory
    output_dir = Path("data/processed") / video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Starting VERA Analysis for: {video_path.name}")
    print(f"📂 Output directory: {output_dir}")

    start_time = time.time()

    # Run pipelines in parallel
    results = {}

    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(run_wrapper, run_audio_pipeline, str(video_path), str(output_dir)): "audio",
            executor.submit(run_wrapper, run_body_pipeline, str(video_path), str(output_dir)): "body",
            executor.submit(run_wrapper, run_face_pipeline, str(video_path), str(output_dir)): "face"
        }

        for future in as_completed(futures):
            module = futures[future]
            try:
                res = future.result()
                results[module] = res
                print(f"✅ {module.capitalize()} module finished.")
            except Exception as e:
                print(f"❌ {module.capitalize()} module failed: {e}")
                results[module] = {}

    # Aggregate Global Results
    global_results = {
        "meta": {
            "video_path": str(video_path),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_sec": time.time() - start_time
        },
        "audio": results.get("audio", {}),
        "body": results.get("body", {}),
        "face": results.get("face", {})
    }

    # Save Global Results
    global_path = output_dir / "results_global.json"
    with open(global_path, "w") as f:
        json.dump(global_results, f, indent=4)

    print("\n" + "="*50)
    print(f"🎉 Analysis Completed in {global_results['meta']['duration_sec']:.2f}s")
    print(f"📄 Global Results: {global_path}")
    print("="*50)

if __name__ == "__main__":
    main()
