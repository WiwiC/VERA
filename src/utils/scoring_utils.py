import numpy as np

def get_optimal_target(buckets):
    """
    Find the center of the 'optimal' bucket to use as the target for interpolation.
    """
    for i, bucket in enumerate(buckets):
        if bucket["label"] in ["optimal", "excellent", "forward", "expressive"]: # Handle various 'best' labels
             # Special case for "expressive" in pitch/volume? No, they use "optimal" or "expressive" as top.
             # Actually, let's look at the tiers. The one with tier (0.8, 1.0) is the target.
             if bucket.get("tier") == (0.8, 1.0):
                 prev_max = buckets[i-1]["max"] if i > 0 else 0
                 curr_max = bucket["max"]
                 if curr_max == 999: # Should not happen for optimal, but just in case
                     return prev_max * 1.5
                 return (prev_max + curr_max) / 2.0
    return 0 # Fallback

def compute_tiered_score(value, buckets):
    """
    Compute score using Tiered Parabolic/Linear logic.

    1. Identify Bucket.
    2. Identify Tier (min_score, max_score).
    3. Identify Target (center of Optimal bucket).
    4. Interpolate:
       - Closer to Target = max_score
       - Further from Target = min_score
    """
    target = get_optimal_target(buckets)

    # 1. Find Bucket
    current_bucket = None
    bucket_min = 0
    bucket_max = 0

    for i, bucket in enumerate(buckets):
        prev_max = buckets[i-1]["max"] if i > 0 else 0
        curr_max = bucket["max"]

        if value <= curr_max:
            current_bucket = bucket
            bucket_min = prev_max
            bucket_max = curr_max
            break

    if current_bucket is None:
        # Value > last max (should be caught by 999, but safety first)
        current_bucket = buckets[-1]
        bucket_min = buckets[-2]["max"] if len(buckets) > 1 else 0
        bucket_max = value * 1.2 # Arbitrary upper bound for interpolation

    # 2. Get Tier
    tier = current_bucket.get("tier", (0.0, 0.0))
    tier_min, tier_max = tier

    # 3. Interpolate
    # We want to map the position of 'value' within [bucket_min, bucket_max]
    # to the range [tier_min, tier_max].
    # Direction: The side closer to 'target' gets 'tier_max'.

    dist_min = abs(bucket_min - target)
    dist_max = abs(bucket_max - target)

    # Handle Open-Ended Buckets (max=999)
    if bucket_max == 999:
        # Decay to 0
        # If we are here, we are likely in a "Poor" bucket > threshold
        # We map bucket_min -> tier_max (e.g. 40%)
        # We map bucket_min * 2 -> tier_min (e.g. 0%)
        # This is a simple linear decay
        # Use 999 as the actual limit for interpolation
        # This ensures smooth decay up to the defined 'max'
        if value >= 999:
            return tier_min
        ratio = (value - bucket_min) / (999 - bucket_min)
        return tier_max - (tier_max - tier_min) * ratio

    # Standard Interpolation
    if dist_min < dist_max:
        # Min side is better (closer to target)
        # value=bucket_min -> score=tier_max
        # value=bucket_max -> score=tier_min
        ratio = (value - bucket_min) / (bucket_max - bucket_min)
        score = tier_max - (tier_max - tier_min) * ratio
    else:
        # Max side is better (closer to target)
        # value=bucket_max -> score=tier_max
        # value=bucket_min -> score=tier_min
        ratio = (value - bucket_min) / (bucket_max - bucket_min)
        score = tier_min + (tier_max - tier_min) * ratio

    # 4. Parabolic Boost for Optimal Bucket
    # If we are in the optimal bucket (tier 0.8-1.0), use a parabola to make the peak flatter
    if tier == (0.8, 1.0):
        # Normalize value to -1 to 1 range within the bucket (0 at center)
        midpoint = (bucket_min + bucket_max) / 2.0
        half_width = (bucket_max - bucket_min) / 2.0
        if half_width > 0:
            norm_pos = (value - midpoint) / half_width
            # Parabola: y = 1 - x^2 (scaled to 0.8-1.0)
            # score = 1.0 - 0.2 * (norm_pos^2)
            score = 1.0 - (1.0 - 0.8) * (norm_pos**2)

    return max(0.0, min(1.0, score))
