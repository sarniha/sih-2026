#!/usr/bin/env bash
# ==============================================================================
# Road Defect Detection — Quickstart Runner
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚌 SmartBus Road Defect Detection Module"
echo "========================================="

# Set environment defaults if not provided
export BACKEND_URL="${BACKEND_URL:-http://localhost:8000/api/v1/events}"
export SERVICE_TOKEN="${SERVICE_TOKEN:-smartbus_secret_token_dev_2026}"
export BUS_ID="${BUS_ID:-4af85ce8-b9b9-4a7c-963d-a5eaceb5e236}"
export TRIP_ID="${TRIP_ID:-004b1d9f-d0b8-471d-9f5d-c14a404a4c5a}"

# Check for model weights
MODEL_FILE="weights/best.pt"
if [ ! -f "$MODEL_FILE" ]; then
    echo "⚠️  $MODEL_FILE not found, falling back to pretrained yolov8n.pt"
    MODEL_FILE="yolov8n.pt"
fi

echo "▶ Running Single-Camera Road Defect Pipeline..."
python3 main.py \
    --video data/synthetic_test.mp4 \
    --gps data/sample_gps.csv \
    --model "$MODEL_FILE" \
    --conf 0.25 \
    --min-hits 3 \
    --out events_output.json \
    "$@"

echo ""
echo "✅ Pipeline run complete. Events saved to events_output.json"
