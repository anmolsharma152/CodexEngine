"use client";

import { useState, useEffect, useCallback } from "react";

export function useSettings(username?: string | null) {
  const [systemPrompt, setSystemPrompt] = useState("");
  const [displayName, setDisplayName] = useState("");

  useEffect(() => {
    setSystemPrompt(localStorage.getItem("codex_system_prompt") || "");

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

  return { systemPrompt, displayName, saveSystemPrompt, saveDisplayName };
}
