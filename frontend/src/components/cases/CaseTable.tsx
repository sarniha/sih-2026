import React, { useState } from "react";
import {
  ShieldCheck,
  Clock,
  Eye,
  X,
  MapPin,
  Calendar,
} from "lucide-react";
import type { IncidentResponse } from "../../types/api";

interface CaseTableProps {
  cases: IncidentResponse[];
}

export const CaseTable: React.FC<CaseTableProps> = ({ cases }) => {
  const [selectedCase, setSelectedCase] = useState<IncidentResponse | null>(null);

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "open":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30">
            open
          </span>
        );
      case "under_review":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            under_review
          </span>
        );
      case "closed":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            closed
          </span>
        );
      case "dismissed":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-700/40 text-slate-400 border border-slate-700/60">
            dismissed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            {status}
          </span>
        );
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return {
        date: d.toLocaleDateString([], {
          year: "numeric",
          month: "short",
          day: "numeric",
        }),
        time: d.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
    } catch {
      return { date: dateStr, time: "" };
    }
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700 rounded-xl overflow-hidden shadow-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-900/80 border-b border-slate-700 text-[11px] font-mono uppercase tracking-wider text-slate-400">
              <th className="py-3 px-4 font-semibold">Date Reported</th>
              <th className="py-3 px-4 font-semibold">Suspect Plate</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold">Notes & Details</th>
              <th className="py-3 px-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/60 text-xs font-mono">
            {cases.map((item) => {
              const { date, time } = formatDate(item.created_at || item.occurred_at);
              const hasMatch = Boolean(item.primary_event_id);

              return (
                <tr
                  key={item.id}
                  className="hover:bg-slate-750/40 transition-colors group"
                >
                  {/* Date Reported */}
                  <td className="py-3 px-4 text-slate-300 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>{date}</span>
                    </div>
                    {time && (
                      <div className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3" />
                        <span>{time}</span>
                      </div>
                    )}
                  </td>

                  {/* Suspect Plate */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    {item.suspected_plate ? (
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-amber-500/30 text-amber-300 font-black tracking-wider text-xs">
                        <span>{item.suspected_plate}</span>
                        {item.suspected_plate_confidence !== null && (
                          <span className="text-[10px] text-amber-400/80 font-normal">
                            ({Math.round(item.suspected_plate_confidence * 100)}%)
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-500 italic">No plate specified</span>
                    )}
                  </td>

                  {/* Status */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    {getStatusBadge(item.status)}
                  </td>

                  {/* Notes */}
                  <td className="py-3 px-4 text-slate-300 max-w-xs md:max-w-md">
                    <p className="line-clamp-2 text-slate-300 text-xs">
                      {item.notes || (
                        <span className="text-slate-500 italic">
                          No notes attached
                        </span>
                      )}
                    </p>
                  </td>

                  {/* Actions */}
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    {hasMatch ? (
                      <button
                        onClick={() => setSelectedCase(item)}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-semibold transition-all hover:scale-105"
                        title="Inspect matched incident and telemetry"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View Match
                      </button>
                    ) : (
                      <span className="text-slate-600 text-[11px] italic">
                        Pending Match
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Match Details Modal Dialog */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-amber-400 font-mono font-bold text-sm">
                <ShieldCheck className="w-4 h-4" />
                Case Match Telemetry
              </div>
              <button
                onClick={() => setSelectedCase(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                <span className="text-slate-400">Suspect License Plate:</span>
                <span className="font-bold text-amber-300 text-sm tracking-wider">
                  {selectedCase.suspected_plate || "N/A"}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                  <div className="text-[11px] text-slate-400">Case ID</div>
                  <div className="text-slate-200 font-semibold truncate mt-0.5" title={selectedCase.id}>
                    {selectedCase.id.slice(0, 13)}...
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                  <div className="text-[11px] text-slate-400">Primary Event Ref</div>
                  <div className="text-cyan-400 font-semibold truncate mt-0.5" title={selectedCase.primary_event_id}>
                    {selectedCase.primary_event_id.slice(0, 13)}...
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700 space-y-1.5">
                <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                  <MapPin className="w-3.5 h-3.5 text-red-400" />
                  GPS Coordinates:
                </div>
                <div className="text-slate-200">
                  {selectedCase.lat !== null && selectedCase.lon !== null
                    ? `${selectedCase.lat.toFixed(5)}° N, ${selectedCase.lon.toFixed(5)}° E`
                    : "Live corridor triangulation pending"}
                </div>
              </div>

              {selectedCase.notes && (
                <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700 space-y-1">
                  <div className="text-[11px] text-slate-400">Officer / Report Notes:</div>
                  <div className="text-slate-200">{selectedCase.notes}</div>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedCase(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-semibold transition-colors"
              >
                Close Window
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
