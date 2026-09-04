import React, { useMemo } from "react";
import {
  AlertTriangle,
  Car,
  Construction,
  Droplets,
  Camera,
  ShieldAlert,
  Signpost,
  Activity,
  Crosshair,
} from "lucide-react";
import { cn } from "../../lib/utils";
import type { EventResponse } from "../../types/api";

// ---------------------------------------------------------------------------
// Event type configuration: icons, label, color
// ---------------------------------------------------------------------------
interface EventTypeConfig {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  color: string;        // Tailwind text color class
  bgColor: string;      // Tailwind bg + border class
}

const EVENT_CONFIG: Record<string, EventTypeConfig> = {
  hit_run: {
    icon: ShieldAlert,
    label: "Hit & Run",
    color: "text-red-400",
    bgColor: "bg-red-500/10 border-red-500/30",
  },
  anpr: {
    icon: Camera,
    label: "ANPR Detection",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10 border-amber-500/30",
  },
  pothole: {
    icon: Construction,
    label: "Pothole",
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10 border-yellow-500/30",
  },
  waterlogging: {
    icon: Droplets,
    label: "Waterlogging",
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10 border-cyan-500/30",
  },
  signboard_damage: {
    icon: Signpost,
    label: "Signboard Damage",
    color: "text-purple-400",
    bgColor: "bg-purple-500/10 border-purple-500/30",
  },
  zebra_crossing_issue: {
    icon: Crosshair,
    label: "Zebra Crossing",
    color: "text-orange-400",
    bgColor: "bg-orange-500/10 border-orange-500/30",
  },
  traffic: {
    icon: Car,
    label: "Traffic",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10 border-blue-500/30",
  },
};

function getConfig(eventType: string): EventTypeConfig {
  return (
    EVENT_CONFIG[eventType] || {
      icon: Activity,
      label: eventType.replace(/_/g, " "),
      color: "text-slate-400",
      bgColor: "bg-slate-500/10 border-slate-500/30",
    }
  );
}

function formatRelativeTime(isoStr: string): string {
  try {
    const diff = Date.now() - new Date(isoStr).getTime();
    const secs = Math.floor(diff / 1000);
    if (secs < 5) return "Just now";
    if (secs < 60) return `${secs}s ago`;
    const mins = Math.floor(secs / 60);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    return `${hours}h ago`;
  } catch {
    return isoStr;
  }
}

// ---------------------------------------------------------------------------
// Single event card
// ---------------------------------------------------------------------------
const EventCard: React.FC<{ event: EventResponse; priority?: boolean }> = ({
  event,
  priority = false,
}) => {
  const cfg = getConfig(event.event_type);
  const Icon = cfg.icon;

  return (
    <div
      className={cn(
        "relative flex items-start gap-3 p-3 rounded-lg border transition-all duration-300",
        priority
          ? "bg-red-500/5 border-red-500/20 hover:border-red-500/40 animate-pulse-slow"
          : "bg-[#131e36]/60 border-[#1e293b] hover:border-[#334155]"
      )}
    >
      {/* Icon badge */}
      <div
        className={cn(
          "flex-shrink-0 mt-0.5 h-8 w-8 rounded-md flex items-center justify-center border",
          cfg.bgColor
        )}
      >
        <Icon className={cn("w-4 h-4", cfg.color)} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span
            className={cn(
              "text-xs font-mono font-bold uppercase tracking-wide",
              cfg.color
            )}
          >
            {cfg.label}
          </span>
          <span className="text-[10px] text-slate-400 font-mono flex-shrink-0">
            {formatRelativeTime(event.occurred_at)}
          </span>
        </div>

        <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-400 font-mono">
          <span>
            Conf:{" "}
            <span className="text-slate-200 font-semibold">
              {(event.confidence * 100).toFixed(0)}%
            </span>
          </span>
          {event.severity && (
            <>
              <span className="text-[#334155]">•</span>
              <span
                className={cn(
                  "px-1 py-0.5 rounded text-[10px] font-bold uppercase",
                  event.severity === "high"
                    ? "bg-red-500/15 text-red-400"
                    : event.severity === "medium"
                    ? "bg-amber-500/15 text-amber-400"
                    : "bg-emerald-500/15 text-emerald-400"
                )}
              >
                {event.severity}
              </span>
            </>
          )}
          {event.lon != null && event.lat != null && (
            <>
              <span className="text-[#334155]">•</span>
              <span className="text-slate-500">
                {event.lat.toFixed(3)}, {event.lon.toFixed(3)}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Feed Panel
// ---------------------------------------------------------------------------
interface LiveFeedPanelProps {
  events: EventResponse[];
}

const HIGH_PRIORITY_TYPES = new Set(["hit_run"]);

export const LiveFeedPanel: React.FC<LiveFeedPanelProps> = ({ events }) => {
  const generalEvents = useMemo(
    () => events.filter((e) => !HIGH_PRIORITY_TYPES.has(e.event_type)),
    [events]
  );

  const priorityEvents = useMemo(
    () =>
      events.filter(
        (e) => HIGH_PRIORITY_TYPES.has(e.event_type) || e.severity === "high"
      ),
    [events]
  );

  return (
    <div className="flex flex-col h-full bg-[#0f172a] border-l border-[#1e293b]">
      {/* ---- Top: Live Event Feed (60%) ---- */}
      <div className="flex-[3] flex flex-col min-h-0 border-b border-[#1e293b]">
        {/* Section Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e293b] bg-[#0b0f17]/60 flex-shrink-0">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
              Live Event Feed
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400 bg-[#1e293b] px-2 py-0.5 rounded border border-[#334155]">
            {events.length} events
          </span>
        </div>

        {/* Scrollable list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {generalEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs font-mono">
              <Activity className="w-8 h-8 mb-2 opacity-30" />
              <span>Awaiting live telemetry…</span>
              <span className="text-[10px] mt-1 text-slate-600">
                WebSocket → ws/events
              </span>
            </div>
          ) : (
            generalEvents.map((event) => (
              <EventCard key={event.id} event={event} />
            ))
          )}
        </div>
      </div>

      {/* ---- Bottom: High-Priority Alerts (40%) ---- */}
      <div className="flex-[2] flex flex-col min-h-0">
        {/* Section Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e293b] bg-red-500/5 flex-shrink-0">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse" />
            <span className="text-xs font-mono font-bold text-red-400 uppercase tracking-wider">
              High-Priority Alerts
            </span>
          </div>
          <span className="text-[10px] font-mono text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
            {priorityEvents.length} active
          </span>
        </div>

        {/* Scrollable alert list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {priorityEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs font-mono">
              <ShieldAlert className="w-8 h-8 mb-2 opacity-20" />
              <span>No critical incidents</span>
              <span className="text-[10px] mt-1 text-slate-600">
                Monitoring for hit_run events
              </span>
            </div>
          ) : (
            priorityEvents.map((event) => (
              <EventCard key={`pri-${event.id}`} event={event} priority />
            ))
          )}
        </div>
      </div>
    </div>
  );
};
