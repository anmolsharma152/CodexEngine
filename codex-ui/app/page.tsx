"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  MessageSquare,
  Plus,
  FileUp,
  Settings,
  Send,
  Menu,
  PanelLeftClose,
  TerminalSquare,
  X,
} from "lucide-react";

type Message = {
  role: "user" | "assistant";
  content: string;
  intent?: string;
  evaluation?: {
    relevant?: boolean;
    sufficient?: boolean;
    grounded?: boolean;
    confidence?: number;
    retry_needed?: boolean;
  };
  context?: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("System Standby");
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [threadId, setThreadId] = useState(() => crypto.randomUUID());
  const [threads, setThreads] = useState<{ id: string; title: string; timestamp: number }[]>([]);

  // Citation Drawer State
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedChunk, setSelectedChunk] = useState("");
  const [selectedSource, setSelectedSource] = useState("");
  const [selectedPage, setSelectedPage] = useState("");
  const [selectedRow, setSelectedRow] = useState("");
  const abortControllerRef = useRef<AbortController | null>(null);

  const stopThinking = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setStatus("Thinking stopped.");
  };

  useEffect(() => {
    const saved = localStorage.getItem("codex_threads");
    if (saved) {
      try {
        setThreads(JSON.parse(saved));
      } catch (e) {
        console.error("Error parsing threads", e);
      }
    }
  }, []);

  const saveThreads = (newThreads: typeof threads) => {
    setThreads(newThreads);
    localStorage.setItem("codex_threads", JSON.stringify(newThreads));
  };

  const selectThread = async (id: string) => {
    if (isStreaming) return;
    setThreadId(id);
    setStatus("Loading conversation history...");
    setMessages([]);
    try {
      const res = await fetch(`http://127.0.0.1:8000/chat/${id}/history`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.history || []);
        setStatus("Conversation loaded.");
      } else {
        setStatus("Failed to load history.");
      }
    } catch (err) {
      setStatus("Error loading history.");
    }
  };

  // Modal State
  const [showDocManager, setShowDocManager] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [documents, setDocuments] = useState<{ filename: string; size_bytes: number; chunks_count: number; status: string }[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const fetchDocuments = async () => {
    setLoadingDocs(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/documents");
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleDeleteDocument = async (filename: string) => {
    if (!confirm(`Are you sure you want to delete ${filename} and all its chunks from the vector database?`)) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/documents/${encodeURIComponent(filename)}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setUploadStatus(`Deleted: ${filename}`);
        fetchDocuments();
        setTimeout(() => setUploadStatus(""), 2000);
      } else {
        setUploadStatus("Failed to delete document.");
      }
    } catch (err) {
      setUploadStatus("Error deleting document.");
    }
  };

  useEffect(() => {
    if (showDocManager) {
      fetchDocuments();
    }
  }, [showDocManager]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isStreaming && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isStreaming]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: isStreaming ? "auto" : "smooth",
    });
  }, [messages, isStreaming]);

  // FILE UPLOAD HANDLER
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadStatus("Uploading...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData, // Do NOT set Content-Type header; the browser sets the multipart boundary automatically
      });

      if (response.ok) {
        setUploadStatus(`Success: ${file.name} uploaded and ingested.`);
        fetchDocuments();
        setTimeout(() => {
          setUploadStatus("");
        }, 2000);
      } else {
        setUploadStatus("Upload failed. Check server logs.");
      }
    } catch (error) {
      setUploadStatus("Network error during upload.");
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage = input;
    setInput("");
    setIsStreaming(true);
    setStatus("Agent routing...");

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage },
      { role: "assistant", content: "" },
    ]);

    // Create/update thread in sidebar if it's the first message
    const exists = threads.some((t) => t.id === threadId);
    if (!exists) {
      const title = userMessage.length > 28 ? userMessage.slice(0, 25) + "..." : userMessage;
      const newThread = { id: threadId, title, timestamp: Date.now() };
      saveThreads([newThread, ...threads]);
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch("http://127.0.0.1:8000/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, thread_id: threadId }),
        signal: controller.signal,
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let streamBuffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        streamBuffer += decoder.decode(value, { stream: true });
        const parts = streamBuffer.split("\n\n");

        // Keep the last partial event segment in the buffer
        streamBuffer = parts.pop() || "";

        for (const part of parts) {
          if (!part.trim()) continue;

          const lines = part.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.type === "status") {
                  setStatus(data.content);
                } else if (data.type === "token") {
                  setMessages((prev) => {
                    const copy = [...prev];
                    const lastIdx = copy.length - 1;
                    copy[lastIdx] = {
                      ...copy[lastIdx],
                      content: copy[lastIdx].content + data.content,
                    };
                    return copy;
                  });
                } else if (data.type === "evaluation") {
                  setMessages((prev) => {
                    const copy = [...prev];
                    const lastIdx = copy.length - 1;
                    copy[lastIdx] = {
                      ...copy[lastIdx],
                      intent: data.intent,
                      evaluation: data.content,
                      context: data.context,
                    };
                    return copy;
                  });
                } else if (data.type === "done") {
                  setStatus("Stream complete.");
                } else if (data.type === "error") {
                  setStatus("Engine Error.");
                  setMessages((prev) => {
                    const copy = [...prev];
                    const lastIdx = copy.length - 1;
                    copy[lastIdx] = {
                      ...copy[lastIdx],
                      content: `⚠️ **System Error:** ${data.content}`,
                    };
                    return copy;
                  });
                }
              } catch (parseError) {
                console.error("JSON parsing crash prevented. Incomplete line:", line, parseError);
              }
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        setStatus("Thinking stopped.");
      } else {
        setStatus("Failed to connect to engine.");
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleCitationClick = (href: string, context: string) => {
    try {
      const cleanHref = href.replace("citation://", "http://temp-host/");
      const url = new URL(cleanHref);
      const source = decodeURIComponent(url.pathname.substring(1));
      const page = url.searchParams.get("page") || "";
      const row = url.searchParams.get("row") || "";

      // Find the matching chunk in context.
      const chunks = context.split("\n\n");
      let matchedChunk = "";

      for (const chunk of chunks) {
        // Try to find the chunk containing the exact citation URL
        if (chunk.includes(href)) {
          const lines = chunk.split("\n");
          matchedChunk = lines.slice(1).join("\n");
          break;
        }
      }

      if (!matchedChunk) {
        // Try a looser match using source name and page/row
        for (const chunk of chunks) {
          const matchesSource = chunk.toLowerCase().includes(source.toLowerCase());
          const matchesPage = page ? chunk.includes(`Page: ${page}`) || chunk.includes(`page=${page}`) : true;
          const matchesRow = row ? chunk.includes(`Row: ${row}`) || chunk.includes(`row=${row}`) : true;
          if (matchesSource && matchesPage && matchesRow) {
            const lines = chunk.split("\n");
            matchedChunk = lines.slice(1).join("\n");
            break;
          }
        }
      }

      setSelectedSource(source);
      setSelectedPage(page);
      setSelectedRow(row);
      setSelectedChunk(matchedChunk || "No matching source text chunk found in retrieved context.");
      setDrawerOpen(true);
    } catch (err) {
      console.error("Error parsing citation:", err);
    }
  };

  return (
    <div className="relative flex h-screen bg-[#0B0C10] text-[#C5C6C7] font-sans overflow-hidden selection:bg-blue-500/30">
      {/* GLOBAL BACKGROUND EFFECTS */}
      <div className="absolute inset-0 z-0 bg-[size:40px_40px] bg-[linear-gradient(to_right,rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)] pointer-events-none" />
      <div
        className="absolute top-0 left-0 w-full h-full z-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(circle at 15% 50%, rgba(76, 29, 149, 0.12), transparent 25%), radial-gradient(circle at 85% 30%, rgba(37, 99, 235, 0.12), transparent 25%)",
        }}
      />

      {/* DOCUMENT MANAGER MODAL */}
      {showDocManager && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-all">
          <div className="bg-[#111216] border border-white/10 p-8 rounded-2xl shadow-2xl w-full max-w-2xl relative flex flex-col max-h-[85vh]">
            <button
              onClick={() => setShowDocManager(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors shrink-0"
            >
              <X size={20} />
            </button>
            <h3 className="text-xl font-bold text-white mb-2 shrink-0">
              Manage Knowledge Base
            </h3>
            <p className="text-sm text-gray-400 mb-6 shrink-0">
              Upload documents or manage currently indexed vector database chunks.
            </p>

            {/* Upload Zone (More compact) */}
            <div className="border border-dashed border-white/10 hover:border-blue-500/50 rounded-xl p-4 flex flex-col items-center justify-center text-center transition-colors bg-white/5 relative group mb-6 shrink-0">
              <FileUp
                size={24}
                className="text-blue-400 mb-2 group-hover:scale-110 transition-transform"
              />
              <span className="text-xs font-medium text-gray-200">
                Click to upload new document
              </span>
              <span className="text-[10px] text-gray-500 mt-0.5">
                PDF, TXT, MD, or CSV (Max 10MB)
              </span>

              {/* Invisible File Input filling the box */}
              <input
                type="file"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                accept=".pdf,.txt,.md,.csv"
                onChange={handleFileUpload}
              />
            </div>

            {uploadStatus && (
              <div className="mb-4 text-xs font-mono text-center text-blue-400 animate-pulse shrink-0">
                {uploadStatus}
              </div>
            )}

            {/* Document List */}
            <div className="flex-1 overflow-y-auto space-y-3 min-h-[200px] border-t border-white/5 pt-4 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/10 hover:[&::-webkit-scrollbar-thumb]:bg-white/20 [&::-webkit-scrollbar-thumb]:rounded-full">
              <div className="flex justify-between items-center text-xs font-mono text-gray-500 mb-2 px-1">
                <span>INDEXED SOURCE FILES</span>
                {loadingDocs && <span className="animate-spin">⚙️</span>}
              </div>

              {documents.length === 0 ? (
                <div className="text-center py-12 text-sm text-gray-600 font-mono">
                  {loadingDocs ? "Loading indexed documents..." : "No source files currently indexed."}
                </div>
              ) : (
                <div className="divide-y divide-white/5">
                  {documents.map((doc) => (
                    <div key={doc.filename} className="flex items-center justify-between py-3 px-1 hover:bg-white/[0.02] rounded-lg transition-colors group">
                      <div className="flex items-center gap-3 min-w-0 flex-1 pr-4">
                        <div className="h-8 w-8 rounded bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 shrink-0">
                          {doc.filename.endsWith(".pdf") ? "📕" : doc.filename.endsWith(".csv") ? "📊" : "📄"}
                        </div>
                        <div className="min-w-0">
                          <div className="text-xs font-medium text-white truncate" title={doc.filename}>
                            {doc.filename}
                          </div>
                          <div className="text-[10px] text-gray-500 font-mono mt-0.5 flex gap-2">
                            <span>{doc.size_bytes > 0 ? `${(doc.size_bytes / 1024).toFixed(1)} KB` : "N/A"}</span>
                            <span>•</span>
                            <span className="text-blue-400 font-semibold">{doc.chunks_count} chunks</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        {/* Status Badge */}
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          doc.status === "Ingested"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : doc.status === "Pending"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse"
                            : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                        }`}>
                          {doc.status}
                        </span>

                        {/* Delete Button */}
                        <button
                          type="button"
                          onClick={() => handleDeleteDocument(doc.filename)}
                          className="p-1 rounded hover:bg-red-500/10 text-gray-500 hover:text-red-400 transition-all cursor-pointer opacity-0 group-hover:opacity-100 focus:opacity-100 shrink-0 text-xs"
                          title="Delete document and chunks"
                        >
                          ❌
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SIDEBAR (Glassmorphic) */}
      <aside
        className={`relative z-10 ${sidebarOpen ? "w-64" : "w-16"} transition-all duration-300 ease-in-out border-r border-white/10 bg-black/20 backdrop-blur-xl flex flex-col overflow-x-hidden`}
      >
        <div
          className={`h-16 flex items-center border-b border-white/10 ${sidebarOpen ? "px-5 justify-between" : "px-0 justify-center"}`}
        >
          {sidebarOpen ? (
            <>
              <div className="flex items-center gap-2 overflow-hidden">
                <TerminalSquare size={18} className="text-blue-400 shrink-0" />
                <span className="font-medium text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 tracking-tight whitespace-nowrap">
                  CodexEngine
                </span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="text-gray-500 hover:text-white transition-colors shrink-0"
              >
                <PanelLeftClose size={18} />
              </button>
            </>
          ) : (
            <button
              onClick={() => setSidebarOpen(true)}
              className="text-gray-500 hover:text-white transition-colors"
            >
              <Menu size={20} />
            </button>
          )}
        </div>

        <div
          className={`flex justify-center ${sidebarOpen ? "p-4" : "py-4 px-0"}`}
        >
          <button
            onClick={() => {
              setThreadId(crypto.randomUUID());
              setMessages([]);
              setStatus("System Standby");
              setTimeout(() => inputRef.current?.focus(), 50);
            }}
            title="New Chat"
            className={`flex items-center justify-center bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-all text-sm font-medium hover:-translate-y-0.5 ${
              sidebarOpen
                ? "w-full gap-2 px-4 py-2 rounded-full"
                : "w-10 h-10 p-0 rounded-full"
            }`}
          >
            <Plus size={16} className="shrink-0" />
            {sidebarOpen && <span className="whitespace-nowrap">New Chat</span>}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto overflow-x-hidden space-y-2 pb-4 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/10 hover:[&::-webkit-scrollbar-thumb]:bg-white/20 [&::-webkit-scrollbar-thumb]:rounded-full">
          {sidebarOpen ? (
            <div className="text-xs font-semibold text-gray-600 mb-3 px-6 uppercase tracking-widest whitespace-nowrap mt-4">
              History
            </div>
          ) : (
            <div className="mt-4"></div>
          )}

          {threads.map((t) => (
            <div key={t.id} className={sidebarOpen ? "px-4" : "px-0"}>
              <button
                onClick={() => selectThread(t.id)}
                className={`flex items-center gap-3 py-2.5 text-sm rounded-lg transition-colors border border-transparent ${
                  threadId === t.id
                    ? "bg-white/10 text-white border-white/10"
                    : "text-gray-400 hover:bg-white/5 hover:text-gray-200 hover:border-white/5"
                } ${sidebarOpen ? "w-full px-3" : "w-10 h-10 justify-center mx-auto p-0"}`}
                title={t.title}
              >
                <MessageSquare size={14} className="shrink-0" />
                {sidebarOpen && (
                  <span className="truncate">{t.title}</span>
                )}
              </button>
            </div>
          ))}
          {threads.length === 0 && sidebarOpen && (
            <div className="text-center py-8 text-xs text-gray-600 font-mono">
              No chat history
            </div>
          )}
        </div>

        <div className="border-t border-white/10 space-y-2 flex flex-col items-center py-4">
          <div className={sidebarOpen ? "w-full px-4" : "w-full px-0"}>
            {/* WIRE UP THE MANAGE DOCUMENTS BUTTON HERE */}
            <button
              onClick={() => setShowDocManager(true)}
              className={`flex items-center gap-3 py-2.5 text-sm text-gray-400 hover:bg-white/5 hover:text-gray-200 rounded-lg transition-colors ${sidebarOpen ? "w-full px-3" : "w-10 h-10 justify-center mx-auto p-0"}`}
              title="Manage Documents"
            >
              <FileUp size={16} className="shrink-0" />
              {sidebarOpen && (
                <span className="whitespace-nowrap">Manage Documents</span>
              )}
            </button>
          </div>
          <div className={sidebarOpen ? "w-full px-4" : "w-full px-0"}>
            <button
              className={`flex items-center gap-3 py-2.5 text-sm text-gray-400 hover:bg-white/5 hover:text-gray-200 rounded-lg transition-colors ${sidebarOpen ? "w-full px-3" : "w-10 h-10 justify-center mx-auto p-0"}`}
              title="Settings"
            >
              <Settings size={16} className="shrink-0" />
              {sidebarOpen && (
                <span className="whitespace-nowrap">Settings</span>
              )}
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN CHAT AREA */}
      <main className="relative z-10 flex-1 flex flex-col h-full">
        <header className="h-16 border-b border-white/5 flex items-center px-6 gap-4 bg-black/10 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="flex h-2 w-2 relative">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isStreaming ? "bg-purple-400" : "bg-blue-400"}`}
              ></span>
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${isStreaming ? "bg-purple-500" : "bg-blue-500"}`}
              ></span>
            </span>
            <span className="text-gray-400">{status}</span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/5 hover:[&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <h2 className="text-3xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500 tracking-tight mb-3">
                CodexEngine V4
              </h2>
              <p className="text-sm font-mono text-gray-500">
                Cognitive Retrieval & Orchestration System is online.
              </p>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-8">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`rounded-2xl p-6 transition-all backdrop-blur-md text-sm md:text-[15px] ${
                      msg.role === "user"
                        ? "bg-white/5 border border-white/10 text-white max-w-[75%]"
                        : "bg-black/20 border border-white/5 text-gray-300 max-w-[90%]"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      msg.content === "" && isStreaming ? (
                        <div className="space-y-4 py-2 w-full min-w-[320px]">
                          {/* Standard Tailwind pulsing gradient bars */}
                          <div className="h-3 rounded-md bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 animate-pulse w-1/3"></div>
                          <div className="h-3 rounded-md bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 animate-pulse w-5/6"></div>
                          <div className="h-3 rounded-md bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 animate-pulse w-2/3"></div>
                          
                          <div className="flex items-center gap-3 mt-4 pt-2 border-t border-white/5">
                            <span className="text-xs font-mono text-gray-500 animate-pulse flex items-center gap-1.5">
                              <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-ping" />
                              {status}
                            </span>
                            <button
                              type="button"
                              onClick={stopThinking}
                              className="px-2.5 py-1 text-[10px] font-mono font-bold bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 hover:border-red-500/40 rounded transition-all cursor-pointer shadow-sm active:scale-95"
                            >
                              Stop Thinking
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-col">
                          {/* Cognition Dashboard */}
                          {(msg.intent || msg.evaluation) && (
                            <details className="group border border-white/10 bg-white/5 rounded-xl mb-4 overflow-hidden max-w-lg">
                              <summary className="flex items-center justify-between px-4 py-2 text-xs font-mono cursor-pointer select-none hover:bg-white/5 transition-colors">
                                <div className="flex items-center gap-2">
                                  <span className={`h-2 w-2 rounded-full ${
                                    msg.intent === "retrieval_required"
                                      ? (msg.evaluation?.grounded ? "bg-emerald-500 animate-pulse" : "bg-amber-500 animate-pulse")
                                      : "bg-blue-500"
                                  }`} />
                                  <span className="font-semibold text-gray-200">
                                    Cognition Panel: {
                                      msg.intent === "retrieval_required"
                                        ? (msg.evaluation?.grounded ? "Grounded RAG" : "Fallback RAG")
                                        : msg.intent === "direct_parametric"
                                        ? "Parametric Engine"
                                        : "Casual Interaction"
                                    }
                                  </span>
                                </div>
                                <span className="text-gray-400 group-open:rotate-180 transition-transform">▼</span>
                              </summary>
                              <div className="px-4 py-3 border-t border-white/5 bg-black/40 text-[11px] font-mono text-gray-300 space-y-2.5">
                                <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                                  <div className="flex justify-between border-b border-white/5 pb-1">
                                    <span className="text-gray-500">Intent:</span>
                                    <span className="text-blue-400 font-semibold">{msg.intent || "retrieval_required"}</span>
                                  </div>
                                  <div className="flex justify-between border-b border-white/5 pb-1">
                                    <span className="text-gray-500">Confidence:</span>
                                    <span className="text-blue-400 font-semibold">
                                      {msg.evaluation?.confidence !== undefined
                                        ? `${(msg.evaluation.confidence * 100).toFixed(0)}%`
                                        : "N/A"}
                                    </span>
                                  </div>
                                  <div className="flex justify-between border-b border-white/5 pb-1">
                                    <span className="text-gray-500">Relevant:</span>
                                    <span className={msg.evaluation?.relevant ? "text-emerald-400 font-semibold" : "text-amber-400 font-semibold"}>
                                      {msg.evaluation?.relevant ? "TRUE" : "FALSE"}
                                    </span>
                                  </div>
                                  <div className="flex justify-between border-b border-white/5 pb-1">
                                    <span className="text-gray-500">Sufficient:</span>
                                    <span className={msg.evaluation?.sufficient ? "text-emerald-400 font-semibold" : "text-amber-400 font-semibold"}>
                                      {msg.evaluation?.sufficient ? "TRUE" : "FALSE"}
                                    </span>
                                  </div>
                                  <div className="flex justify-between border-b border-white/5 pb-1">
                                    <span className="text-gray-500">Grounded:</span>
                                    <span className={msg.evaluation?.grounded ? "text-emerald-400 font-semibold" : "text-amber-400 font-semibold"}>
                                      {msg.evaluation?.grounded ? "TRUE" : "FALSE"}
                                    </span>
                                  </div>
                                  <div className="flex justify-between border-b border-white/5 pb-1">
                                    <span className="text-gray-500">Retry needed:</span>
                                    <span className={msg.evaluation?.retry_needed ? "text-red-400 font-semibold" : "text-gray-400 font-semibold"}>
                                      {msg.evaluation?.retry_needed ? "TRUE" : "FALSE"}
                                    </span>
                                  </div>
                                </div>
                                {msg.intent === "direct_parametric" && (
                                  <div className="text-[10px] text-amber-400/80 bg-amber-400/5 border border-amber-400/10 p-2 rounded-lg">
                                    ⚠️ Context database bypassed. Relying on pre-trained parametric knowledge.
                                  </div>
                                )}
                              </div>
                            </details>
                          )}

                          <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 prose-pre:rounded-xl prose-code:text-blue-300">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                a(props) {
                                  const { href, children, ...rest } = props;
                                  if (href && href.startsWith("citation://")) {
                                    try {
                                      const cleanHref = href.replace("citation://", "http://temp-host/");
                                      const url = new URL(cleanHref);
                                      const source = decodeURIComponent(url.pathname.substring(1));
                                      const page = url.searchParams.get("page") || "";
                                      const row = url.searchParams.get("row") || "";
                                      const label = page ? `p. ${page}` : (row ? `r. ${row}` : "doc");
                                      return (
                                        <button
                                          type="button"
                                          onClick={() => handleCitationClick(href, msg.context || "")}
                                          title={`Source: ${source}${page ? ` | Page: ${page}` : ""}${row ? ` | Row: ${row}` : ""}`}
                                          className="inline-flex items-center justify-center px-1 py-0.5 mx-0.5 rounded text-[9px] font-mono font-bold bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 transition-all cursor-pointer align-super"
                                        >
                                          [{label}]
                                        </button>
                                      );
                                    } catch (e) {
                                      console.error("Error parsing citation link", e);
                                    }
                                  }
                                  return (
                                    <a
                                      href={href}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-400 hover:underline"
                                      {...rest}
                                    >
                                      {children}
                                    </a>
                                  );
                                }
                              }}
                            >
                              {msg.content}
                            </ReactMarkdown>
                          </div>
                        </div>
                      )
                    ) : (
                      <div className="whitespace-pre-wrap leading-relaxed">
                        {msg.content}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="p-6">
          <form
            onSubmit={sendMessage}
            className="max-w-4xl mx-auto relative flex items-center group"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isStreaming}
              placeholder="Query the engine..."
              className="w-full bg-black/40 text-gray-100 border border-white/10 rounded-full pl-6 pr-16 py-4 focus:outline-none focus:border-white/30 focus:bg-black/60 transition-all disabled:opacity-50 backdrop-blur-xl shadow-lg"
              autoFocus
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={stopThinking}
                className="absolute right-2 p-2.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 rounded-full transition-all cursor-pointer shadow-md active:scale-95 flex items-center justify-center"
                title="Stop Thinking"
              >
                <X size={18} />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="absolute right-2 p-2.5 bg-white/10 hover:bg-white/20 text-white rounded-full transition-all disabled:opacity-0"
              >
                <Send size={18} />
              </button>
            )}
          </form>
          <div className="text-center mt-4 text-[10px] text-gray-600 font-mono uppercase tracking-widest">
            V4.0 Architecture • AsyncPostgres Active
          </div>
        </div>
      </main>

      {/* Drawer Overlay */}
      {drawerOpen && (
        <div
          onClick={() => setDrawerOpen(false)}
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 transition-opacity duration-300"
        />
      )}

      {/* CONTEXT DRAWER (Slides from right) */}
      <aside
        className={`fixed top-0 right-0 h-full w-full sm:w-[450px] bg-[#111216]/95 backdrop-blur-2xl border-l border-white/10 shadow-2xl z-50 transform ${
          drawerOpen ? "translate-x-0" : "translate-x-full"
        } transition-transform duration-300 ease-in-out flex flex-col`}
      >
        <div className="h-16 flex items-center justify-between px-6 border-b border-white/10">
          <div className="flex items-center gap-2">
            <TerminalSquare className="text-blue-400" size={18} />
            <span className="font-bold text-white tracking-tight">Source Context</span>
          </div>
          <button
            onClick={() => setDrawerOpen(false)}
            className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-all"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="space-y-1">
            <div className="text-[10px] uppercase tracking-wider text-gray-500 font-mono">Document</div>
            <div className="text-sm font-semibold text-white break-all">{selectedSource}</div>
          </div>

          {(selectedPage || selectedRow) && (
            <div className="flex gap-6">
              {selectedPage && (
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-gray-500 font-mono">Page</div>
                  <div className="text-sm font-semibold text-blue-400 font-mono">{selectedPage}</div>
                </div>
              )}
              {selectedRow && (
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-gray-500 font-mono">Row Index</div>
                  <div className="text-sm font-semibold text-blue-400 font-mono">{selectedRow}</div>
                </div>
              )}
            </div>
          )}

          <div className="space-y-2">
            <div className="text-[10px] uppercase tracking-wider text-gray-500 font-mono">Retrieved Chunk</div>
            <div className="bg-black/40 border border-white/5 rounded-xl p-4 text-xs font-mono text-gray-300 whitespace-pre-wrap leading-relaxed max-h-[50vh] overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full">
              {selectedChunk}
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-white/10 bg-black/20 text-[10px] font-mono text-gray-600 text-center">
          V4 Ingestion Pipeline • fitz-compiled page offsets
        </div>
      </aside>
    </div>
  );
}

