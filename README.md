# SmartBus — AI-Powered Onboard & Centralized Urban Sensing Platform
### Smart India Hackathon 2026 — Problem Statement #SIH26124

> **Transforming Urban Public Transit Buses into Real-Time Mobile Sensing Units**  
> Public transit buses traverse every primary road corridor in modern cities daily. SmartBus harnesses multi-camera bus dashcams with edge AI to detect road defects (potholes, structural cracks, road damage), monitor traffic density, read vehicle license plates (ANPR), and flag hit-and-run incidents—synchronizing telemetry in real-time to a centralized command center.

---

## 1. System Architecture

```
                                  [ BUS EDGE INFRASTRUCTURE ]
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  Multi-Camera Streams (Front Windshield, Rear Road View, Left/Right Side)    │
  └───────────────┬─────────────────────────────────────────────┬───────────────┘
                  │                                             │
                  ▼                                             ▼
  ┌───────────────────────────────┐             ┌───────────────────────────────┐
  │   road-defect-detection/      │             │      vehicle-tracking/        │
  │ • YOLOv8 Pothole & Distress   │             │ • YOLOv8 Vehicle Detection    │
  │ • ByteTrack Temporal Confirm  │             │ • Speed & Trajectory Tracking │
  │ • Severity Ranking (Low/Med/Hi│             │ • Zone Congestion Scoring     │
  │ • GPS Log Interpolation       │             │ • Anomaly & Traffic Alerts    │
  │ • Multi-Camera Deduplication  │             │                               │
  │ • Evidence Snapshot Capture   │             │                               │
  └───────────────┬───────────────┘             └───────────────┬───────────────┘
                  │                                             │
                  └──────────────────────┬──────────────────────┘
                                         │ HTTP REST / X-Service-Token
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                           backend/ (Central Command)                         │
  │ • FastAPI High-Performance ASGI Engine                                       │
  │ • PostgreSQL + PostGIS Geospatial Spatial-Temporal Deduplication (10m / 5s)  │
  │ • WebSocket Broadcast Manager for Real-Time Fleet Streaming                 │
  │ • Automated Safety Incident Escalation (Collision / Hit-and-Run Triage)     │
  │ • Evidence Asset Storage & Static Media Serving (/static/evidence/...)       │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │ WebSockets & REST APIs
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                          frontend/ (Operator Dashboard)                      │
  │ • React + Vite + TypeScript Dark-Mode Tactical Glassmorphism Command Center │
  │ • Leaflet / GeoJSON Live Interactive Fleet & Road Health Map                │
  │ • Real-Time Audio-Visual Incident Feed & Pothole Alert Banner               │
  │ • Optical Evidence Inspection Modal with Full-Resolution Frame Zoom         │
  │ • Analytics & Road Surface Quality Indexing (Defect Breakdown & Trends)     │
  └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Repository Structure

| Directory | Description | Primary Technologies |
|---|---|---|
| **[`backend/`](backend/)** | Central Command API, spatial database, incident triage & WebSockets | FastAPI, PostgreSQL, PostGIS, GeoAlchemy2, SQLAlchemy 2.0, Alembic |
| **[`frontend/`](frontend/)** | Real-time tactical dashboard for municipal & transit operators | React 18, Vite, TypeScript, TailwindCSS, Leaflet, Lucide Icons |
| **[`vehicle-tracking/`](vehicle-tracking/)** | Vehicle trajectory, speed anomalies, and traffic congestion sensing | Ultralytics YOLOv8, ByteTrack, OpenCV |
| **[`road-defect-detection/`](road-defect-detection/)** | Pothole & road distress detector, multi-camera deduplication & evidence capture | Ultralytics YOLOv8, ByteTrack, OpenCV, Shapely, Requests |

---

## 3. Quickstart & Local Setup

### Step 1: Central Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run migrations and start server
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```
* Interactive API Documentation: `http://localhost:8000/docs`

### Step 2: Operator Command Dashboard
```bash
cd frontend
npm install
npm run dev
```
* Dashboard URL: `http://localhost:5173`

### Step 3: Road Defect & Pothole Sensing Module
```bash
cd road-defect-detection
pip install -r requirements.txt

# Run single-camera inference on verification video with live backend sync
python main.py --video data/synthetic_test.mp4 --gps data/sample_gps.csv --send-backend

# Or run multi-camera concurrent simulation
python multi_camera.py --cameras front=data/synthetic_test.mp4 rear=data/synthetic_test.mp4 --send-backend
```

### Step 4: Vehicle Tracking & Traffic Telemetry
```bash
cd vehicle-tracking
pip install -r requirements.txt
python main.py
```

---

## 4. Key Innovation Highlights

1. **Temporal Anti-False-Positive Filtering**: Potholes and defects must persist across $\ge 3$ video frames within a sliding tracking window before an event is confirmed, eliminating transient shadows and camera shake artifacts.
2. **PostGIS Dual-Layer Deduplication**:
   * *Edge Layer*: Multi-camera cross-feed spatial clustering deduplicates sightings between front, rear, and side cameras within 10 meters.
   * *Central Layer*: PostGIS `ST_DWithin` spatial-temporal deduplication suppresses repeat sightings across bus trips, updating the canonical record when higher confidence is observed.
3. **Geometric Severity Rating**: Automatically computes distress square area and aspect ratio relative to roadway perspective to grade defects into actionable maintenance tiers (`low`, `medium`, `high`).
4. **Instant Optical Evidence**: Real high-resolution captured crops are uploaded directly to the central command static repository and instantly viewable on the operator's live map modal.
