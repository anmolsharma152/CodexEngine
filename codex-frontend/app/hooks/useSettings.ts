"use client";

import { useState, useEffect, useCallback } from "react";

export function useSettings(username?: string | null) {
  const [systemPrompt, setSystemPrompt] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [provider, setProvider] = useState("groq");
  const [model, setModel] = useState("qwen/qwen3.6-27b");

  useEffect(() => {
    setSystemPrompt(localStorage.getItem("codex_system_prompt") || "");
    setProvider(localStorage.getItem("codex_provider") || "groq");
    setModel(localStorage.getItem("codex_model") || "qwen/qwen3.6-27b");

    const savedName = localStorage.getItem("codex_display_name");
    if (savedName) {
      setDisplayName(savedName);
    } else if (username) {
      const formatted = username.charAt(0).toUpperCase() + username.slice(1);
      setDisplayName(formatted);
      localStorage.setItem("codex_display_name", formatted);
    }
  }, [username]);

  const saveSystemPrompt = useCallback((val: string) => {
    setSystemPrompt(val);
    localStorage.setItem("codex_system_prompt", val);
  }, []);

  const saveDisplayName = useCallback((val: string) => {
    setDisplayName(val);
    localStorage.setItem("codex_display_name", val);
  }, []);

  const saveProvider = useCallback((val: string) => {
    setProvider(val);
    localStorage.setItem("codex_provider", val);
  }, []);

  const saveModel = useCallback((val: string) => {
    setModel(val);
    localStorage.setItem("codex_model", val);
  }, []);

  return { systemPrompt, displayName, provider, model, saveSystemPrompt, saveDisplayName, saveProvider, saveModel };
}
