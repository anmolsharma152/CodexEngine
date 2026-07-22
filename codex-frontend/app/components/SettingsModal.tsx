"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Settings, X, Trash2, RefreshCw, Info, User, MessageSquare } from "lucide-react";

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
  username: string | null;
  displayName: string;
  systemPrompt: string;
  provider?: string;
  model?: string;
  onSaveDisplayName: (val: string) => void;
  onSaveSystemPrompt: (val: string) => void;
  onSaveProvider?: (val: string) => void;
  onSaveModel?: (val: string) => void;
}

export default function SettingsModal({
  open, onClose, username, displayName: savedDisplayName, systemPrompt: savedSystemPrompt,
  provider: savedProvider = "groq", model: savedModel = "qwen/qwen3.6-27b",
  onSaveDisplayName, onSaveSystemPrompt, onSaveProvider, onSaveModel,
}: SettingsModalProps) {
  const [editName, setEditName] = useState(savedDisplayName);
  const [editPrompt, setEditPrompt] = useState(savedSystemPrompt);
  const [editProvider, setEditProvider] = useState(savedProvider);
  const [editModel, setEditModel] = useState(savedModel);
  const [nameDirty, setNameDirty] = useState(false);
  const [promptDirty, setPromptDirty] = useState(false);
  const [providerDirty, setProviderDirty] = useState(false);

  if (!open) return null;

  const handleSaveName = () => {
    onSaveDisplayName(editName);
    setNameDirty(false);
  };

  const handleSavePrompt = () => {
    onSaveSystemPrompt(editPrompt);
    setPromptDirty(false);
  };

  const handleClose = () => {
    setEditName(savedDisplayName);
    setEditPrompt(savedSystemPrompt);
    setNameDirty(false);
    setPromptDirty(false);
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={handleClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="relative w-full max-w-lg max-h-[85vh] mx-4 bg-[#151b23] border border-[var(--border-hover)] rounded-2xl shadow-xl flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-default)] shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-lg bg-[var(--accent-blue-dim)] flex items-center justify-center">
                  <Settings size={16} className="text-[var(--accent-blue)]" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Settings</h3>
                  <p className="text-xs text-[var(--text-tertiary)]">Configure your workspace</p>
                </div>
              </div>
              <button onClick={handleClose} className="h-8 w-8 rounded-lg flex items-center justify-center text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-all cursor-pointer">
                <X size={18} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Profile */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <User size={14} className="text-[var(--accent-blue)]" />
                  <span className="text-2xs uppercase tracking-widest text-[var(--text-tertiary)] font-mono font-semibold">Profile</span>
                </div>
                <div className="bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[var(--text-tertiary)] font-mono">Account</span>
                    <span className="text-xs font-medium text-[var(--text-secondary)]">{username || "—"}</span>
                  </div>
                  <div className="border-t border-[var(--border-default)]" />
                  <div>
                    <span className="text-xs text-[var(--text-tertiary)] font-mono block mb-1.5">Display Name</span>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => { setEditName(e.target.value); setNameDirty(true); }}
                        placeholder="Your display name"
                        className="flex-1 bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] outline-none focus:border-[var(--accent-blue)]/40 transition-colors placeholder:text-[var(--text-disabled)]"
                      />
                      <button
                        type="button"
                        onClick={handleSaveName}
                        disabled={!nameDirty}
                        className="px-4 py-2 rounded-lg text-xs font-semibold bg-[var(--accent-blue-dim)] text-[var(--accent-blue)] border border-[var(--accent-blue-dim)] transition-all disabled:opacity-30 disabled:pointer-events-none cursor-pointer active:scale-95 hover:bg-[var(--accent-blue)]/20 shrink-0"
                      >
                        {nameDirty ? "Save" : "Saved"}
                      </button>
                    </div>
                  </div>
                </div>
              </section>

              {/* Custom Instructions */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <MessageSquare size={14} className="text-[var(--accent-purple)]" />
                  <span className="text-2xs uppercase tracking-widest text-[var(--text-tertiary)] font-mono font-semibold">Custom Instructions</span>
                </div>
                <div className="bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4 space-y-3">
                  <p className="text-xs text-[var(--text-tertiary)] leading-relaxed">
                    Prepend these instructions to every conversation. Use them to set tone, format, or domain context.
                  </p>
                  <textarea
                    value={editPrompt}
                    onChange={(e) => { setEditPrompt(e.target.value); setPromptDirty(true); }}
                    placeholder="e.g. Always respond in plain English. Use bullet points for lists. Cite sources when possible."
                    rows={6}
                    className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-xl px-3 py-2.5 text-sm text-[var(--text-primary)] outline-none focus:border-[var(--accent-purple)]/40 transition-colors resize-y min-h-[120px] placeholder:text-[var(--text-disabled)] leading-relaxed"
                  />
                  <div className="flex items-center justify-between">
                    <span className="text-2xs text-[var(--text-disabled)] font-mono">
                      {editPrompt.length > 0 ? `${editPrompt.length} characters` : "No custom instructions set"}
                    </span>
                    <button
                      type="button"
                      onClick={handleSavePrompt}
                      disabled={!promptDirty}
                      className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-[var(--accent-purple-dim)] text-[var(--accent-purple)] border border-[var(--accent-purple-dim)] transition-all disabled:opacity-30 disabled:pointer-events-none cursor-pointer active:scale-95 hover:bg-[var(--accent-purple)]/20"
                    >
                      {promptDirty ? "Save" : "Saved"}
                    </button>
                  </div>
                </div>
              </section>

              {/* LLM Engine & Provider */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <RefreshCw size={14} className="text-[var(--accent-emerald)]" />
                  <span className="text-2xs uppercase tracking-widest text-[var(--text-tertiary)] font-mono font-semibold">LLM Engine & Provider</span>
                </div>
                <div className="bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <span className="text-xs text-[var(--text-tertiary)] font-mono block mb-1.5">Provider</span>
                      <select
                        value={editProvider}
                        onChange={(e) => {
                          const p = e.target.value;
                          setEditProvider(p);
                          setProviderDirty(true);
                          if (p === "groq") setEditModel("qwen/qwen3.6-27b");
                          else if (p === "openai") setEditModel("gpt-4o-mini");
                          else if (p === "gemini") setEditModel("gemini-2.0-flash");
                          else if (p === "anthropic") setEditModel("anthropic/claude-3.5-sonnet");
                          else if (p === "openrouter") setEditModel("openrouter/free");
                        }}
                        className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--accent-emerald)]/40 transition-colors cursor-pointer font-mono"
                      >
                        <option value="groq">Groq Cloud (Qwen 27B / Llama 70B)</option>
                        <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                        <option value="gemini">Google Gemini (Gemini 2.0 Flash)</option>
                        <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
                        <option value="openrouter">OpenRouter Free (Auto-Router)</option>
                      </select>
                    </div>
                    <div>
                      <span className="text-xs text-[var(--text-tertiary)] font-mono block mb-1.5">Model</span>
                      <input
                        type="text"
                        value={editModel}
                        onChange={(e) => { setEditModel(e.target.value); setProviderDirty(true); }}
                        className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--accent-emerald)]/40 transition-colors font-mono"
                      />
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-2xs text-[var(--text-tertiary)]">
                      {editProvider === "openrouter" ? "🔒 Guaranteed 100% Free Model" : "⚡ Zero billing risk"}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        onSaveProvider?.(editProvider);
                        onSaveModel?.(editModel);
                        setProviderDirty(false);
                      }}
                      disabled={!providerDirty}
                      className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-[var(--accent-emerald-dim)] text-[var(--accent-emerald)] border border-[var(--accent-emerald-dim)] transition-all disabled:opacity-30 disabled:pointer-events-none cursor-pointer active:scale-95 hover:bg-[var(--accent-emerald)]/20"
                    >
                      {providerDirty ? "Save Model" : "Saved"}
                    </button>
                  </div>
                </div>
              </section>

              {/* Configuration */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <Info size={14} className="text-[var(--accent-blue)]" />
                  <span className="text-2xs uppercase tracking-widest text-[var(--text-tertiary)] font-mono font-semibold">Configuration</span>
                </div>
                <div className="bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4 space-y-2.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--text-tertiary)]">Backend URL</span>
                    <span className="text-[var(--accent-blue)] font-mono font-medium">
                      {typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000") : "..."}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--text-tertiary)]">Supabase</span>
                    <span className="text-[var(--text-secondary)] font-mono font-medium">
                      {typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_SUPABASE_URL ? "Configured" : "Not configured") : "..."}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--text-tertiary)]">Version</span>
                    <span className="text-[var(--text-primary)] font-mono font-semibold">v4.0.0</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--text-tertiary)]">Architecture</span>
                    <span className="text-[var(--text-emerald)] font-mono font-semibold">Agentic (v5)</span>
                  </div>
                </div>
              </section>

              {/* Actions */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <RefreshCw size={14} className="text-[var(--accent-amber)]" />
                  <span className="text-2xs uppercase tracking-widest text-[var(--text-tertiary)] font-mono font-semibold">Actions</span>
                </div>
                <div className="bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4 space-y-3">
                  <p className="text-xs text-[var(--text-tertiary)] leading-relaxed">
                    These actions affect your local session. Backend data is unaffected.
                  </p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => { localStorage.removeItem("codex_onboarding_seen"); window.location.reload(); }}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-[var(--accent-amber-dim)] hover:bg-[var(--accent-amber)]/20 text-[var(--accent-amber)] border border-[var(--accent-amber-dim)] transition-all cursor-pointer active:scale-95"
                    >
                      <RefreshCw size={12} />
                      Reset Onboarding
                    </button>
                    <button
                      type="button"
                      onClick={() => { localStorage.clear(); window.location.reload(); }}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-[var(--accent-red-dim)] hover:bg-[var(--accent-red)]/20 text-[var(--accent-red)] border border-[var(--accent-red-dim)] transition-all cursor-pointer active:scale-95"
                    >
                      <Trash2 size={12} />
                      Clear Local Data
                    </button>
                  </div>
                </div>
              </section>
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-[var(--border-default)] bg-[var(--bg-inset)] shrink-0">
              <p className="text-2xs font-mono text-center text-[var(--text-disabled)]">
                CodexEngine v4.0.0 — agentic branch
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
