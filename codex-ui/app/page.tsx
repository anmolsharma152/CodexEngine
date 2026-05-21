"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MessageSquare, Plus, FileUp, Settings, Send, Menu, PanelLeftClose, TerminalSquare } from "lucide-react";

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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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

    try {
      const response = await fetch("http://localhost:8000/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, thread_id: "linear_ui_test" }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));

            if (data.type === "status") {
              setStatus(data.content);
            } else if (data.type === "token") {
              setMessages((prev) => {
                const copy = [...prev];
                const lastIdx = copy.length - 1;
                copy[lastIdx] = { ...copy[lastIdx], content: copy[lastIdx].content + data.content };
                return copy;
              });
            } else if (data.type === "done") {
              setStatus("Stream complete.");
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
      
      {/* GLOBAL BACKGROUND EFFECTS (From your Linear.html) */}
      <div className="absolute inset-0 z-0 bg-[size:40px_40px] bg-[linear-gradient(to_right,rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)] pointer-events-none" />
      <div className="absolute top-0 left-0 w-full h-full z-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 15% 50%, rgba(76, 29, 149, 0.12), transparent 25%), radial-gradient(circle at 85% 30%, rgba(37, 99, 235, 0.12), transparent 25%)' }} />

      {/* SIDEBAR (Glassmorphic) */}
      <aside className={`relative z-10 ${sidebarOpen ? "w-64" : "w-0"} transition-all duration-300 ease-in-out border-r border-white/10 bg-black/20 backdrop-blur-xl flex flex-col`}>
        <div className="p-5 flex justify-between items-center border-b border-white/10">
          <div className="flex items-center gap-2">
            <TerminalSquare size={18} className="text-blue-400" />
            <span className="font-medium text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 tracking-tight">CodexEngine</span>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="text-gray-500 hover:text-white transition-colors">
            <PanelLeftClose size={18} />
          </button>
        </div>
        
        <div className="p-4">
          <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-full transition-all text-sm font-medium hover:-translate-y-0.5">
            <Plus size={16} /> New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <div className="text-xs font-semibold text-gray-600 mb-3 px-2 uppercase tracking-widest">History</div>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-400 hover:bg-white/5 hover:text-gray-200 rounded-lg transition-colors truncate border border-transparent hover:border-white/5">
            <MessageSquare size={14} /> FlashAttention implementation
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-400 hover:bg-white/5 hover:text-gray-200 rounded-lg transition-colors truncate border border-transparent hover:border-white/5">
            <MessageSquare size={14} /> What is DBeaver?
          </button>
        </div>

        <div className="p-4 border-t border-white/10 space-y-1">
          <button className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-400 hover:bg-white/5 hover:text-gray-200 rounded-lg transition-colors">
            <FileUp size={16} /> Manage Documents
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-400 hover:bg-white/5 hover:text-gray-200 rounded-lg transition-colors">
            <Settings size={16} /> Settings
          </button>
        </div>
      </aside>

      {/* MAIN CHAT AREA */}
      <main className="relative z-10 flex-1 flex flex-col h-full">
        
        {/* Top Nav */}
        <header className="h-16 border-b border-white/5 flex items-center px-6 gap-4 bg-black/10 backdrop-blur-sm">
          {!sidebarOpen && (
            <button onClick={() => setSidebarOpen(true)} className="text-gray-500 hover:text-white transition-colors">
              <Menu size={20} />
            </button>
          )}
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="flex h-2 w-2 relative">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isStreaming ? 'bg-purple-400' : 'bg-blue-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isStreaming ? 'bg-purple-500' : 'bg-blue-500'}`}></span>
            </span>
            <span className="text-gray-400">{status}</span>
          </div>
        </header>

        {/* Chat Feed */}
        <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <h2 className="text-3xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500 tracking-tight mb-3">CodexEngine V3</h2>
              <p className="text-sm font-mono text-gray-500">Agentic RAG Pipeline is ready.</p>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-8">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`rounded-2xl p-6 transition-all backdrop-blur-md ${
                    msg.role === "user" 
                      ? "bg-white/5 border border-white/10 text-white max-w-[75%]" 
                      : "bg-black/20 border border-white/5 text-gray-300 max-w-[90%]"
                  }`}>
                    {msg.role === "assistant" ? (
                      <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 prose-pre:rounded-xl prose-code:text-blue-300">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-6">
          <form onSubmit={sendMessage} className="max-w-4xl mx-auto relative flex items-center group">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isStreaming}
              placeholder="Query the engine..."
              className="w-full bg-black/40 text-gray-100 border border-white/10 rounded-full pl-6 pr-16 py-4 focus:outline-none focus:border-white/30 focus:bg-black/60 transition-all disabled:opacity-50 backdrop-blur-xl shadow-lg"
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
