"use client";

import { Sparkles } from "lucide-react";

interface AuthFormProps {
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

export default function AuthForm({
  authMode, setAuthMode,
  authEmail, setAuthEmail,
  authRegUsername, setAuthRegUsername,
  authPassword, setAuthPassword,
  authError, setAuthError,
  authLoading, handleAuth,
}: AuthFormProps) {
  return (
    <div className="lg:col-span-5 p-8 lg:p-12 flex flex-col justify-center">
      <div className="w-full max-w-sm mx-auto space-y-6">
        <div className="text-center lg:text-left space-y-1">
          <h2 className="text-xl font-bold text-[var(--text-primary)] tracking-tight">
            {authMode === "login" ? "Welcome Back" : "Create Account"}
          </h2>
          <p className="text-xs text-[var(--text-tertiary)]">
            {authMode === "login" ? "Sign in to access your secure knowledge workspace" : "Register a new account to isolate your RAG sessions"}
          </p>
        </div>

        <div className="flex w-full border-b border-[var(--border-default)] font-medium text-xs">
          <button onClick={() => { setAuthMode("login"); setAuthError(""); }} className={`flex-1 pb-3 text-center transition-colors cursor-pointer ${authMode === "login" ? "text-[var(--accent-blue)] border-b-2 border-[var(--accent-blue)] font-semibold" : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"}`}>Sign In</button>
          <button onClick={() => { setAuthMode("register"); setAuthError(""); }} className={`flex-1 pb-3 text-center transition-colors cursor-pointer ${authMode === "register" ? "text-[var(--accent-blue)] border-b-2 border-[var(--accent-blue)] font-semibold" : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"}`}>Register</button>
        </div>

        <form onSubmit={handleAuth} className="space-y-4">
          <div>
            <label className="block text-2xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider mb-1.5">Email</label>
            <input type="email" value={authEmail} onChange={(e) => setAuthEmail(e.target.value)} className="w-full px-4 py-2.5 rounded-xl bg-[var(--bg-hover)] border border-[var(--border-default)] focus:border-[var(--accent-blue)] text-[var(--text-primary)] outline-none transition-all text-xs font-medium" placeholder="e.g. you@example.com" required />
          </div>
          {authMode === "register" && (
            <div>
              <label className="block text-2xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider mb-1.5">Username</label>
              <input type="text" value={authRegUsername} onChange={(e) => setAuthRegUsername(e.target.value)} className="w-full px-4 py-2.5 rounded-xl bg-[var(--bg-hover)] border border-[var(--border-default)] focus:border-[var(--accent-blue)] text-[var(--text-primary)] outline-none transition-all text-xs font-medium" placeholder="e.g. recruiter_demo" />
            </div>
          )}
          <div>
            <label className="block text-2xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider mb-1.5">Password</label>
            <input type="password" value={authPassword} onChange={(e) => setAuthPassword(e.target.value)} className="w-full px-4 py-2.5 rounded-xl bg-[var(--bg-hover)] border border-[var(--border-default)] focus:border-[var(--accent-blue)] text-[var(--text-primary)] outline-none transition-all text-xs font-medium" placeholder="••••••••" required />
          </div>
          {authError && (
            <div className={`text-xs p-3 rounded-lg border leading-relaxed ${authError.includes("successfully") ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" : "bg-red-500/10 border-red-500/20 text-red-400"}`}>
              {authError}
            </div>
          )}
          <button type="submit" disabled={authLoading} className="w-full py-2.5 rounded-xl bg-gradient-to-r from-[var(--accent-blue)] to-[var(--accent-emerald)] text-white text-xs font-semibold transition-all shadow-lg shadow-[var(--accent-blue)]/15 cursor-pointer active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none">
            {authLoading ? "Verifying..." : authMode === "login" ? "Sign In" : "Register"}
          </button>
        </form>
      </div>
    </div>
  );
}
