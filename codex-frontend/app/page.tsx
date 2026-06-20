"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Download } from "lucide-react";
import { useAuth } from "./hooks/useAuth";
import { useThreads } from "./hooks/useThreads";
import { useDocuments } from "./hooks/useDocuments";
import { useChat } from "./hooks/useChat";
import { useSettings } from "./hooks/useSettings";
import { useProjects } from "./hooks/useProjects";
import LandingPage from "./components/LandingPage";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import EmptyState from "./components/EmptyState";
import QuickPrompts from "./components/QuickPrompts";
import InputBar from "./components/InputBar";
import DocManager from "./components/DocManager";
import CitationDrawer from "./components/CitationDrawer";
import OnboardingBanner from "./components/OnboardingBanner";
import SettingsModal from "./components/SettingsModal";

export default function Home() {
  const auth = useAuth();
  const threads = useThreads(auth.authFetch, auth.token);
  const docs = useDocuments(auth.authFetch);

  const sessionFiles = useMemo(
    () => docs.documents.filter(d => d.thread_id === threads.threadId),
    [docs.documents, threads.threadId]
  );

  const settings = useSettings(auth.username);

  const projects = useProjects();

  const chat = useChat(auth.authFetch, docs.documents, sessionFiles, threads.threadId, settings.systemPrompt, projects.activeProjectId);

  const [isMounted, setIsMounted] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const [showSettings, setShowSettings] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedChunk, setSelectedChunk] = useState("");
  const [selectedSource, setSelectedSource] = useState("");
  const [selectedPage, setSelectedPage] = useState("");
  const [selectedRow, setSelectedRow] = useState("");

  const [onboardingSeen, setOnboardingSeen] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    threads.setThreadId(crypto.randomUUID());
    setOnboardingSeen(localStorage.getItem("codex_onboarding_seen") === "true");
    setIsMounted(true);
    if (window.innerWidth < 768) setSidebarOpen(false);
  }, []);

  const showOnboarding = !onboardingSeen && threads.threads.length === 0 && chat.messages.length === 0;

  const handleDismissOnboarding = useCallback(() => {
    setOnboardingSeen(true);
    localStorage.setItem("codex_onboarding_seen", "true");
  }, []);

  const handleCitationClick = useCallback((href: string, context: string) => {
    try {
      const cleanHref = href.replace("citation://", "http://temp-host/");
      const url = new URL(cleanHref);
      const source = decodeURIComponent(url.pathname.substring(1));
      const page = url.searchParams.get("page") || "";
      const row = url.searchParams.get("row") || "";
      const chunks = context.split("\n\n");
      let matchedChunk = "";
      for (const chunk of chunks) {
        if (chunk.includes(href)) {
          matchedChunk = chunk.split("\n").slice(1).join("\n");
          break;
        }
      }
      if (!matchedChunk) {
        for (const chunk of chunks) {
          const matchesSource = chunk.toLowerCase().includes(source.toLowerCase());
          const matchesPage = page ? (chunk.includes(`Page: ${page}`) || chunk.includes(`page=${page}`)) : true;
          const matchesRow = row ? (chunk.includes(`Row: ${row}`) || chunk.includes(`row=${row}`)) : true;
          if (matchesSource && matchesPage && matchesRow) {
            matchedChunk = chunk.split("\n").slice(1).join("\n");
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
  }, []);

  const handleSelectThread = useCallback(async (id: string) => {
    const history = await threads.selectThread(id);
    if (history) {
      chat.setMessages(history);
      chat.setStatus("Conversation loaded.");
    } else {
      chat.setStatus("Failed to load history.");
    }
    return history || [];
  }, [threads, chat]);

  const projectThreads = useMemo(
    () => threads.threads.filter(t => (t.projectId || "default") === projects.activeProjectId),
    [threads.threads, projects.activeProjectId]
  );
  const projectPinned = useMemo(
    () => projectThreads.filter(t => t.pinned),
    [projectThreads]
  );
  const projectRecent = useMemo(
    () => projectThreads.filter(t => !t.pinned).sort((a, b) => b.timestamp - a.timestamp),
    [projectThreads]
  );

  const handleDeleteThread = useCallback((id: string) => {
    threads.deleteThread(id, threads.threadId, chat.setMessages, chat.setStatus, docs.fetchDocuments);
  }, [threads, chat, docs]);

  const handleClearAllThreads = useCallback(() => {
    threads.clearAllThreads(docs.fetchDocuments);
    chat.setMessages([]);
    chat.setStatus("System Standby");
  }, [threads, docs, chat]);

  const handleSendMessage = useCallback((e: React.FormEvent) => {
    const cmd = chat.input.trim().toLowerCase();
    if (cmd === "/clear") {
      e.preventDefault();
      chat.setInput("");
      chat.setMessages([]);
      return;
    }
    if (cmd === "/export") {
      e.preventDefault();
      chat.exportChatMarkdown();
      chat.setInput("");
      return;
    }
    if (cmd === "/settings") {
      e.preventDefault();
      setShowSettings(true);
      chat.setInput("");
      return;
    }
    if (cmd === "/help") {
      e.preventDefault();
      chat.setMessages([{ role: "assistant", content: "**Available commands:**\n- `/clear` — Clear conversation\n- `/export` — Export chat as markdown\n- `/settings` — Open settings\n- `/help` — Show this message" }]);
      chat.setInput("");
      return;
    }
    chat.sendMessage(e, threads.threads, threads.saveThreads);
  }, [chat, threads]);

  const handleTemporalFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    docs.handleTemporalFileUpload(e, threads.threadId);
  }, [docs, threads.threadId]);

  const handleRemoveTemporalFile = useCallback((filename: string) => {
    docs.handleRemoveTemporalFile(filename, threads.threadId);
  }, [docs, threads.threadId]);

  const handleEditMessage = useCallback((idx: number, newContent: string) => {
    chat.setMessages((prev) =>
      prev.map((msg, i) => (i === idx ? { ...msg, content: newContent } : msg))
    );
  }, []);

  useEffect(() => {
    if (auth.token) {
      threads.fetchThreads();
    } else {
      threads.setThreads([]);
    }
  }, [auth.token]);

  useEffect(() => {
    if (auth.token) {
      docs.fetchDocuments();
    }
  }, [auth.token]);

  useEffect(() => {
    if (docs.showDocManager && auth.token) {
      docs.fetchDocuments();
    }
  }, [docs.showDocManager, auth.token]);

  useEffect(() => {
    chat.selectSuggestedPrompts();
  }, [docs.documents, sessionFiles]);

  const pollCountRef = useRef(0);
  useEffect(() => {
    const hasPending = sessionFiles.some(f => f.status === "Pending");
    if (hasPending && auth.token && pollCountRef.current < 30) {
      pollCountRef.current++;
      const timer = setTimeout(() => docs.fetchDocuments(), 2000);
      return () => clearTimeout(timer);
    }
    if (!hasPending) {
      pollCountRef.current = 0;
    }
  }, [sessionFiles, auth.token]);

  useEffect(() => {
    if (!chat.isStreaming && chat.inputRef.current) {
      chat.inputRef.current.focus();
    }
  }, [chat.isStreaming]);

  if (!isMounted) {
    return (
      <div className="relative flex min-h-screen items-center justify-center overflow-hidden select-none">
        <div className="flex flex-col items-center gap-3">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          <span className="text-xs font-medium tracking-wider uppercase text-[var(--text-tertiary)]">Initializing CodexEngine...</span>
        </div>
      </div>
    );
  }

  if (!auth.token) {
    return <LandingPage {...auth} />;
  }

  return (
    <div className="relative flex h-screen overflow-hidden">

      <DocManager
        visible={docs.showDocManager}
        onClose={() => docs.setShowDocManager(false)}
        documents={docs.documents}
        loadingDocs={docs.loadingDocs}
        uploadStatus={docs.uploadStatus}
        onFileUpload={docs.handleFileUpload}
        onReingest={docs.handleReingestDocument}
        onDelete={docs.handleDeleteDocument}
      />

      <Sidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        threadId={threads.threadId}
        setThreadId={threads.setThreadId}
        setMessages={chat.setMessages}
        setStatus={chat.setStatus}
        inputRef={chat.inputRef}
        threads={projectThreads}
        pinnedThreads={projectPinned}
        recentThreads={projectRecent}
        editingThreadId={threads.editingThreadId}
        editTitle={threads.editTitle}
        setEditTitle={threads.setEditTitle}
        setEditingThreadId={threads.setEditingThreadId}
        username={auth.username}
        displayName={settings.displayName}
        onSelectThread={handleSelectThread}
        onTogglePin={threads.togglePin}
        onStartRename={threads.startRename}
        onSaveRename={threads.saveRename}
        onDeleteThread={handleDeleteThread}
        onClearAllThreads={handleClearAllThreads}
        onShowDocManager={() => docs.setShowDocManager(true)}
        onShowSettings={() => setShowSettings(true)}
        onLogout={auth.logout}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        projects={projects.projects}
        activeProjectId={projects.activeProjectId}
        onProjectSelect={projects.setActiveProjectId}
        onCreateProject={projects.createProject}
        onRenameProject={projects.renameProject}
        onDeleteProject={projects.deleteProject}
      />

      {sidebarOpen && (
        <div className="fixed inset-0 z-20 bg-black/60 backdrop-blur-sm md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <main className="relative z-10 flex-1 flex flex-col h-full min-w-0">
        <header className="h-16 border-b border-white/5 flex items-center justify-end px-6 bg-black/10 backdrop-blur-sm shrink-0">
          {chat.messages.length > 0 && (
            <button onClick={chat.exportChatMarkdown} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-white/10 hover:border-white/20 hover:bg-white/5 text-gray-300 hover:text-white transition-all cursor-pointer shadow-sm active:scale-95">
              <Download size={14} />
              <span>Export Chat</span>
            </button>
          )}
        </header>

        {chat.messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center overflow-y-auto p-6">
            {showOnboarding ? (
              <OnboardingBanner onDismiss={handleDismissOnboarding} />
            ) : (
              <EmptyState threadId={threads.threadId} />
            )}
            <QuickPrompts
              prompts={chat.suggestedPrompts}
              onSelect={chat.handleQuickPromptClick}
              onShuffle={chat.selectSuggestedPrompts}
            />
          </div>
        ) : (
          <ChatArea
            messages={chat.messages}
            isStreaming={chat.isStreaming}
            copiedIndex={chat.copiedIndex}
            onCopy={chat.copyToClipboard}
            onCitationClick={handleCitationClick}
            onStopThinking={chat.stopThinking}
            onEditMessage={handleEditMessage}
          />
        )}

        <InputBar
          input={chat.input}
          setInput={chat.setInput}
          isStreaming={chat.isStreaming}
          sessionFiles={sessionFiles}
          uploadingFile={docs.uploadingFile}
          threadId={threads.threadId}
          onSend={handleSendMessage}
          onStopThinking={chat.stopThinking}
          onFileSelect={handleTemporalFileUpload}
          onRemoveFile={handleRemoveTemporalFile}
          inputRef={chat.inputRef}
          fileInputRef={fileInputRef}
        />
      </main>

      <CitationDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        source={selectedSource}
        page={selectedPage}
        row={selectedRow}
        chunk={selectedChunk}
      />
      <SettingsModal
        open={showSettings}
        onClose={() => setShowSettings(false)}
        username={auth.username}
        displayName={settings.displayName}
        systemPrompt={settings.systemPrompt}
        onSaveDisplayName={settings.saveDisplayName}
        onSaveSystemPrompt={settings.saveSystemPrompt}
      />
    </div>
  );
}
