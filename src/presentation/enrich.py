"""
Enrichment layer that:
1. Restructures flat scoring output into nested format
2. Adds human-readable context from metrics_spec.json
"""

import json
from pathlib import Path

SPEC_PATH = Path(__file__).parent.parent / "schemas" / "metrics_spec.json"

_spec_cache = None


def load_spec():
    """Load and cache metrics_spec.json"""
    global _spec_cache
    if _spec_cache is None:
        with open(SPEC_PATH) as f:
            data = json.load(f)
        _spec_cache = {m["metric_id"]: m for m in data["metrics"]}
    return _spec_cache


# Define which metrics belong to which module
MODULE_METRICS = {
    "face": ["head_stability", "gaze_stability", "smile_activation", "head_down_ratio"],
    "body": ["gesture_magnitude", "gesture_activity", "gesture_stability", "body_sway", "posture_openness"],
    "audio": ["speech_rate", "pause_ratio", "pitch_dynamic", "volume_dynamic", "vocal_punch"],
}

# Map flat key patterns to nested key names
KEY_MAPPINGS = {
    "_communication_score": "communication_score",
    "_communication_interpretation": "communication_interpretation",
    "_communication_coaching": "communication_coaching",
    "_score": "score",  # For audio metrics (no comm/cons split)
    "_interpretation": "interpretation",
    "_coaching": "coaching",
}


def enrich_results(global_results: dict) -> dict:
    """
    Transform flat scoring results into nested structure with enrichment.

    Input (flat):
        {"face": {"head_stability_communication_score": 0.84, ...}}

    Output (nested):
        {"face": {"global": {...}, "metrics": {"head_stability": {...}}}}
    """
    spec = load_spec()
    interp_map = _build_interpretation_map(spec)

    enriched = {
        "meta": global_results.get("meta", {})
    }

    for module_id, metric_ids in MODULE_METRICS.items():
        if module_id not in global_results:
            continue

        flat_data = global_results[module_id]

        # Build nested structure
        module_output = {
            "global": _build_global_section(module_id, flat_data, spec),
            "metrics": {}
        }

        # Process each metric
        for metric_id in metric_ids:
            metric_data = _extract_metric_data(metric_id, flat_data, spec)
            metric_spec = spec.get(metric_id, {})

            # Add enrichment from spec
            metric_data["what"] = metric_spec.get("what_is_measured", "")
            metric_data["how"] = metric_spec.get("how_it_is_measured", "")
            metric_data["why"] = metric_spec.get("why_it_matters", "")
            metric_data["score_semantics"] = metric_spec.get("score_semantics", {})

            module_output["metrics"][metric_id] = metric_data

        enriched[module_id] = module_output

    return enriched


def _to_percent(score: float) -> int:
    """Convert 0-1 score to 0-100 integer for UX display."""
    clamped = max(0.0, min(1.0, score))
    return round(clamped * 100)


def _build_global_section(module_id: str, flat_data: dict, spec: dict) -> dict:
    """Build the global section for a module."""
    global_spec = spec.get(f"{module_id}_global_score", {})

    if module_id == "audio":
        raw_score = flat_data.get("audio_global_score", 0)
        return {
            "score": _to_percent(raw_score),
            "interpretation": flat_data.get("audio_global_interpretation", ""),
            "what": global_spec.get("what_is_measured", ""),
            "why": global_spec.get("why_it_matters", ""),
        }
    else:
        raw_score = flat_data.get("global_comm_score", 0)
        return {
            "score": _to_percent(raw_score),
            "interpretation": flat_data.get(f"{module_id}_global_interpretation", ""),
            "what": global_spec.get("what_is_measured", ""),
            "why": global_spec.get("why_it_matters", ""),
        }


def _extract_metric_data(metric_id: str, results: dict, spec: dict) -> dict:
    """
    Extract score, interpretation, coaching, and label for a metric.
    Uses the explicit label from the results if available.
    """
    # 1. Get metric definition from spec (not directly used here, but good for context)
    # metric_def = spec.get(metric_id, {})

    # 2. Extract score
    score_key = f"{metric_id}_score"
    # Some body metrics use _communication_score suffix
    if score_key not in results:
        score_key = f"{metric_id}_communication_score"

    score = results.get(score_key)
    if score is not None:
        score = _to_percent(score)

    # 3. Extract interpretation & coaching
    # Try standard keys first
    interp_key = f"{metric_id}_interpretation"
    coach_key = f"{metric_id}_coaching"

    # Try communication keys if standard not found
    if interp_key not in results:
        interp_key = f"{metric_id}_communication_interpretation"
    if coach_key not in results:
        coach_key = f"{metric_id}_communication_coaching"

    interpretation = results.get(interp_key)
    coaching = results.get(coach_key)

    # 4. Extract Label (NEW: Explicit label from scoring)
    # Try standard key first
    label_key = f"{metric_id}_label"
    label = results.get(label_key)

    # If not found, try to look it up (fallback for backward compatibility)
    if not label and interpretation:
        # This fallback should ideally not be needed after refactor
        # But keeping it for safety
        interp_map = _build_interpretation_map(spec)
        metric_map = interp_map.get(metric_id, {})
        # Normalize text for lookup
        label = metric_map.get(interpretation.strip())

    # 5. Extract Raw Value (NEW: For calibration distance)
    # Try standard key first
    raw_key = f"{metric_id}_val"
    raw_value = results.get(raw_key)

    return {
        "score": score,
        "raw_value": raw_value,
        "interpretation": interpretation,
        "coaching": coaching,
        "label": label
    }


def _build_interpretation_map(spec: dict) -> dict:
    """
    Build a mapping from interpretation text (user_text) to bucket label.
    Returns: {metric_id: {user_text: label}}
    """
    interp_map = {}

    # spec is {metric_id: metric_data}
    for metric in spec.values():
        metric_id = metric.get("metric_id")
        buckets = metric.get("interpretation_buckets", [])

        metric_map = {}
        for bucket in buckets:
            label = bucket.get("label")
            user_text = bucket.get("user_text")
            if label and user_text:
                # Normalize text for robust matching
                metric_map[user_text.strip()] = label.lower()

        interp_map[metric_id] = metric_map

    return interp_map
