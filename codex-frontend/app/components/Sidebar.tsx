"use client";

import { Plus, FileUp, Settings, LogOut, BookOpen, Menu, ChevronsLeft, Pin, Trash } from "lucide-react";
import type { Thread } from "../lib/types";
import ThreadItem from "./ThreadItem";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
  threadId: string;
  setThreadId: (v: string) => void;
  setMessages: (msgs: any[]) => void;
  setStatus: (s: string) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
  threads: Thread[];
  pinnedThreads: Thread[];
  recentThreads: Thread[];
  editingThreadId: string | null;
  editTitle: string;
  setEditTitle: (v: string) => void;
  setEditingThreadId: (v: string | null) => void;
  username: string | null;
  displayName?: string;
  onSelectThread: (id: string) => Promise<any[]>;
  onTogglePin: (id: string) => void;
  onStartRename: (id: string, title: string) => void;
  onSaveRename: (id: string) => void;
  onDeleteThread: (id: string) => void;
  onClearAllThreads: () => void;
  onShowDocManager: () => void;
  onShowSettings: () => void;
  onLogout: () => void;
}

export default function Sidebar({
  sidebarOpen, setSidebarOpen,
  threadId, setThreadId, setMessages, setStatus, inputRef,
  threads, pinnedThreads, recentThreads,
  editingThreadId, editTitle, setEditTitle, setEditingThreadId,
  username, displayName,
  onSelectThread, onTogglePin, onStartRename, onSaveRename, onDeleteThread,
  onClearAllThreads, onShowDocManager, onShowSettings, onLogout,
}: SidebarProps) {
  const newChat = () => {
    setThreadId(crypto.randomUUID());
    setMessages([]);
    setStatus("System Standby");
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  return (
    <aside className={`relative z-10 ${sidebarOpen ? "w-64" : "w-16"} transition-all duration-300 ease-in-out border-r border-[var(--border-default)] bg-[var(--bg-surface)] backdrop-blur-xl flex flex-col overflow-x-hidden`}>
      <div className={`h-16 flex items-center border-b border-[var(--border-default)] ${sidebarOpen ? "px-5 justify-between" : "px-0 justify-center"}`}>
        {sidebarOpen ? (
          <>
            <div className="flex items-center gap-2 overflow-hidden">
              <BookOpen size={16} className="text-[var(--accent-blue)] shrink-0" />
              <span className="text-sm font-semibold text-primary tracking-tight whitespace-nowrap">CodexEngine</span>
            </div>
            <button onClick={() => setSidebarOpen(false)} className="text-[var(--text-tertiary)] hover:text-primary transition-colors shrink-0"><ChevronsLeft size={18} /></button>
          </>
        ) : (
          <button onClick={() => setSidebarOpen(true)} className="text-[var(--text-tertiary)] hover:text-primary transition-colors"><Menu size={20} /></button>
        )}
      </div>

      <div className={`flex justify-center ${sidebarOpen ? "p-4" : "py-4 px-0"}`}>
        <button onClick={newChat} title="New Chat" className={`flex items-center justify-center bg-[var(--bg-elevated)] hover:bg-[var(--bg-hover)] text-primary transition-all text-sm font-medium ${sidebarOpen ? "w-full gap-2 px-4 py-2.5 rounded-lg" : "w-10 h-10 p-0 rounded-lg"}`}>
          <Plus size={16} className="shrink-0" />
          {sidebarOpen && <span className="whitespace-nowrap">New Chat</span>}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden space-y-4 pb-4 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-[var(--border-default)] hover:[&::-webkit-scrollbar-thumb]:bg-[var(--border-hover)] [&::-webkit-scrollbar-thumb]:rounded-full">
        {sidebarOpen && threads.length > 0 && (
          <div className="flex items-center justify-end px-6 mt-3 mb-1">
            <button onClick={onClearAllThreads} title="Clear all chat history" className="p-1 rounded text-[var(--text-tertiary)] hover:text-red-400 hover:bg-[var(--bg-hover)] transition-all cursor-pointer">
              <Trash size={12} />
            </button>
          </div>
        )}
        {threads.length === 0 ? (
          sidebarOpen && <div className="text-center py-8 text-xs text-[var(--text-tertiary)]">No chat history</div>
        ) : (
          <>
            {pinnedThreads.length > 0 && (
              <div>
                {sidebarOpen && <div className="text-xs text-[var(--text-tertiary)] mb-1.5 px-6 whitespace-nowrap mt-3 flex items-center gap-1.5"><Pin size={10} className="rotate-45 text-blue-400 fill-blue-400" /> Pinned</div>}
                {pinnedThreads.map((t) => (
                  <ThreadItem key={t.id} t={t} isActive={threadId === t.id} isEditing={editingThreadId === t.id} editTitle={editTitle} sidebarOpen={sidebarOpen} onSelect={onSelectThread} onTogglePin={onTogglePin} onStartRename={onStartRename} onSaveRename={onSaveRename} onDelete={onDeleteThread} setEditTitle={setEditTitle} setEditingThreadId={setEditingThreadId} />
                ))}
              </div>
            )}
            <div>
              {sidebarOpen && <div className="text-xs text-[var(--text-tertiary)] mb-1.5 px-6 whitespace-nowrap mt-3">Recent</div>}
              {recentThreads.map((t) => (
                <ThreadItem key={t.id} t={t} isActive={threadId === t.id} isEditing={editingThreadId === t.id} editTitle={editTitle} sidebarOpen={sidebarOpen} onSelect={onSelectThread} onTogglePin={onTogglePin} onStartRename={onStartRename} onSaveRename={onSaveRename} onDelete={onDeleteThread} setEditTitle={setEditTitle} setEditingThreadId={setEditingThreadId} />
              ))}
            </div>
          </>
        )}
      </div>

      <div className="border-t border-[var(--border-default)] space-y-2 flex flex-col items-center py-4">
        <div className={sidebarOpen ? "w-full px-4" : "w-full px-0"}>
            {sidebarOpen ? (
            <button onClick={onShowDocManager} className="flex items-center gap-3 py-2.5 text-sm text-primary hover:bg-[var(--bg-hover)] hover:text-primary rounded-lg w-full px-3 transition-colors bg-[var(--bg-elevated)]">
              <FileUp size={16} className="shrink-0" />
              <span className="whitespace-nowrap">Manage Documents</span>
            </button>
          ) : (
            <Tooltip>
              <TooltipTrigger onClick={onShowDocManager} className="flex items-center justify-center w-10 h-10 text-primary bg-[var(--bg-elevated)] hover:bg-[var(--bg-hover)] hover:text-primary rounded-lg mx-auto p-0 transition-colors cursor-pointer">
                <FileUp size={16} />
              </TooltipTrigger>
              <TooltipContent side="right">Manage Documents</TooltipContent>
            </Tooltip>
          )}
        </div>
        <div className={sidebarOpen ? "w-full px-4" : "w-full px-0"}>
            {sidebarOpen ? (
            <button onClick={onShowSettings} className="flex items-center gap-3 py-2.5 text-sm text-primary hover:bg-[var(--bg-hover)] hover:text-primary rounded-lg w-full px-3 transition-colors bg-[var(--bg-elevated)]">
              <Settings size={16} className="shrink-0" />
              <span className="whitespace-nowrap">Settings</span>
            </button>
          ) : (
            <Tooltip>
              <TooltipTrigger onClick={onShowSettings} className="flex items-center justify-center w-10 h-10 text-primary bg-[var(--bg-elevated)] hover:bg-[var(--bg-hover)] hover:text-primary rounded-lg mx-auto p-0 transition-colors cursor-pointer">
                <Settings size={16} />
              </TooltipTrigger>
              <TooltipContent side="right">Settings</TooltipContent>
            </Tooltip>
          )}
        </div>
        {username && (
          <div className={`mt-2 border-t border-[var(--border-default)] pt-3 ${sidebarOpen ? "w-full px-4" : "px-0"}`}>
            {sidebarOpen ? (
              <div className="flex items-center justify-between gap-2 w-full px-3 py-2.5 rounded-lg bg-[var(--bg-elevated)]">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[var(--accent-blue)] to-[var(--accent-emerald)] flex items-center justify-center text-white font-bold text-xs uppercase shrink-0">{(displayName || username).charAt(0)}</div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-sm font-semibold text-primary truncate max-w-[130px]" title={displayName || username}>{displayName || username}</span>
                  </div>
                </div>
                <button onClick={onLogout} className="p-2 rounded-lg text-[var(--text-tertiary)] hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer shrink-0" title="Log Out"><LogOut size={16} /></button>
              </div>
            ) : (
              <Tooltip>
                <TooltipTrigger onClick={onLogout} className="flex items-center justify-center w-10 h-10 rounded-lg text-[var(--text-tertiary)] bg-[var(--bg-elevated)] hover:text-red-400 hover:bg-red-500/10 transition-colors mx-auto cursor-pointer">
                  <LogOut size={16} />
                </TooltipTrigger>
                <TooltipContent side="right">Log Out</TooltipContent>
              </Tooltip>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
