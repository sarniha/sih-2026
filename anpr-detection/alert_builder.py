"""
alert_builder.py — Construct the backend event payload for ANPR/incident alerts

Maps the pipeline's internal data to the backend's existing EventCreate schemas:
  - "hit_run"  → HitRunEvent  (plate optional — incident auto-spawned by backend)
  - "anpr"     → AnprEvent    (plate confirmed, no incident — informational)

The backend's ingest_event() + evaluate_and_spawn_incident() handles everything
else: incident row creation, evidence attachment, WebSocket broadcast.

Payload format matches the Pydantic schemas in backend/app/schemas/event.py.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple

from config import BUS_ID, CAMERA_ID, TRIP_ID


def build_alert(
    track_id:      int,
    incident_type: str,                       # "hit_and_run" | "rash_driving"
    plate_text:    Optional[str],             # cleaned plate or None
    plate_conf:    float,                     # 0.0 – 1.0
    raw_plate_text: Optional[str],            # before cleaning (for metadata)
    vehicle_bbox:  Tuple[int, int, int, int], # (x1, y1, x2, y2) full-frame px
    vehicle_class: str,                       # "car" | "motorcycle" | etc.
    evidence_url:  Optional[str],             # relative path for /static/ mount
    gps:           dict,                      # {"lat": float, "lon": float}
    frame_num:     int,
    fps:           float,
    speed_px_sec:  float,
) -> dict:
    """
    Build the JSON payload ready to POST to /api/v1/events.

    Returns a dict that matches one of the EventCreate union types.
    Includes a `_meta` key with pipeline-internal context (not sent to backend).
    """
    x1, y1, x2, y2 = vehicle_bbox
    now_iso = datetime.now(timezone.utc).isoformat()

    # event_type mapping:
    #   hit_and_run → "hit_run"  (backend spawns incident automatically)
    #   rash_driving → "hit_run" (still triggers incident for human review)
    event_type = "hit_run"

    # Confidence: use plate_conf if plate was read, else a low synthetic value
    detection_confidence = round(max(plate_conf, 0.3), 3)

    payload = {
        "event_type":  event_type,
        "trip_id":     TRIP_ID,
        "bus_id":      BUS_ID,
        "object_id":   f"track_{track_id}",
        "confidence":  detection_confidence,
        "bbox": {
            "x1": x1, "y1": y1,
            "x2": x2, "y2": y2,
        },
        "lon":          gps.get("lon"),
        "lat":          gps.get("lat"),
        "occurred_at":  now_iso,
        "severity":     _severity(plate_conf, incident_type),
        "evidence_url": evidence_url,
    }

    # Attach plate fields if we got a reading
    if plate_text:
        payload["plate_text"]       = plate_text
        payload["plate_confidence"] = round(plate_conf, 3)

    # Internal metadata — strip _meta before sending to backend
    payload["_meta"] = {
        "incident_type":  incident_type,      # "hit_and_run" or "rash_driving"
        "raw_plate_text": raw_plate_text,
        "track_id":       track_id,
        "vehicle_class":  vehicle_class,
        "elapsed_sec":    round(frame_num / fps, 2) if fps > 0 else 0,
        "speed_px_sec":   round(speed_px_sec, 1),
        "camera_id":      CAMERA_ID,
    }

    return payload


def strip_meta(payload: dict) -> dict:
    """Return a copy of payload without the internal _meta key."""
    return {k: v for k, v in payload.items() if k != "_meta"}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _severity(plate_conf: float, incident_type: str) -> str:
    """
    Severity heuristic:
      - hit_and_run with good plate read → high
      - rash_driving or uncertain plate  → medium
    """
    if incident_type == "hit_and_run" and plate_conf >= 0.6:
        return "high"
    if plate_conf >= 0.4:
        return "medium"
    return "medium"
