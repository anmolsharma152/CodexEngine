"use client";

import { RefreshCw } from "lucide-react";
import type { QuickPrompt } from "../lib/types";

interface QuickPromptsProps {
  prompts: QuickPrompt[];
  onSelect: (text: string) => void;
  onShuffle: () => void;
}

export default function QuickPrompts({ prompts, onSelect, onShuffle }: QuickPromptsProps) {
  return (
    <div className="flex flex-col items-center gap-3 max-w-2xl w-full px-4 mt-6">
      <div className="flex items-center gap-2">
        <span className="text-sm text-[var(--text-tertiary)]">Try:</span>
        <button type="button" onClick={onShuffle} className="p-1 text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] transition-colors cursor-pointer" title="Shuffle Prompts">
          <RefreshCw size={14} />
        </button>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {prompts.map((card, i) => (
          <button key={i} type="button" onClick={() => onSelect(card.text)} className="px-4 py-2 text-sm text-primary bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-default)] hover:border-[var(--border-hover)] rounded-lg transition-all cursor-pointer active:scale-95 whitespace-nowrap">
            {card.title}
          </button>
        ))}
      </div>
    </div>
  );
}
