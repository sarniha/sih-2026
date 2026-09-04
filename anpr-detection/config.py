import os


# ─── Vehicle Detection ────────────────────────────────────────────────────────
MODEL_PATH          = "yolov8n.pt"          # COCO pretrained — no training needed
TRACKER_CONFIG      = "bytetrack.yaml"
VEHICLE_CLASSES     = [2, 3, 5, 7]          # COCO: car, motorcycle, bus, truck
CONFIDENCE_THRESHOLD = 0.25
INPUT_SIZE           = 640

# ─── Plate Detection ──────────────────────────────────────────────────────────
# Primary: keremberke's pretrained LP detector (pulled via ultralytics hub)
# Fallback: classical CV contour approach (auto-selected if YOLO pull fails)
PLATE_MODEL_ID      = "keremberke/yolov8n-license-plate-detection"
PLATE_CONFIDENCE    = 0.35

# ─── Incident Detection (Method A — Speed Anomaly) ────────────────────────────
# A vehicle is flagged when its smoothed pixel-speed exceeds this threshold.
# Tune this against your test footage; 180 px/s is a good starting point.
SPEED_ANOMALY_THRESHOLD = 662   # pixels per second
SPEED_WINDOW_FRAMES     = 5     # rolling average window
INCIDENT_COOLDOWN_SEC   = 10 
MAX_PLAUSIBLE_SPEED =1200   # suppress re-flagging same track within N sec

# ─── Pipeline Perf ────────────────────────────────────────────────────────────
PROCESS_EVERY_N_FRAMES = 2      # run detection every 2nd frame

# ─── GPS (static placeholder — replace with live NMEA reader post-hackathon) ──
DEFAULT_GPS = {"lat": 28.5522, "lon": 77.0582}   # Central Delhi placeholder

# ─── Evidence Storage ─────────────────────────────────────────────────────────
EVIDENCE_DIR = "evidence_incidents"   # annotated full frames
PLATE_DIR    = "plate_crops"          # cropped plate images

# ─── Backend Push ─────────────────────────────────────────────────────────────
SEND_TO_BACKEND = True
BACKEND_URL     = "http://localhost:8000/api/v1/events"
SERVICE_TOKEN   = os.environ.get("SERVICE_TOKEN", "")

# Real bus/trip UUIDs from Supabase seeded data (same as vehicle-tracking/)
BUS_ID  = "4af85ce8-b9b9-4a7c-963d-a5eaceb5e236"
TRIP_ID = "004b1d9f-d0b8-471d-9f5d-c14a404a4c5a"

CAMERA_ID = "front"

# ─── Video Source ─────────────────────────────────────────────────────────────
VIDEO_PATH = "test_footage.mp4"   # change to 0 for webcam
