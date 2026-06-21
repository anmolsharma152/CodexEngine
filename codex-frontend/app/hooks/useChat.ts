"use client";

import { useState, useRef, useCallback } from "react";
import type { Message, QuickPrompt } from "../lib/types";
import { API_BASE } from "../lib/constants";
import { toast } from "sonner";

const ALL_QUICK_PROMPTS: QuickPrompt[] = [
  { title: "Capabilities Overview", desc: "Ask how to upload documents and query them in CodexEngine.", text: "Can you give me an overview of CodexEngine's features and how to upload custom PDFs?", docKeywords: ["help", "info", "system", "readme", "upload", "pdf"] },
  { title: "Write a Python Script", desc: "Generate programming code blocks instantly.", text: "Write a clean Python function to check if a number is prime and explain its complexity.", docKeywords: ["python", "code", "prime", "script"] },
  { title: "Draft SQL Queries", desc: "Formulate database query structures.", text: "Draft a PostgreSQL query to calculate average order value by month from an orders table.", docKeywords: ["sql", "database", "postgres", "query"] },
  { title: "Format Markdown Tables", desc: "Format unstructured text inputs into Markdown.", text: "Convert this list of users into a clean Markdown table with columns Name, Email, and Role:\n- John Doe, john@example.com, Admin\n- Jane Smith, jane@example.com, Editor", docKeywords: ["format", "table", "markdown", "csv"] },
  { title: "Explain RAG Pipelines", desc: "Ask the assistant to explain RAG concepts generally.", text: "What is Retrieval-Augmented Generation (RAG) and what are its main advantages over vanilla LLMs?", docKeywords: ["rag", "retrieval", "augmented", "generation"] },
  { title: "Creative Writing Help", desc: "Draft copy or clean up communications.", text: "Help me draft a short, professional email summarizing a project launch for a team newsletter.", docKeywords: ["email", "draft", "write", "creative"] },
  { title: "Debug JavaScript", desc: "Identify and fix code issues.", text: "Identify the bug in this JavaScript code and explain why it fails: let arr = []; for (var i = 0; i < 5; i++) { arr.push(() => i); } console.log(arr[0]());", docKeywords: ["debug", "javascript", "js", "bug", "code"] },
  { title: "Explain Big O", desc: "Break down algorithm complexity.", text: "Explain the differences between O(n), O(n log n), and O(n²) with simple code examples for each.", docKeywords: ["algorithm", "complexity", "big-o", "performance"] },
  { title: "Docker Compose Setup", desc: "Generate container configs.", text: "Write a docker-compose.yml for a Node.js app with a PostgreSQL database and a Redis cache.", docKeywords: ["docker", "compose", "container", "devops"] },
  { title: "Git Workflow Tips", desc: "Suggest branching strategies.", text: "What's a good Git branching strategy for a team of 5 developers working on a single repository?", docKeywords: ["git", "branch", "workflow", "version-control"] },
  { title: "Compare ML Models", desc: "Weigh model trade-offs.", text: "Compare linear regression, random forest, and gradient boosting for a tabular regression problem with 10k rows and 50 features.", docKeywords: ["ml", "model", "regression", "forest", "boosting"] },
  { title: "API Design Patterns", desc: "Structure REST endpoints.", text: "What are the best practices for designing a RESTful API for a multi-tenant SaaS application?", docKeywords: ["api", "rest", "design", "saas"] },
];

export function useChat(
  authFetch: (url: string, options?: RequestInit) => Promise<Response>,
  documents: any[],
  sessionFiles: any[],
  threadId: string,
  systemPrompt?: string,
  projectId?: string,
) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("System Standby");
  const [isStreaming, setIsStreaming] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [suggestedPrompts, setSuggestedPrompts] = useState<QuickPrompt[]>(() => [...ALL_QUICK_PROMPTS].sort(() => Math.random() - 0.5).slice(0, 3));

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const selectSuggestedPrompts = useCallback(() => {
    const allDocs = [...documents, ...sessionFiles];
    const matching = ALL_QUICK_PROMPTS.filter(prompt =>
      allDocs.some(doc => prompt.docKeywords.some(keyword => doc.filename.toLowerCase().includes(keyword)))
    );
    const shuffleArray = <T,>(arr: T[]): T[] => [...arr].sort(() => Math.random() - 0.5);
    let selected: QuickPrompt[] = [];
    if (matching.length >= 3) {
      selected = shuffleArray(matching).slice(0, 3);
    } else {
      selected = [...matching];
      const remaining = ALL_QUICK_PROMPTS.filter(p => !matching.includes(p));
      selected = [...selected, ...shuffleArray(remaining).slice(0, 3 - selected.length)];
    }
    setSuggestedPrompts(selected);
  }, [documents, sessionFiles]);

  const handleQuickPromptClick = useCallback((text: string) => {
    setInput(text);
    setTimeout(() => inputRef.current?.focus(), 50);
  }, []);

  const copyToClipboard = useCallback((text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    toast.success("Copied to clipboard");
    setTimeout(() => setCopiedIndex(null), 2000);
  }, []);

  const stopThinking = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setStatus("Thinking stopped.");
  }, []);

  const sendMessage = useCallback(async (e: React.FormEvent, threads: any[], saveThreads: (t: any[]) => void) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage = input;
    setInput("");
    setIsStreaming(true);
    setStatus("Agent routing...");

    setMessages((prev) => [...prev, { role: "user", content: userMessage }, { role: "assistant", content: "" }]);

    const exists = threads.some((t) => t.id === threadId);
    if (!exists) {
      const title = userMessage.length > 28 ? userMessage.slice(0, 25) + "..." : userMessage;
      const newThread = { id: threadId, title, timestamp: Date.now(), projectId };
      saveThreads([newThread, ...threads]);
      authFetch(`${API_BASE}/threads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newThread),
      }).catch((e) => console.error("Failed to sync new thread", e));
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await authFetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, thread_id: threadId, system_prompt: systemPrompt }),
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
                    copy[lastIdx] = { ...copy[lastIdx], content: copy[lastIdx].content + data.content };
                    return copy;
                  });
                } else if (data.type === "done") {
                  setStatus("Stream complete.");
                } else if (data.type === "error") {
                  setStatus("Engine Error.");
                  setMessages((prev) => {
                    const copy = [...prev];
                    const lastIdx = copy.length - 1;
                    copy[lastIdx] = { ...copy[lastIdx], content: `⚠️ **System Error:** ${data.content}` };
                    return copy;
                  });
                }
              } catch (parseError) {
                console.error("JSON parsing crash prevented.", parseError);
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
  }, [input, isStreaming, threadId, authFetch]);

  const exportChatMarkdown = useCallback(() => {
    if (messages.length === 0) return;
    let content = `# CodexEngine Chat Transcript - Thread: ${threadId}\n\n`;
    messages.forEach((msg) => {
      content += `### **${msg.role === "user" ? "User" : "Assistant"}**\n\n${msg.content}\n\n---\n\n`;
    });
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `chat-transcript-${threadId.slice(0, 8)}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [messages, threadId]);

  return {
    messages, setMessages,
    input, setInput,
    status, setStatus,
    isStreaming,
    copiedIndex,
    suggestedPrompts,
    abortControllerRef,
    messagesEndRef,
    inputRef,
    selectSuggestedPrompts,
    handleQuickPromptClick,
    copyToClipboard,
    stopThinking,
    sendMessage,
    exportChatMarkdown,
  };
}
