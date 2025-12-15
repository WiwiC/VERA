import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analysis.data_processing import update_master_dataset

def refresh_all():
    processed_dir = Path("data/processed")
    if not processed_dir.exists():
        print(f"❌ Processed directory not found: {processed_dir}")
        return

    # Clear existing master dataset to ensure clean slate
    master_path = Path("data/clustering_dataset/master_vector_data_set.csv")
    if master_path.exists():
        os.remove(master_path)
        print(f"🗑️ Deleted existing master dataset: {master_path}")

    # Iterate over all subdirectories
    count = 0
    for video_dir in processed_dir.iterdir():
        if video_dir.is_dir():
            video_name = video_dir.name
            print(f"🔄 Refreshing data for: {video_name}")
            update_master_dataset(video_name, video_dir)
            count += 1

    print(f"\n✅ Refreshed clustering data for {count} videos.")

if __name__ == "__main__":
    refresh_all()
