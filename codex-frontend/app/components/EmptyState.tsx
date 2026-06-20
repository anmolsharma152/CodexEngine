"use client";

import { BookOpen } from "lucide-react";

interface EmptyStateProps {
  threadId: string | null;
}

export default function EmptyState({ threadId }: EmptyStateProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      <div className="flex flex-col items-center gap-4 mb-6">
        <div className="h-16 w-16 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-default)] flex items-center justify-center shadow-lg">
          <BookOpen size={28} className="text-[var(--accent-blue)]" />
        </div>
        <h1 className="text-2xl font-bold text-primary tracking-tight">Codex Engine</h1>
        <p className="text-sm text-[var(--text-tertiary)] font-medium">Untangle your documents. Amplify your knowledge.</p>
      </div>

      {!threadId && (
        <div className="mt-8 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm font-medium">
          <span className="animate-pulse">⬅️</span>
          <span className="font-medium">Create a new thread in the sidebar to begin your session</span>
        </div>
      )}
    </div>
  );
}
