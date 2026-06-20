"use client";

import { Search, X } from "lucide-react";

interface SearchChatProps {
  query: string;
  onChange: (q: string) => void;
}

export default function SearchChat({ query, onChange }: SearchChatProps) {
  return (
    <div className="relative">
      <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] pointer-events-none" />
      <input
        type="text"
        value={query}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search chats..."
        className="w-full bg-[var(--bg-elevated)] text-primary text-xs pl-8 pr-8 py-2 rounded-lg border border-transparent focus:border-[var(--accent-blue)]/50 focus:outline-none transition-colors placeholder:text-[var(--text-tertiary)]"
      />
      {query && (
        <button
          onClick={() => onChange("")}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded text-[var(--text-tertiary)] hover:text-primary transition-colors cursor-pointer"
        >
          <X size={12} />
        </button>
      )}
    </div>
  );
}
