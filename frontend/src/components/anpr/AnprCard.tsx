import React, { useState } from "react";
import {
  CameraOff,
  AlertTriangle,
  ShieldCheck,
  Clock,
  Bus,
  Tag,
  Maximize2,
} from "lucide-react";
import type { EventResponse } from "../../types/api";
import { useEvidenceViewer } from "../../contexts/EvidenceViewerContext";

interface AnprCardProps {
  event: EventResponse;
}

export const AnprCard: React.FC<AnprCardProps> = ({ event }) => {
  const { openModal } = useEvidenceViewer();
  const [imgError, setImgError] = useState(false);

  const rawPlate = event.plate_text?.trim();
  const isReadable = Boolean(
    rawPlate &&
    rawPlate.toLowerCase() !== "null" &&
    rawPlate.toLowerCase() !== "undefined" &&
    rawPlate !== ""
  );

  // Use plate_confidence if available, falling back to event.confidence
  const confidence = event.plate_confidence ?? event.confidence ?? 0;
  const confidencePct = Math.round(confidence * 100);
  const isLowConfidence = confidence < 0.6;

  const hasEvidence = Boolean(event.evidence_url && !imgError);

  // Format occurrence timestamp
  const formattedTime = (() => {
    try {
      const d = new Date(event.occurred_at || event.created_at);
      return d.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch {
      return "Recent";
    }
  })();

  const handleEvidenceClick = () => {
    if (hasEvidence && event.evidence_url) {
      openModal(event.evidence_url);
    }
  };

  return (
    <div className="bg-[#131e36] border border-[#1e293b] rounded-xl overflow-hidden shadow-lg hover:border-slate-600 transition-all flex flex-col group">
      {/* Evidence Image or CameraOff Placeholder */}
      <div
        onClick={handleEvidenceClick}
        className={`relative w-full h-44 bg-slate-900/90 border-b border-slate-800 flex items-center justify-center overflow-hidden ${
          hasEvidence ? "cursor-pointer" : ""
        }`}
        title={hasEvidence ? "Click to view full resolution evidence" : undefined}
      >
        {hasEvidence ? (
          <>
            <img
              src={event.evidence_url!}
              alt={isReadable ? `Plate ${rawPlate}` : "Vehicle Evidence"}
              onError={() => setImgError(true)}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
            {/* Hover overlay hint */}
            <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center pointer-events-none">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/90 text-cyan-300 text-xs font-mono border border-cyan-500/40 backdrop-blur-sm">
                <Maximize2 className="w-3.5 h-3.5" />
                Enlarge Frame
              </span>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center text-slate-500 gap-2 p-4">
            <div className="p-3 rounded-full bg-slate-800/80 border border-slate-700/50">
              <CameraOff className="w-6 h-6 text-slate-400" />
            </div>
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
              No Frame Capture
            </span>
          </div>
        )}

        {/* Top Floating Badges */}
        <div className="absolute top-2 left-2 flex items-center gap-1.5">
          {event.object_id ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-900/80 backdrop-blur-md text-cyan-300 border border-cyan-500/30">
              <Tag className="w-3 h-3" />
              {event.object_id}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-900/80 backdrop-blur-md text-slate-400 border border-slate-700/50">
              Isolated
            </span>
          )}
        </div>

        {/* Confidence Badge overlay on image */}
        <div className="absolute top-2 right-2">
          {isLowConfidence ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-950/80 backdrop-blur-md text-amber-400 border border-amber-500/40">
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              {confidencePct}% Low Conf
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-950/80 backdrop-blur-md text-emerald-400 border border-emerald-500/40">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              {confidencePct}%
            </span>
          )}
        </div>
      </div>

      {/* Card Content Area */}
      <div className="p-4 flex-1 flex flex-col justify-between gap-3">
        {/* License Plate Banner */}
        <div className="flex flex-col items-center justify-center my-1">
          {isReadable ? (
            <div className="w-full bg-amber-400 text-slate-950 font-mono font-black text-center text-lg tracking-widest py-2 px-3 rounded-md border-2 border-slate-950 shadow-md flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-800 bg-amber-300 px-1 py-0.5 rounded border border-amber-500">
                IND
              </span>
              <span className="mx-auto uppercase select-all">{rawPlate}</span>
              <span className="text-[10px] font-bold text-slate-800">●</span>
            </div>
          ) : (
            <div className="w-full bg-slate-800/80 text-slate-400 border border-slate-700/70 font-mono text-xs text-center py-2.5 px-3 rounded-md italic flex items-center justify-center gap-2">
              <AlertTriangle className="w-4 h-4 text-slate-500" />
              <span>Plate not readable</span>
            </div>
          )}
        </div>

        {/* Meta details footer */}
        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
          <div className="flex items-center gap-1 text-slate-300">
            <Bus className="w-3.5 h-3.5 text-slate-400" />
            <span className="truncate max-w-[110px]" title={event.bus_id}>
              Bus {event.bus_id.slice(0, 8)}
            </span>
          </div>

          <div className="flex items-center gap-1 text-slate-400">
            <Clock className="w-3.5 h-3.5" />
            <span>{formattedTime}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
