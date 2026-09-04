import React, { useEffect } from "react";
import { useLiveEvents } from "../hooks/useLiveEvents";
import { useWsStatus } from "../contexts/WsStatusContext";
import { LiveMap } from "../components/map/LiveMap";
import { LiveFeedPanel } from "../components/feed/LiveFeedPanel";

export const MapPage: React.FC = () => {
  const { events, status } = useLiveEvents();
  const { setStatus } = useWsStatus();

  // Sync WebSocket status up to Header via context
  useEffect(() => {
    setStatus(status);
  }, [status, setStatus]);

  return (
    <div className="flex flex-col lg:flex-row h-full w-full overflow-hidden flex-1">
      {/* Left: Live Map (grows to fill) */}
      <div className="flex-1 h-full w-full relative min-h-[300px]">
        <LiveMap events={events} />

        {/* Floating connection status badge on map */}
        <div className="absolute top-3 left-3 z-[1000] pointer-events-none">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0f172a]/90 backdrop-blur border border-[#1e293b] shadow-lg pointer-events-auto">
            <span
              className={`h-2 w-2 rounded-full ${
                status === "connected"
                  ? "bg-emerald-500 shadow-emerald-500/50 shadow-sm"
                  : status === "reconnecting"
                  ? "bg-amber-500 animate-pulse"
                  : "bg-red-500"
              }`}
            />
            <span className="text-[10px] font-mono font-semibold text-slate-300 uppercase tracking-wider">
              {status === "connected"
                ? "WS LIVE"
                : status === "reconnecting"
                ? "RECONNECTING"
                : "WS OFFLINE"}
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              | {events.length} events
            </span>
          </div>
        </div>
      </div>

      {/* Right: Feed Panel (fixed width on desktop) */}
      <div className="w-full lg:w-96 h-64 lg:h-full flex-shrink-0">
        <LiveFeedPanel events={events} />
      </div>
    </div>
  );
};
