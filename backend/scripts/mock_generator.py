"""
Mock AI Event Generator (Step 8)
Simulates an edge AI pipeline (YOLO + ByteTrack + OCR) running on a city bus.
Fabricates realistic road, traffic, and safety events along a moving GPS corridor,
supports multi-frame detection bursts, and continuously POSTs events to /api/v1/events.

Usage:
    python scripts/mock_generator.py --help
    python scripts/mock_generator.py --dry-run --count 5
    python scripts/mock_generator.py --count 10 --interval 1.0
    python scripts/mock_generator.py --burst-prob 1.0 --count 6
"""

import argparse
import json
import math
import os
import random
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from app.core.config import settings

# Ensure project root is in sys.path when executed directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pydantic import TypeAdapter, ValidationError
from app.schemas.event import EventCreate

# Local schema validator to catch any payload discrepancies before HTTP transmission
EVENT_ADAPTER = TypeAdapter(EventCreate)


# =============================================================================
# 1. GPS Route Simulator
# =============================================================================

# Realistic transit corridor in Patna along Bailey Road / Ashok Rajpath
# lon, lat ordering per PostGIS convention!
DEFAULT_WAYPOINTS: List[Tuple[float, float]] = [
    (85.1200, 25.5900),  # Saguna More / Danapur
    (85.1265, 25.5935),  # RPS More
    (85.1330, 25.5970),  # Gola Road
    (85.1410, 25.6015),  # Bailey Road Canal
    (85.1490, 25.6060),  # Ashiana More
    (85.1565, 25.6095),  # Raja Bazar / Pillar 60
    (85.1650, 25.6130),  # Sheikhpura
    (85.1740, 25.6165),  # Patna Zoo / Bailey Rd
    (85.1830, 25.6190),  # High Court / Dak Bungalow
    (85.1910, 25.6210),  # Gandhi Maidan
]


def haversine_distance_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate distance in meters between two coordinates."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class GPSRouteSimulator:
    """Simulates a vehicle driving back and forth along a list of waypoints."""

    def __init__(
        self,
        waypoints: List[Tuple[float, float]] = DEFAULT_WAYPOINTS,
        speed_kmh: float = 30.0,
    ):
        self.waypoints = waypoints
        self.speed_mps = speed_kmh / 3.6
        self.current_idx = 0
        self.direction = 1  # 1 for forward, -1 for reverse
        self.segment_progress_m = 0.0
        self.last_time = time.time()

    def get_next_coordinate(self) -> Tuple[float, float]:
        """Advance vehicle position based on elapsed time and return (lon, lat)."""
        now = time.time()
        dt = max(0.05, now - self.last_time)
        self.last_time = now

        distance_moved = self.speed_mps * dt
        self.segment_progress_m += distance_moved

        next_idx = self.current_idx + self.direction
        if next_idx >= len(self.waypoints):
            self.direction = -1
            next_idx = self.current_idx - 1
        elif next_idx < 0:
            self.direction = 1
            next_idx = self.current_idx + 1

        p1 = self.waypoints[self.current_idx]
        p2 = self.waypoints[next_idx]
        seg_distance = haversine_distance_m(p1[0], p1[1], p2[0], p2[1])

        if seg_distance <= 0.0:
            self.current_idx = next_idx
            self.segment_progress_m = 0.0
            return p2

        if self.segment_progress_m >= seg_distance:
            self.current_idx = next_idx
            self.segment_progress_m = 0.0
            return p2

        ratio = self.segment_progress_m / seg_distance
        lon = p1[0] + ratio * (p2[0] - p1[0])
        lat = p1[1] + ratio * (p2[1] - p1[1])
        return (round(lon, 6), round(lat, 6))


# =============================================================================
# 2. Event Fabricator
# =============================================================================

SEVERITIES = ["low", "medium", "high"]
EVENT_TYPES = [
    "pothole",
    "waterlogging",
    "signboard_damage",
    "zebra_crossing_issue",
    "traffic",
    "anpr",
    "hit_run",
]
EVENT_WEIGHTS = [0.30, 0.15, 0.10, 0.08, 0.20, 0.15, 0.02]

INDIAN_STATES = ["BR", "DL", "MH", "KA", "UP", "WB"]


def random_plate_number() -> str:
    """Generate realistic Indian license plate, e.g. BR01AB1234."""
    state = random.choice(INDIAN_STATES)
    rto = f"{random.randint(1, 99):02d}"
    series = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=2))
    digits = f"{random.randint(1000, 9999)}"
    return f"{state}{rto}{series}{digits}"


class EventFactory:
    """Fabricates schema-compliant event payloads matching app.schemas.event."""

    def __init__(self, bus_id: uuid.UUID, trip_id: uuid.UUID):
        self.bus_id = bus_id
        self.trip_id = trip_id
        self._track_counter = 1000

    def next_track_id(self, prefix: str = "obj") -> str:
        self._track_counter += 1
        return f"{prefix}_{self._track_counter}"

    def build_event(
        self,
        event_type: str,
        lon: float,
        lat: float,
        object_id: Optional[str] = None,
        confidence: Optional[float] = None,
        occurred_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Build a single validated event dictionary."""
        if confidence is None:
            confidence = round(random.uniform(0.72, 0.98), 3)

        if occurred_at is None:
            occurred_at = datetime.now(timezone.utc)
        elif occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)
        else:
            occurred_at = occurred_at.astimezone(timezone.utc)

        base: Dict[str, Any] = {
            "bus_id": str(self.bus_id),
            "trip_id": str(self.trip_id),
            "object_id": object_id or self.next_track_id(event_type[:4]),
            "confidence": confidence,
            "lon": lon,
            "lat": lat,
            "occurred_at": occurred_at.isoformat(),
            "event_type": event_type,
        }

        # Event-specific fields per discriminated union schema
        if event_type in (
            "pothole",
            "waterlogging",
            "signboard_damage",
            "zebra_crossing_issue",
        ):
            base["severity"] = random.choice(SEVERITIES)
            base["bbox"] = {
                "x": random.randint(100, 800),
                "y": random.randint(300, 900),
                "w": random.randint(80, 250),
                "h": random.randint(40, 180),
            }
        elif event_type == "traffic":
            base["severity"] = random.choice(SEVERITIES)
            base["bbox"] = None
        elif event_type == "anpr":
            base["plate_text"] = random_plate_number()
            base["plate_confidence"] = round(random.uniform(0.85, 0.99), 3)
            base["bbox"] = {
                "x": random.randint(200, 600),
                "y": random.randint(400, 700),
                "w": random.randint(120, 200),
                "h": random.randint(50, 90),
            }
        elif event_type == "hit_run":
            base["severity"] = "high"
            base["plate_text"] = random_plate_number()
            base["plate_confidence"] = round(random.uniform(0.75, 0.95), 3)
            base["evidence_url"] = f"/static/evidence/hit_run_{base['object_id']}.jpg"
            base["bbox"] = {
                "x": random.randint(150, 700),
                "y": random.randint(350, 750),
                "w": random.randint(140, 220),
                "h": random.randint(70, 110),
            }

        return base

    def build_burst(
        self,
        event_type: str,
        base_lon: float,
        base_lat: float,
        frames: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Build a multi-frame burst: same defect tracked across consecutive frames.
        Same object_id, timestamps separated by ~150-250ms, coordinates within < 3m.
        This provides the exact data pattern needed for Step 9 deduplication.
        """
        object_id = self.next_track_id(f"{event_type[:4]}_trk")
        base_confidence = random.uniform(0.82, 0.95)
        now = datetime.now(timezone.utc)
        events = []

        for i in range(frames):
            # Frame time delta ~150ms
            occurred_at = datetime.fromtimestamp(
                now.timestamp() + (i * 0.18), tz=timezone.utc
            )
            # Small jitter ~0.5 to 1.5m (~0.00001 deg is ~1.1m)
            jitter_lon = base_lon + random.uniform(-0.000015, 0.000015)
            jitter_lat = base_lat + random.uniform(-0.000015, 0.000015)
            conf_jitter = max(
                0.01,
                min(
                    0.999,
                    round(base_confidence + random.uniform(-0.04, 0.04), 3),
                ),
            )

            ev = self.build_event(
                event_type=event_type,
                lon=round(jitter_lon, 6),
                lat=round(jitter_lat, 6),
                object_id=object_id,
                confidence=conf_jitter,
                occurred_at=occurred_at,
            )
            events.append(ev)

        return events


# =============================================================================
# 3. Database Resolver (Auto-seeds demo Bus and Trip if needed)
# =============================================================================


def resolve_or_create_bus_and_trip(
    cli_bus_id: Optional[str] = None, cli_trip_id: Optional[str] = None
) -> Tuple[uuid.UUID, uuid.UUID]:
    """Ensure valid bus_id and trip_id exist to satisfy PostgreSQL foreign keys."""
    if cli_bus_id and cli_trip_id:
        return uuid.UUID(cli_bus_id), uuid.UUID(cli_trip_id)

    try:
        from app.db.session import SessionLocal
        from app.models import Bus, Trip

        db = SessionLocal()
        try:
            # 1. Resolve or create Bus
            bus = None
            if cli_bus_id:
                bus = db.query(Bus).filter(Bus.id == uuid.UUID(cli_bus_id)).first()
            if not bus:
                bus = db.query(Bus).first()
            if not bus:
                bus = Bus(
                    name="Patna City Transit - Bus 101",
                    registration_number="BR01P1001",
                )
                db.add(bus)
                db.commit()
                db.refresh(bus)
                print(f"[DB] Created demo Bus: {bus.id} ({bus.name})", flush=True)

            # 2. Resolve or create active Trip
            trip = None
            if cli_trip_id:
                trip = db.query(Trip).filter(Trip.id == uuid.UUID(cli_trip_id)).first()
            if not trip:
                trip = (
                    db.query(Trip)
                    .filter(Trip.bus_id == bus.id, Trip.ended_at.is_(None))
                    .first()
                )
            if not trip:
                trip = Trip(
                    bus_id=bus.id,
                    started_at=datetime.now(timezone.utc),
                    source="mock_generator",
                )
                db.add(trip)
                db.commit()
                db.refresh(trip)
                print(f"[DB] Created active Trip: {trip.id} (Bus: {bus.id})", flush=True)

            return bus.id, trip.id
        finally:
            db.close()
    except Exception as exc:
        print(f"[WARN] Could not connect to DB to resolve Bus/Trip: {exc}", flush=True)
        print("[WARN] Falling back to default mock UUIDs (may fail FK checks if POSTed to DB).", flush=True)
        return (
            uuid.UUID(cli_bus_id or "00000000-0000-0000-0000-000000000001"),
            uuid.UUID(cli_trip_id or "00000000-0000-0000-0000-000000000002"),
        )


# =============================================================================
# 4. HTTP Poster & Console Logger
# =============================================================================


def post_event_http(url: str, payload: Dict[str, Any], token: str) -> Tuple[int, Optional[Dict[str, Any]]]:
    """Send JSON POST to FastAPI /api/v1/events using stdlib urllib."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Service-Token": token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else None
    except urllib.error.HTTPError as he:
        body = he.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return he.code, parsed
    except urllib.error.URLError as ue:
        return 0, {"error": str(ue.reason)}

# =============================================================================
# 5. Main Execution Loop
# =============================================================================


def run_generator():
    parser = argparse.ArgumentParser(
        description="SIH26124 Edge AI Mock Event Generator"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/v1/events",
        help="Target API endpoint (default: http://localhost:8000/api/v1/events)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Interval in seconds between normal events (default: 2.0s)",
    )
    parser.add_argument(
        "--burst-prob",
        type=float,
        default=0.35,
        help="Probability of generating a multi-frame burst (default: 0.35)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Total number of events to emit (default: continuous / infinite)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=35.0,
        help="Simulated bus speed in km/h (default: 35.0)",
    )
    parser.add_argument(
        "--bus-id",
        type=str,
        default=None,
        help="Explicit bus UUID to use",
    )
    parser.add_argument(
        "--trip-id",
        type=str,
        default=None,
        help="Explicit trip UUID to use",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fabricate and print events without sending HTTP requests",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Service token override (default: reads SERVICE_TOKEN from .env via settings)",
    )

    args = parser.parse_args()

    # Resolve service token (skip entirely for dry runs, which never hit the network)
    service_token = args.token or settings.service_token
    if not args.dry_run and not service_token:
        print("[FATAL] No service token available. Set SERVICE_TOKEN in .env or pass --token.", flush=True)
        sys.exit(1)

    print("=" * 70, flush=True)
    print("  SIH26124 Edge AI Mock Event Generator (Step 8)", flush=True)
    print("=" * 70, flush=True)
    print(f"Target URL:    {args.url}", flush=True)
    print(f"Interval:      {args.interval}s", flush=True)
    print(f"Burst Prob:    {args.burst_prob * 100:.0f}%", flush=True)
    print(f"Bus Speed:     {args.speed} km/h", flush=True)
    print(f"Max Count:     {args.count or 'Infinite (press Ctrl+C to stop)'}", flush=True)
    print(f"Dry Run Mode:  {args.dry_run}", flush=True)
    print("-" * 70, flush=True)

    # Resolve bus and trip
    if args.dry_run and not (args.bus_id and args.trip_id):
        bus_id = uuid.uuid4()
        trip_id = uuid.uuid4()
        print(f"[DryRun] Generated transient bus_id={bus_id}, trip_id={trip_id}", flush=True)
    else:
        bus_id, trip_id = resolve_or_create_bus_and_trip(args.bus_id, args.trip_id)
        print(f"[Ready] Using bus_id={bus_id}, trip_id={trip_id}", flush=True)

    route_sim = GPSRouteSimulator(speed_kmh=args.speed)
    factory = EventFactory(bus_id=bus_id, trip_id=trip_id)

    emitted_count = 0

    try:
        while True:
            lon, lat = route_sim.get_next_coordinate()
            is_burst = random.random() < args.burst_prob

            # Select event type
            ev_type = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=1)[0]

            if is_burst and ev_type in (
                "pothole",
                "waterlogging",
                "signboard_damage",
                "zebra_crossing_issue",
            ):
                # Emit multi-frame burst for the same defect
                frames = random.randint(3, 5)
                burst_events = factory.build_burst(
                    ev_type, lon, lat, frames=frames
                )
                print(
                    f"\n>>> [BURST DETECTED] Simulating {frames} consecutive frames for {ev_type} (Track: {burst_events[0]['object_id']})",
                    flush=True,
                )

                for ev in burst_events:
                    if args.count and emitted_count >= args.count:
                        break

                    # Local schema validation before transmitting
                    try:
                        EVENT_ADAPTER.validate_python(ev)
                    except ValidationError as val_err:
                        print(
                            f"[SCHEMA_ERROR] Burst event failed local schema validation: {val_err}",
                            flush=True,
                        )
                        continue

                    emitted_count += 1
                    if args.dry_run:
                        print(
                            f"[#{emitted_count:03d} DRY-RUN] {ev['event_type']:<20} | obj: {ev['object_id']} | "
                            f"lon: {ev['lon']}, lat: {ev['lat']} | conf: {ev['confidence']}",
                            flush=True,
                        )
                    else:
                        status_code, resp = post_event_http(args.url, ev, service_token)
                        if status_code == 201:
                            print(
                                f"[#{emitted_count:03d} 201 OK] {ev['event_type']:<20} | obj: {ev['object_id']} | "
                                f"({ev['lon']}, {ev['lat']}) | conf: {ev['confidence']} -> ID: {resp.get('id', 'N/A')}",
                                flush=True,
                            )
                        else:
                            print(
                                f"[#{emitted_count:03d} ERR {status_code}] Failed: {resp}",
                                flush=True,
                            )

                    time.sleep(0.2)  # Multi-frame inter-arrival delay

            else:
                # Emit single steady-state cruising event
                ev = factory.build_event(ev_type, lon, lat)

                # Local schema validation before transmitting
                try:
                    EVENT_ADAPTER.validate_python(ev)
                except ValidationError as val_err:
                    print(
                        f"[SCHEMA_ERROR] Event failed local schema validation: {val_err}",
                        flush=True,
                    )
                    continue

                emitted_count += 1

                extra_info = ""
                if ev_type == "anpr":
                    extra_info = f"plate: {ev.get('plate_text')} ({ev.get('plate_confidence')})"
                elif ev_type == "hit_run":
                    extra_info = f"SUSPECTED HIT-AND-RUN | plate: {ev.get('plate_text')}"
                elif "severity" in ev:
                    extra_info = f"severity: {ev.get('severity')}"

                if args.dry_run:
                    print(
                        f"[#{emitted_count:03d} DRY-RUN] {ev['event_type']:<20} | obj: {ev['object_id']} | "
                        f"lon: {ev['lon']}, lat: {ev['lat']} | conf: {ev['confidence']} | {extra_info}",
                        flush=True,
                    )
                else:
                    status_code, resp = post_event_http(args.url, ev, service_token)
                    if status_code == 201:
                        print(
                            f"[#{emitted_count:03d} 201 OK] {ev['event_type']:<20} | obj: {ev['object_id']} | "
                            f"({ev['lon']}, {ev['lat']}) | conf: {ev['confidence']} -> ID: {resp.get('id', 'N/A')} | {extra_info}",
                            flush=True,
                        )
                    elif status_code == 0:
                        print(
                            f"[#{emitted_count:03d} CONN_ERR] Backend not reachable at {args.url}. Is uvicorn running?",
                            flush=True,
                        )
                    else:
                        print(
                            f"[#{emitted_count:03d} ERR {status_code}] Failed to ingest: {resp}",
                            flush=True,
                        )

            if args.count and emitted_count >= args.count:
                print(f"\n[Done] Reached target count of {args.count} events.", flush=True)
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n[Stopped] Mock generator interrupted by user after {emitted_count} events.", flush=True)


if __name__ == "__main__":
    run_generator()