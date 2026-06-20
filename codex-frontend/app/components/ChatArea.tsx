"use client";

import { useEffect, useRef } from "react";
import type { Message } from "../lib/types";
import MessageBubble from "./MessageBubble";

interface ChatAreaProps {
  messages: Message[];
  isStreaming: boolean;
  copiedIndex: number | null;
  onCopy: (text: string, idx: number) => void;
  onCitationClick: (href: string, context: string) => void;
  onStopThinking: () => void;
}

export default function ChatArea({ messages, isStreaming, copiedIndex, onCopy, onCitationClick, onStopThinking }: ChatAreaProps) {
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-[var(--border-default)] hover:[&::-webkit-scrollbar-thumb]:bg-[var(--border-hover)] [&::-webkit-scrollbar-thumb]:rounded-full">
      <div className="max-w-4xl mx-auto space-y-6">
        {messages.map((msg, idx) => (
          <MessageBubble
            key={idx}
            msg={msg}
            idx={idx}
            isStreaming={isStreaming}
            copiedIndex={copiedIndex}
            onCopy={onCopy}
            onCitationClick={onCitationClick}
            onStopThinking={onStopThinking}
          />
        ))}
      </div>
      <div ref={chatEndRef} />
    </div>
  );
}
