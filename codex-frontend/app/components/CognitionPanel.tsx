"use client";

interface CognitionPanelProps {
  intent?: string;
  evaluation?: {
    relevant?: boolean;
    sufficient?: boolean;
    grounded?: boolean;
    confidence?: number;
    retry_needed?: boolean;
  };
}

export default function CognitionPanel({ intent, evaluation }: CognitionPanelProps) {
  const mode = intent === "retrieval_required"
    ? (evaluation?.grounded ? "Grounded RAG" : "Fallback RAG")
    : intent === "direct_parametric"
    ? "Parametric Engine"
    : "Casual Interaction";

  return (
    <details className="group border border-[var(--border-default)] bg-[var(--bg-hover)] rounded-xl mb-4 overflow-hidden max-w-lg">
      <summary className="flex items-center justify-between px-4 py-2 text-xs font-mono cursor-pointer select-none hover:bg-[var(--bg-hover)]/80 transition-colors">
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${
            intent === "retrieval_required"
              ? (evaluation?.grounded ? "bg-emerald-500 animate-pulse" : "bg-amber-500 animate-pulse")
              : "bg-blue-500"
          }`} />
          <span className="font-semibold text-[var(--text-secondary)]">Cognition Panel: {mode}</span>
        </div>
        <span className="text-[var(--text-tertiary)] group-open:rotate-180 transition-transform">▼</span>
      </summary>
      <div className="px-4 py-3 border-t border-[var(--border-default)] bg-[var(--bg-surface)]/80 text-xs font-mono text-[var(--text-secondary)] space-y-2.5">
        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
          {[
            { label: "Intent:", value: intent || "retrieval_required", color: "text-blue-400" },
            { label: "Confidence:", value: evaluation?.confidence !== undefined ? `${(evaluation.confidence * 100).toFixed(0)}%` : "N/A", color: "text-blue-400" },
            { label: "Relevant:", value: evaluation?.relevant ? "TRUE" : "FALSE", color: evaluation?.relevant ? "text-emerald-400" : "text-amber-400" },
            { label: "Sufficient:", value: evaluation?.sufficient ? "TRUE" : "FALSE", color: evaluation?.sufficient ? "text-emerald-400" : "text-amber-400" },
            { label: "Grounded:", value: evaluation?.grounded ? "TRUE" : "FALSE", color: evaluation?.grounded ? "text-emerald-400" : "text-amber-400" },
            { label: "Retry needed:", value: evaluation?.retry_needed ? "TRUE" : "FALSE", color: evaluation?.retry_needed ? "text-red-400" : "text-[var(--text-tertiary)]" },
          ].map((item, i) => (
            <div key={i} className="flex justify-between border-b border-[var(--border-default)] pb-1">
              <span className="text-[var(--text-tertiary)]">{item.label}</span>
              <span className={`font-semibold ${item.color}`}>{item.value}</span>
            </div>
          ))}
        </div>
        {intent === "direct_parametric" && (
          <div className="text-2xs text-amber-400/80 bg-amber-400/5 border border-amber-400/10 p-2 rounded-lg">
            ⚠️ Context database bypassed. Relying on pre-trained parametric knowledge.
          </div>
        )}
      </div>
    </details>
  );
}
