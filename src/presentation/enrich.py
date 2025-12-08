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
    "face": ["head_stability", "gaze_consistency", "smile_activation"],
    "body": ["gesture_magnitude", "gesture_activity", "gesture_jitter", "body_sway", "posture_openness"],
    "audio": ["speech_rate", "pause_ratio", "pitch_dynamic", "volume_dynamic", "vocal_punch"],
}

# Map flat key patterns to nested key names
KEY_MAPPINGS = {
    "_communication_score": "communication_score",
    "_communication_interpretation": "communication_interpretation", 
    "_communication_coaching": "communication_coaching",
    "_consistency_score": "consistency_score",
    "_consistency_interpretation": "consistency_interpretation",
    "_consistency_coaching": "consistency_coaching",
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
            metric_data = _extract_metric_data(metric_id, flat_data, module_id)
            metric_spec = spec.get(metric_id, {})
            
            # Add enrichment from spec
            metric_data["what"] = metric_spec.get("what_is_measured", "")
            metric_data["how"] = metric_spec.get("how_it_is_measured", "")
            metric_data["why"] = metric_spec.get("why_it_matters", "")
            metric_data["score_semantics"] = metric_spec.get("score_semantics", {})
            
            module_output["metrics"][metric_id] = metric_data
        
        enriched[module_id] = module_output
    
    return enriched


def _build_global_section(module_id: str, flat_data: dict, spec: dict) -> dict:
    """Build the global section for a module."""
    global_spec = spec.get(f"{module_id}_global_score", {})
    
    if module_id == "audio":
        return {
            "score": flat_data.get("audio_global_score", 0),
            "interpretation": flat_data.get("audio_global_interpretation", ""),
            "what": global_spec.get("what_is_measured", ""),
            "why": global_spec.get("why_it_matters", ""),
        }
    else:
        return {
            "communication_score": flat_data.get("global_comm_score", 0),
            "consistency_score": flat_data.get("global_consistency_score", 0),
            "interpretation": flat_data.get(f"{module_id}_global_interpretation", ""),
            "what": global_spec.get("what_is_measured", ""),
            "why": global_spec.get("why_it_matters", ""),
        }


def _extract_metric_data(metric_id: str, flat_data: dict, module_id: str) -> dict:
    """Extract all data for a single metric from flat structure."""
    result = {}
    
    # Audio has simpler structure (no comm/cons split in keys)
    if module_id == "audio":
        prefixes = [
            (f"{metric_id}_score", "score"),
            (f"{metric_id}_interpretation", "interpretation"),
            (f"{metric_id}_coaching", "coaching"),
        ]
    else:
        prefixes = [
            (f"{metric_id}_communication_score", "communication_score"),
            (f"{metric_id}_communication_interpretation", "communication_interpretation"),
            (f"{metric_id}_communication_coaching", "communication_coaching"),
            (f"{metric_id}_consistency_score", "consistency_score"),
            (f"{metric_id}_consistency_interpretation", "consistency_interpretation"),
            (f"{metric_id}_consistency_coaching", "consistency_coaching"),
        ]
    
    for flat_key, nested_key in prefixes:
        if flat_key in flat_data:
            result[nested_key] = flat_data[flat_key]
    
    return result
