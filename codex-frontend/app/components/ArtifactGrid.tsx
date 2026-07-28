import React, { useEffect, useState } from "react";
import { FileText, Layout, Lightbulb, Clock } from "lucide-react";
import { API_BASE } from "../lib/constants";

interface Artifact {
  path: string;
  artifact_type: string;
  updated_at: number;
  snippet: string;
}

interface ArtifactGridProps {
  projectId: string;
  authFetch: (url: string, options?: RequestInit) => Promise<Response>;
  onSelectArtifact: (path: string) => void;
}

export default function ArtifactGrid({ projectId, authFetch, onSelectArtifact }: ArtifactGridProps) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    if (!projectId) return;

    setLoading(true);
    setError(null);
    authFetch(`${API_BASE}/projects/${projectId}/artifacts`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch artifacts");
        return res.json();
      })
      .then(data => {
        if (isMounted) {
          setArtifacts(data.artifacts || []);
          setLoading(false);
        }
      })
      .catch(err => {
        if (isMounted) {
          console.error(err);
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [projectId, authFetch]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center h-full">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 p-8 text-red-500">
        Error loading workspace: {error}
      </div>
    );
  }

  if (artifacts.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full text-[var(--text-tertiary)]">
        <Layout className="w-12 h-12 mb-4 opacity-50" />
        <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">Empty Workspace</h3>
        <p className="max-w-md text-center text-sm">
          No artifacts found in this project. Ask the agent to analyze, summarize, or plan to see documents appear here.
        </p>
      </div>
    );
  }

  const getIcon = (type: string) => {
    if (type === "plan") return <Layout className="w-4 h-4" />;
    if (type === "analysis" || type === "summary") return <Lightbulb className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  return (
    <div className="flex-1 bg-white dark:bg-[#191919] h-full flex flex-col border-l border-[var(--border-default)]">
      <header className="h-16 shrink-0 border-b border-[var(--border-default)] flex items-center px-6 bg-white dark:bg-[#191919]">
        <h2 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Project Workspace</h2>
      </header>
      <div className="flex-1 overflow-y-auto p-8">
        <div className="columns-1 md:columns-2 lg:columns-3 gap-6 space-y-6">
          {artifacts.map((a) => (
            <div 
              key={a.path}
              onClick={() => onSelectArtifact(a.path)}
              className="break-inside-avoid cursor-pointer group bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-default)] hover:border-blue-500/50 rounded-xl p-5 transition-all shadow-sm hover:shadow-md"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2 text-blue-500 dark:text-blue-400">
                  {getIcon(a.artifact_type)}
                  <span className="text-xs font-semibold uppercase tracking-wider">{a.artifact_type}</span>
                </div>
              </div>
              <h3 className="text-[var(--text-primary)] font-medium mb-2 leading-snug">{a.path}</h3>
              <p className="text-[var(--text-secondary)] text-sm mb-4 line-clamp-4 leading-relaxed font-mono break-all whitespace-pre-wrap">
                {a.snippet}...
              </p>
              <div className="flex items-center gap-1.5 text-xs text-[var(--text-tertiary)]">
                <Clock className="w-3.5 h-3.5" />
                <span>{new Date(a.updated_at * 1000).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
