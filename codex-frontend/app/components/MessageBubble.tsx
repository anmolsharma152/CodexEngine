"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check, Pencil, X, CheckSquare } from "lucide-react";
import type { Message } from "../lib/types";
import CognitionPanel from "./CognitionPanel";

interface MessageBubbleProps {
  msg: Message;
  idx: number;
  isStreaming: boolean;
  copiedIndex: number | null;
  onCopy: (text: string, idx: number) => void;
  onCitationClick: (href: string, context: string) => void;
  onStopThinking: () => void;
  onEdit?: (idx: number, newContent: string) => void;
}

export default function MessageBubble({ msg, idx, isStreaming, copiedIndex, onCopy, onCitationClick, onStopThinking, onEdit }: MessageBubbleProps) {
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(msg.content);

  const handleSave = () => {
    if (editText.trim() && onEdit) {
      onEdit(idx, editText.trim());
    }
    setEditing(false);
  };

  const handleCancel = () => {
    setEditText(msg.content);
    setEditing(false);
  };

  return (
    <div className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
      <div className={`rounded-2xl p-4 md:p-6 transition-all backdrop-blur-md text-sm md:text-base ${
        msg.role === "user"
          ? "bg-[var(--accent-blue-dim)] border border-[var(--accent-blue-dim)] text-primary max-w-[85%] md:max-w-[75%]"
          : "bg-[var(--bg-elevated)]/60 border border-[var(--border-default)] text-[var(--text-secondary)] max-w-full md:max-w-[90%]"
      }`}>
        {msg.role === "assistant" ? (
          msg.content === "" && isStreaming ? (
            <div className="space-y-4 py-2 w-full min-w-[320px]">
              <div className="h-3 rounded-md bg-gradient-to-r from-[var(--accent-blue)] via-[var(--accent-purple)] to-[var(--accent-emerald)] animate-pulse w-1/3"></div>
              <div className="h-3 rounded-md bg-gradient-to-r from-[var(--accent-blue)] via-[var(--accent-purple)] to-[var(--accent-emerald)] animate-pulse w-5/6"></div>
              <div className="h-3 rounded-md bg-gradient-to-r from-[var(--accent-blue)] via-[var(--accent-purple)] to-[var(--accent-emerald)] animate-pulse w-2/3"></div>
              <div className="flex items-center gap-3 mt-4 pt-2 border-t border-[var(--border-default)]">
                <span className="text-xs text-[var(--text-tertiary)] animate-pulse flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent-blue)] animate-ping" />
                  Generating...
                </span>
                <button type="button" onClick={onStopThinking} className="px-2.5 py-1 text-2xs font-bold bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 hover:border-red-500/40 rounded transition-all cursor-pointer shadow-sm active:scale-95">
                  Stop Thinking
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col">
              {(msg.intent || msg.evaluation) && (
                <CognitionPanel intent={msg.intent} evaluation={msg.evaluation} />
              )}
              <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-[var(--bg-surface)]/80 prose-pre:border prose-pre:border-[var(--border-default)] prose-pre:rounded-xl prose-code:text-[var(--accent-blue)]">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a(props) {
                      const { href, children, ...rest } = props;
                      if (href && href.startsWith("citation://")) {
                        try {
                          const cleanHref = href.replace("citation://", "http://temp-host/");
                          const url = new URL(cleanHref);
                          const source = decodeURIComponent(url.pathname.substring(1));
                          const page = url.searchParams.get("page") || "";
                          const row = url.searchParams.get("row") || "";
                          const label = page ? `p. ${page}` : (row ? `r. ${row}` : "doc");
                          return (
                            <button type="button" onClick={() => onCitationClick(href, msg.context || "")} title={`${source} ${page ? `p. ${page}` : row ? `r. ${row}` : "doc"}`} className="inline-flex items-center justify-center px-1 py-0.5 mx-0.5 rounded text-2xs font-mono font-bold bg-[var(--accent-blue-dim)] hover:bg-[var(--accent-blue-dim)]/80 text-[var(--accent-blue)] border border-[var(--accent-blue-dim)] transition-all cursor-pointer align-super">
                              [{label}]
                            </button>
                          );
                        } catch (e) {
                          console.error("Error parsing citation link", e);
                        }
                      }
                      return <a href={href} target="_blank" rel="noopener noreferrer" className="text-[var(--accent-blue)] hover:underline" {...rest}>{children}</a>;
                    },
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
                {msg.content !== "" && (
                  <div className="flex justify-end mt-2 pt-2 border-t border-[var(--border-default)]">
                    <button type="button" onClick={() => onCopy(msg.content, idx)} className="flex items-center gap-1 px-2 py-1 text-2xs font-mono text-[var(--text-tertiary)] hover:text-primary rounded hover:bg-[var(--bg-hover)] transition-colors cursor-pointer" title="Copy response to clipboard">
                      {copiedIndex === idx ? (
                        <><Check size={10} className="text-emerald-400" /><span className="text-emerald-400 font-bold">Copied</span></>
                      ) : (
                        <><Copy size={10} /><span>Copy</span></>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          )
        ) : editing ? (
          <div className="flex flex-col gap-2">
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && e.metaKey) handleSave(); if (e.key === "Escape") handleCancel(); }}
              className="w-full bg-[var(--bg-inset)] text-primary border border-[var(--accent-blue)]/50 rounded-xl px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-[var(--accent-blue)] resize-none min-h-[60px]"
              autoFocus
            />
            <div className="flex items-center gap-2 justify-end">
              <button type="button" onClick={handleCancel} className="flex items-center gap-1 px-2.5 py-1 text-xs text-[var(--text-secondary)] hover:text-primary hover:bg-[var(--bg-hover)] rounded-lg transition-colors cursor-pointer">
                <X size={12} />
                Cancel
              </button>
              <button type="button" onClick={handleSave} className="flex items-center gap-1 px-2.5 py-1 text-xs text-white bg-[var(--accent-blue)] hover:bg-[var(--accent-blue)]/80 rounded-lg transition-colors cursor-pointer">
                <CheckSquare size={12} />
                Save
              </button>
            </div>
          </div>
        ) : (
          <div className="group relative">
            <div className="whitespace-pre-wrap leading-relaxed pr-6">{msg.content}</div>
            <button
              type="button"
              onClick={() => { setEditing(true); setEditText(msg.content); }}
              className="absolute top-0 right-0 p-1 rounded text-[var(--text-tertiary)] hover:text-primary hover:bg-[var(--bg-hover)] transition-all opacity-0 group-hover:opacity-100 cursor-pointer"
              title="Edit message"
            >
              <Pencil size={12} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
