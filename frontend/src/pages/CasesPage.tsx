import React from "react";
import {
  FolderLock,
  RefreshCw,
  AlertCircle,
  ClipboardList,
} from "lucide-react";
import { useCases } from "../hooks/useCases";
import { CaseTable } from "../components/cases/CaseTable";
import { NewCaseForm } from "../components/cases/NewCaseForm";

export const CasesPage: React.FC = () => {
  const { cases, isLoading, error, refresh, submitNewCase } = useCases();

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-wide flex items-center gap-3">
            <FolderLock className="w-5 h-5 text-amber-400" />
            Active Case Registry
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Citizen report logging, suspect vehicle hot-listing, and automated edge fleet cross-referencing
          </p>
        </div>

        <button
          onClick={refresh}
          disabled={isLoading}
          className="self-start sm:self-auto flex items-center gap-2 px-3 py-2 rounded-lg bg-[#131e36] hover:bg-[#1e293b] border border-[#1e293b] hover:border-[#334155] text-slate-300 hover:text-white text-xs font-mono font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          title="Refresh Case Registry"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* ── Loading Skeleton ───────────────────────────────── */}
      {isLoading && cases.length === 0 && (
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
      {error && !isLoading && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-sm font-mono font-bold text-red-400">
              Case Registry Connection Error
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

      {/* ── Main Two-Column Layout ─────────────────────────── */}
      {(!isLoading || cases.length > 0) && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Left Column: Case Table or Empty State (span 2) */}
          <div className="lg:col-span-2 space-y-4">
            {cases.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 px-6 bg-slate-800/50 rounded-xl border border-slate-700/60 text-center">
                <ClipboardList className="w-16 h-16 text-slate-600 mb-4 opacity-40" />
                <h3 className="text-sm font-mono font-bold text-slate-300">
                  No active cases
                </h3>
                <p className="text-xs text-slate-500 font-mono mt-1 max-w-md">
                  No suspect vehicle records found in registry. Use the form on the right to log a suspect license plate from citizen or police alerts.
                </p>
              </div>
            ) : (
              <CaseTable cases={cases} />
            )}
          </div>

          {/* Right Column: New Case Form (span 1) */}
          <div className="lg:col-span-1 sticky top-6">
            <NewCaseForm onSubmitCase={submitNewCase} />
          </div>
        </div>
      )}
    </div>
  );
};
