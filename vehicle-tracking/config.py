# Model
MODEL_PATH = "yolov8s.pt"        # was yolov8n.pt — better accuracy, especially for small/fast objects
TRACKER_CONFIG = "bytetrack.yaml"   # back to default

# Vehicle classes (COCO IDs): car, motorcycle, bus, truck
VEHICLE_CLASSES = [2, 3, 5, 7]

# Zone of interest (x1, y1, x2, y2) — retune per video resolution/angle
ZONE = (600, 50, 1250, 450)

# Congestion thresholds
DENSITY_LOW_MAX = 6
DENSITY_MEDIUM_MAX = 12
SPEED_JAM_THRESHOLD = 20

CONFIDENCE_THRESHOLD = 0.15       # was YOLO's default 0.25 — lets borderline bike detections through
INPUT_SIZE = 960                  # was default 640 — more pixels for small/distant objects
PROCESS_EVERY_N_FRAMES = 2      # process every 2nd frame; try 3 if still too slow

# Event emission
EMIT_INTERVAL_SECONDS = 5

# Backend (set to True once P4's endpoint is live)
SEND_TO_BACKEND = False
BACKEND_URL = "http://localhost:8000/events"

# Video source
VIDEO_PATH = "traffic.mp4"