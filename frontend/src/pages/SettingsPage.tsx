import React from "react";
import { Settings, Lock, Bell, Moon, RefreshCw, Shield, Server } from "lucide-react";

export const SettingsPage: React.FC = () => {
  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-4xl mx-auto">
      {/* ── Page Header ────────────────────────────────────── */}
      <div>
        <h1 className="text-xl font-bold text-slate-100 font-mono tracking-wide flex items-center gap-3">
          <Settings className="w-5 h-5 text-cyan-400" />
          System Settings
        </h1>
        <p className="text-xs text-slate-400 mt-1 font-mono">
          Command terminal preferences, Edge AI telemetry thresholds, and network endpoints
        </p>
      </div>

      {/* ── Demo Locked Notice ─────────────────────────────── */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
        <Lock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <div className="text-xs font-mono font-bold text-amber-300 uppercase tracking-wider">
            Demo Environment Lock
          </div>
          <p className="text-xs font-mono text-amber-200/80 mt-0.5">
            Settings configuration is locked for this demo environment. Parameter adjustments require administrator privileges.
          </p>
        </div>
      </div>

      {/* ── General Preferences Section ────────────────────── */}
      <div className="bg-[#131e36] border border-[#1e293b] rounded-xl p-6 shadow-xl space-y-5">
        <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 pb-3 border-b border-slate-800 flex items-center gap-2">
          <Moon className="w-4 h-4 text-cyan-400" />
          Interface & Telemetry Preferences
        </h2>

        <div className="space-y-4">
          {/* Dark Mode Toggle */}
          <div className="flex items-center justify-between py-2">
            <div>
              <div className="text-xs font-mono font-semibold text-slate-200">
                Command Center Dark Palette
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                Enforces high-contrast OLED-optimized slate theme
              </div>
            </div>
            <button
              type="button"
              disabled
              className="relative inline-flex h-6 w-11 shrink-0 cursor-not-allowed rounded-full bg-cyan-500/60 p-0.5 transition-colors opacity-70"
            >
              <span className="translate-x-5 inline-block h-5 w-5 transform rounded-full bg-slate-100 shadow transition" />
            </button>
          </div>

          {/* Desktop Notifications Toggle */}
          <div className="flex items-center justify-between py-2 border-t border-slate-800/80">
            <div>
              <div className="text-xs font-mono font-semibold text-slate-200 flex items-center gap-1.5">
                <Bell className="w-3.5 h-3.5 text-slate-400" />
                Desktop Incident Alerts
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                Push browser notifications for high-priority hit-and-run events
              </div>
            </div>
            <button
              type="button"
              disabled
              className="relative inline-flex h-6 w-11 shrink-0 cursor-not-allowed rounded-full bg-slate-800 p-0.5 transition-colors opacity-60"
            >
              <span className="translate-x-0 inline-block h-5 w-5 transform rounded-full bg-slate-400 shadow transition" />
            </button>
          </div>

          {/* Auto-Refresh Feeds Toggle */}
          <div className="flex items-center justify-between py-2 border-t border-slate-800/80">
            <div>
              <div className="text-xs font-mono font-semibold text-slate-200 flex items-center gap-1.5">
                <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
                Auto-Refresh Analytics Feeds
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                30s background polling for fleet diagnostics and telemetry
              </div>
            </div>
            <button
              type="button"
              disabled
              className="relative inline-flex h-6 w-11 shrink-0 cursor-not-allowed rounded-full bg-emerald-500/60 p-0.5 transition-colors opacity-70"
            >
              <span className="translate-x-5 inline-block h-5 w-5 transform rounded-full bg-slate-100 shadow transition" />
            </button>
          </div>
        </div>
      </div>

      {/* ── Threshold & Configuration Parameters ───────────── */}
      <div className="bg-[#131e36] border border-[#1e293b] rounded-xl p-6 shadow-xl space-y-5">
        <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 pb-3 border-b border-slate-800 flex items-center gap-2">
          <Shield className="w-4 h-4 text-amber-400" />
          AI Filter Thresholds & Parameters
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
            <div className="text-[11px] font-mono text-slate-400 uppercase">
              ANPR Low-Confidence Threshold
            </div>
            <div className="text-base font-mono font-bold text-amber-400 mt-1">
              60.0%
            </div>
            <div className="text-[10px] font-mono text-slate-500 mt-0.5">
              Readings below 0.60 trigger low-confidence warnings
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
            <div className="text-[11px] font-mono text-slate-400 uppercase">
              Live Buffer Depth
            </div>
            <div className="text-base font-mono font-bold text-cyan-400 mt-1">
              100 Frames
            </div>
            <div className="text-[10px] font-mono text-slate-500 mt-0.5">
              Rolling in-memory telemetry buffer depth
            </div>
          </div>
        </div>
      </div>

      {/* ── Endpoints & Environment ─────────────────────────── */}
      <div className="bg-[#131e36] border border-[#1e293b] rounded-xl p-6 shadow-xl space-y-4">
        <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 pb-3 border-b border-slate-800 flex items-center gap-2">
          <Server className="w-4 h-4 text-emerald-400" />
          Endpoint Topology
        </h2>

        <div className="space-y-3 font-mono text-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800 gap-1">
            <span className="text-slate-400">FastAPI REST Gateway:</span>
            <span className="text-slate-200 select-all">http://127.0.0.1:8000/api/v1</span>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800 gap-1">
            <span className="text-slate-400">WebSocket Stream:</span>
            <span className="text-slate-200 select-all">ws://localhost:8000/api/v1/ws/events</span>
          </div>
        </div>
      </div>
    </div>
  );
};
