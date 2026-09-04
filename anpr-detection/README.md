# ANPR + Incident Detection Module

Sub-module 2 of the SIH 2026 Urban Intelligence Platform.

## What This Does

Watches a vehicle video feed, detects incidents (sudden acceleration / rash driving / hit-and-run), reads the offending vehicle's license plate, and pushes a structured alert to the central command backend.

```
Video → Vehicle Tracking → Incident Detection → Plate Detection → OCR → Alert Push
```

## Quick Start

### 1. Install dependencies

```powershell
cd anpr-detection
pip install -r requirements.txt
```

### 2. Set the service token (same value as backend `.env`)

```powershell
$env:SERVICE_TOKEN = "PUi_TEc7mmn35WtnsQRrLHBUgTq2KG8VHtfyeinESrA"
```

### 3. Put your test video in this directory

```
anpr-detection/test_footage.mp4
```

Or point to any path with `--video`.

### 4. Run

```powershell
# Normal run (needs display)
python anpr_pipeline.py

# Custom video path
python anpr_pipeline.py --video "C:\footage\dashcam.mp4"

# Dry run — alerts printed locally, NOT sent to backend
python anpr_pipeline.py --dry-run

# Headless (no GUI window, useful on servers)
python anpr_pipeline.py --no-display
```

Press **Q** to quit the display window.

## Configuration

Edit `config.py`:

| Variable | Default | Purpose |
|---|---|---|
| `VIDEO_PATH` | `test_footage.mp4` | Input video / camera index |
| `SEND_TO_BACKEND` | `True` | Toggle backend push |
| `BACKEND_URL` | `http://localhost:8000/api/v1/events` | Backend endpoint |
| `SPEED_ANOMALY_THRESHOLD` | `180` px/s | Tune per your test footage |
| `INCIDENT_COOLDOWN_SEC` | `10` | Suppress duplicate flags |
| `PLATE_CONFIDENCE` | `0.35` | Plate detector minimum confidence |
| `DEFAULT_GPS` | Delhi coords | Replace with live GPS reader |
| `BUS_ID` / `TRIP_ID` | Seeded UUIDs | Must match Supabase seeded data |

## How Incidents Are Processed

1. `anpr_pipeline.py` posts a `"hit_run"` event to `/api/v1/events`
2. The backend's `evaluate_and_spawn_incident()` automatically:
   - Creates an `incidents` row (`status="open"`)
   - Attaches `incident_evidence` rows (frame + plate crop)
   - Broadcasts over WebSocket to the frontend dashboard
3. Operators can review via `PATCH /api/v1/incidents/{id}`

## Output

**Console** (per incident):
```
[INCIDENT] track=42 | hit_and_run | speed=223.4 px/s
[PLATE]    Detected (yolo) conf=0.71 bbox=(12,44,118,82)
[OCR]      raw='MH 12 AB 1234' → clean='MH12AB1234' conf=0.847
[EVIDENCE] Saved → evidence_incidents/incident_42_MH12AB1234_1725466245.jpg
[AlertPusher] ✅ 201 Created | event_id=<uuid> | plate=MH12AB1234
```

**Files saved:**
```
evidence_incidents/incident_42_MH12AB1234_1725466245.jpg   ← annotated frame
plate_crops/plate_42_1725466245.jpg                        ← plate crop only
```

## File Structure

```
anpr-detection/
├── anpr_pipeline.py        ← Main entrypoint
├── incident_detector.py    ← Speed-anomaly detection (Method A)
├── plate_detector.py       ← YOLO LP detector + classical CV fallback
├── ocr_reader.py           ← EasyOCR wrapper + Indian plate cleaning
├── alert_builder.py        ← Constructs backend-compatible event payload
├── alert_pusher.py         ← HTTPS push with retry queue
├── evidence_saver.py       ← Annotated frame + plate crop writer
├── config.py               ← All tunable parameters
├── requirements.txt
├── models/                 ← YOLO weights auto-downloaded here at runtime
└── evidence_incidents/     ← Annotated frames (runtime-created)
```

## Post-Hackathon Improvements

- [ ] Fine-tune plate YOLO on [Roboflow Indian LP dataset](https://universe.roboflow.com)
- [ ] PaddleOCR swap for better curved/worn plate accuracy
- [ ] Method B/C incident detection (IoU overlap + CADP classifier)
- [ ] Live GPS via NMEA serial reader instead of static coordinates
- [ ] HMAC-SHA256 alert signing (`X-Signature-SHA256`) for production
