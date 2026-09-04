import React, { useState } from "react";
import {
  Camera,
  Layers,
  ListFilter,
  RefreshCw,
  AlertCircle,
  Car,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { useAnprEvents } from "../hooks/useAnprEvents";
import { AnprCard } from "../components/anpr/AnprCard";

type ViewMode = "grouped" | "raw";

export const AnprPage: React.FC = () => {
  const { rawEvents, groupedEvents, isLoading, error, refresh } = useAnprEvents();
  const [viewMode, setViewMode] = useState<ViewMode>("grouped");

  const displayEvents = viewMode === "grouped" ? groupedEvents : rawEvents;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-wide flex items-center gap-3">
            <Camera className="w-5 h-5 text-amber-400" />
            ANPR & Vehicle Surveillance
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Edge-driven automated plate recognition and vehicle trajectory deduplication
          </p>
        </div>

        {/* Top Controls: View Toggle & Refresh Button */}
        <div className="flex items-center gap-3 self-start sm:self-auto">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-900/90 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setViewMode("grouped")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
                viewMode === "grouped"
                  ? "bg-amber-400/10 text-amber-400 border border-amber-400/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 border border-transparent"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Grouped (Best Read)
            </button>
            <button
              onClick={() => setViewMode("raw")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
                viewMode === "raw"
                  ? "bg-amber-400/10 text-amber-400 border border-amber-400/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 border border-transparent"
              }`}
            >
              <ListFilter className="w-3.5 h-3.5" />
              Raw Stream
            </button>
          </div>

          {/* Refresh Button */}
          <button
            onClick={refresh}
            disabled={isLoading}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#131e36] hover:bg-[#1e293b] border border-[#1e293b] hover:border-[#334155] text-slate-300 hover:text-white text-xs font-mono font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            title="Refresh ANPR Events"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Subheader Statistics Counter Bar ───────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <span className="text-slate-200 font-semibold">
            {viewMode === "grouped"
              ? `Showing ${groupedEvents.length} Unique Vehicle${groupedEvents.length === 1 ? "" : "s"}`
              : `Showing ${rawEvents.length} Total Frame${rawEvents.length === 1 ? "" : "s"}`}
          </span>
          {viewMode === "grouped" && (
            <span className="text-slate-500">
              (Deduplicated from {rawEvents.length} frames across {new Set(rawEvents.map((e) => e.object_id).filter(Boolean)).size} tracked targets)
            </span>
          )}
        </div>

        <div className="flex items-center gap-4 text-[11px] text-slate-500">
          <span className="flex items-center gap-1">
            <Zap className="w-3 h-3 text-cyan-400" />
            Query Limit: 200
          </span>
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            Confidence Threshold: 60%
          </span>
        </div>
      </div>

      {/* ── Loading Skeleton ───────────────────────────────── */}
      {isLoading && rawEvents.length === 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="animate-pulse bg-[#131e36] border border-[#1e293b] rounded-xl overflow-hidden h-72 flex flex-col"
            >
              <div className="h-44 bg-slate-800/60" />
              <div className="p-4 space-y-3 flex-1">
                <div className="h-9 bg-slate-800/80 rounded-md w-3/4 mx-auto" />
                <div className="flex justify-between pt-2 border-t border-slate-800/60">
                  <div className="h-4 bg-slate-800/60 rounded w-20" />
                  <div className="h-4 bg-slate-800/60 rounded w-16" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Error State ────────────────────────────────────── */}
      {error && !isLoading && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-sm font-mono font-bold text-red-400">
              ANPR Data Connection Error
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mb-4">{error}</p>
          <button
            onClick={refresh}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-mono font-semibold transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry Connection
          </button>
        </div>
      )}

      {/* ── Empty State ────────────────────────────────────── */}
      {!isLoading && !error && displayEvents.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 bg-slate-900/30 rounded-xl border border-slate-800/50">
          <Car className="w-16 h-16 text-slate-600 mb-4 opacity-40" />
          <p className="text-sm text-slate-400 font-mono font-medium">
            No ANPR events detected
          </p>
          <p className="text-xs text-slate-500 font-mono mt-1 max-w-sm text-center">
            No vehicle license plates have been captured by edge cameras yet. Ensure edge feeds or mock generators are actively publishing.
          </p>
          <button
            onClick={refresh}
            className="mt-5 flex items-center gap-2 px-4 py-2 rounded-lg bg-[#131e36] hover:bg-[#1e293b] border border-[#1e293b] text-slate-300 text-xs font-mono transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Check for New Captures
          </button>
        </div>
      )}

      {/* ── Main Layout: Responsive Grid ───────────────────── */}
      {!isLoading && !error && displayEvents.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayEvents.map((event) => (
            <AnprCard key={event.id} event={event} />
          ))}
        </div>
      )}
    </div>
  );
};
