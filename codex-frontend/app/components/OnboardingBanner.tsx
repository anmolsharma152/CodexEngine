"use client";

import { Upload, MessageSquare, Search, ArrowRight } from "lucide-react";
import { useState } from "react";

interface OnboardingBannerProps {
  onDismiss: () => void;
}

const steps = [
  {
    icon: Upload,
    title: "Upload Documents",
    desc: "Click the paperclip icon or open Manage Documents to upload PDFs, CSVs, or Markdown files. Files attach to your current thread.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
  },
  {
    icon: MessageSquare,
    title: "Ask Questions",
    desc: "Type your question in the input bar. The engine searches your documents using vector + keyword search, then generates a grounded answer.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
  },
  {
    icon: Search,
    title: "Verify with Citations",
    desc: "Every answer shows citations — click [p. X] or [r. X] badges to inspect the exact source chunk the engine used.",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
  },
];

export default function OnboardingBanner({ onDismiss }: OnboardingBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="w-full max-w-2xl mx-auto mb-6 animate-fade-in">
      <div className="bg-gradient-to-br from-blue-500/[0.08] to-purple-500/[0.08] border border-[var(--border-default)] rounded-2xl p-6 backdrop-blur-sm">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-primary tracking-tight">Welcome to CodexEngine</h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">Here&apos;s how to get started in three steps:</p>
          </div>
        </div>

        <div className="space-y-3">
          {steps.map((step, i) => (
            <div key={i} className={`flex items-start gap-3 p-3 rounded-xl ${step.bg} ${step.border} border`}>
              <div className={`h-8 w-8 rounded-lg ${step.bg} ${step.border} border flex items-center justify-center shrink-0 mt-0.5`}>
                <step.icon size={16} className={step.color} />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="flex items-center justify-center h-5 w-5 rounded-full bg-[var(--bg-hover)] text-2xs font-bold text-[var(--text-tertiary)] shrink-0">{i + 1}</span>
                  <span className="text-sm font-semibold text-primary">{step.title}</span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={() => { setDismissed(true); onDismiss(); }}
          className="mt-4 w-full py-2.5 rounded-xl bg-gradient-to-r from-[var(--accent-blue)] to-[var(--accent-purple)] hover:opacity-90 text-white text-xs font-semibold transition-all shadow-lg shadow-[var(--accent-blue)]/15 cursor-pointer active:scale-[0.98] flex items-center justify-center gap-2"
        >
          <span>Got it — start exploring</span>
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}
