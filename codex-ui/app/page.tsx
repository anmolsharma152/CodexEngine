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
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("System Standby");
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [threadId, setThreadId] = useState(() => crypto.randomUUID());
  const [threads, setThreads] = useState<{ id: string; title: string; timestamp: number }[]>([]);

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
        setUploadStatus(`Success: ${file.name} uploaded to engine.`);
        setTimeout(() => {
          setUploadStatus("");
          setShowDocManager(false);
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

    try {
      const response = await fetch("http://127.0.0.1:8000/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, thread_id: threadId }),
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
      setStatus("Failed to connect to engine.");
    } finally {
      setIsStreaming(false);
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
          <div className="bg-[#111216] border border-white/10 p-8 rounded-2xl shadow-2xl w-full max-w-md relative">
            <button
              onClick={() => setShowDocManager(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>
            <h3 className="text-xl font-bold text-white mb-2">
              Manage Knowledge Base
            </h3>
            <p className="text-sm text-gray-400 mb-6">
              Upload PDFs or text files to expand the engine's local retrieval
              context.
            </p>

            <div className="border-2 border-dashed border-white/10 hover:border-blue-500/50 rounded-xl p-8 flex flex-col items-center justify-center text-center transition-colors bg-white/5 relative group">
              <FileUp
                size={32}
                className="text-blue-400 mb-3 group-hover:scale-110 transition-transform"
              />
              <span className="text-sm font-medium text-gray-200">
                Click to upload document
              </span>
              <span className="text-xs text-gray-500 mt-1">
                PDF, TXT, or MD (Max 10MB)
              </span>

              {/* Invisible File Input filling the box */}
              <input
                type="file"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                accept=".pdf,.txt,.md"
                onChange={handleFileUpload}
              />
            </div>

            {uploadStatus && (
              <div className="mt-4 text-sm font-mono text-center text-blue-400 animate-pulse">
                {uploadStatus}
              </div>
            )}
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
                CodexEngine V3
              </h2>
              <p className="text-sm font-mono text-gray-500">
                Agentic RAG Pipeline is ready.
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
                    className={`rounded-2xl p-6 transition-all backdrop-blur-md ${
                      msg.role === "user"
                        ? "bg-white/5 border border-white/10 text-white max-w-[75%]"
                        : "bg-black/20 border border-white/5 text-gray-300 max-w-[90%]"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      msg.content === "" && isStreaming ? (
                        <div className="flex items-center gap-3 text-blue-400 font-mono text-sm py-2">
                          <span className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></span>
                          <span className="animate-pulse">{status}</span>
                        </div>
                      ) : (
                        <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 prose-pre:rounded-xl prose-code:text-blue-300">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
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
            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              className="absolute right-2 p-2.5 bg-white/10 hover:bg-white/20 text-white rounded-full transition-all disabled:opacity-0"
            >
              <Send size={18} className={isStreaming ? "animate-pulse" : ""} />
            </button>
          </form>
          <div className="text-center mt-4 text-[10px] text-gray-600 font-mono uppercase tracking-widest">
            V3.0 Architecture • AsyncPostgres Active
          </div>
        </div>
      </main>
    </div>
  );
}

