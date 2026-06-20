"use client";

import { X, FileUp } from "lucide-react";
import type { Document } from "../lib/types";

interface DocManagerProps {
  visible: boolean;
  onClose: () => void;
  documents: Document[];
  loadingDocs: boolean;
  uploadStatus: string;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onReingest: (filename: string, threadId?: string) => void;
  onDelete: (filename: string, threadId?: string) => void;
}

export default function DocManager({ visible, onClose, documents, loadingDocs, uploadStatus, onFileUpload, onReingest, onDelete }: DocManagerProps) {
  if (!visible) return null;

  const globalDocs = documents.filter(d => !d.thread_id);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-all p-4">
      <div className="bg-[var(--bg-elevated)] border border-[var(--border-default)] p-4 md:p-8 rounded-2xl shadow-2xl w-full max-w-2xl relative flex flex-col max-h-[85vh]">
        <button onClick={onClose} className="absolute top-4 right-4 text-[var(--text-tertiary)] hover:text-primary transition-colors shrink-0"><X size={20} /></button>
        <h3 className="text-xl font-bold text-primary mb-2 shrink-0">Manage Knowledge Base</h3>
        <p className="text-sm text-[var(--text-secondary)] mb-6 shrink-0">Upload documents or manage currently indexed vector database chunks.</p>

        <div className="border border-dashed border-[var(--border-default)] hover:border-[var(--accent-blue)]/50 rounded-xl p-4 flex flex-col items-center justify-center text-center transition-colors bg-[var(--bg-hover)] relative group mb-6 shrink-0">
          <FileUp size={24} className="text-[var(--accent-blue)] mb-2 group-hover:scale-110 transition-transform" />
          <span className="text-xs font-medium text-primary">Click to upload new document</span>
          <span className="text-2xs text-[var(--text-tertiary)] mt-0.5">PDF, TXT, MD, or CSV (Max 10MB)</span>
          <input type="file" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" accept=".pdf,.txt,.md,.csv" onChange={onFileUpload} />
        </div>

        {uploadStatus && <div className="mb-4 text-xs font-mono text-center text-[var(--accent-blue)] animate-pulse shrink-0">{uploadStatus}</div>}

        <div className="flex-1 overflow-y-auto space-y-3 min-h-[200px] border-t border-[var(--border-default)] pt-4 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-[var(--border-default)] hover:[&::-webkit-scrollbar-thumb]:bg-[var(--border-hover)] [&::-webkit-scrollbar-thumb]:rounded-full">
          <div className="flex justify-between items-center text-xs font-mono text-[var(--text-tertiary)] mb-2 px-1">
            <span>INDEXED SOURCE FILES</span>
            {loadingDocs && <span className="animate-spin">⚙️</span>}
          </div>
          {globalDocs.length === 0 ? (
            <div className="text-center py-12 text-sm text-[var(--text-tertiary)] font-mono">{loadingDocs ? "Loading indexed documents..." : "No source files currently indexed."}</div>
          ) : (
            <div className="divide-y divide-[var(--border-default)]">
              {globalDocs.map((doc) => (
                <div key={doc.filename} className="flex items-center justify-between py-3 px-1 hover:bg-[var(--bg-hover)] rounded-lg transition-colors group">
                  <div className="flex items-center gap-3 min-w-0 flex-1 pr-4">
                    <div className="h-8 w-8 rounded bg-[var(--bg-hover)] border border-[var(--border-default)] flex items-center justify-center text-[var(--text-secondary)] shrink-0">
                      {doc.filename.endsWith(".pdf") ? "📕" : doc.filename.endsWith(".csv") ? "📊" : "📄"}
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-primary truncate" title={doc.filename}>{doc.filename}</div>
                      <div className="text-2xs text-[var(--text-tertiary)] font-mono mt-0.5 flex gap-2">
                        <span>{doc.size_bytes > 0 ? `${(doc.size_bytes / 1024).toFixed(1)} KB` : "N/A"}</span>
                        <span>•</span>
                        <span className="text-[var(--accent-blue)] font-semibold">{doc.chunks_count} chunks</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className={`px-2 py-0.5 rounded text-2xs font-mono font-bold ${
                      doc.status === "Ingested" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : doc.status === "Pending" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse" : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    }`}>{doc.status}</span>
                    {doc.status !== "Ingested (DB only)" && (
                      <button type="button" onClick={() => onReingest(doc.filename, doc.thread_id)} className="p-1 rounded hover:bg-blue-500/10 text-[var(--text-tertiary)] hover:text-blue-400 transition-all cursor-pointer opacity-0 group-hover:opacity-100 focus:opacity-100 shrink-0 text-xs" title="Re-ingest/Retry document processing">🔄</button>
                    )}
                    <button type="button" onClick={() => onDelete(doc.filename, doc.thread_id)} className="p-1 rounded hover:bg-red-500/10 text-[var(--text-tertiary)] hover:text-red-400 transition-all cursor-pointer opacity-0 group-hover:opacity-100 focus:opacity-100 shrink-0 text-xs" title="Delete document and chunks">❌</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
