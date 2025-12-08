"""
Temporal Analysis Utilities.

This module provides functions to transform and analyze temporal data,
specifically for converting sliding window metrics into continuous timelines.
"""

import pandas as pd
import numpy as np

def project_windows_to_seconds(window_df, total_seconds=None):
    """
    Project overlapping window scores onto a 1Hz timeline (per second).

    For each second t, the score is the average of all windows that cover t.

    Args:
        window_df (pd.DataFrame): DataFrame containing window metrics.
                                  Must have 'start_sec', 'end_sec', and score columns.
        total_seconds (int, optional): Total duration of the video in seconds.
                                       If None, inferred from max(end_sec).

    Returns:
        pd.DataFrame: Timeline DataFrame with 'second' and averaged scores.
    """
    if window_df.empty:
        return pd.DataFrame()

    # Determine duration
    max_end = int(window_df["end_sec"].max())
    if total_seconds is None:
        duration = max_end
    else:
        duration = max(total_seconds, max_end)

    # Identify score columns (exclude start/end)
    score_cols = [c for c in window_df.columns if c not in ["start_sec", "end_sec"]]

    timeline_data = []

    for t in range(duration):
        # Find windows active at second t (start <= t < end)
        # Note: Windows are typically [start, end).
        # Adjust logic if your windows are inclusive/exclusive differently.
        # Assuming standard 5s window: 0-5 covers 0, 1, 2, 3, 4.
        active_windows = window_df[
            (window_df["start_sec"] <= t) &
            (window_df["end_sec"] > t)
        ]

        row = {"second": t}

        if not active_windows.empty:
            # Calculate mean for all score columns
            for col in score_cols:
                row[col] = active_windows[col].mean()
        else:
            # No windows cover this second (e.g., end of video padding)
            # Forward fill or leave as NaN?
            # For now, leave as NaN or 0?
            # Better to leave as NaN and handle later, or fill with 0 if appropriate.
            # Let's use NaN to indicate "no data".
            for col in score_cols:
                row[col] = np.nan

        timeline_data.append(row)

    timeline_df = pd.DataFrame(timeline_data)

    # Optional: Interpolate missing values if needed
    # timeline_df = timeline_df.interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')

    return timeline_df
