"""
Unified VERA Orchestrator
- Can be used from Streamlit via run_pipelines(video_path)
- Can be executed as a CLI tool: python src/main.py <video_path>
"""

import sys
import os
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Allow running directly as a script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.audio.pipeline import run_audio_pipeline
from src.body.pipeline import run_body_pipeline
from src.face.pipeline import run_face_pipeline
from src.analysis.data_processing import update_master_dataset
from src.presentation.enrich import enrich_results


def run_wrapper(pipeline_func, video_path, output_dir):
    """Wrapper to safely run a pipeline and catch errors."""
    try:
        return pipeline_func(video_path, output_dir)
    except Exception as e:
        print(f"❌ Error in {pipeline_func.__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {}


def run_pipelines(video_path):
    """
    Runs audio, body, and face pipelines in parallel.
    Returns (output_dir, results_dict).
    Suitable for Streamlit or any external caller.
    """

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"❌ Video not found: {video_path}")

    # Create output directory
    output_dir = Path("data/processed") / video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Starting VERA Analysis for: {video_path.name}")
    print(f"📂 Output directory: {output_dir}")

    start_time = time.time()
    results = {}

    # Run pipelines in parallel
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(run_wrapper, run_audio_pipeline, str(video_path), str(output_dir)): "audio",
            executor.submit(run_wrapper, run_body_pipeline, str(video_path), str(output_dir)): "body",
            executor.submit(run_wrapper, run_face_pipeline, str(video_path), str(output_dir)): "face",
        }

        for future in as_completed(futures):
            module = futures[future]
            try:
                results[module] = future.result()
                print(f"✅ {module.capitalize()} module finished.")
            except Exception as e:
                print(f"❌ {module.capitalize()} module failed: {e}")
                results[module] = {}

    # Build global results (flat structure)
    global_results = {
        "meta": {
            "video_path": str(video_path),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_sec": time.time() - start_time,
        },
        "audio": results.get("audio", {}),
        "body": results.get("body", {}),
        "face": results.get("face", {}),
    }

    # Save original flat results
    global_results_path = output_dir / "results_global.json"
    with open(global_results_path, "w") as f:
        json.dump(global_results, f, indent=4)

    # Create enriched version (nested structure with context)
    enriched_results = enrich_results(global_results)
    enriched_results_path = output_dir / "results_global_enriched.json"
    with open(enriched_results_path, "w") as f:
        json.dump(enriched_results, f, indent=4)

    # Update Clustering Dataset
    print("\n--- Clustering Data Update ---")
    video_name = video_path.stem
    update_master_dataset(video_name, output_dir)

    print("\n" + "=" * 50)
    print(f"🎉 Analysis Completed in {global_results['meta']['duration_sec']:.2f}s")
    print(f"📄 Results saved at: {global_results_path}")
    print(f"📄 Enriched results saved at: {enriched_results_path}")
    print("=" * 50)

    return output_dir, results



def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python src/main.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    try:
        run_pipelines(video_path)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
