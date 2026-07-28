import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Edit2, Copy, Download, Save, X } from "lucide-react";
import { toast } from "sonner";

interface CanvasProps {
  content: string;
  title: string;
  type: string;
  onSave?: (content: string) => void;
  onClose: () => void;
}

export default function Canvas({ content, title, type, onSave, onClose }: CanvasProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(content);

  // Sync state if external content changes when not editing
  useEffect(() => {
    if (!isEditing) {
      setEditContent(content);
    }
  }, [content, isEditing]);

  const handleCopy = () => {
    navigator.clipboard.writeText(isEditing ? editContent : content);
    toast.success("Copied to clipboard");
  };

  const handleDownload = () => {
    const blob = new Blob([isEditing ? editContent : content], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", title || "document.md");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSave = () => {
    if (onSave) {
      onSave(editContent);
      toast.success("Document saved successfully");
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditContent(content);
    setIsEditing(false);
  };

  return (
    <div className="flex-1 bg-white dark:bg-[#191919] h-full flex flex-col border-l border-[var(--border-default)]">
      {/* Header and Toolbar */}
      <header className="h-16 shrink-0 border-b border-[var(--border-default)] flex items-center justify-between px-4 md:px-6 bg-white dark:bg-[#191919]">
        <div className="flex items-center gap-3 overflow-hidden">
          <span className="text-sm font-semibold text-[var(--text-primary)] truncate">{title}</span>
          <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium shrink-0">
            {type}
          </span>
        </div>
        <div className="flex items-center gap-1.5 md:gap-3 shrink-0">
          {!isEditing ? (
            <button onClick={() => setIsEditing(true)} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:text-white hover:bg-[var(--bg-hover)] rounded-md transition-colors">
              <Edit2 size={14} />
              <span className="hidden md:inline">Edit</span>
            </button>
          ) : (
            <>
              <button onClick={handleCancel} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:text-white hover:bg-[var(--bg-hover)] rounded-md transition-colors">
                <X size={14} />
                <span className="hidden md:inline">Cancel</span>
              </button>
              <button onClick={handleSave} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors shadow-sm">
                <Save size={14} />
                <span className="hidden md:inline">Save</span>
              </button>
            </>
          )}

          <div className="w-px h-6 bg-[var(--border-default)] mx-1" />

          <button onClick={handleCopy} title="Copy" className="p-1.5 text-[var(--text-secondary)] hover:text-white hover:bg-[var(--bg-hover)] rounded-md transition-colors">
            <Copy size={16} />
          </button>
          <button onClick={handleDownload} title="Download" className="p-1.5 text-[var(--text-secondary)] hover:text-white hover:bg-[var(--bg-hover)] rounded-md transition-colors">
            <Download size={16} />
          </button>
          <button onClick={onClose} title="Close Workspace" className="ml-2 p-1.5 text-[var(--text-tertiary)] hover:text-red-400 hover:bg-red-400/10 rounded-md transition-colors">
            <X size={18} />
          </button>
        </div>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 lg:p-12 relative">
        <div className="max-w-4xl mx-auto w-full h-full flex flex-col">
          {isEditing ? (
            <textarea
              className="flex-1 w-full h-full bg-transparent text-[var(--text-primary)] resize-none outline-none font-mono text-sm leading-relaxed p-4 border border-[var(--border-default)] rounded-xl focus:border-blue-500 transition-colors"
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              placeholder="Start typing..."
              autoFocus
            />
          ) : (
            <div className="prose dark:prose-invert prose-blue w-full max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content || "No content yet..."}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
