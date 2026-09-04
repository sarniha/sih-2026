import os

# Base Directories
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, ".."))

# Model Configuration
MODEL_PATH = os.environ.get(
    "ROAD_DEFECT_MODEL_PATH",
    os.path.join(MODULE_DIR, "weights", "best.pt")
)
TRACKER_CONFIG = "bytetrack.yaml"

# Detection Tuning
CONFIDENCE_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45
INPUT_SIZE = 640

# Temporal Confirmation (eliminates single-frame false positives)
MIN_HITS_CONFIRMATION = 3  # Must be tracked across at least N frames to confirm
MAX_AGE_FRAMES = 15        # Maximum frames to keep lost tracks alive

# Defect Severity Classification (based on bbox area ratio to frame)
SEVERITY_RATIO_LOW_MAX = 0.005     # < 0.5% of frame area is low severity
SEVERITY_RATIO_MEDIUM_MAX = 0.025  # 0.5% - 2.5% is medium severity, > 2.5% is high

# Spatial & Temporal Deduplication
DEDUP_DISTANCE_METERS = 10.0
DEDUP_WINDOW_SECONDS = 5.0

# Backend Integration
SEND_TO_BACKEND = os.environ.get("SEND_TO_BACKEND", "true").lower() in ("true", "1", "yes")
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8000")
BACKEND_URL = os.environ.get("BACKEND_URL", f"{BACKEND_BASE_URL}/api/v1/events")
EVIDENCE_UPLOAD_URL = os.environ.get("EVIDENCE_UPLOAD_URL", f"{BACKEND_BASE_URL}/api/v1/evidence/upload")
SERVICE_TOKEN = os.environ.get("SERVICE_TOKEN", "")
if not SERVICE_TOKEN:
    backend_env_path = os.path.join(PROJECT_ROOT, "backend", ".env")
    if os.path.exists(backend_env_path):
        try:
            with open(backend_env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SERVICE_TOKEN="):
                        SERVICE_TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
if not SERVICE_TOKEN:
    SERVICE_TOKEN = "smartbus_secret_token_dev_2026"

# Seeded transit identifiers (matching Supabase test seeds)
BUS_ID = os.environ.get("BUS_ID", "4af85ce8-b9b9-4a7c-963d-a5eaceb5e236")
TRIP_ID = os.environ.get("TRIP_ID", "004b1d9f-d0b8-471d-9f5d-c14a404a4c5a")
CAMERA_ID = os.environ.get("CAMERA_ID", None)
CAMERA_POSITION = os.environ.get("CAMERA_POSITION", "windshield_front")

# Evidence Management
SAVE_EVIDENCE = True
BACKEND_STATIC_EVIDENCE_DIR = os.path.join(PROJECT_ROOT, "backend", "static", "evidence")
LOCAL_EVIDENCE_DIR = os.path.join(MODULE_DIR, "evidence")
