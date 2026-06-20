"use client";

import { useState, useRef, useEffect } from "react";
import { Paperclip, Send, X, HelpCircle, Trash2, Download, Settings, Slash } from "lucide-react";
import type { Document } from "../lib/types";

interface SlashCommand {
  id: string;
  label: string;
  description: string;
  icon: typeof HelpCircle;
  action: (input: string, setInput: (v: string) => void) => void;
}

const SLASH_COMMANDS: SlashCommand[] = [
  { id: "help", label: "Help", description: "Show available commands and features", icon: HelpCircle, action: (_, setInput) => setInput("/help") },
  { id: "clear", label: "Clear", description: "Clear current conversation", icon: Trash2, action: (_, setInput) => setInput("/clear") },
  { id: "export", label: "Export", description: "Export chat as markdown", icon: Download, action: (_, setInput) => setInput("/export") },
  { id: "settings", label: "Settings", description: "Open settings panel", icon: Settings, action: (_, setInput) => setInput("/settings") },
];

interface InputBarProps {
  input: string;
  setInput: (v: string) => void;
  isStreaming: boolean;
  sessionFiles: Document[];
  uploadingFile: boolean;
  threadId: string;
  onSend: (e: React.FormEvent) => void;
  onStopThinking: () => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemoveFile: (filename: string) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
}

export default function InputBar({
  input, setInput, isStreaming, sessionFiles, uploadingFile, threadId,
  onSend, onStopThinking, onFileSelect, onRemoveFile,
  inputRef, fileInputRef,
}: InputBarProps) {
  const [slashOpen, setSlashOpen] = useState(false);
  const [slashIndex, setSlashIndex] = useState(0);
  const slashRef = useRef<HTMLDivElement>(null);

  const isSlashActive = input.startsWith("/") && !input.includes(" ");
  const filteredCommands = isSlashActive
    ? SLASH_COMMANDS.filter((c) => c.id.startsWith(input.slice(1).toLowerCase()))
    : SLASH_COMMANDS;

  useEffect(() => {
    if (isSlashActive && filteredCommands.length > 0) {
      setSlashOpen(true);
      setSlashIndex(0);
    } else {
      setSlashOpen(false);
    }
  }, [input, isSlashActive, filteredCommands.length]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (slashRef.current && !slashRef.current.contains(e.target as Node)) {
        setSlashOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!slashOpen) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSlashIndex((i) => Math.min(i + 1, filteredCommands.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSlashIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" || e.key === "Tab") {
      if (filteredCommands[slashIndex]) {
        e.preventDefault();
        filteredCommands[slashIndex].action(input, setInput);
        setSlashOpen(false);
      }
    } else if (e.key === "Escape") {
      setSlashOpen(false);
    }
  };

  return (
    <div className="p-6">
      <input type="file" ref={fileInputRef} onChange={onFileSelect} accept=".pdf,.txt,.md,.csv" className="hidden" />

      {(sessionFiles.length > 0 || uploadingFile) && (
        <div className="max-w-4xl mx-auto mb-3 flex flex-wrap gap-2">
          {sessionFiles.map((file) => (
            <div key={file.filename} className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs border backdrop-blur-md transition-all ${file.status === "Pending" ? "bg-amber-500/10 text-amber-300 border-amber-500/20 animate-pulse" : "bg-[var(--accent-blue-dim)] text-[var(--accent-blue)] border-[var(--accent-blue-dim)]"}`}>
              <span>{file.filename.endsWith(".pdf") ? "📕" : file.filename.endsWith(".csv") ? "📊" : "📄"}</span>
              <span className="max-w-[150px] truncate font-medium" title={file.filename}>{file.filename}</span>
              {file.status === "Pending" ? <span className="text-2xs text-amber-400 animate-spin">⚙️</span> : <span className="text-2xs font-bold font-mono">({file.chunks_count})</span>}
              <button type="button" onClick={() => onRemoveFile(file.filename)} className="hover:text-red-400 text-[var(--text-secondary)] transition-colors ml-1 p-0.5 rounded-full hover:bg-[var(--bg-hover)]" title="Remove attachment"><X size={12} /></button>
            </div>
          ))}
          {uploadingFile && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs bg-purple-500/10 text-purple-300 border border-purple-500/20 animate-pulse">
              <span className="animate-spin text-purple-400">⚙️</span>
              <span>Uploading file...</span>
            </div>
          )}
        </div>
      )}

      <div className="max-w-4xl mx-auto relative">
        {slashOpen && filteredCommands.length > 0 && (
          <div ref={slashRef} className="absolute bottom-full left-0 right-0 mb-2 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl shadow-xl overflow-hidden z-50">
            <div className="px-3 py-2 text-2xs font-bold uppercase tracking-wider text-[var(--text-tertiary)] font-mono border-b border-[var(--border-default)] flex items-center gap-1.5">
              <Slash size={10} />
              Commands
            </div>
            {filteredCommands.map((cmd, i) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={cmd.id}
                  type="button"
                  onMouseDown={(e) => { e.preventDefault(); cmd.action(input, setInput); setSlashOpen(false); }}
                  onMouseEnter={() => setSlashIndex(i)}
                  className={`flex items-center gap-3 w-full px-3 py-2.5 text-left transition-colors cursor-pointer ${i === slashIndex ? "bg-[var(--bg-hover)]" : ""}`}
                >
                  <Icon size={14} className="text-[var(--accent-blue)] shrink-0" />
                  <div className="flex flex-col min-w-0">
                    <span className="text-sm text-primary font-medium">{cmd.label}</span>
                    <span className="text-2xs text-[var(--text-tertiary)]">{cmd.description}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
        <form onSubmit={onSend} className="relative flex items-center group">
          <input ref={inputRef} type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} disabled={isStreaming} placeholder="Query the engine... (type / for commands)" className="w-full bg-[var(--bg-surface)]/60 text-primary border border-[var(--border-default)] rounded-full pl-4 md:pl-6 pr-24 md:pr-28 py-3 md:py-4 focus:outline-none focus:border-[var(--accent-blue)]/50 focus:bg-[var(--bg-hover)] transition-all disabled:opacity-50 backdrop-blur-xl shadow-lg text-sm placeholder:text-[var(--text-tertiary)]" />
          <div className="absolute right-2 md:right-3 flex items-center gap-1 md:gap-1.5">
            <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isStreaming || uploadingFile} className="p-2 md:p-2.5 text-primary hover:text-primary bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] rounded-full transition-all disabled:opacity-30 active:scale-95 flex items-center justify-center cursor-pointer" title="Attach document to this thread">
              <Paperclip size={18} />
            </button>
            {isStreaming ? (
              <button type="button" onClick={onStopThinking} className="p-2.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 rounded-full transition-all cursor-pointer shadow-md active:scale-95 flex items-center justify-center" title="Stop Thinking">
                <X size={18} />
              </button>
            ) : (
              <button type="submit" disabled={!input.trim()} className="p-2.5 bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] text-primary rounded-full transition-all disabled:opacity-0 active:scale-95 flex items-center justify-center cursor-pointer">
                <Send size={18} />
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
