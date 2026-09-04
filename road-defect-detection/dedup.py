"""
dedup.py — Spatial deduplication for confirmed road defect events.
Prevents the same physical defect from being reported multiple times.
"""

import json
import math
from typing import List, Tuple, Dict, Any, Optional

from config import DEDUP_DISTANCE_METERS

RADIUS_METRES = DEDUP_DISTANCE_METERS
SAME_CLASS_ONLY = True


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two lat/lon coordinates."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def deduplicate_events(events: List[Dict[str, Any]], radius_m: float = RADIUS_METRES) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Remove spatially duplicate events from a list.
    Keeps the event with highest confidence / severity.
    """
    sorted_events = sorted(events, key=lambda e: (e.get("confidence", 0.0)), reverse=True)
    kept = []
    dropped = []

    for ev in sorted_events:
        lat1 = ev.get("lat")
        lon1 = ev.get("lon")
        if lat1 is None or lon1 is None:
            kept.append(ev)
            continue

        cls1 = ev.get("metadata", {}).get("defect_class", ev.get("event_type", ""))

        is_dup = False
        for kept_ev in kept:
            lat2 = kept_ev.get("lat")
            lon2 = kept_ev.get("lon")
            if lat2 is None or lon2 is None:
                continue

            cls2 = kept_ev.get("metadata", {}).get("defect_class", kept_ev.get("event_type", ""))
            if SAME_CLASS_ONLY and cls1 != cls2:
                continue

            dist = haversine_m(lat1, lon1, lat2, lon2)
            if dist <= radius_m:
                is_dup = True
                break

        if is_dup:
            dropped.append(ev)
        else:
            kept.append(ev)

    return kept, dropped


def dedup_json_file(input_path: str, output_path: Optional[str] = None, radius_m: float = RADIUS_METRES) -> List[Dict[str, Any]]:
    with open(input_path, "r") as f:
        events = json.load(f)

    kept, dropped = deduplicate_events(events, radius_m)
    print(f"📦 Deduplication ({input_path})")
    print(f"   Input: {len(events)}, Kept: {len(kept)}, Dropped: {len(dropped)} (radius={radius_m}m)")

    out_path = output_path or input_path.replace(".json", "_deduped.json")
    with open(out_path, "w") as f:
        json.dump(kept, f, indent=2)

    return kept
