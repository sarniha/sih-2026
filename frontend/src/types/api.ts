/**
 * Strict TypeScript API and Data Contracts for SmartBus Command Dashboard
 * Mirrors FastAPI models & PostgreSQL PostGIS database check constraints.
 */

// ============================================================================
// 1. Enums & Literal Types (Matching DB Check Constraints)
// ============================================================================

export type EventType =
  | "pothole"
  | "waterlogging"
  | "signboard_damage"
  | "zebra_crossing_issue"
  | "traffic"
  | "anpr"
  | "hit_run";

export type Severity = "low" | "medium" | "high";

export type EventStatus =
  | "stored"
  | "reviewed"
  | "resolved"
  | "false_positive";

export type IncidentType =
  | "suspected_collision"
  | "suspected_hit_and_run";

export type IncidentStatus =
  | "open"
  | "under_review"
  | "closed"
  | "dismissed";

export type EvidenceType =
  | "image"
  | "vehicle_crop"
  | "plate_crop"
  | "video_clip";

export type CameraStatus = "online" | "offline";

export type SystemHealthStatus = "ok" | "degraded" | "error";

export type CongestionLevel = "low" | "moderate" | "severe";

export type RiskLevel = "low" | "medium" | "high";

// ============================================================================
// 2. Event Contracts
// ============================================================================

export interface EventBasePayload {
  trip_id: string; // UUID
  bus_id: string; // UUID
  camera_id?: string | null;
  object_id?: string | null;
  confidence: number;
  bbox?: Record<string, any> | null;
  lon?: number | null;
  lat?: number | null;
  occurred_at: string;
  severity?: Severity | null;
  evidence_url?: string | null;
}

export interface EventResponse {
  id: string; // UUID
  event_type: EventType | string;
  trip_id: string;
  bus_id: string;
  confidence: number;
  lon: number | null;
  lat: number | null;
  occurred_at: string;
  created_at: string;
  severity: Severity | string | null;
  status: EventStatus | string;
  camera_id?: string | null;
  object_id?: string | null;
  plate_text?: string | null;
  plate_confidence?: number | null;
  evidence_url?: string | null;
}

export interface EventDetailResponse extends EventResponse {
  bbox?: Record<string, any> | null;
  metadata_?: Record<string, any> | null;
}

export interface PaginatedEventResponse {
  total: number;
  limit: number;
  offset: number;
  items: EventResponse[];
}

// RFC 7946 GeoJSON
export interface GeoJSONFeatureGeometry {
  type: "Point";
  coordinates: [number, number]; // [lon, lat]
}

export interface GeoJSONFeature {
  type: "Feature";
  geometry: GeoJSONFeatureGeometry;
  properties: {
    id: string;
    event_type: string;
    trip_id: string;
    bus_id: string;
    confidence: number | null;
    severity: string | null;
    status: string;
    occurred_at: string | null;
    created_at: string | null;
    evidence_url: string | null;
    plate_text: string | null;
    [key: string]: any;
  };
}

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
}

// ============================================================================
// 3. Incident Contracts
// ============================================================================

export interface IncidentEvidenceResponse {
  id: string; // UUID
  incident_id: string; // UUID
  evidence_type: EvidenceType | string;
  url: string;
  captured_at: string;
}

export interface IncidentResponse {
  id: string; // UUID
  primary_event_id: string; // UUID
  incident_type: IncidentType | string;
  status: IncidentStatus | string;
  suspected_plate: string | null;
  suspected_plate_confidence: number | null;
  lon: number | null;
  lat: number | null;
  occurred_at: string;
  created_at: string;
  notes: string | null;
}

export interface IncidentDetailResponse extends IncidentResponse {
  evidence_items: IncidentEvidenceResponse[];
}

export interface IncidentUpdate {
  status?: IncidentStatus | null;
  notes?: string | null;
}

export interface IncidentCreate {
  suspected_plate: string;
  notes?: string | null;
  incident_type?: IncidentType | string;
}

export interface PaginatedIncidentResponse {
  total: number;
  limit: number;
  offset: number;
  items: IncidentResponse[];
}

// ============================================================================
// 4. Fleet & Hardware Diagnostics Contracts
// ============================================================================

export interface BusStatusResponse {
  id: string; // UUID
  name: string | null;
  registration_number: string | null;
  is_active: boolean;
  total_trips: number;
  last_trip_started_at: string | null;
}

export interface CameraStatusResponse {
  id: string; // UUID
  bus_id: string; // UUID
  name: string;
  camera_type: string;
  status: CameraStatus;
  last_heartbeat: string | null;
}

export interface FleetSummaryResponse {
  total_buses: number;
  active_buses: number;
  total_cameras: number;
  online_cameras: number;
  buses: BusStatusResponse[];
  cameras: CameraStatusResponse[];
}

export interface SystemHealthResponse {
  status: SystemHealthStatus;
  database: string;
  total_events: number;
  total_incidents: number;
  active_ws_connections: number;
  evidence_storage_files: number;
  evidence_storage_bytes: number;
  server_time: string;
}

// ============================================================================
// 5. Traffic & Road Health Analytics Contracts
// ============================================================================

export interface HeatmapPoint {
  lon: number;
  lat: number;
  weight: number;
  event_type: string;
  severity: string | null;
}

export interface HeatmapResponse {
  total: number;
  points: HeatmapPoint[];
}

export interface TrafficAnalyticsResponse {
  total_events: number;
  anpr_count: number;
  traffic_count: number;
  congestion_level: CongestionLevel;
  average_confidence: number;
}

export interface RoadHealthSummaryResponse {
  total_defects: number;
  potholes_count: number;
  waterlogging_count: number;
  signboard_damage_count: number;
  zebra_crossing_issue_count: number;
  road_quality_index: number;
  risk_level: RiskLevel;
}
