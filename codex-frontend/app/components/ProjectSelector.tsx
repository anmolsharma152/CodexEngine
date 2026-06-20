"use client";

import { useState } from "react";
import { Folder, Plus, Check, Pencil, Trash, ChevronDown } from "lucide-react";
import type { Project } from "../lib/types";

interface ProjectSelectorProps {
  projects: Project[];
  activeProjectId: string;
  onSelect: (id: string) => void;
  onCreate: (name: string) => void;
  onRename: (id: string, name: string) => void;
  onDelete: (id: string) => void;
}

export default function ProjectSelector({
  projects, activeProjectId, onSelect, onCreate, onRename, onDelete,
}: ProjectSelectorProps) {
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");

  const active = projects.find((p) => p.id === activeProjectId);

  const handleCreate = () => {
    if (newName.trim()) {
      onCreate(newName.trim());
      setNewName("");
      setCreating(false);
    }
  };

  const handleRename = (id: string) => {
    if (editName.trim()) {
      onRename(id, editName.trim());
      setEditingId(null);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-primary hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
      >
        <Folder size={14} className="text-[var(--accent-blue)] shrink-0" />
        <span className="truncate flex-1 text-left">{active?.name || "General"}</span>
        <ChevronDown size={12} className="text-[var(--text-tertiary)] shrink-0" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => { setOpen(false); setCreating(false); setEditingId(null); }} />
          <div className="absolute left-0 right-0 top-full mt-1 z-20 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl shadow-xl overflow-hidden">
            <div className="max-h-48 overflow-y-auto p-1 space-y-0.5">
              {projects.map((p) => (
                <div key={p.id} className="group flex items-center gap-1 px-2 py-1.5 rounded-lg hover:bg-[var(--bg-hover)]">
                  {editingId === p.id ? (
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") handleRename(p.id); if (e.key === "Escape") setEditingId(null); }}
                      onBlur={() => handleRename(p.id)}
                      className="flex-1 bg-[var(--bg-inset)] text-primary text-xs border border-[var(--accent-blue)]/50 rounded px-2 py-1 outline-none focus:ring-1 focus:ring-[var(--accent-blue)]"
                      autoFocus
                    />
                  ) : (
                    <button
                      onClick={() => { onSelect(p.id); setOpen(false); }}
                      className={`flex items-center gap-2 flex-1 text-left text-xs py-0.5 ${p.id === activeProjectId ? "text-primary font-semibold" : "text-[var(--text-secondary)]"}`}
                    >
                      <Folder size={12} className="text-[var(--text-tertiary)] shrink-0" />
                      <span className="truncate">{p.name}</span>
                      {p.id === activeProjectId && <Check size={12} className="text-[var(--accent-blue)] shrink-0 ml-auto" />}
                    </button>
                  )}
                  {p.id !== "default" && editingId !== p.id && (
                    <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                      <button onClick={() => { setEditingId(p.id); setEditName(p.name); }} className="p-1 rounded hover:bg-[var(--bg-hover)] text-[var(--text-tertiary)] hover:text-primary transition-colors cursor-pointer">
                        <Pencil size={10} />
                      </button>
                      <button onClick={() => onDelete(p.id)} className="p-1 rounded hover:bg-red-500/10 text-[var(--text-tertiary)] hover:text-red-400 transition-colors cursor-pointer">
                        <Trash size={10} />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
            {creating ? (
              <div className="border-t border-[var(--border-default)] p-2">
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleCreate(); if (e.key === "Escape") { setCreating(false); setNewName(""); } }}
                  placeholder="Project name..."
                  className="w-full bg-[var(--bg-inset)] text-primary text-xs border border-[var(--accent-blue)]/50 rounded px-2 py-1.5 outline-none focus:ring-1 focus:ring-[var(--accent-blue)]"
                  autoFocus
                />
              </div>
            ) : (
              <button
                onClick={() => setCreating(true)}
                className="flex items-center gap-2 w-full px-3 py-2 text-xs text-[var(--text-secondary)] hover:text-primary hover:bg-[var(--bg-hover)] transition-colors border-t border-[var(--border-default)] cursor-pointer"
              >
                <Plus size={12} />
                <span>New Project</span>
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
