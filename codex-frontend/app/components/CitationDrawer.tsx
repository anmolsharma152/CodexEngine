"use client";

import { TerminalSquare, X } from "lucide-react";

interface CitationDrawerProps {
  open: boolean;
  onClose: () => void;
  source: string;
  page: string;
  row: string;
  chunk: string;
}

export default function CitationDrawer({ open, onClose, source, page, row, chunk }: CitationDrawerProps) {
  if (!open) return null;

  return (
    <>
      <div onClick={onClose} className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 transition-opacity duration-300" />
      <aside className={`fixed top-0 right-0 h-full w-full sm:w-[450px] bg-[var(--bg-elevated)]/95 backdrop-blur-2xl border-l border-[var(--border-default)] shadow-2xl z-50 transform translate-x-0 transition-transform duration-300 ease-in-out flex flex-col`}>
        <div className="h-16 flex items-center justify-between px-6 border-b border-[var(--border-default)]">
          <div className="flex items-center gap-2">
            <TerminalSquare className="text-[var(--accent-blue)]" size={18} />
            <span className="font-bold text-primary tracking-tight">Source Context</span>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-[var(--text-secondary)] hover:text-primary hover:bg-[var(--bg-hover)] transition-all"><X size={20} /></button>
        </div>
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="space-y-1">
            <div className="text-2xs uppercase tracking-wider text-[var(--text-tertiary)] font-mono">Document</div>
            <div className="text-sm font-semibold text-primary break-all">{source}</div>
          </div>
          {(page || row) && (
            <div className="flex gap-6">
              {page && <div><div className="text-2xs uppercase tracking-wider text-[var(--text-tertiary)] font-mono">Page</div><div className="text-sm font-semibold text-[var(--accent-blue)] font-mono">{page}</div></div>}
              {row && <div><div className="text-2xs uppercase tracking-wider text-[var(--text-tertiary)] font-mono">Row Index</div><div className="text-sm font-semibold text-[var(--accent-blue)] font-mono">{row}</div></div>}
            </div>
          )}
          <div className="space-y-2">
            <div className="text-2xs uppercase tracking-wider text-[var(--text-tertiary)] font-mono">Retrieved Chunk</div>
            <div className="bg-[var(--bg-surface)]/80 border border-[var(--border-default)] rounded-xl p-4 text-xs font-mono text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed max-h-[50vh] overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-[var(--border-default)] [&::-webkit-scrollbar-thumb]:rounded-full">{chunk}</div>
          </div>
        </div>
        <div className="p-6 border-t border-[var(--border-default)] bg-[var(--bg-inset)] text-2xs font-mono text-[var(--text-tertiary)] text-center">V5.0 Agentic • Custom Loop</div>
      </aside>
    </>
  );
}
