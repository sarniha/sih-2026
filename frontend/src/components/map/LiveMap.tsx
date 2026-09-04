import React, { useMemo } from "react";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { MapContainer, TileLayer, Marker, Popup, ZoomControl } from "react-leaflet";
import type { EventResponse } from "../../types/api";
import { useEvidenceViewer } from "../../contexts/EvidenceViewerContext";

// ---------------------------------------------------------------------------
// Fix default Leaflet icon bug (webpack/vite strips default icon paths)
// ---------------------------------------------------------------------------
// @ts-ignore
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

// ---------------------------------------------------------------------------
// Custom SVG marker icons per event type
// ---------------------------------------------------------------------------
function createSvgIcon(color: string, strokeColor: string = "#0f172a"): L.DivIcon {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="36" viewBox="0 0 28 36">
      <path d="M14 0C6.27 0 0 6.27 0 14c0 10.5 14 22 14 22s14-11.5 14-22C28 6.27 21.73 0 14 0z"
            fill="${color}" stroke="${strokeColor}" stroke-width="1.5"/>
      <circle cx="14" cy="13" r="5.5" fill="white" opacity="0.9"/>
    </svg>`;
  return L.divIcon({
    html: svg,
    className: "custom-marker-icon",
    iconSize: [28, 36],
    iconAnchor: [14, 36],
    popupAnchor: [0, -36],
  });
}

const EVENT_ICONS: Record<string, L.DivIcon> = {
  hit_run: createSvgIcon("#ef4444", "#7f1d1d"),       // red
  anpr: createSvgIcon("#f59e0b", "#78350f"),           // amber
  pothole: createSvgIcon("#eab308", "#713f12"),        // yellow
  waterlogging: createSvgIcon("#06b6d4", "#164e63"),   // cyan
  signboard_damage: createSvgIcon("#a855f7", "#3b0764"), // purple
  zebra_crossing_issue: createSvgIcon("#f97316", "#7c2d12"), // orange
  traffic: createSvgIcon("#3b82f6", "#1e3a5f"),        // blue
};

function getEventIcon(eventType: string): L.DivIcon {
  return EVENT_ICONS[eventType] || createSvgIcon("#64748b");
}

function severityBadge(severity: string | null): string {
  if (!severity) return "bg-slate-600 text-slate-200";
  switch (severity) {
    case "high": return "bg-red-500/20 text-red-400 border border-red-500/30";
    case "medium": return "bg-amber-500/20 text-amber-400 border border-amber-500/30";
    case "low": return "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
    default: return "bg-slate-600 text-slate-200";
  }
}

function formatTime(isoStr: string): string {
  try {
    return new Date(isoStr).toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return isoStr;
  }
}

interface LiveMapProps {
  events: EventResponse[];
}

const DELHI_CENTER: [number, number] = [28.6139, 77.2090];

export const LiveMap: React.FC<LiveMapProps> = ({ events }) => {
  const { openModal } = useEvidenceViewer();

  // Filter to only events with valid coordinates
  const mappableEvents = useMemo(
    () => events.filter((e) => e.lat != null && e.lon != null),
    [events]
  );

  return (
    <MapContainer
      center={DELHI_CENTER}
      zoom={13}
      zoomControl={false}
      className="w-full h-full z-0"
      style={{ background: "#0b0f17" }}
    >
      <ZoomControl position="bottomright" />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {mappableEvents.map((event) => (
        <Marker
          key={event.id}
          position={[event.lat!, event.lon!]}
          icon={getEventIcon(event.event_type)}
        >
          <Popup className="command-popup" maxWidth={280}>
            <div className="bg-[#131e36] text-slate-100 rounded-lg p-3 min-w-[220px] border border-[#334155] font-sans text-sm -m-[13px] -mt-[10px]">
              {/* Header */}
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono font-bold text-xs uppercase tracking-wider text-emerald-400">
                  {event.event_type.replace(/_/g, " ")}
                </span>
                <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${severityBadge(event.severity)}`}>
                  {(event.severity || "n/a").toUpperCase()}
                </span>
              </div>

              {/* Stats */}
              <div className="space-y-1 text-xs text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-400">Confidence</span>
                  <span className="font-mono font-semibold text-white">
                    {(event.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Detected At</span>
                  <span className="font-mono">{formatTime(event.occurred_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Coords</span>
                  <span className="font-mono text-[11px]">
                    {event.lat?.toFixed(4)}, {event.lon?.toFixed(4)}
                  </span>
                </div>
              </div>

              {/* Action */}
              <button
                onClick={() =>
                  openModal(
                    event.evidence_url ||
                      `https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1200&q=80`
                  )
                }
                className="mt-3 w-full py-1.5 text-xs font-semibold text-center bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded hover:bg-emerald-500/20 transition-colors font-mono"
              >
                View Evidence →
              </button>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};
