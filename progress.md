# SmartBus Command Dashboard — Implementation Progress

## Milestone 1: Frontend Foundation & Architecture Setup

### ✅ Step 1: Fix Backend CORS
* **File Updated**: [`backend/app/main.py`](file:///c:/Users/Asus/Desktop/sih-2026/backend/app/main.py)
* **Actions Taken**:
  * Imported `CORSMiddleware` from `fastapi.middleware.cors`.
  * Added CORS middleware to `FastAPI` app instance with `allow_origins=["*"]`, `allow_credentials=True`, `allow_methods=["*"]`, and `allow_headers=["*"]`.
  * Allows Vite dev server (`http://localhost:5173`) and local API consumers to connect without browser preflight blocking.

---

### ✅ Step 2: Initialize Frontend Scaffold
* **Project Directory**: [`frontend/`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/)
* **Stack**: Vite + React 19 + TypeScript + Tailwind CSS
* **Dependencies Installed**:
  * `react-router-dom`: SPA routing & history management
  * `lucide-react`: High-contrast icon suite for command rail and headers
  * `clsx` & `tailwind-merge`: Dynamic and collision-safe utility class composition
  * `tailwindcss`, `postcss`, `autoprefixer`: Utility-first CSS engine
* **Theme Configuration**:
  * [`frontend/tailwind.config.js`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/tailwind.config.js): Custom `command` dark palette (`#0b0f17` background, `#0f172a` surface, slate accents) and `radar` semantic status colors (emerald, amber, red, cyan).
  * [`frontend/src/index.css`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/index.css): Base Tailwind directives, dark mode defaults, and command center scrollbars.
  * [`frontend/src/lib/utils.ts`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/lib/utils.ts): Exported `cn()` helper.

---

### ✅ Step 3: Strict TypeScript Data Contracts
* **File Created**: [`frontend/src/types/api.ts`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/types/api.ts)
* **Contracts Defined**:
  * **Enums & Types (Matching DB Check Constraints)**:
    * `EventType`: `'pothole' | 'waterlogging' | 'signboard_damage' | 'zebra_crossing_issue' | 'traffic' | 'anpr' | 'hit_run'`
    * `Severity`: `'low' | 'medium' | 'high'`
    * `EventStatus`: `'stored' | 'reviewed' | 'resolved' | 'false_positive'`
    * `IncidentType`: `'suspected_collision' | 'suspected_hit_and_run'`
    * `IncidentStatus`: `'open' | 'under_review' | 'closed' | 'dismissed'`
    * `EvidenceType`: `'image' | 'vehicle_crop' | 'plate_crop' | 'video_clip'`
    * `CameraStatus`: `'online' | 'offline'`
    * `SystemHealthStatus`: `'ok' | 'degraded' | 'error'`
    * `CongestionLevel`: `'low' | 'moderate' | 'severe'`
    * `RiskLevel`: `'low' | 'medium' | 'high'`
  * **Core Interfaces**:
    * `EventResponse`, `EventDetailResponse`, `PaginatedEventResponse`
    * `GeoJSONFeature`, `GeoJSONFeatureGeometry`, `GeoJSONFeatureCollection` (RFC 7946)
    * `IncidentResponse`, `IncidentDetailResponse`, `IncidentEvidenceResponse`, `IncidentUpdate`, `PaginatedIncidentResponse`
    * `BusStatusResponse`, `CameraStatusResponse`, `FleetSummaryResponse`, `SystemHealthResponse`
    * `HeatmapPoint`, `HeatmapResponse`, `TrafficAnalyticsResponse`, `RoadHealthSummaryResponse`

---

### ✅ Step 4: Build Global Shell & Routing
* **Components Built**:
  1. [`frontend/src/components/layout/Header.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/layout/Header.tsx):
     * App branding: `SMARTBUS COMMAND // PATNA LIVE`
     * Visual animated **System Online** status indicator (`#10b981` pulsating radar dot)
     * Real-time live digital clock
     * Active incident notification bell with badge counter
     * Operator station badge (`OP1`) and API status indicator
  2. [`frontend/src/components/layout/Sidebar.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/layout/Sidebar.tsx):
     * Navigation rail with high-contrast active state indicators
     * 7 command routes:
       * 📍 **Live Map** (`/`)
       * ⚡ **Traffic** (`/traffic`)
       * 🚨 **ANPR / Incidents** (`/anpr`) with `LIVE` status badge
       * 📁 **Case Registry** (`/cases`)
       * 🚌 **Fleet** (`/fleet`)
       * 📊 **Insights** (`/insights`)
       * ⚙️ **Settings** (`/settings`)
     * Bottom edge status card showing active edge node telemetry and deduplication metrics
  3. [`frontend/src/components/layout/Layout.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/layout/Layout.tsx):
     * Unified viewport shell joining Header, Sidebar, and scrollable `<Outlet />`
  4. [`frontend/src/App.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/App.tsx):
     * `BrowserRouter` configuration mapping all 7 routes to dedicated page placeholder components under [`frontend/src/pages/`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/pages/)
* **Build Validation**:
  * Verified with `tsc -b && vite build` — production bundle compiles cleanly with 0 type errors.

---

### ✅ Step 5: Live Map & WebSocket Integration

#### 5.1 — Map Dependencies
* Installed `leaflet`, `react-leaflet`, and `@types/leaflet`.

#### 5.2 — WebSocket Hook
* **File**: [`frontend/src/hooks/useLiveEvents.ts`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/hooks/useLiveEvents.ts)
* Connects to `ws://localhost:8000/api/v1/ws/events`.
* Maintains a rolling buffer of the latest 100 `EventResponse` objects.
* Exports `events: EventResponse[]` and `status: WsConnectionStatus` (`connected` | `reconnecting` | `disconnected` | `error`).
* Features:
  * Exponential backoff auto-reconnection (1s → 15s cap).
  * 25s heartbeat ping to keep the socket alive.
  * Cleanup on unmount.

#### 5.3 — LiveMap Component
* **File**: [`frontend/src/components/map/LiveMap.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/map/LiveMap.tsx)
* Leaflet CSS imported at top, default icon bug fixed via CDN fallback.
* Custom SVG `DivIcon` markers color-coded per event type:
  * 🔴 `hit_run` → red, 🟡 `pothole` → yellow, 🔵 `traffic` → blue, 🟠 `anpr` → amber, 🟢 `waterlogging` → cyan, 🟣 `signboard_damage` → purple, 🟧 `zebra_crossing_issue` → orange.
* Map centered on Delhi (`[28.6139, 77.2090]`) at zoom 13 with OpenStreetMap tiles.
* `<Popup>` shows: event type, severity badge, confidence %, detection time, coords, and "View Evidence" button.

#### 5.4 — LiveFeedPanel
* **File**: [`frontend/src/components/feed/LiveFeedPanel.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/feed/LiveFeedPanel.tsx)
* Split layout:
  * **Top 60%**: General event feed (potholes, traffic, ANPR, waterlogging, etc.) with Lucide icons per type, severity badges, and relative timestamps.
  * **Bottom 40%**: High-priority alerts (filtered for `hit_run` or `severity === "high"`). Cards styled with faint red/amber bg and pulsating border animation.
* Empty-state messaging when no events are received.

#### 5.5 — MapPage Assembly
* **File**: [`frontend/src/pages/MapPage.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/pages/MapPage.tsx)
* Responsive layout: `flex-col lg:flex-row h-full overflow-hidden`.
* Left: `LiveMap` (flex-grow), Right: `LiveFeedPanel` (`w-96` fixed on desktop).
* Floating WS connection badge overlaid on map.
* Syncs WebSocket status to global context via `useWsStatus`.

#### 5.6 — Header WebSocket Integration
* **File**: [`frontend/src/components/layout/Header.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/layout/Header.tsx)
* System Online indicator now reads real `WsConnectionStatus` from context:
  * 🟢 `connected` → green pulsing dot + "SYSTEM ONLINE"
  * 🟡 `reconnecting` → amber pulsing dot + "RECONNECTING"
  * 🔴 `disconnected`/`error` → red dot + "SYSTEM OFFLINE"
* **Context**: [`frontend/src/contexts/WsStatusContext.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/contexts/WsStatusContext.tsx)
* **App wrapper**: [`frontend/src/App.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/App.tsx) wraps all routes in `<WsStatusProvider>`.

#### Build Verification
* `tsc -b && vite build` passed with **0 type errors**.
* Production bundle: `index.js 438 kB (135 kB gzipped)`, `index.css 30 kB (10 kB gzipped)`.

---

### ✅ Step 6: Traffic Density Analytics Page (`/traffic`)

#### 6.1 — Data Fetching Hook
* **File**: [`frontend/src/hooks/useTrafficAnalytics.ts`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/hooks/useTrafficAnalytics.ts)
* Fetches `GET /api/v1/traffic/analytics` with `fetch`.
* Returns `{ data: TrafficAnalyticsResponse | null, isLoading, error, refresh }`.
* `refresh()` callable for manual reload.

#### 6.2 — Reusable UI Components
* **StatCard**: [`frontend/src/components/ui/StatCard.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/ui/StatCard.tsx)
  * Accepts `title`, `value`, `icon`, `trend`, `colorClass`. Dark card (`bg-[#131e36]`, `border-[#1e293b]`). Icon badge with dynamic color. Hover scale effect.
* **CongestionPanel**: [`frontend/src/components/traffic/CongestionPanel.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/traffic/CongestionPanel.tsx)
  * Dynamic text/border/bar colors: emerald (low), amber (moderate), red (severe).
  * Animated progress bar, severity icon, description text.
  * Fallback UI for undefined/unrecognized levels.

#### 6.3 — TrafficPage Assembly
* **File**: [`frontend/src/pages/TrafficPage.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/pages/TrafficPage.tsx)
* State handling:
  * **Loading**: 4 skeleton cards + 1 skeleton panel (`animate-pulse`).
  * **Error**: Red error boundary card with "Retry Connection" button.
  * **Empty**: Centered `BarChart2` icon with "No traffic data available".
* Main layout: header with Refresh button, 4-column StatCard grid (`total_events`, `traffic_count`, `anpr_count`, `average_confidence`), full-width CongestionPanel.

#### Build Verification
* `tsc -b && vite build` passed with **0 type errors**.

---

### ✅ Step 7: ANPR & Incidents Page (`/anpr`)

#### 7.1 — Data Fetching Hook
* **File**: [`frontend/src/hooks/useAnprEvents.ts`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/hooks/useAnprEvents.ts)
* Fetches data from `http://127.0.0.1:8000/api/v1/events?event_type=anpr&limit=200` via `useEffect`.
* Manages `rawEvents` (`EventResponse[]`), `groupedEvents`, `isLoading`, `error`, and `refresh()`.

#### 7.2 — Deduplication Logic
* **File**: [`frontend/src/lib/anpr.ts`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/lib/anpr.ts)
* `groupAnprEvents()` groups raw events by `object_id` (edge tracking identifier).
* Retains only the single event per `object_id` with the highest `plate_confidence` (or fallback confidence).
* Lacking an `object_id` triggers treatment as an isolated event.
* Returns deduplicated events chronologically sorted by detection time.

#### 7.3 — ANPR Card Component
* **File**: [`frontend/src/components/anpr/AnprCard.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/anpr/AnprCard.tsx)
* **Plate Rendering**: High-contrast Indian license plate pill (`bg-amber-400 text-slate-950 font-mono font-black`) with `IND` badge and bold tracking.
* **Null Handling (CRITICAL)**: If `plate_text` is null, empty, or unreadable, explicitly displays `"Plate not readable"` in muted gray styling with a warning icon.
* **Confidence UI**: Displays formatted percentage with dynamic badge styling:
  * `< 60%`: Amber badge with `AlertTriangle` warning icon and `"Low Conf"` indicator.
  * `≥ 60%`: Emerald badge with `ShieldCheck` icon.
* **Evidence Placeholder**: Displays `<img src={evidence_url} />` if available; smoothly falls back on load error or absence to a dark placeholder card with a `CameraOff` icon.
* **Footer Metadata**: Edge vehicle tracking tag (`object_id`), Bus ID, and formatted detection timestamp.

#### 7.4 — ANPR Page Assembly
* **File**: [`frontend/src/pages/AnprPage.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/pages/AnprPage.tsx)
* **View Mode Toggle**: Interactive selector between `"Grouped (Best Read)"` and `"Raw Stream"`.
* **Header Counters**: Displays dynamic record counts based on active view mode (`Showing X Unique Vehicles` vs `Showing Y Total Frames`), including deduplication summary.
* **State Handling**:
  * **Loading**: Grid of 6 animated pulse skeleton cards (`grid-cols-1 md:grid-cols-2 lg:grid-cols-3`).
  * **Error**: Red error boundary card with message and `"Retry Connection"` button.
  * **Empty**: Centered `Car` icon state with instructions to activate edge feeds or mock generators.
* **Main Layout**: Responsive 3-column grid (`grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`) rendering `AnprCard` components.

#### Build Verification
* `tsc -b && vite build` passed with **0 type errors**.
* Production bundle: `index.js 458.28 kB (139.87 kB gzipped)`, `index.css 35.97 kB (11.30 kB gzipped)`.

---

### ✅ Step 8: Case Registry & Incidents Page (`/cases`)

#### 8.1 — Data Fetching Hook
* **File**: [`frontend/src/hooks/useCases.ts`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/hooks/useCases.ts)
* Fetches data from `http://127.0.0.1:8000/api/v1/incidents?limit=200` based on `IncidentResponse` contract.
* Manages `cases` (`IncidentResponse[]`), `isLoading`, and `error`.
* Implements `submitNewCase(plate_text, notes)`:
  * Dispatches `POST` request to `/api/v1/incidents` with normalized uppercase plate.
  * Automatically invokes `fetchCases()` refresh on resolution to sync the table in real time.

#### 8.2 — Case Form Component
* **File**: [`frontend/src/components/cases/NewCaseForm.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/cases/NewCaseForm.tsx)
* Dark-themed card (`bg-slate-800 border-slate-700 rounded-xl p-6`).
* Input for `suspected_plate` (enforcing uppercase visual treatment with monospace font).
* Textarea for incident notes and citizen report context.
* Disabled submit button with `Loader2` spinner during execution.
* Displays 5-second green dismissible success notification and clears fields upon submission.

#### 8.3 — Case Table Component
* **File**: [`frontend/src/components/cases/CaseTable.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/cases/CaseTable.tsx)
* Responsive full-width data table with dark table styling and hover highlights.
* Columns: **Date Reported**, **Suspect Plate**, **Status**, **Notes & Details**, **Actions**.
* Status Badges:
  * `open`: Sky blue badge (`bg-sky-500/10 text-sky-400`).
  * `under_review`: Amber badge (`bg-amber-500/10 text-amber-400`).
  * `closed`: Emerald green badge (`bg-emerald-500/10 text-emerald-400`).
  * `dismissed`: Muted slate badge (`bg-slate-700/40 text-slate-400`).
* If case has a `primary_event_id`, renders a `"View Match"` button triggering an inspect modal with telemetry, GPS coordinates, and incident reference metadata.

#### 8.4 — Cases Page Assembly
* **File**: [`frontend/src/pages/CasesPage.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/pages/CasesPage.tsx)
* Header with `h1` "Active Case Registry" and manual refresh action.
* Desktop two-column layout (`grid-cols-1 lg:grid-cols-3 gap-6 items-start`):
  * Left column (`lg:col-span-2`): CaseTable component.
  * Right column (`lg:col-span-1`): Sticky NewCaseForm component.
* Strict state handling:
  * **Loading**: 4 pulse skeleton cards + table skeleton.
  * **Error**: Red error boundary card with retry connection button.
  * **Empty**: Centered `ClipboardList` card prompting users to register suspect plates.

#### 8.5 — Backend Alignment
* Added `IncidentCreate` schema in [`backend/app/schemas/incident.py`](file:///c:/Users/Asus/Desktop/sih-2026/backend/app/schemas/incident.py).
* Added `create_manual_case()` in [`backend/app/services/incident_service.py`](file:///c:/Users/Asus/Desktop/sih-2026/backend/app/services/incident_service.py) to cross-reference AI vehicle detections, link events and evidence, broadcast WebSocket notifications, and commit to PostgreSQL.
* Added `POST /api/v1/incidents` route handler in [`backend/app/api/v1/incidents.py`](file:///c:/Users/Asus/Desktop/sih-2026/backend/app/api/v1/incidents.py).

#### Build Verification
* `tsc -b && vite build` passed with **0 type errors**.
* Production bundle: `index.js 475.05 kB (143.03 kB gzipped)`, `index.css 41.05 kB (12.10 kB gzipped)`.

---

### ✅ Step 9: Fleet & Hardware Diagnostics Page (`/fleet`)

#### 9.1 — Data Fetching Hook
* **File**: [`frontend/src/hooks/useFleetStatus.ts`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/hooks/useFleetStatus.ts)
* Fetches data from `http://127.0.0.1:8000/api/v1/fleet/summary` based on the `FleetSummaryResponse` contract.
* Manages `data`, `isLoading`, and `error` states.
* Implements a 30-second polling interval (`setInterval`) with clean unmount teardown, plus a manual `refresh()` trigger.

#### 9.2 — Fleet Stat Grid Component
* **File**: [`frontend/src/components/fleet/FleetStatGrid.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/fleet/FleetStatGrid.tsx)
* Reuses `StatCard` to display 4 high-level hardware metrics:
  * **Total Buses**: Registered transit fleet units (`text-blue-400`).
  * **Active Buses**: Operational vehicles with live trip telemetry (`text-emerald-400`).
  * **Total Cameras**: Deployed edge AI optical sensors (`text-cyan-400`).
  * **Online Cameras**: Fraction transmitting live feeds with conditional styling:
    * All online: `text-emerald-400` with "100% optical sensors transmitting".
    * Hardware offline: Highlights card with `text-amber-400` / `text-red-400` warning and alerts operator of offline units.

#### 9.3 — Fleet Health Table Component
* **File**: [`frontend/src/components/fleet/FleetTable.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/fleet/FleetTable.tsx)
* Full-width dark data table listing each vehicle from `summary.buses`.
* Columns: **Bus Name / ID**, **Registration**, **Bus Status**, **Last Active / Trips**, **Camera Health**.
* Status Badges: Pulsating green `"Active"` badge when `is_active === true`, otherwise muted `"Inactive"`.
* Camera Health: Filters `summary.cameras` by `bus_id` to render individual optical unit pills (e.g., "Front Cam", "Rear Cam"):
  * 🟢 Green pill when `status === "online"`.
  * 🔴 Red pill when `status === "offline"`.

#### 9.4 — Fleet Page Assembly
* **File**: [`frontend/src/pages/FleetPage.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/pages/FleetPage.tsx)
* Header with `h1` "Fleet & Hardware Diagnostics", a subtle `"Auto-updating every 30s"` indicator, and manual refresh button.
* Strict state handling:
  * **Loading**: 4 pulse skeleton cards + table skeleton.
  * **Error**: Red error boundary card with retry connection button.
  * **Empty**: Centered `Bus` icon indicating no fleet registered.
* Layout: `FleetStatGrid` at top followed by full-width `FleetTable`.

#### Build Verification
* `tsc -b && vite build` passed with **0 type errors**.
* Production bundle: `index.js 484.09 kB (144.36 kB gzipped)`, `index.css 41.34 kB (12.15 kB gzipped)`.

---

### ✅ Step 10: Insights & Road Health Page (`/insights`)

#### 10.1 — Data Fetching Hook
* **File**: [`frontend/src/hooks/useRoadHealth.ts`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/hooks/useRoadHealth.ts)
* Fetches analytics data from `http://127.0.0.1:8000/api/v1/analytics/road-health` based on the `RoadHealthSummaryResponse` contract.
* Manages `data`, `isLoading`, and `error` states, and provides a manual `refresh()` trigger.

#### 10.2 — Analytics Components
* **RoadQualityScore**: [`frontend/src/components/insights/RoadQualityScore.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/insights/RoadQualityScore.tsx)
  * Renders a 260° SVG circular arc gauge displaying the 0–100 Road Quality Index (RQI) score.
  * Color coded thresholds:
    * `> 80`: Green (`text-emerald-400`, "Optimal Surface Quality").
    * `50 – 80`: Amber (`text-amber-400`, "Moderate Degradation").
    * `< 50`: Red (`text-red-400`, "Severe Surface Hazards").
  * Displays prominent score number, Risk Level badge (`Low`, `Medium`, `High`), and structural status text.
* **DefectBreakdown**: [`frontend/src/components/insights/DefectBreakdown.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/insights/DefectBreakdown.tsx)
  * 4-item responsive grid breakdown for all defect categories:
    * 🟡 **Potholes & Cracks** (`AlertTriangle`, amber progress bar).
    * 🔵 **Waterlogging Zones** (`Droplets`, cyan progress bar).
    * 🟣 **Signboard Damage** (`Signpost`, purple progress bar).
    * 🟠 **Zebra Crossing Issues** (`Footprints`, orange progress bar).
  * Calculates percentage shares of total defects with animated visual fill bars.

#### 10.3 — Insights Page Assembly
* **File**: [`frontend/src/pages/InsightsPage.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/pages/InsightsPage.tsx)
* Header with `h1` "Route Insights & Road Health" and a manual refresh button.
* Strict state handling:
  * **Loading**: Pulse skeleton grid for gauge, summary, and defect breakdown.
  * **Error**: Red error boundary card with retry connection button.
  * **Empty**: Centered `BarChart3` icon indicating no historical road defect data.
* AI Executive Digest:
  * Plain text auto-generated insight summary block dynamically identifying the prevailing defect class and risk assessment.
  * Corridor Risk Status recommendation and Maintenance Dispatch advisory cards.
* Layout: Top section features `RoadQualityScore` alongside the AI Executive Digest; bottom section features `DefectBreakdown`.

#### Build Verification
* `tsc -b && vite build` passed with **0 type errors**.
* Production bundle: `index.js 498.09 kB (147.25 kB gzipped)`, `index.css 42.69 kB (12.30 kB gzipped)`.

### ✅ Step 11: System Settings Shell (`/settings`)

#### 11.1 — Settings Page Component
* **File**: [`frontend/src/pages/SettingsPage.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/pages/SettingsPage.tsx)
* Header with `h1` "System Settings".
* Prominent alert card: "Demo Environment Lock — Settings configuration is locked for this demo environment. Parameter adjustments require administrator privileges."
* Interface & Telemetry Preferences:
  * Command Center Dark Palette (enabled & disabled toggle)
  * Desktop Incident Alerts (disabled toggle)
  * Auto-Refresh Analytics Feeds (enabled 30s background polling)
* AI Filter Thresholds & Parameters:
  * ANPR Low-Confidence Threshold (60.0% cutoff)
  * Live Buffer Depth (100 rolling frames)
* Network Endpoint Topology:
  * FastAPI REST Gateway: `http://127.0.0.1:8000/api/v1`
  * WebSocket Stream: `ws://localhost:8000/api/v1/ws/events`

---

### ✅ Step 12: Global Evidence Viewer Modal

#### 12.1 — Evidence Viewer Context
* **File**: [`frontend/src/contexts/EvidenceViewerContext.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/contexts/EvidenceViewerContext.tsx)
* React Context providing `{ isOpen, imageUrl, openModal(url), closeModal() }`.
* Hook: `useEvidenceViewer()`.

#### 12.2 — Evidence Viewer Modal Component
* **File**: [`frontend/src/components/ui/EvidenceViewerModal.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/ui/EvidenceViewerModal.tsx)
* Fullscreen dark backdrop (`bg-black/85 backdrop-blur-md fixed inset-0 z-50`).
* Scaled evidence container (`max-h-[90vh] max-w-[90vw]`) with smooth borders, shadows, and subtle controls.
* Top bar with full-screen link and close button.
* Dismissible via backdrop click, Close button, or `Escape` key listener.

#### 12.3 — Global Integration
* **App Shell**: [`frontend/src/App.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/App.tsx) wrapped in `<EvidenceViewerProvider>` and `<EvidenceViewerModal />` mounted at root level.
* **ANPR Cards**: [`frontend/src/components/anpr/AnprCard.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/anpr/AnprCard.tsx) triggers `openModal(event.evidence_url)` upon clicking evidence image with hover zoom effect.
* **Live Map Popups**: [`frontend/src/components/map/LiveMap.tsx`](file:///c:/Users/Asus/Desktop/sih-2026/frontend/src/components/map/LiveMap.tsx) "View Evidence →" button wired to `openModal`.

#### Build Verification
* `tsc -b && vite build` passed with **0 type errors**.
* Production bundle: `index.js 508.37 kB (149.32 kB gzipped)`, `index.css 45.28 kB (12.65 kB gzipped)`.

---

## 🎉 Project Milestone Complete: All 12 Steps Successfully Implemented!

1. ✅ **Fix Backend CORS**
2. ✅ **Initialize Frontend Scaffold** (Vite + React 19 + TypeScript + Tailwind CSS)
3. ✅ **Strict TypeScript Data Contracts** (`types/api.ts`)
4. ✅ **Global Shell & Routing** (Header, Sidebar, Layout, 7 command routes)
5. ✅ **Live Map & WebSocket Integration** (Leaflet, DivIcon markers, live feed, WS status)
6. ✅ **Traffic Density Analytics Page** (`/traffic`)
7. ✅ **ANPR & Incidents Page** (`/anpr` with edge vehicle deduplication)
8. ✅ **Case Registry & Incidents Page** (`/cases` with manual plate registration)
9. ✅ **Fleet & Hardware Diagnostics Page** (`/fleet` with 30s hardware polling)
10. ✅ **Route Insights & Road Health Page** (`/insights` with RQI circular gauge & defect breakdown)
11. ✅ **System Settings Shell** (`/settings`)
12. ✅ **Global Evidence Viewer** (Full-screen lightbox modal & image magnification)
