"use client";

import React, { useState, useRef, useEffect } from "react";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import {
  useChatRuntime,
  AssistantChatTransport,
} from "@assistant-ui/react-ai-sdk";
import { Thread } from "@/components/assistant-ui/thread";
import { MessageCircle, X, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import { AssistantCloud } from "assistant-cloud";

export const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const cloud = React.useMemo(() => {
    if (
      process.env.NEXT_PUBLIC_ASSISTANT_BASE_URL &&
      process.env.NEXT_PUBLIC_ASSISTANT_API_KEY &&
      process.env.NEXT_PUBLIC_ASSISTANT_WORKSPACE_ID
    ) {
      return new AssistantCloud({
        baseUrl: process.env.NEXT_PUBLIC_ASSISTANT_BASE_URL,
        apiKey: process.env.NEXT_PUBLIC_ASSISTANT_API_KEY,
        workspaceId: process.env.NEXT_PUBLIC_ASSISTANT_WORKSPACE_ID,
        userId: "default-user",
      });
    }
    return undefined;
  }, []);

  const runtime = useChatRuntime({
    transport: new AssistantChatTransport({
      api: "/api/chat",
    }),
    cloud: cloud,
  });

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {/* Chat Panel */}
      <div
        ref={panelRef}
        className={cn(
          "fixed bottom-24 right-6 z-50 flex flex-col overflow-hidden rounded-2xl border border-border bg-background shadow-2xl transition-all duration-300 ease-in-out",
          isOpen
            ? "pointer-events-auto h-[min(600px,80dvh)] w-[min(420px,calc(100vw-2rem))] scale-100 opacity-100"
            : "pointer-events-none h-0 w-0 scale-90 opacity-0"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b bg-primary px-4 py-3 text-primary-foreground">
          <div className="flex items-center gap-2">
            <MessageCircle className="size-5" />
            <span className="font-semibold text-sm">i95Dev Assistant</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsOpen(false)}
              className="rounded-md p-1 transition-colors hover:bg-primary-foreground/20"
              aria-label="Minimize chat"
            >
              <Minus className="size-4" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="rounded-md p-1 transition-colors hover:bg-primary-foreground/20"
              aria-label="Close chat"
            >
              <X className="size-4" />
            </button>
          </div>
        </div>

        {/* Thread Body */}
        <div className="flex-1 overflow-hidden">
          <Thread />
        </div>
      </div>

      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className={cn(
          "fixed bottom-6 right-6 z-50 flex size-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          isOpen && "rotate-0"
        )}
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        <div className="relative flex items-center justify-center">
          <MessageCircle
            className={cn(
              "size-6 transition-all duration-300",
              isOpen ? "scale-0 opacity-0" : "scale-100 opacity-100"
            )}
          />
          <X
            className={cn(
              "absolute size-6 transition-all duration-300",
              isOpen ? "scale-100 opacity-100" : "scale-0 opacity-0"
            )}
          />
        </div>
      </button>
    </AssistantRuntimeProvider>
  );
};
