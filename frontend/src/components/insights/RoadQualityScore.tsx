import React from "react";
import { ShieldCheck, AlertTriangle, AlertOctagon, Gauge } from "lucide-react";
import type { RiskLevel } from "../../types/api";

interface RoadQualityScoreProps {
  roadQualityIndex: number;
  riskLevel: RiskLevel | string;
}

export const RoadQualityScore: React.FC<RoadQualityScoreProps> = ({
  roadQualityIndex,
  riskLevel,
}) => {
  const score = Math.max(0, Math.min(100, Math.round(roadQualityIndex)));

  // Color coding: >80 is Green, 50-80 is Amber, <50 is Red
  const { colorClass, strokeColor, bgColor, borderColor, label, Icon } = (() => {
    if (score > 80) {
      return {
        colorClass: "text-emerald-400",
        strokeColor: "#34d399",
        bgColor: "bg-emerald-500/10",
        borderColor: "border-emerald-500/30",
        label: "Optimal Surface Quality",
        Icon: ShieldCheck,
      };
    } else if (score >= 50) {
      return {
        colorClass: "text-amber-400",
        strokeColor: "#fbbf24",
        bgColor: "bg-amber-500/10",
        borderColor: "border-amber-500/30",
        label: "Moderate Degradation",
        Icon: AlertTriangle,
      };
    } else {
      return {
        colorClass: "text-red-400",
        strokeColor: "#f87171",
        bgColor: "bg-red-500/10",
        borderColor: "border-red-500/30",
        label: "Severe Surface Hazards",
        Icon: AlertOctagon,
      };
    }
  })();

  // SVG Gauge Calculations
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  // Use a 260-degree arc gauge
  const arcLength = circumference * 0.75;
  const strokeDashoffset = arcLength - (score / 100) * arcLength;

  return (
    <div className="bg-[#131e36] border border-[#1e293b] rounded-xl p-6 shadow-xl flex flex-col items-center justify-center relative overflow-hidden">
      {/* Header */}
      <div className="w-full flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2 text-slate-300 font-mono text-xs font-semibold uppercase tracking-wider">
          <Gauge className="w-4 h-4 text-cyan-400" />
          Road Quality Index (RQI)
        </div>
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider border ${bgColor} ${borderColor} ${colorClass}`}
        >
          <Icon className="w-3 h-3" />
          {riskLevel} Risk
        </span>
      </div>

      {/* Circular Gauge */}
      <div className="relative w-48 h-44 flex items-center justify-center my-2">
        <svg
          className="w-48 h-48 -rotate-90 transform"
          viewBox="0 0 160 160"
        >
          {/* Background Track */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke="#1e293b"
            strokeWidth="12"
            fill="none"
            strokeDasharray={arcLength}
            strokeDashoffset="0"
            strokeLinecap="round"
          />
          {/* Animated Value Arc */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke={strokeColor}
            strokeWidth="12"
            fill="none"
            strokeDasharray={arcLength}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center Prominent Score */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center pt-2">
          <div className="flex items-baseline justify-center">
            <span
              className={`text-5xl font-mono font-black tracking-tight ${colorClass}`}
            >
              {score}
            </span>
            <span className="text-slate-500 font-mono text-sm ml-1">/100</span>
          </div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 mt-1">
            Safety Score
          </span>
        </div>
      </div>

      {/* Description Assessment */}
      <div className="text-center mt-2">
        <div className={`text-xs font-mono font-bold ${colorClass}`}>
          {label}
        </div>
        <p className="text-[11px] font-mono text-slate-400 mt-1 max-w-xs">
          Calculated dynamically from detected road surface anomalies, structural degradation, and pavement defects.
        </p>
      </div>
    </div>
  );
};
