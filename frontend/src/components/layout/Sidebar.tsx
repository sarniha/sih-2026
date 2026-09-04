import React from "react";
import { NavLink } from "react-router-dom";
import {
  Map,
  Activity,
  ShieldAlert,
  FolderKanban,
  Bus,
  BarChart3,
  Settings,
  Terminal,
} from "lucide-react";
import { cn } from "../../lib/utils";

interface NavItem {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const navItems: NavItem[] = [
  { name: "Live Map", path: "/", icon: Map },
  { name: "Traffic", path: "/traffic", icon: Activity },
  { name: "ANPR / Incidents", path: "/anpr", icon: ShieldAlert, badge: "LIVE" },
  { name: "Case Registry", path: "/cases", icon: FolderKanban },
  { name: "Fleet", path: "/fleet", icon: Bus },
  { name: "Insights", path: "/insights", icon: BarChart3 },
  { name: "Settings", path: "/settings", icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-[#0f172a] border-r border-[#1e293b] flex flex-col justify-between select-none">
      {/* Navigation Links */}
      <div className="py-4 px-3 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
          Command Rail
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group",
                  isActive
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#1e293b]/70 border border-transparent"
                )
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 transition-transform group-hover:scale-110" />
                <span>{item.name}</span>
              </div>

              {item.badge && (
                <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/30 rounded">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Bottom Telemetry Footer */}
      <div className="p-3 border-t border-[#1e293b] bg-[#0b0f17]/40 m-2 rounded-lg">
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
          <Terminal className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-[11px] text-slate-300 font-semibold">EDGE NODE : PAT-01</span>
        </div>
        <p className="text-[10px] text-slate-400 leading-tight">
          Spatial deduplication: 10m / 5s. Auto-incident spawn active.
        </p>
      </div>
    </aside>
  );
};
