# SmartBus Command Dashboard — Backend Architecture Analysis (`current.md`)

## 1. Tech Stack Detected

### Core Web Framework & Runtime
* **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (`v0.100+`) — High-performance Python ASGI web framework with automatic OpenAPI documentation.
* **ASGI Server**: [Uvicorn](https://www.uvicorn.org/) — Lightning-fast ASGI web server implementation.
* **Python Runtime**: Python 3.10+ (using standard async features, type annotations, and context managers).

### Database & Spatial Data Handling
* **Database**: [PostgreSQL](https://www.postgresql.org/) with the **PostGIS** extension for spatial-temporal geospatial indexing and spatial queries (`ST_DWithin`, `ST_MakeEnvelope`, `Geography(POINT, 4326)`).
* **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) (`v2.0+` style) configured with connection pooling (`pool_pre_ping=True`).
* **Spatial Tooling**: 
  * [GeoAlchemy2](https://geoalchemy2.readthedocs.io/) — Integrates SQLAlchemy with PostGIS spatial types (`Geography`).
  * [Shapely](https://shapely.readthedocs.io/) — Python library for geometric transformations (`Point`, `box`, `to_shape`, `from_shape`).
* **Migrations**: [Alembic](https://alembic.sqlalchemy.org/) — Database schema migration tool with revision tracking under `migrations/versions/`.
* **Database Driver**: `psycopg2-binary`.

### Data Validation & Settings Management
* **Validation**: [Pydantic v2](https://docs.pydantic.dev/) (`BaseModel`, `ConfigDict`, `field_validator`, discriminated union patterns).
* **Configuration**: `pydantic-settings` (`BaseSettings` reading from `.env`).

### Authentication & Security
* **Auth Scheme**: Header-based shared service token (`X-Service-Token`) validated with constant-time equality check (`secrets.compare_digest`). Deliberately lightweight; applied to write/mutation endpoints (`POST /events`, `PATCH /incidents`).

### Static File Storage & Media Handling
* **Static Mount**: FastAPI `StaticFiles` mounted at `/static` pointing to the local `backend/static` directory for storing and serving evidence snapshots (`/static/evidence/...`).

### Companion Edge / CV Module (`vehicle-tracking/`)
* **Computer Vision**: [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) (`yolov8s.pt`) + [ByteTrack](https://github.com/ifzhang/ByteTrack) for real-time vehicle detection, tracking, speed calculation, and zone-based density scoring on bus camera feeds.
* **HTTP Client**: `requests` for pushing telemetry and events to the backend.

---

## 2. Directory Structure

```
backend/
├── .env                              # Environment variables (DATABASE_URL, SERVICE_TOKEN)
├── .env.example                      # Template for environment configuration
├── alembic.ini                       # Alembic database migration config
├── requirements.txt                  # Python dependencies
├── test_event.json                   # Sample JSON event payload for testing
├── test_event_insert.py              # Script testing raw database event insertions
│
├── app/
│   ├── main.py                       # FastAPI application factory and router mounting
│   ├── api/
│   │   └── v1/
│   │       ├── events.py             # Event ingestion, spatial queries, and GeoJSON routes
│   │       ├── fleet.py              # Fleet summary and camera monitoring endpoints
│   │       ├── health.py             # Health check & system diagnostics endpoints
│   │       ├── incidents.py          # Incident lifecycle, listing, and operator triage routes
│   │       ├── traffic.py            # Traffic analytics, congestion, and road health summaries
│   │       └── websockets.py         # Real-time WebSocket connection endpoints
│   ├── core/
│   │   ├── config.py                 # Pydantic Settings configuration loader
│   │   ├── logging.py                # Logging configuration
│   │   └── security.py               # X-Service-Token header validation logic
│   ├── db/
│   │   ├── base.py                   # DeclarativeBase SQLAlchemy model root
│   │   └── session.py                # Database engine and SessionLocal dependency
│   ├── models/                       # SQLAlchemy Database ORM Models
│   │   ├── __init__.py               # Model package exports
│   │   ├── bus.py                    # Bus entity model
│   │   ├── camera.py                 # Edge camera entity model
│   │   ├── event.py                  # AI detection event entity with PostGIS location
│   │   ├── incident.py               # Auto-escalated safety incident model
│   │   ├── incident_evidence.py      # Incident evidence media relation model
│   │   └── trip.py                   # Bus transit trip model
│   ├── repositories/                 # Data access layer & SQL/spatial queries
│   │   ├── analytics_repository.py   # Aggregations for heatmaps, defects, & traffic
│   │   ├── event_repository.py       # Spatial queries, deduplication lookup, ST_DWithin
│   │   └── incident_repository.py    # Incident CRUD operations and queries
│   ├── schemas/                      # Pydantic Request/Response Models
│   │   ├── analytics.py              # Analytics and heatmap response contracts
│   │   ├── event.py                  # Ingestion union schemas, detail responses, GeoJSON
│   │   ├── fleet.py                  # Fleet inventory and system diagnostics schemas
│   │   └── incident.py               # Incident request and response schemas
│   └── services/                     # Business logic and coordination
│       ├── analytics_service.py      # Road quality indexing and traffic congestion calculations
│       ├── event_service.py          # Spatial-temporal deduplication and ingestion pipeline
│       ├── evidence_service.py       # Static filesystem evidence directory and dummy assets
│       ├── fleet_service.py          # Bus and camera status diagnostics
│       ├── incident_service.py       # Incident escalation rules and triage workflows
│       └── websocket_manager.py      # In-memory broadcast manager for events and alerts
│
├── migrations/                       # Alembic database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 70c8d91ef07c_create_events_table.py
│       ├── 840a464508a7_create_buses_cameras_trips.py
│       └── 99a8d91ef07d_create_incidents_tables.py
│
├── scripts/
│   └── mock_generator.py             # Realistic transit corridor GPS + AI event burst generator
│
├── static/
│   └── evidence/                     # Storage folder for incident images and vehicle crops
│
└── tests/                            # Pytest test suite (13 test modules)
    ├── test_analytics.py
    ├── test_auth.py
    ├── test_event_bad_payloads.py
    ├── test_event_dedup.py
    ├── test_event_queries.py
    ├── test_event_schemas.py
    ├── test_evidence.py
    ├── test_fleet_and_health.py
    ├── test_incidents.py
    ├── test_integration_full_pipeline.py
    ├── test_mock_generator.py
    └── test_websockets.py
```

---

## 3. Data Models

### A. Database Models (SQLAlchemy ORM)

#### 1. `Bus` (`buses`)
| Field | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key, `default=uuid.uuid4` | Unique bus identifier |
| `name` | `Text` | `nullable=False` | Display name (e.g., "Bus-101") |
| `registration_number` | `Text` | `unique=True`, `nullable=True` | License plate/registration number |
| `created_at` | `DateTime(timezone=True)` | `server_default=func.now()` | Registration timestamp |

#### 2. `Camera` (`cameras`)
| Field | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key, `default=uuid.uuid4` | Unique camera sensor identifier |
| `bus_id` | `UUID` | Foreign Key (`buses.id`), `nullable=False` | Host vehicle reference |
| `position` | `Text` | `nullable=True` | Placement (e.g., "windshield_front", "rear") |
| `created_at` | `DateTime(timezone=True)` | `server_default=func.now()` | Creation timestamp |

#### 3. `Trip` (`trips`)
| Field | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key, `default=uuid.uuid4` | Unique trip run identifier |
| `bus_id` | `UUID` | Foreign Key (`buses.id`), `nullable=False` | Assigned vehicle |
| `started_at` | `DateTime(timezone=True)` | `nullable=False` | Start timestamp |
| `ended_at` | `DateTime(timezone=True)` | `nullable=True` | Completion timestamp |
| `source` | `Text` | `nullable=True` | Mode flag (e.g. `"live"`, `"recorded:<filename>"`) |
| `created_at` | `DateTime(timezone=True)` | `server_default=func.now()` | Record creation timestamp |

#### 4. `Event` (`events`)
| Field | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key, `default=uuid.uuid4` | Unique event identifier |
| `event_type` | `Text` | `nullable=False`, Check constraint: `'pothole'`, `'waterlogging'`, `'signboard_damage'`, `'zebra_crossing_issue'`, `'traffic'`, `'anpr'`, `'hit_run'` | Classification type |
| `trip_id` | `UUID` | Foreign Key (`trips.id`), `nullable=False` | Active trip reference |
| `bus_id` | `UUID` | Foreign Key (`buses.id`), `nullable=False` | Detecting vehicle |
| `camera_id` | `UUID` | Foreign Key (`cameras.id`), `nullable=True` | Detecting camera |
| `object_id` | `Text` | `nullable=True` | ByteTrack tracking ID or unique object ID |
| `confidence` | `Numeric(4, 3)` | `nullable=False`, Check constraint: `0 <= confidence <= 1` | Detection confidence |
| `bbox` | `JSONB` | `nullable=True` | Bounding box coordinates `{x, y, w, h}` |
| `location` | `Geography(POINT, 4326)` | `nullable=True` | PostGIS spatial coordinate point |
| `occurred_at` | `DateTime(timezone=True)` | `nullable=False` | Real-world detection timestamp |
| `created_at` | `DateTime(timezone=True)` | `server_default=func.now()` | Ingestion timestamp |
| `severity` | `Text` | `nullable=True`, Check constraint: `'low'`, `'medium'`, `'high'` | Severity ranking |
| `plate_text` | `Text` | `nullable=True` | License plate string (for ANPR / Hit & Run) |
| `plate_confidence`| `Numeric(4, 3)` | `nullable=True` | OCR license plate confidence |
| `evidence_url` | `Text` | `nullable=True` | Path to media snapshot (`/static/evidence/...`) |
| `status` | `Text` | `nullable=False`, `default='stored'`, Check: `'stored'`, `'reviewed'`, `'resolved'`, `'false_positive'` | Lifecycle status |
| `metadata_` | `JSONB` (column `"metadata"`) | `nullable=True` | Arbitrary additional diagnostic metadata |

#### 5. `Incident` (`incidents`)
| Field | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key, `default=uuid.uuid4` | Unique incident identifier |
| `primary_event_id` | `UUID` | Foreign Key (`events.id`), `nullable=False` | Triggering event reference |
| `incident_type` | `Text` | `nullable=False`, Check constraint: `'suspected_collision'`, `'suspected_hit_and_run'` | Incident category |
| `status` | `Text` | `nullable=False`, `default='open'`, Check: `'open'`, `'under_review'`, `'closed'`, `'dismissed'` | Workflow state |
| `suspected_plate` | `Text` | `nullable=True` | Accused/involved vehicle license plate |
| `suspected_plate_confidence` | `Numeric(4, 3)` | `nullable=True` | OCR score |
| `location` | `Geography(POINT, 4326)` | `nullable=True` | Incident geographic coordinates |
| `occurred_at` | `DateTime(timezone=True)` | `nullable=False` | Occurrence timestamp |
| `created_at` | `DateTime(timezone=True)` | `server_default=func.now()` | Creation timestamp |
| `notes` | `Text` | `nullable=True` | Investigation/triage notes |

#### 6. `IncidentEvidence` (`incident_evidence`)
| Field | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key, `default=uuid.uuid4` | Unique evidence file ID |
| `incident_id` | `UUID` | Foreign Key (`incidents.id`), `nullable=False` | Associated incident |
| `evidence_type` | `Text` | `nullable=False`, Check: `'image'`, `'vehicle_crop'`, `'plate_crop'`, `'video_clip'` | File content type |
| `url` | `Text` | `nullable=False` | Static asset URL |
| `captured_at` | `DateTime(timezone=True)` | `server_default=func.now()` | Evidence capture timestamp |

---

### B. Request & Response Schemas (Pydantic Models)

#### 1. Ingestion Schemas (`app.schemas.event`)
* **`EventBase`**:
  * `trip_id: UUID`
  * `bus_id: UUID`
  * `camera_id: Optional[UUID] = None`
  * `object_id: Optional[str] = None`
  * `confidence: float` (`0.0 <= confidence <= 1.0`)
  * `bbox: Optional[dict] = None`
  * `lon: Optional[float] = None` (`-180.0 <= lon <= 180.0`)
  * `lat: Optional[float] = None` (`-90.0 <= lat <= 90.0`)
  * `occurred_at: datetime`
  * `severity: Optional[Literal["low", "medium", "high"]] = None`
  * `evidence_url: Optional[str] = None`
* **Polymorphic Event Payloads**:
  * `PotholeEvent`: `event_type: Literal["pothole"]`
  * `WaterloggingEvent`: `event_type: Literal["waterlogging"]`
  * `SignboardDamageEvent`: `event_type: Literal["signboard_damage"]`
  * `ZebraCrossingIssueEvent`: `event_type: Literal["zebra_crossing_issue"]`
  * `TrafficEvent`: `event_type: Literal["traffic"]`
  * `AnprEvent`: `event_type: Literal["anpr"]`, `plate_text: str`, `plate_confidence: float`
  * `HitRunEvent`: `event_type: Literal["hit_run"]`, `plate_text: Optional[str] = None`, `plate_confidence: Optional[float] = None`
* **`EventCreate`**: Discriminated Union of all 7 event schemas.

#### 2. Event Response Schemas
* **`EventResponse`**:
  * `id: UUID`
  * `event_type: str`
  * `trip_id: UUID`
  * `bus_id: UUID`
  * `confidence: float`
  * `lon: Optional[float]`
  * `lat: Optional[float]`
  * `occurred_at: datetime`
  * `created_at: datetime`
  * `severity: Optional[str]`
  * `status: str`
* **`EventDetailResponse`** (Extends `EventResponse`):
  * `camera_id: Optional[UUID]`
  * `object_id: Optional[str]`
  * `bbox: Optional[dict]`
  * `plate_text: Optional[str]`
  * `plate_confidence: Optional[float]`
  * `evidence_url: Optional[str]`
  * `metadata_: Optional[dict]`
* **`PaginatedEventResponse`**:
  * `total: int`
  * `limit: int`
  * `offset: int`
  * `items: List[EventResponse]`
* **GeoJSON Schemas (RFC 7946)**:
  * `GeoJSONFeatureGeometry`: `type: Literal["Point"]`, `coordinates: List[float]` (`[lon, lat]`)
  * `GeoJSONFeature`: `type: Literal["Feature"]`, `geometry: GeoJSONFeatureGeometry`, `properties: Dict[str, Any]`
  * `GeoJSONFeatureCollection`: `type: Literal["FeatureCollection"]`, `features: List[GeoJSONFeature]`

#### 3. Incident Schemas (`app.schemas.incident`)
* **`IncidentEvidenceResponse`**:
  * `id: UUID`, `incident_id: UUID`, `evidence_type: str`, `url: str`, `captured_at: datetime`
* **`IncidentResponse`**:
  * `id: UUID`, `primary_event_id: UUID`, `incident_type: str`, `status: str`, `suspected_plate: Optional[str]`, `suspected_plate_confidence: Optional[float]`, `lon: Optional[float]`, `lat: Optional[float]`, `occurred_at: datetime`, `created_at: datetime`, `notes: Optional[str]`
* **`IncidentDetailResponse`** (Extends `IncidentResponse`):
  * `evidence_items: List[IncidentEvidenceResponse]`
* **`IncidentUpdate`**:
  * `status: Optional[Literal["open", "under_review", "closed", "dismissed"]] = None`
  * `notes: Optional[str] = None`
* **`PaginatedIncidentResponse`**:
  * `total: int`, `limit: int`, `offset: int`, `items: List[IncidentResponse]`

#### 4. Fleet & Diagnostics Schemas (`app.schemas.fleet`)
* **`BusStatusResponse`**:
  * `id: UUID`, `name: Optional[str]`, `registration_number: Optional[str]`, `is_active: bool`, `total_trips: int`, `last_trip_started_at: Optional[datetime]`
* **`CameraStatusResponse`**:
  * `id: UUID`, `bus_id: UUID`, `name: str`, `camera_type: str`, `status: Literal["online", "offline"]`, `last_heartbeat: Optional[datetime]`
* **`FleetSummaryResponse`**:
  * `total_buses: int`, `active_buses: int`, `total_cameras: int`, `online_cameras: int`, `buses: List[BusStatusResponse]`, `cameras: List[CameraStatusResponse]`
* **`SystemHealthResponse`**:
  * `status: Literal["ok", "degraded", "error"]`, `database: str`, `total_events: int`, `total_incidents: int`, `active_ws_connections: int`, `evidence_storage_files: int`, `evidence_storage_bytes: int`, `server_time: datetime`

#### 5. Analytics Schemas (`app.schemas.analytics`)
* **`HeatmapPoint`**:
  * `lon: float`, `lat: float`, `weight: float` (`0.0 <= weight <= 1.0`), `event_type: str`, `severity: Optional[str]`
* **`HeatmapResponse`**:
  * `total: int`, `points: List[HeatmapPoint]`
* **`TrafficAnalyticsResponse`**:
  * `total_events: int`, `anpr_count: int`, `traffic_count: int`, `congestion_level: Literal["low", "moderate", "severe"]`, `average_confidence: float`
* **`RoadHealthSummaryResponse`**:
  * `total_defects: int`, `potholes_count: int`, `waterlogging_count: int`, `signboard_damage_count: int`, `zebra_crossing_issue_count: int`, `road_quality_index: float` (0 to 100), `risk_level: Literal["low", "medium", "high"]`

---

## 4. REST API Endpoints

All application API endpoints are mounted under `/api/v1`.

| Method | Route Path | Auth Required | Request Parameters / Body | Response Status & Schema |
|---|---|---|---|---|
| **POST** | `/api/v1/events` | `X-Service-Token` | **Body**: `EventCreate` (JSON) | `201 Created` → `EventResponse`<br>*Deduplicates within 5s / 10m. Spawns incident if hit_run.* |
| **GET** | `/api/v1/events` | None | **Query**: `event_type`, `severity`, `status`, `trip_id`, `bus_id`, `start_time`, `end_time`, `limit` (default 100, max 1000), `offset` (default 0) | `200 OK` → `PaginatedEventResponse` |
| **GET** | `/api/v1/events/nearby` | None | **Query**: `lon` (req), `lat` (req), `radius_m` (default 500), `event_type`, `severity`, `limit` (default 100), `offset` (default 0) | `200 OK` → `PaginatedEventResponse` |
| **GET** | `/api/v1/events/bbox` | None | **Query**: `min_lon` (req), `min_lat` (req), `max_lon` (req), `max_lat` (req), `event_type`, `severity`, `limit` (default 500, max 2000), `offset` (default 0) | `200 OK` → `GeoJSONFeatureCollection` |
| **GET** | `/api/v1/events/geojson` | None | **Query**: `event_type`, `severity`, `status`, `trip_id`, `bus_id`, `limit` (default 500, max 2000), `offset` (default 0) | `200 OK` → `GeoJSONFeatureCollection` |
| **GET** | `/api/v1/events/{event_id}` | None | **Path**: `event_id: UUID` | `200 OK` → `EventDetailResponse`<br>`404 Not Found` |
| **GET** | `/api/v1/incidents` | None | **Query**: `status`, `incident_type`, `limit` (default 100), `offset` (default 0) | `200 OK` → `PaginatedIncidentResponse` |
| **GET** | `/api/v1/incidents/{incident_id}` | None | **Path**: `incident_id: UUID` | `200 OK` → `IncidentDetailResponse`<br>`404 Not Found` |
| **PATCH** | `/api/v1/incidents/{incident_id}` | `X-Service-Token` | **Path**: `incident_id: UUID`<br>**Body**: `IncidentUpdate` (`status`, `notes`) | `200 OK` → `IncidentDetailResponse`<br>`404 Not Found` |
| **GET** | `/api/v1/traffic/heatmap` | None | **Query**: `min_lon`, `min_lat`, `max_lon`, `max_lat`, `event_type`, `limit` (default 1000, max 5000) | `200 OK` → `HeatmapResponse` |
| **GET** | `/api/v1/traffic/analytics` | None | **Query**: `start_time`, `end_time` | `200 OK` → `TrafficAnalyticsResponse` |
| **GET** | `/api/v1/analytics/road-health` | None | **Query**: `start_time`, `end_time` | `200 OK` → `RoadHealthSummaryResponse` |
| **GET** | `/api/v1/fleet/summary` | None | None | `200 OK` → `FleetSummaryResponse` |
| **GET** | `/api/v1/fleet/cameras` | None | None | `200 OK` → `{"total": int, "cameras": List[CameraStatusResponse]}` |
| **GET** | `/api/v1/health` | None | None | `200 OK` → `{"status": "ok" \| "degraded", "database": "connected" \| "error: ..."}` |
| **GET** | `/api/v1/health/system` | None | None | `200 OK` → `SystemHealthResponse` |
| **GET** | `/static/{file_path}` | None | **Path**: Static file path | `200 OK` → Static image / file content |

---

## 5. WebSocket Endpoints

The backend maintains two persistent WebSocket endpoints managed by `ConnectionManager` (`app/services/websocket_manager.py`).

### 1. Live Events Feed: `ws://<host>:<port>/api/v1/ws/events`
* **Purpose**: Streams new road hazard detections, traffic observations, and ANPR events immediately upon ingestion.
* **Client Handling**: Accepts connection, keeps socket alive with incoming text ping/heartbeat, removes on disconnect.
* **Broadcast Trigger**: Triggered asynchronously during `POST /api/v1/events` when an event is accepted.
* **Emitted JSON Structure**:
```json
{
  "id": "e2f07ab9-7098-4c91-b3eb-46b78297b102",
  "event_type": "pothole",
  "trip_id": "97e6e587-84aa-4933-9799-a9a7aef1fba5",
  "bus_id": "4b63889b-fbf7-4228-a3f1-0819198642ae",
  "confidence": 0.94,
  "lon": 85.141205,
  "lat": 25.601522,
  "occurred_at": "2026-09-04T15:30:00+00:00",
  "created_at": "2026-09-04T15:30:01.428192+00:00",
  "severity": "high",
  "status": "stored"
}
```

### 2. Live Safety Incident Alerts: `ws://<host>:<port>/api/v1/ws/incidents`
* **Purpose**: Broadcasts safety-critical alerts (e.g., hit & run, collision) spawned by the event ingestion pipeline to alert command center dispatchers.
* **Client Handling**: Accepts connection, handles ping/heartbeat, cleans up dead sockets.
* **Broadcast Trigger**: Triggered when `evaluate_and_spawn_incident` creates a new `Incident` and associated evidence.
* **Emitted JSON Structure**:
```json
{
  "id": "7b58c738-95d8-4f51-b0e2-7634f19ca012",
  "primary_event_id": "b3e005d2-0691-4e4b-a25e-3d1911475149",
  "incident_type": "suspected_hit_and_run",
  "status": "open",
  "suspected_plate": "BR01AB9876",
  "suspected_plate_confidence": 0.892,
  "lon": 85.156510,
  "lat": 25.609530,
  "occurred_at": "2026-09-04T15:32:10+00:00",
  "created_at": "2026-09-04T15:32:10.910243+00:00",
  "notes": "Auto-spawned from AI detection pipeline (hit_run).",
  "evidence_items": [
    {
      "id": "a98e2195-bf34-4537-8e6f-68f76d49bc80",
      "incident_id": "7b58c738-95d8-4f51-b0e2-7634f19ca012",
      "evidence_type": "image",
      "url": "/static/evidence/evidence_image_8b21c4fa.jpg",
      "captured_at": "2026-09-04T15:32:10+00:00"
    },
    {
      "id": "5f1c9041-3891-4965-b1a7-cf25f0563b71",
      "incident_id": "7b58c738-95d8-4f51-b0e2-7634f19ca012",
      "evidence_type": "plate_crop",
      "url": "/static/evidence/evidence_plate_crop_8b21c4fa.jpg",
      "captured_at": "2026-09-04T15:32:10+00:00"
    }
  ]
}
```

---

## 6. Missing Elements

The following structural, architectural, and protocol gaps should be addressed before or during frontend implementation:

1. **CORS Middleware Missing on FastAPI**:
   * `app/main.py` instantiates `FastAPI` without `CORSMiddleware`. Any modern frontend (e.g. running on `http://localhost:3000` or `5173`) will encounter CORS preflight rejections on all API requests.
2. **No Real-Time Bus Telemetry / GPS Tracking Stream**:
   * The backend currently tracks events recorded *by* buses, but has **no bus GPS telemetry ingestion endpoint** (e.g. `POST /api/v1/fleet/telemetry` or `ws://.../ws/telemetry`) to transmit live bus coordinates, speed, heading, and route progression.
   * Without this, moving bus markers on a real-time command map cannot be animated without inferring position from sporadic defect events.
3. **Static Mock Fleet & Camera Diagnostics**:
   * In `app/services/fleet_service.py`, `CameraStatusResponse` returns hardcoded `"online"` with artificial timestamps. There is no active heartbeat ingestion endpoint for camera sensors or edge devices to report real network availability or FPS metrics.
4. **No Broadcast on Incident Status Triage / Updates**:
   * While newly created incidents trigger `broadcast_incident`, updating an incident's status or notes (`PATCH /api/v1/incidents/{incident_id}`) **does not broadcast the update** over `ws/incidents`. Operators viewing the dashboard simultaneously will not see real-time updates when a colleague closes or updates an incident without manually refreshing.
5. **No Mutation Route for Event Verification / False Positives**:
   * While `Event` has a `status` field (`'stored'`, `'reviewed'`, `'resolved'`, `'false_positive'`), there is no REST route (e.g. `PATCH /api/v1/events/{id}`) allowing operators to review, verify, or dismiss road defect events.
6. **No Operator Authentication or Role-Based Access (RBAC)**:
   * Endpoints are either public (read queries) or protected by a single shared `X-Service-Token` intended for machine-to-machine edge ingestion. There is no session/JWT operator auth, user login, or audit trail identifying which officer triaged an incident.
7. **Multipart File / Video Clip Upload Route**:
   * Evidence media URLs are either supplied as string references or generated as synthetic dummy files by `generate_sample_evidence()`. An endpoint accepting `multipart/form-data` uploads is needed for real camera snapshot transmissions.
8. **Trip Breadcrumb Trace / Trajectory Route**:
   * `trips` records start and end timestamps, but does not store a GPS line string or ordered sequence of waypoints, making retrospective trip route playback impossible without custom reconstruction.
