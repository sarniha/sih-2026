import { Bus, RefreshCw, AlertCircle } from "lucide-react";
import { useFleetStatus } from "../hooks/useFleetStatus";
import { FleetStatGrid } from "../components/fleet/FleetStatGrid";
import { FleetTable } from "../components/fleet/FleetTable";

export const FleetPage: React.FC = () => {
  const { data, isLoading, error, refresh } = useFleetStatus();

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-wide flex items-center gap-3">
            <Bus className="w-5 h-5 text-blue-400" />
            Fleet & Hardware Diagnostics
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Edge AI compute unit monitoring, optical sensor diagnostics, and bus telemetry
          </p>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          {/* Subtle auto-poll text indicator */}
          <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] font-mono text-slate-400 bg-slate-900/80 border border-slate-800 px-2.5 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Auto-updating every 30s
          </span>

          {/* Manual refresh button */}
          <button
            onClick={() => refresh()}
            disabled={isLoading}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#131e36] hover:bg-[#1e293b] border border-[#1e293b] hover:border-[#334155] text-slate-300 hover:text-white text-xs font-mono font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            title="Refresh Fleet Status"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Loading Skeleton ───────────────────────────────── */}
      {isLoading && !data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="animate-pulse bg-slate-800/80 border border-slate-700 h-28 rounded-xl"
              />
            ))}
          </div>
          <div className="animate-pulse bg-slate-800/80 border border-slate-700 h-72 rounded-xl" />
        </div>
      )}

      {/* ── Error State ────────────────────────────────────── */}
      {error && !isLoading && !data && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-sm font-mono font-bold text-red-400">
              Fleet Hardware Telemetry Error
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mb-4">{error}</p>
          <button
            onClick={() => refresh()}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-mono font-semibold transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry Connection
          </button>
        </div>
      )}

      {/* ── Empty State ────────────────────────────────────── */}
      {!isLoading && !error && data && data.total_buses === 0 && (
        <div className="flex flex-col items-center justify-center py-24 bg-slate-800/40 rounded-xl border border-slate-700/60 text-center">
          <Bus className="w-16 h-16 text-slate-600 mb-4 opacity-40" />
          <h3 className="text-sm font-mono font-bold text-slate-300">
            No fleet registered
          </h3>
          <p className="text-xs text-slate-500 font-mono mt-1 max-w-sm">
            No buses or edge camera units detected in the centralized database. Initialize fleet records or run setup scripts.
          </p>
          <button
            onClick={() => refresh()}
            className="mt-5 flex items-center gap-2 px-4 py-2 rounded-lg bg-[#131e36] hover:bg-[#1e293b] border border-[#1e293b] text-slate-300 text-xs font-mono transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Check Fleet Hardware
          </button>
        </div>
      )}

      {/* ── Main Data Layout ───────────────────────────────── */}
      {data && (
        <div className="space-y-6">
          {/* High-level Metric Stat Grid */}
          <FleetStatGrid summary={data} />

          {/* Full Fleet & Hardware Table */}
          <FleetTable buses={data.buses} cameras={data.cameras} />
        </div>
      )}
    </div>
  );
};
