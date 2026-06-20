"use client";

import { FileText, Trash2 } from "lucide-react";
import type { Document } from "../lib/types";

interface SessionFilesProps {
  files: Document[];
  onRemove: (filename: string) => void;
}

export default function SessionFiles({ files, onRemove }: SessionFilesProps) {
  if (files.length === 0) return null;

  return (
    <div className="px-2 pb-2 space-y-1">
      <div className="px-2 py-1 text-2xs font-mono uppercase tracking-wider text-[var(--text-tertiary)] font-bold">Session Files</div>
      {files.map((file) => (
        <div key={file.filename} className="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-[var(--bg-hover)] transition-colors text-xs group">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <FileText size={12} className="text-[var(--text-tertiary)] shrink-0" />
            <span className="truncate text-[var(--text-secondary)]" title={file.filename}>{file.filename}</span>
            <span className={`text-2xs font-mono shrink-0 ${
              file.status === "Ingested" ? "text-emerald-500" : file.status === "Pending" ? "text-amber-400 animate-pulse" : "text-blue-400"
            }`}>({file.chunks_count})</span>
          </div>
          <button
            type="button"
            onClick={() => onRemove(file.filename)}
            className="p-0.5 rounded text-[var(--text-tertiary)] hover:text-red-400 hover:bg-red-500/10 transition-all opacity-0 group-hover:opacity-100 focus:opacity-100 cursor-pointer"
            title="Remove from session"
          >
            <Trash2 size={10} />
          </button>
        </div>
      ))}
    </div>
  );
}
