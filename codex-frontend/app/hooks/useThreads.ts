"use client";

import { useState, useCallback } from "react";
import type { Thread } from "../lib/types";
import { API_BASE } from "../lib/constants";

export function useThreads(authFetch: (url: string, options?: RequestInit) => Promise<Response>, token: string | null) {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [threadId, setThreadId] = useState("");
  const [editingThreadId, setEditingThreadId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const fetchThreads = useCallback(async () => {
    try {
      const res = await authFetch(`${API_BASE}/threads`);
      if (res.ok) {
        const data = await res.json();
        setThreads(data.threads || []);
      }
    } catch (e) {
      console.error("Failed to fetch threads:", e);
    }
  }, [authFetch]);

  const saveThreads = useCallback((newThreads: Thread[]) => {
    setThreads(newThreads);
    localStorage.setItem("codex_threads", JSON.stringify(newThreads));
  }, []);

  const togglePin = useCallback(async (id: string) => {
    const thread = threads.find((t) => t.id === id);
    if (!thread) return;
    const updatedThread = { ...thread, pinned: !thread.pinned };
    const updated = threads.map((t) => (t.id === id ? updatedThread : t));
    saveThreads(updated);
    if (token) {
      try {
        await authFetch(`${API_BASE}/threads`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updatedThread),
        });
      } catch (e) {
        console.error("Failed to sync pin state", e);
      }
    }
  }, [threads, token, authFetch, saveThreads]);

  const startRename = useCallback((id: string, title: string) => {
    setEditingThreadId(id);
    setEditTitle(title);
  }, []);

  const saveRename = useCallback(async (id: string) => {
    if (!editTitle.trim()) return;
    const thread = threads.find((t) => t.id === id);
    if (!thread) return;
    const updatedThread = { ...thread, title: editTitle.trim() };
    const updated = threads.map((t) => (t.id === id ? updatedThread : t));
    saveThreads(updated);
    setEditingThreadId(null);
    if (token) {
      try {
        await authFetch(`${API_BASE}/threads`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updatedThread),
        });
      } catch (e) {
        console.error("Failed to sync rename", e);
      }
    }
  }, [editTitle, threads, token, authFetch, saveThreads]);

  const deleteThread = useCallback(async (id: string, threadId: string, setMessages: (msgs: any[]) => void, setStatus: (s: string) => void, fetchDocuments: () => void) => {
    if (!confirm("Are you sure you want to delete this chat and all its temporal documents?")) return;
    const updated = threads.filter((t) => t.id !== id);
    saveThreads(updated);
    if (threadId === id) {
      setThreadId(crypto.randomUUID());
      setMessages([]);
      setStatus("System Standby");
    }
    try {
      if (token) {
        await authFetch(`${API_BASE}/threads/${id}`, { method: "DELETE" });
      } else {
        await fetch(`${API_BASE}/chat/${id}/temporal`, { method: "DELETE" });
      }
      fetchDocuments();
    } catch (err) {
      console.error("Failed to delete temporal backend files:", err);
    }
  }, [threads, token, authFetch, saveThreads]);

  const selectThread = useCallback(async (id: string) => {
    setEditingThreadId(null);
    setThreadId(id);
    try {
      const res = await authFetch(`${API_BASE}/chat/${id}/history`);
      if (res.ok) {
        const data = await res.json();
        return data.history || [];
      }
    } catch (err) {
      console.error("Error loading history:", err);
    }
    return [];
  }, [authFetch]);

  const clearAllThreads = useCallback(async (fetchDocuments: () => void) => {
    if (!confirm("Are you sure you want to delete ALL chat histories and their attached temporal documents?")) return;
    const idsToDelete = threads.map(t => t.id);
    saveThreads([]);
    setThreadId(crypto.randomUUID());
    for (const id of idsToDelete) {
      try {
        if (token) {
          await authFetch(`${API_BASE}/threads/${id}`, { method: "DELETE" });
        } else {
          await fetch(`${API_BASE}/chat/${id}/temporal`, { method: "DELETE" });
        }
      } catch (err) {
        console.error(`Failed to delete temporal backend files for thread ${id}:`, err);
      }
    }
    fetchDocuments();
  }, [threads, token, authFetch, saveThreads]);

  const pinnedThreads = threads.filter((t) => t.pinned);
  const recentThreads = threads.filter((t) => !t.pinned);

  return {
    threads, setThreads,
    threadId, setThreadId,
    editingThreadId, setEditingThreadId,
    editTitle, setEditTitle,
    fetchThreads, saveThreads,
    togglePin, startRename, saveRename, deleteThread, selectThread, clearAllThreads,
    pinnedThreads, recentThreads,
  };
}
