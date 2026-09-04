import React from "react";
import {
  TrendingUp,
  RefreshCw,
  AlertCircle,
  BarChart3,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
} from "lucide-react";
import { useRoadHealth } from "../hooks/useRoadHealth";
import { RoadQualityScore } from "../components/insights/RoadQualityScore";
import { DefectBreakdown } from "../components/insights/DefectBreakdown";

export const InsightsPage: React.FC = () => {
  const { data, isLoading, error, refresh } = useRoadHealth();

  // Compute highest defect count category for auto-generated summary
  const summaryInsight = React.useMemo(() => {
    if (!data) return "";

    const defectTypes = [
      { name: "potholes and asphalt fissures", count: data.potholes_count },
      { name: "waterlogging and poor drainage zones", count: data.waterlogging_count },
      { name: "damaged or obscured signboards", count: data.signboard_damage_count },
      { name: "eroded zebra crossings", count: data.zebra_crossing_issue_count },
    ];

    const highest = defectTypes.reduce((prev, curr) =>
      curr.count > prev.count ? curr : prev
    );

    const total = Math.max(1, data.total_defects);
    const highestPct = Math.round((highest.count / total) * 100);

    if (data.total_defects === 0) {
      return "City road corridors demonstrate optimal structural integrity with zero active anomalies logged.";
    }

    return `City road quality is currently classified as ${data.risk_level.toUpperCase()} risk (Score: ${Math.round(
      data.road_quality_index
    )}/100), driven primarily by ${highest.name} (${highest.count} incidents, accounting for ${highestPct}% of all detected carriageway defects).`;
  }, [data]);

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-wide flex items-center gap-3">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            Route Insights & Road Health
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Pavement structural integrity, defect severity clustering, and municipal maintenance prioritization
          </p>
        </div>

        <button
          onClick={refresh}
          disabled={isLoading}
          className="self-start sm:self-auto flex items-center gap-2 px-3 py-2 rounded-lg bg-[#131e36] hover:bg-[#1e293b] border border-[#1e293b] hover:border-[#334155] text-slate-300 hover:text-white text-xs font-mono font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          title="Refresh Road Health Analytics"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* ── Loading Skeleton ───────────────────────────────── */}
      {isLoading && !data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="animate-pulse bg-[#131e36] border border-[#1e293b] h-72 rounded-xl" />
            <div className="lg:col-span-2 animate-pulse bg-[#131e36] border border-[#1e293b] h-72 rounded-xl" />
          </div>
          <div className="animate-pulse bg-[#131e36] border border-[#1e293b] h-64 rounded-xl" />
        </div>
      )}

      {/* ── Error State ────────────────────────────────────── */}
      {error && !isLoading && !data && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-sm font-mono font-bold text-red-400">
              Road Health Analytics Connection Error
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
      {!isLoading && !error && data && data.total_defects === 0 && data.road_quality_index === 0 && (
        <div className="flex flex-col items-center justify-center py-24 bg-slate-900/30 rounded-xl border border-slate-800/60 text-center">
          <BarChart3 className="w-16 h-16 text-slate-600 mb-4 opacity-40" />
          <h3 className="text-sm font-mono font-bold text-slate-300">
            No historical road defect data
          </h3>
          <p className="text-xs text-slate-500 font-mono mt-1 max-w-sm">
            Road defect aggregation models require active bus telemetry. Verify edge nodes or mock generator activity.
          </p>
          <button
            onClick={refresh}
            className="mt-5 flex items-center gap-2 px-4 py-2 rounded-lg bg-[#131e36] hover:bg-[#1e293b] border border-[#1e293b] text-slate-300 text-xs font-mono transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Check Data Feed
          </button>
        </div>
      )}

      {/* ── Main Data Layout ───────────────────────────────── */}
      {data && (
        <div className="space-y-6">
          {/* Top Section: Quality Score + Auto-generated Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
            {/* Left: Road Quality Score Gauge */}
            <div className="lg:col-span-1">
              <RoadQualityScore
                roadQualityIndex={data.road_quality_index}
                riskLevel={data.risk_level}
              />
            </div>

            {/* Right: Executive Auto-Generated Insight Summary */}
            <div className="lg:col-span-2 bg-[#131e36] border border-[#1e293b] rounded-xl p-6 shadow-xl flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-slate-300 font-mono text-xs font-semibold uppercase tracking-wider pb-3 border-b border-slate-800 mb-4">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  AI Executive Road Condition Digest
                </div>

                {/* Main Insight Summary Block */}
                <div className="p-4 rounded-lg bg-slate-900/90 border border-slate-800">
                  <p className="text-sm font-mono text-slate-200 leading-relaxed">
                    {summaryInsight}
                  </p>
                </div>

                {/* Risk and Action Recommendations */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                  <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex items-start gap-2.5">
                    {data.risk_level === "low" ? (
                      <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    ) : data.risk_level === "medium" ? (
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    ) : (
                      <AlertOctagon className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <div className="text-[11px] font-mono font-bold text-slate-300 uppercase">
                        Corridor Risk Status
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                        {data.risk_level === "low"
                          ? "Normal transit operations recommended. Minimal structural risk."
                          : data.risk_level === "medium"
                          ? "Advisory warning issued for heavy axle public buses."
                          : "Immediate civil intervention and speed reduction required."}
                      </div>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex items-start gap-2.5">
                    <TrendingUp className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-[11px] font-mono font-bold text-slate-300 uppercase">
                        Maintenance Dispatch
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                        Automated work orders can be prioritized directly through the Case Registry.
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-500">
                <span>Data Source: Edge Bus Computer Vision Pipeline</span>
                <span>Calculated over active patrol routes</span>
              </div>
            </div>
          </div>

          {/* Bottom Section: Defect Classification Breakdown */}
          <DefectBreakdown data={data} />
        </div>
      )}
    </div>
  );
};
