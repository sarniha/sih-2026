import React from "react";
import { Gauge, ShieldCheck, AlertTriangle, Flame } from "lucide-react";
import { cn } from "../../lib/utils";

interface CongestionPanelProps {
  congestion_level?: string | null;
}

interface LevelConfig {
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  textColor: string;
  borderColor: string;
  bgColor: string;
  barWidth: string;
  barColor: string;
  glowColor: string;
}

const LEVEL_CONFIG: Record<string, LevelConfig> = {
  low: {
    label: "LOW",
    description: "Traffic is flowing smoothly across monitored corridors. No congestion detected.",
    icon: ShieldCheck,
    textColor: "text-emerald-400",
    borderColor: "border-emerald-500/30",
    bgColor: "bg-emerald-500/5",
    barWidth: "w-1/4",
    barColor: "bg-emerald-500",
    glowColor: "shadow-emerald-500/20",
  },
  moderate: {
    label: "MODERATE",
    description: "Elevated vehicle density detected. Expect slowdowns on primary routes.",
    icon: AlertTriangle,
    textColor: "text-amber-400",
    borderColor: "border-amber-500/30",
    bgColor: "bg-amber-500/5",
    barWidth: "w-2/3",
    barColor: "bg-amber-500",
    glowColor: "shadow-amber-500/20",
  },
  severe: {
    label: "SEVERE",
    description: "Critical congestion level. Multiple corridors experiencing gridlock conditions.",
    icon: Flame,
    textColor: "text-red-400",
    borderColor: "border-red-500/30",
    bgColor: "bg-red-500/5",
    barWidth: "w-full",
    barColor: "bg-red-500",
    glowColor: "shadow-red-500/20",
  },
};

export const CongestionPanel: React.FC<CongestionPanelProps> = ({
  congestion_level,
}) => {
  const cfg = congestion_level ? LEVEL_CONFIG[congestion_level] : null;

  // Fallback for undefined / unrecognized level
  if (!cfg) {
    return (
      <div className="bg-[#131e36] rounded-lg border border-[#1e293b] p-6">
        <div className="flex items-center gap-3 mb-3">
          <Gauge className="w-5 h-5 text-slate-500" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
            Congestion Level
          </span>
        </div>
        <div className="text-center py-6">
          <Gauge className="w-10 h-10 text-slate-600 mx-auto mb-3 opacity-40" />
          <p className="text-sm text-slate-500 font-mono">
            Congestion data unavailable
          </p>
        </div>
      </div>
    );
  }

  const Icon = cfg.icon;

  return (
    <div
      className={cn(
        "rounded-lg border p-6 transition-colors",
        cfg.bgColor,
        cfg.borderColor
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Gauge className={cn("w-5 h-5", cfg.textColor)} />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
            Congestion Level
          </span>
        </div>
        <div
          className={cn(
            "flex items-center gap-2 px-3 py-1 rounded-md border",
            cfg.bgColor,
            cfg.borderColor
          )}
        >
          <Icon className={cn("w-4 h-4", cfg.textColor)} />
          <span
            className={cn(
              "text-xs font-mono font-bold uppercase tracking-widest",
              cfg.textColor
            )}
          >
            {cfg.label}
          </span>
        </div>
      </div>

      {/* Large Level Display */}
      <div className="mb-4">
        <span
          className={cn(
            "text-4xl font-bold font-mono tracking-tight",
            cfg.textColor
          )}
        >
          {cfg.label}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="h-2 w-full bg-[#1e293b] rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-700 ease-out shadow-sm",
              cfg.barColor,
              cfg.barWidth,
              cfg.glowColor
            )}
          />
        </div>
      </div>

      {/* Description */}
      <p className="text-xs text-slate-400 font-mono leading-relaxed">
        {cfg.description}
      </p>
    </div>
  );
};
