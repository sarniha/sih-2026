import React, { useEffect } from "react";
import { X, ExternalLink, Image as ImageIcon } from "lucide-react";
import { useEvidenceViewer } from "../../contexts/EvidenceViewerContext";

export const EvidenceViewerModal: React.FC = () => {
  const { isOpen, imageUrl, closeModal } = useEvidenceViewer();

  // Close on Escape key press
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeModal();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, closeModal]);

  if (!isOpen || !imageUrl) {
    return null;
  }

  return (
    <div
      onClick={closeModal}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-200"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative max-w-[90vw] max-h-[90vh] flex flex-col items-center justify-center bg-slate-950/90 rounded-2xl border border-slate-700/80 shadow-2xl overflow-hidden group"
      >
        {/* Top Control Bar */}
        <div className="w-full flex items-center justify-between px-4 py-3 bg-slate-900/90 border-b border-slate-800 text-xs font-mono text-slate-300">
          <div className="flex items-center gap-2">
            <ImageIcon className="w-4 h-4 text-cyan-400" />
            <span className="font-semibold text-slate-200 uppercase tracking-wider">
              Optical Evidence Viewer
            </span>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={imageUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              title="Open full resolution in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
            <button
              onClick={closeModal}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Close viewer (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Enlarged Image */}
        <div className="p-3 flex items-center justify-center max-w-[90vw] max-h-[82vh] overflow-auto">
          <img
            src={imageUrl}
            alt="Enlarged Evidence Frame"
            className="max-w-[88vw] max-h-[78vh] object-contain rounded-lg shadow-inner"
          />
        </div>

        {/* Footer info bar */}
        <div className="w-full px-4 py-2 bg-slate-900/70 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-500">
          <span className="truncate max-w-sm" title={imageUrl}>
            {imageUrl}
          </span>
          <span className="hidden sm:inline">Press Esc or click outside to dismiss</span>
        </div>
      </div>
    </div>
  );
};
