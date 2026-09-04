import React from "react";
import {
  AlertTriangle,
  Droplets,
  Signpost,
  Footprints,
  Layers,
} from "lucide-react";
import type { RoadHealthSummaryResponse } from "../../types/api";

interface DefectBreakdownProps {
  data: RoadHealthSummaryResponse;
}

export const DefectBreakdown: React.FC<DefectBreakdownProps> = ({ data }) => {
  const total = Math.max(1, data.total_defects);

  const defects = [
    {
      id: "potholes",
      label: "Potholes & Cracks",
      count: data.potholes_count,
      pct: Math.round((data.potholes_count / total) * 100),
      colorClass: "text-amber-400",
      bgClass: "bg-amber-500/10",
      borderClass: "border-amber-500/20",
      barClass: "bg-amber-400",
      Icon: AlertTriangle,
      desc: "Surface structural depressions and asphalt tears",
    },
    {
      id: "waterlogging",
      label: "Waterlogging Zones",
      count: data.waterlogging_count,
      pct: Math.round((data.waterlogging_count / total) * 100),
      colorClass: "text-cyan-400",
      bgClass: "bg-cyan-500/10",
      borderClass: "border-cyan-500/20",
      barClass: "bg-cyan-400",
      Icon: Droplets,
      desc: "Storm drainage pooling and submerged carriageways",
    },
    {
      id: "signboard",
      label: "Signboard Damage",
      count: data.signboard_damage_count,
      pct: Math.round((data.signboard_damage_count / total) * 100),
      colorClass: "text-purple-400",
      bgClass: "bg-purple-500/10",
      borderClass: "border-purple-500/20",
      barClass: "bg-purple-400",
      Icon: Signpost,
      desc: "Obscured, tilted, or defaced traffic signboards",
    },
    {
      id: "zebra",
      label: "Zebra Crossing Issues",
      count: data.zebra_crossing_issue_count,
      pct: Math.round((data.zebra_crossing_issue_count / total) * 100),
      colorClass: "text-orange-400",
      bgClass: "bg-orange-500/10",
      borderClass: "border-orange-500/20",
      barClass: "bg-orange-400",
      Icon: Footprints,
      desc: "Faded, eroded, or non-compliant pedestrian crossings",
    },
  ];

  return (
    <div className="bg-[#131e36] border border-[#1e293b] rounded-xl p-6 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2 text-slate-300 font-mono text-xs font-semibold uppercase tracking-wider">
          <Layers className="w-4 h-4 text-emerald-400" />
          Road Defect Classification Breakdown
        </div>
        <span className="text-xs font-mono text-slate-400">
          <strong className="text-slate-200">{data.total_defects}</strong> Total Defect
          {data.total_defects === 1 ? "" : "s"}
        </span>
      </div>

      {/* Grid of Defect Items */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {defects.map((item) => {
          const { Icon } = item;
          return (
            <div
              key={item.id}
              className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors flex flex-col justify-between gap-3 group"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`p-2 rounded-lg border ${item.bgClass} ${item.borderClass} ${item.colorClass}`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-mono font-bold text-slate-200">
                      {item.label}
                    </h4>
                    <p className="text-[10px] font-mono text-slate-500 mt-0.5">
                      {item.desc}
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <div
                    className={`text-lg font-mono font-bold tracking-tight ${item.colorClass}`}
                  >
                    {item.count}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500">
                    {item.pct}% of total
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${item.barClass}`}
                  style={{ width: `${item.pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
