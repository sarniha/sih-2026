import os

# Model
MODEL_PATH = "yolov8s.pt"
TRACKER_CONFIG = "bytetrack.yaml"

# Vehicle classes (COCO IDs): car, motorcycle, bus, truck
VEHICLE_CLASSES = [2, 3, 5, 7]

# Detection tuning
CONFIDENCE_THRESHOLD = 0.15
INPUT_SIZE = 960

# Zone of interest (x1, y1, x2, y2) — retune per video resolution/angle
ZONE = (0, 150, 1250, 700)

# Congestion thresholds — retuned against real test footage
DENSITY_LOW_MAX = 6
DENSITY_MEDIUM_MAX = 12
SPEED_JAM_THRESHOLD = 20  # px/second

# Performance
PROCESS_EVERY_N_FRAMES = 2

# Event emission
EMIT_INTERVAL_SECONDS = 5

# Backend integration
SEND_TO_BACKEND = True
BACKEND_URL = "http://localhost:8000/api/v1/events"
SERVICE_TOKEN = os.environ.get("SERVICE_TOKEN", "")  # set via: $env:SERVICE_TOKEN = "..."

# Real bus/trip UUIDs from Supabase (seeded test data)
BUS_ID = "4af85ce8-b9b9-4a7c-963d-a5eaceb5e236"
TRIP_ID = "004b1d9f-d0b8-471d-9f5d-c14a404a4c5a"

# Video source
VIDEO_PATH = "traffic.mp4"