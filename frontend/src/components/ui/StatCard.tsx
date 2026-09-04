import React from "react";
import { cn } from "../../lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  trend?: string;
  colorClass?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon: Icon,
  trend,
  colorClass = "text-emerald-400",
}) => {
  return (
    <div className="bg-[#131e36] rounded-lg border border-[#1e293b] p-4 hover:border-[#334155] transition-colors group">
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400">
          {title}
        </span>
        <div
          className={cn(
            "h-8 w-8 rounded-md flex items-center justify-center border bg-opacity-10 transition-transform group-hover:scale-110",
            colorClass === "text-emerald-400"
              ? "bg-emerald-500/10 border-emerald-500/20"
              : colorClass === "text-amber-400"
              ? "bg-amber-500/10 border-amber-500/20"
              : colorClass === "text-cyan-400"
              ? "bg-cyan-500/10 border-cyan-500/20"
              : colorClass === "text-blue-400"
              ? "bg-blue-500/10 border-blue-500/20"
              : colorClass === "text-red-400"
              ? "bg-red-500/10 border-red-500/20"
              : "bg-slate-500/10 border-slate-500/20"
          )}
        >
          <Icon className={cn("w-4 h-4", colorClass)} />
        </div>
      </div>

      {/* Value */}
      <div className={cn("text-2xl font-bold font-mono tracking-tight", colorClass)}>
        {value}
      </div>

      {/* Trend / Subtitle */}
      {trend && (
        <div className="mt-1.5 text-[11px] text-slate-400 font-mono">
          {trend}
        </div>
      )}
    </div>
  );
};
