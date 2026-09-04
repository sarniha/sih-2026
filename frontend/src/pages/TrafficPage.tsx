import React from "react";
import {
  Activity,
  Car,
  Camera,
  BarChart2,
  RefreshCw,
  Target,
  AlertCircle,
} from "lucide-react";
import { useTrafficAnalytics } from "../hooks/useTrafficAnalytics";
import { StatCard } from "../components/ui/StatCard";
import { CongestionPanel } from "../components/traffic/CongestionPanel";

export const TrafficPage: React.FC = () => {
  const { data, isLoading, error, refresh } = useTrafficAnalytics();

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-wide flex items-center gap-3">
            <Activity className="w-5 h-5 text-emerald-400" />
            Traffic & Mobility Analytics
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Real-time vehicle density, ANPR telemetry, and corridor congestion assessment
          </p>
        </div>
        <button
          onClick={refresh}
          disabled={isLoading}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#131e36] hover:bg-[#1e293b] border border-[#1e293b] hover:border-[#334155] text-slate-300 hover:text-white text-xs font-mono font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* ── Loading Skeleton ───────────────────────────────── */}
      {isLoading && !data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="animate-pulse bg-[#131e36] border border-[#1e293b] h-32 rounded-lg"
              />
            ))}
          </div>
          <div className="animate-pulse bg-[#131e36] border border-[#1e293b] h-48 rounded-lg" />
        </>
      )}

      {/* ── Error State ────────────────────────────────────── */}
      {error && !isLoading && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-sm font-mono font-bold text-red-400">
              Connection Error
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
      {!isLoading && !error && !data && (
        <div className="flex flex-col items-center justify-center py-20">
          <BarChart2 className="w-16 h-16 text-slate-600 mb-4 opacity-50" />
          <p className="text-sm text-slate-400 font-mono">
            No traffic data available
          </p>
          <p className="text-[11px] text-slate-500 font-mono mt-1">
            Start the mock generator or wait for live edge telemetry
          </p>
        </div>
      )}

      {/* ── Main Data Layout ───────────────────────────────── */}
      {data && (
        <>
          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Events"
              value={data.total_events.toLocaleString()}
              icon={Activity}
              trend="All traffic + ANPR detections"
              colorClass="text-emerald-400"
            />
            <StatCard
              title="Traffic Detections"
              value={data.traffic_count.toLocaleString()}
              icon={Car}
              trend="Vehicle density observations"
              colorClass="text-blue-400"
            />
            <StatCard
              title="ANPR Captures"
              value={data.anpr_count.toLocaleString()}
              icon={Camera}
              trend="License plate recognitions"
              colorClass="text-amber-400"
            />
            <StatCard
              title="Avg Confidence"
              value={`${(data.average_confidence * 100).toFixed(1)}%`}
              icon={Target}
              trend="Mean detection accuracy"
              colorClass="text-cyan-400"
            />
          </div>

          {/* Congestion Panel */}
          <CongestionPanel congestion_level={data.congestion_level} />
        </>
      )}
    </div>
  );
};
