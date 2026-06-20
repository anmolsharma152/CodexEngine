"use client";

import { MessageSquare, Pin, Edit2, Trash2 } from "lucide-react";
import type { Thread } from "../lib/types";

interface ThreadItemProps {
  t: Thread;
  isActive: boolean;
  isEditing: boolean;
  editTitle: string;
  sidebarOpen: boolean;
  onSelect: (id: string) => void;
  onTogglePin: (id: string) => void;
  onStartRename: (id: string, title: string) => void;
  onSaveRename: (id: string) => void;
  onDelete: (id: string) => void;
  setEditTitle: (v: string) => void;
  setEditingThreadId: (v: string | null) => void;
}

export default function ThreadItem({
  t, isActive, isEditing, editTitle, sidebarOpen,
  onSelect, onTogglePin, onStartRename, onSaveRename, onDelete,
  setEditTitle, setEditingThreadId,
}: ThreadItemProps) {
  if (!sidebarOpen) {
    return (
      <div className="px-0 relative group mb-1.5 flex justify-center">
        <button onClick={() => onSelect(t.id)} className={`flex items-center justify-center w-10 h-10 rounded-lg transition-all border border-transparent relative ${isActive ? "bg-[var(--accent-blue-dim)] text-[var(--accent-blue)] border-[var(--accent-blue-dim)]" : "text-[var(--text-tertiary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-secondary)] hover:border-[var(--border-default)]"}`} title={t.title}>
          <MessageSquare size={16} />
          {t.pinned && <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-[var(--accent-blue)]" />}
        </button>
      </div>
    );
  }

  return (
    <div className="px-4 mb-1">
      <div className={`group flex items-center justify-between rounded-lg transition-all border border-transparent ${isActive ? "bg-[var(--accent-blue-dim)] text-[var(--accent-blue)] border-[var(--accent-blue-dim)]" : "text-[var(--text-tertiary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-secondary)] hover:border-[var(--border-default)]"}`}>
        {isEditing ? (
          <input type="text" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") onSaveRename(t.id); if (e.key === "Escape") setEditingThreadId(null); }} onBlur={() => onSaveRename(t.id)} className="flex-1 bg-[var(--bg-inset)] text-primary border border-[var(--accent-blue)]/50 rounded px-2.5 py-1.5 text-xs font-sans outline-none focus:ring-1 focus:ring-[var(--accent-blue)] min-w-0" autoFocus />
        ) : (
          <div className="flex-1 flex items-center min-w-0 pr-1 py-1 px-2">
            <button onClick={() => onSelect(t.id)} className="flex-1 flex items-center gap-2.5 text-sm font-medium transition-all text-left min-w-0 py-1" title={t.title}>
              <MessageSquare size={14} className="text-[var(--text-tertiary)] shrink-0 group-hover:text-[var(--accent-blue)] transition-colors" />
              <span className="truncate pr-1">{t.title}</span>
            </button>
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity pr-1">
              <button onClick={() => onTogglePin(t.id)} title={t.pinned ? "Unpin Chat" : "Pin Chat"} className={`p-1 rounded hover:bg-[var(--bg-hover)] transition-colors ${t.pinned ? "text-[var(--accent-blue)]" : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"}`}>
                <Pin size={12} className={t.pinned ? "rotate-45 fill-[var(--accent-blue)]" : "rotate-45"} />
              </button>
              <button onClick={() => onStartRename(t.id, t.title)} title="Rename" className="p-1 rounded hover:bg-[var(--bg-hover)] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] transition-colors">
                <Edit2 size={12} />
              </button>
              <button onClick={() => onDelete(t.id)} title="Delete" className="p-1 rounded hover:bg-[var(--bg-hover)] text-[var(--text-tertiary)] hover:text-red-400 transition-colors">
                <Trash2 size={12} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
