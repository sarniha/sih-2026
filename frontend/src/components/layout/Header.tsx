import React, { useState, useEffect } from "react";
import { Bell, Radio, Server, Clock } from "lucide-react";
import { useWsStatus } from "../../contexts/WsStatusContext";

export const Header: React.FC = () => {
  const [time, setTime] = useState<string>("");
  const { status: wsStatus } = useWsStatus();

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(
        now.toLocaleTimeString("en-GB", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const isOnline = wsStatus === "connected";
  const isReconnecting = wsStatus === "reconnecting";

  return (
    <header className="h-16 bg-[#0f172a] border-b border-[#1e293b] px-6 flex items-center justify-between select-none z-30">
      {/* Brand & App Title */}
      <div className="flex items-center gap-3">
        <div
          className={`h-9 w-9 rounded-lg border flex items-center justify-center transition-colors ${
            isOnline
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : isReconnecting
              ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
              : "bg-red-500/10 border-red-500/30 text-red-400"
          }`}
        >
          <Radio className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold tracking-wider text-slate-100 font-mono">
              SMARTBUS <span className="text-emerald-400">COMMAND</span>
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded font-mono">
              PATNA // LIVE
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-medium">
            AI Fleet Telemetry & Safety Incident Operations
          </p>
        </div>
      </div>

      {/* Center / System Telemetry Status */}
      <div className="hidden md:flex items-center gap-6 text-xs text-slate-400 font-mono">
        {/* System Online indicator – now reacts to WebSocket state */}
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md border transition-colors ${
            isOnline
              ? "bg-[#131e36] border-emerald-500/30 text-emerald-400"
              : isReconnecting
              ? "bg-amber-500/5 border-amber-500/30 text-amber-400"
              : "bg-red-500/5 border-red-500/30 text-red-400"
          }`}
        >
          <span className="relative flex h-2.5 w-2.5">
            <span
              className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isOnline
                  ? "animate-ping bg-emerald-400"
                  : isReconnecting
                  ? "animate-ping bg-amber-400"
                  : "bg-red-400"
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isOnline
                  ? "bg-emerald-500"
                  : isReconnecting
                  ? "bg-amber-500"
                  : "bg-red-500"
              }`}
            />
          </span>
          <span className="font-semibold tracking-wide text-xs">
            {isOnline
              ? "SYSTEM ONLINE"
              : isReconnecting
              ? "RECONNECTING"
              : "SYSTEM OFFLINE"}
          </span>
          <span className="text-[10px] text-slate-400">| POSTGIS</span>
        </div>

        {/* Live Clock */}
        <div className="flex items-center gap-1.5 text-slate-300 bg-[#1e293b]/50 px-2.5 py-1 rounded border border-[#334155]">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{time || "00:00:00"}</span>
        </div>
      </div>

      {/* Right Action Icons */}
      <div className="flex items-center gap-3">
        {/* Service status pill */}
        <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-400 bg-[#1e293b]/50 px-2.5 py-1 rounded border border-[#334155]">
          <Server className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-300">FastAPI v1</span>
        </div>

        {/* Notification Bell with Badge */}
        <button
          className="relative p-2 rounded-lg bg-[#1e293b] hover:bg-[#334155] text-slate-300 hover:text-white transition-colors border border-[#334155]"
          title="Incident Alerts"
          type="button"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white shadow-sm">
            2
          </span>
        </button>

        {/* User / Operator Badge */}
        <div className="flex items-center gap-2 pl-2 border-l border-[#1e293b]">
          <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 text-xs font-mono font-bold">
            OP1
          </div>
        </div>
      </div>
    </header>
  );
};
