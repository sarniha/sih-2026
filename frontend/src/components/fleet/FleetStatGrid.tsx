import React from "react";
import { Bus, Radio, Camera, Video, AlertTriangle } from "lucide-react";
import type { FleetSummaryResponse } from "../../types/api";
import { StatCard } from "../ui/StatCard";

interface FleetStatGridProps {
  summary: FleetSummaryResponse;
}

export const FleetStatGrid: React.FC<FleetStatGridProps> = ({ summary }) => {
  const hasOfflineCameras = summary.online_cameras < summary.total_cameras;
  const activeBusPct = summary.total_buses > 0
    ? Math.round((summary.active_buses / summary.total_buses) * 100)
    : 0;

  const cameraColorClass = hasOfflineCameras
    ? summary.online_cameras === 0
      ? "text-red-400"
      : "text-amber-400"
    : "text-emerald-400";

  const cameraTrend = hasOfflineCameras
    ? `⚠️ ${summary.total_cameras - summary.online_cameras} offline hardware unit(s)`
    : "100% optical sensors transmitting";

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Total Buses"
        value={summary.total_buses}
        icon={Bus}
        trend="Registered fleet vehicles"
        colorClass="text-blue-400"
      />

      <StatCard
        title="Active Buses"
        value={summary.active_buses}
        icon={Radio}
        trend={`${activeBusPct}% fleet operational`}
        colorClass="text-emerald-400"
      />

      <StatCard
        title="Total Cameras"
        value={summary.total_cameras}
        icon={Camera}
        trend="Deployed Edge AI camera units"
        colorClass="text-cyan-400"
      />

      <StatCard
        title="Online Cameras"
        value={`${summary.online_cameras} / ${summary.total_cameras}`}
        icon={hasOfflineCameras ? AlertTriangle : Video}
        trend={cameraTrend}
        colorClass={cameraColorClass}
      />
    </div>
  );
};
