import React from "react";
import { Bus, Clock, Video, VideoOff } from "lucide-react";
import type { BusStatusResponse, CameraStatusResponse } from "../../types/api";

interface FleetTableProps {
  buses: BusStatusResponse[];
  cameras: CameraStatusResponse[];
}

export const FleetTable: React.FC<FleetTableProps> = ({ buses, cameras }) => {
  const formatTime = (timeStr: string | null) => {
    if (!timeStr) return "No active trips";
    try {
      const d = new Date(timeStr);
      return d.toLocaleDateString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return timeStr;
    }
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700 rounded-xl overflow-hidden shadow-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-900/80 border-b border-slate-700 text-[11px] font-mono uppercase tracking-wider text-slate-400">
              <th className="py-3 px-4 font-semibold">Bus Name / ID</th>
              <th className="py-3 px-4 font-semibold">Registration</th>
              <th className="py-3 px-4 font-semibold">Bus Status</th>
              <th className="py-3 px-4 font-semibold">Last Active / Trips</th>
              <th className="py-3 px-4 font-semibold">Camera Health</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/60 text-xs font-mono">
            {buses.map((bus) => {
              const busCameras = cameras.filter((cam) => cam.bus_id === bus.id);

              return (
                <tr
                  key={bus.id}
                  className="hover:bg-slate-750/40 transition-colors"
                >
                  {/* Bus Name / ID */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-300">
                        <Bus className="w-4 h-4 text-blue-400" />
                      </div>
                      <div>
                        <div className="font-bold text-slate-200">
                          {bus.name || "City Transit Unit"}
                        </div>
                        <div
                          className="text-[11px] text-slate-500 truncate max-w-[140px]"
                          title={bus.id}
                        >
                          ID: {bus.id.slice(0, 8)}...
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Registration Number */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    {bus.registration_number ? (
                      <span className="inline-block px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-amber-300 font-mono font-bold tracking-wider text-xs">
                        {bus.registration_number}
                      </span>
                    ) : (
                      <span className="text-slate-500 italic">Pending Reg</span>
                    )}
                  </td>

                  {/* Bus Status */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    {bus.is_active ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-700/40 text-slate-400 border border-slate-700/60">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                        Inactive
                      </span>
                    )}
                  </td>

                  {/* Last Active / Trips */}
                  <td className="py-3.5 px-4 whitespace-nowrap text-slate-300">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>{formatTime(bus.last_trip_started_at)}</span>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      {bus.total_trips} recorded trip{bus.total_trips === 1 ? "" : "s"}
                    </div>
                  </td>

                  {/* Camera Health */}
                  <td className="py-3.5 px-4">
                    {busCameras.length === 0 ? (
                      <span className="text-slate-500 text-[11px] italic">
                        No cameras linked
                      </span>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {busCameras.map((cam) => {
                          const isOnline = cam.status === "online";
                          return (
                            <span
                              key={cam.id}
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${
                                isOnline
                                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                                  : "bg-red-500/10 text-red-400 border-red-500/30"
                              }`}
                              title={`${cam.name} (${cam.camera_type}): ${cam.status.toUpperCase()}`}
                            >
                              {isOnline ? (
                                <Video className="w-3 h-3 text-emerald-400" />
                              ) : (
                                <VideoOff className="w-3 h-3 text-red-400" />
                              )}
                              <span>{cam.name}</span>
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
