"use client";

import { useState, useEffect, useCallback } from "react";
import { supabase, API_BASE } from "../lib/constants";

export function useAuth() {
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authRegUsername, setAuthRegUsername] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  useEffect(() => {
    setToken(localStorage.getItem("codex_auth_token"));
    setUsername(localStorage.getItem("codex_auth_user"));
  }, []);

  const logout = useCallback(async () => {
    await supabase.auth.signOut();
    setToken(null);
    setUsername(null);
    localStorage.removeItem("codex_auth_token");
    localStorage.removeItem("codex_auth_user");
    localStorage.removeItem("codex_threads");
  }, []);

  const authFetch = useCallback(async (url: string, options: RequestInit = {}) => {
    const headers = new Headers(options.headers || {});
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    let response: Response;
    try {
      response = await fetch(url, { ...options, headers });
    } catch {
      return new Response(JSON.stringify({ message: "Network error" }), { status: 502 });
    }
    if (response.status === 401) {
      logout();
      setAuthError("Session expired. Please log in again.");
      return new Response(JSON.stringify({ message: "Unauthorized" }), { status: 401 });
    }
    return response;
  }, [token, logout]);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    const email = authEmail.trim();
    const password = authPassword;
    if (!email || !password) {
      setAuthError("Email and password are required.");
      return;
    }
    setAuthLoading(true);
    try {
      if (authMode === "login") {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error || !data.session) throw new Error(error?.message || "Login failed");
        const newToken = data.session.access_token;
        const meRes = await fetch(`${API_BASE}/user/me`, {
          headers: { Authorization: `Bearer ${newToken}` },
        });
        const meData = await meRes.json();
        setToken(newToken);
        setUsername(meData.username || meData.email);
        localStorage.setItem("codex_auth_token", newToken);
        localStorage.setItem("codex_auth_user", meData.username || meData.email);
        setAuthEmail("");
        setAuthPassword("");
        setAuthRegUsername("");
      } else {
        const usernameVal = authRegUsername.trim() || email.split("@")[0];
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { username: usernameVal } },
        });
        if (error) throw new Error(error.message);
        setAuthMode("login");
        setAuthError("Registered successfully! Please log in.");
      }
    } catch (err: any) {
      setAuthError(err.message || "An error occurred during authentication.");
    } finally {
      setAuthLoading(false);
    }
  };

  return {
    token, setToken,
    username, setUsername,
    authMode, setAuthMode,
    authEmail, setAuthEmail,
    authRegUsername, setAuthRegUsername,
    authPassword, setAuthPassword,
    authError, setAuthError,
    authLoading,
    logout, authFetch, handleAuth,
  };
}
