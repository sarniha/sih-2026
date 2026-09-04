import React, { useState } from "react";
import { PlusCircle, Loader2, CheckCircle2, AlertTriangle, ShieldAlert } from "lucide-react";

interface NewCaseFormProps {
  onSubmitCase: (plate: string, notes?: string) => Promise<boolean>;
}

export const NewCaseForm: React.FC<NewCaseFormProps> = ({ onSubmitCase }) => {
  const [plate, setPlate] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanPlate = plate.trim().toUpperCase();
    if (!cleanPlate) {
      setErrorMessage("Please enter a suspect license plate.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await onSubmitCase(cleanPlate, notes.trim());
      setPlate("");
      setNotes("");
      setSuccessMessage(`Case for suspect plate "${cleanPlate}" registered and queued for cross-referencing.`);
      setTimeout(() => {
        setSuccessMessage(null);
      }, 5000);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to log case");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl flex flex-col justify-between">
      <div>
        {/* Card Header */}
        <div className="flex items-center gap-2.5 pb-4 border-b border-slate-700/80 mb-5">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
              Log Suspect Vehicle
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Cross-reference live bus AI feeds
            </p>
          </div>
        </div>

        {/* Status Alerts */}
        {successMessage && (
          <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-start gap-2 animate-in fade-in duration-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>{successMessage}</span>
          </div>
        )}

        {errorMessage && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-mono flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Suspect Plate Input */}
          <div>
            <label
              htmlFor="suspected_plate"
              className="block text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 mb-1.5"
            >
              Suspect Plate <span className="text-red-400">*</span>
            </label>
            <input
              id="suspected_plate"
              type="text"
              value={plate}
              onChange={(e) => setPlate(e.target.value.toUpperCase())}
              placeholder="e.g. BR01AB1234"
              maxLength={15}
              disabled={isSubmitting}
              className="w-full uppercase font-mono tracking-wider px-3.5 py-2.5 rounded-lg bg-slate-900/90 border border-slate-700 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400/50 transition-all disabled:opacity-50"
            />
            <p className="text-[11px] text-slate-500 font-mono mt-1">
              Forced uppercase. Standard Indian/state format.
            </p>
          </div>

          {/* Notes Textarea */}
          <div>
            <label
              htmlFor="case_notes"
              className="block text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 mb-1.5"
            >
              Incident Notes & Details
            </label>
            <textarea
              id="case_notes"
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Citizen police report, hit-and-run description, vehicle color/make..."
              disabled={isSubmitting}
              className="w-full font-mono px-3.5 py-2.5 rounded-lg bg-slate-900/90 border border-slate-700 text-slate-100 placeholder-slate-500 text-xs focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400/50 transition-all resize-none disabled:opacity-50"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting || !plate.trim()}
            className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono font-bold text-xs tracking-wider transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md hover:shadow-amber-500/20"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Cross-referencing Feeds...
              </>
            ) : (
              <>
                <PlusCircle className="w-4 h-4" />
                Register Suspect Case
              </>
            )}
          </button>
        </form>
      </div>

      <div className="mt-6 pt-4 border-t border-slate-700/60 text-[11px] text-slate-500 font-mono flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
        AI background cross-checks incoming frames against all open cases.
      </div>
    </div>
  );
};
