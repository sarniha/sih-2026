"""
events.py — Event construction, evidence frame export, and backend synchronization
for the Road Defect Detection module.
"""

import os
import time
import uuid
import cv2
import requests
from typing import Dict, Any, Optional

from config import (
    BACKEND_URL,
    BACKEND_BASE_URL,
    EVIDENCE_UPLOAD_URL,
    SERVICE_TOKEN,
    BUS_ID,
    TRIP_ID,
    CAMERA_ID,
    CAMERA_POSITION,
    SEND_TO_BACKEND,
    BACKEND_STATIC_EVIDENCE_DIR,
    LOCAL_EVIDENCE_DIR,
)


def ensure_evidence_dirs():
    """Ensure evidence directories exist."""
    os.makedirs(LOCAL_EVIDENCE_DIR, exist_ok=True)
    if os.path.exists(os.path.dirname(BACKEND_STATIC_EVIDENCE_DIR)):
        os.makedirs(BACKEND_STATIC_EVIDENCE_DIR, exist_ok=True)


def save_evidence_snapshot(
    frame,
    bbox: list,
    track_id: Any,
    label: str = "pothole",
    severity: str = "medium",
    conf: float = 0.8,
) -> Optional[str]:
    """
    Saves an annotated evidence frame to local directory and backend static folder,
    or uploads to backend evidence upload endpoint if remote.
    Returns the relative or absolute evidence URL.
    """
    ensure_evidence_dirs()
    timestamp_str = int(time.time())
    unique_suffix = uuid.uuid4().hex[:6]
    filename = f"defect_{label}_{track_id}_{timestamp_str}_{unique_suffix}.jpg"

    # Annotate a copy of frame for evidence inspection
    annotated = frame.copy()
    x1, y1, x2, y2 = [int(v) for v in bbox]
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
    tag = f"{label.upper()} [{severity.upper()}] {conf:.2f}"
    cv2.putText(
        annotated,
        tag,
        (x1, max(20, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 255),
        2,
    )

    # 1. Save locally in road-defect-detection/evidence/
    local_path = os.path.join(LOCAL_EVIDENCE_DIR, filename)
    cv2.imwrite(local_path, annotated)

    # 2. If backend static directory is directly accessible on filesystem, save there
    if os.path.exists(BACKEND_STATIC_EVIDENCE_DIR):
        backend_dest = os.path.join(BACKEND_STATIC_EVIDENCE_DIR, filename)
        cv2.imwrite(backend_dest, annotated)
        return f"/static/evidence/{filename}"

    # 3. Otherwise, try uploading to backend evidence endpoint if enabled
    if SEND_TO_BACKEND and EVIDENCE_UPLOAD_URL:
        try:
            with open(local_path, "rb") as f:
                resp = requests.post(
                    EVIDENCE_UPLOAD_URL,
                    files={"file": (filename, f, "image/jpeg")},
                    headers={"X-Service-Token": SERVICE_TOKEN},
                    timeout=5,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return data.get("url", f"/static/evidence/{filename}")
        except Exception as e:
            # Fallback to standard URL path
            pass

    return f"/static/evidence/{filename}"


def build_defect_event(
    object_id: Any,
    confidence: float,
    severity: str,
    bbox: list,
    lon: Optional[float] = None,
    lat: Optional[float] = None,
    occurred_at: Optional[str] = None,
    evidence_url: Optional[str] = None,
    defect_class: str = "pothole",
    camera_id: Optional[str] = None,
    bus_id: Optional[str] = None,
    trip_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Constructs an event dictionary complying strictly with backend PotholeEvent schema.
    """
    x1, y1, x2, y2 = [int(v) for v in bbox]
    box_w = max(0, x2 - x1)
    box_h = max(0, y2 - y1)

    event_payload = {
        "event_type": "pothole",
        "trip_id": trip_id or TRIP_ID,
        "bus_id": bus_id or BUS_ID,
        "camera_id": camera_id or CAMERA_ID,
        "object_id": f"pothole_{object_id}",
        "confidence": round(min(max(float(confidence), 0.0), 1.0), 3),
        "occurred_at": occurred_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "severity": severity.lower(),
        "bbox": {"x": x1, "y": y1, "w": box_w, "h": box_h},
        "metadata": {
            "defect_class": defect_class,
            "camera_position": CAMERA_POSITION,
            "detected_by": "road-defect-detection-edge",
        },
    }

    if lon is not None and lat is not None:
        event_payload["lon"] = round(lon, 7)
        event_payload["lat"] = round(lat, 7)

    if evidence_url:
        event_payload["evidence_url"] = evidence_url

    return event_payload


def send_defect_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Sends the defect event payload to the central backend.
    """
    if not SEND_TO_BACKEND:
        print(f"[DRY RUN EVENT] {event['event_type']} (severity: {event['severity']}, conf: {event['confidence']})")
        return None

    try:
        resp = requests.post(
            BACKEND_URL,
            json=event,
            headers={
                "Content-Type": "application/json",
                "X-Service-Token": SERVICE_TOKEN,
            },
            timeout=5,
        )
        if resp.status_code == 201:
            body = resp.json()
            event_id = body.get("id", "unknown")
            print(f"[BACKEND 201 OK] Defect event registered: id={event_id}, type={event['event_type']}")
            return body
        else:
            print(f"[BACKEND ERR {resp.status_code}] {resp.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[BACKEND CONN_ERR] Unable to dispatch event to {BACKEND_URL}: {e}")
        return None
