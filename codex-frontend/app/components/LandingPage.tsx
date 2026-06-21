"use client";

import { Sparkles, Search, Shield, Brain, FileText } from "lucide-react";
import AuthForm from "./AuthForm";

interface LandingPageProps {
  authMode: "login" | "register";
  setAuthMode: (mode: "login" | "register") => void;
  authEmail: string;
  setAuthEmail: (v: string) => void;
  authRegUsername: string;
  setAuthRegUsername: (v: string) => void;
  authPassword: string;
  setAuthPassword: (v: string) => void;
  authError: string;
  setAuthError: (v: string) => void;
  authLoading: boolean;
  handleAuth: (e: React.FormEvent) => Promise<void>;
}

export default function LandingPage(props: LandingPageProps) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-y-auto select-none p-4 lg:p-8">

      <div className="relative z-10 w-full max-w-5xl bg-[var(--bg-elevated)]/60 backdrop-blur-xl border border-[var(--border-default)] rounded-3xl shadow-xl overflow-hidden grid grid-cols-1 lg:grid-cols-12 gap-0">

        <div className="lg:col-span-7 p-8 lg:p-12 border-b lg:border-b-0 lg:border-r border-[var(--border-default)] flex flex-col justify-between space-y-8">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--accent-blue-dim)] border border-[var(--accent-blue-dim)] text-[var(--accent-blue)] text-xs font-semibold uppercase tracking-wider">
              <Sparkles size={12} className="animate-pulse" />
              Self-Hosted Document Intelligence
            </div>
            <div>
              <h1 className="text-4xl lg:text-5xl font-extrabold bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent tracking-tight">CodexEngine</h1>
              <p className="text-sm font-medium text-[var(--accent-blue)] mt-1 uppercase tracking-widest">Research Engine</p>
            </div>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed max-w-xl">
              Upload documents, ask questions, get cited answers backed by your own knowledge base.
              Your data stays on your infrastructure.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              {[
                { icon: Search, color: "#3b82f6", title: "Hybrid Search", desc: "Vector + BM25 search across your documents with source citations." },
                { icon: Shield, color: "#10b981", title: "Self-Hosted", desc: "Your data stays on your infrastructure. No third-party document access." },
                { icon: Brain, color: "#8b5cf6", title: "Multi-Provider LLM", desc: "Works with Groq, OpenAI, Together, and Gemini — you choose." },
                { icon: FileText, color: "#f59e0b", title: "Flexible Agent Loop", desc: "The LLM decides which tools to call — search, research, or answer directly." },
              ].map((feat, i) => (
                <div key={i} className="space-y-1.5 p-4 rounded-xl bg-[var(--bg-hover)] border border-[var(--border-default)] hover:border-[var(--border-hover)] transition-all duration-300 group">
                  <div className="flex items-center gap-2 text-[var(--text-primary)] font-semibold text-sm">
                    <feat.icon size={16} style={{ color: feat.color }} className="group-hover:scale-110 transition-transform" />
                    <span>{feat.title}</span>
                  </div>
                  <p className="text-xs text-[var(--text-tertiary)] leading-relaxed">{feat.desc}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-[var(--accent-blue-dim)] border border-[var(--accent-blue-dim)] text-xs text-[var(--text-secondary)] leading-relaxed flex items-start gap-3">
            <span className="text-base leading-none">💡</span>
            <div>
              <span className="text-[var(--text-primary)] font-semibold">Recruiter Quick Access:</span> Register any custom username and password to log in. No invite code required.
            </div>
          </div>
        </div>

        <AuthForm {...props} />
      </div>
    </div>
  );
}
