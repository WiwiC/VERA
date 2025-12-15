import subprocess
import sys
import time

VIDEOS = [
    "6", "11", "16", "23", "25",
    "58", "59", "62", "64", "65",
    "66", "70", "71", "72", "73",
    "74", "75"
]

def run_pipeline(video_id):
    video_path = f"data/raw/{video_id}.mp4"
    print(f"\n🚀 Processing Video {video_id}...")

    # Clean output dir first to ensure fresh results
    subprocess.run(f"rm -rf data/processed/{video_id}", shell=True)

    cmd = f"source VERA-env/bin/activate && python src/main.py {video_path}"

    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    duration = time.time() - start_time

    if result.returncode != 0:
        print(f"❌ Error processing {video_id}:\n{result.stderr}")
        return False
    else:
        print(f"✅ Finished {video_id} in {duration:.1f}s")
        return True

def main():
    print(f"Starting batch processing for {len(VIDEOS)} videos...")

    success_count = 0
    failed = []

    for vid in VIDEOS:
        if run_pipeline(vid):
            success_count += 1
        else:
            failed.append(vid)

    print("\n" + "="*50)
    print(f"Batch Complete.")
    print(f"Success: {success_count}/{len(VIDEOS)}")
    if failed:
        print(f"Failed: {failed}")
    print("="*50)

if __name__ == "__main__":
    main()
