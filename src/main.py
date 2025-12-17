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
from src.analysis.predict_persona import predict_persona


def run_wrapper(pipeline_func, video_path, output_dir):
    """Wrapper to safely run a pipeline and catch errors."""
    try:
        return pipeline_func(video_path, output_dir)
    except Exception as e:
        print(f"❌ Error in {pipeline_func.__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {}


def run_pipelines_iterator(video_path, output_base_dir="data/processed", progress_callback=None):
    """
    Generator that yields progress updates during pipeline execution.
    Yields:
        ("start", output_dir)
        ("progress", module_name, result)
        ("error", module_name, exception)
        ("final", output_dir, results_dict)
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"❌ Video not found: {video_path}")

    # Create output directory
    output_dir = Path(output_base_dir) / video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Starting VERA Analysis for: {video_path.name}")
    print(f"📂 Output directory: {output_dir}")

    yield ("start", output_dir)

    start_time = time.time()
    results = {}

    # Run pipelines
    if progress_callback:
        # SEQUENTIAL MODE (for real-time progress updates)
        # Weights: Audio 5%, Face 60%, Body 100%

        # 1. Audio (0-5%)
        progress_callback(0.0, "Processing - Audio analysis")
        try:
            res_audio = run_wrapper(run_audio_pipeline, str(video_path), str(output_dir))
            results["audio"] = res_audio or {}
            print("✅ Audio module finished.")
            yield ("progress", "audio", results["audio"])
        except Exception as e:
            print(f"❌ Audio module failed: {e}")
            results["audio"] = {}
            yield ("error", "audio", e)
        progress_callback(0.05, "Processing - Audio debug file creation") # Simulated since audio is fast

        # 2. Face (5-59%)
        def face_cb(p, msg=None):
            # Map 0-1 to 0.05-0.59
            # If msg is provided, pass it through. Otherwise default.
            global_p = 0.05 + (p * 0.54)
            progress_callback(global_p, msg)

        try:
            res_face = run_face_pipeline(str(video_path), str(output_dir), progress_callback=face_cb)
            results["face"] = res_face or {}
            print("✅ Face module finished.")
            yield ("progress", "face", results["face"])
        except Exception as e:
            print(f"❌ Face module failed: {e}")
            results["face"] = {}
            yield ("error", "face", e)
        progress_callback(0.60)

        # 3. Body (60-99%)
        def body_cb(p, msg=None):
            # Map 0-1 to 0.60-0.99
            global_p = 0.60 + (p * 0.39)
            progress_callback(global_p, msg)

        try:
            res_body = run_body_pipeline(str(video_path), str(output_dir), progress_callback=body_cb)
            results["body"] = res_body or {}
            print("✅ Body module finished.")
            yield ("progress", "body", results["body"])
        except Exception as e:
             print(f"❌ Body module failed: {e}")
             results["body"] = {}
             yield ("error", "body", e)
        progress_callback(1.0, "Done.")

    else:
        # PARALLEL MODE (Standard)
        with ProcessPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(run_wrapper, run_audio_pipeline, str(video_path), str(output_dir)): "audio",
                executor.submit(run_wrapper, run_body_pipeline, str(video_path), str(output_dir)): "body",
                executor.submit(run_wrapper, run_face_pipeline, str(video_path), str(output_dir)): "face",
            }

            for future in as_completed(futures):
                module = futures[future]
                try:
                    res = future.result()
                    results[module] = res
                    print(f"✅ {module.capitalize()} module finished.")
                    yield ("progress", module, res)
                except Exception as e:
                    print(f"❌ {module.capitalize()} module failed: {e}")
                    results[module] = {}
                    yield ("error", module, e)

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

    # --- CLUSTERING PREDICTION ---
    print("\n--- Predicting Communication Persona ---")
    try:
        persona = predict_persona(global_results)
        if persona:
            enriched_results["clustering"] = persona
            print(f"✅ Persona Assigned: {persona['name']}")
        else:
            print("⚠️ Clustering prediction returned None.")
    except Exception as e:
        print(f"⚠️ Clustering prediction failed: {e}")

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

    yield ("final", output_dir, results)


def run_pipelines(video_path, output_base_dir="data/processed"):
    """
    Wrapper for backward compatibility.
    Runs the iterator to completion and returns the final result.
    """
    iterator = run_pipelines_iterator(video_path, output_base_dir)
    output_dir = None
    results = {}

    for event_type, *args in iterator:
        if event_type == "final":
            output_dir, results = args

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
