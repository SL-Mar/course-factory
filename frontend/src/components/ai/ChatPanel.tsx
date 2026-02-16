import { useState, useRef, useEffect, useCallback } from "react";
import type { ChatMessage } from "../../types";
import { sendChatMessage } from "../../api/ai";
import { MarkdownRenderer } from "../editor/MarkdownRenderer";

interface ChatPanelProps {
  activePageId?: string;
  activePageContent?: string;
}

export function ChatPanel({
  activePageId,
  activePageContent,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMessage: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage({
        message: text,
        include_context: true,
      });
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.response,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to send message";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <div className="h-full flex flex-col bg-content">
      {/* Header */}
      <div className="px-6 pt-6 pb-3 flex items-center justify-between border-b border-content-border">
        <div>
          <h1 className="text-xl font-bold text-content-text">AI Chat</h1>
          <p className="text-xs text-content-muted mt-0.5">
            Ask questions about your knowledge base
            {activePageId && " (page context active)"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {activePageId && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-accent/10 text-accent-light">
              Page context
            </span>
          )}
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="px-3 py-1.5 text-xs text-content-muted hover:text-content-text border border-content-border rounded-md hover:bg-content-tertiary transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-sm">
              <div className="text-4xl mb-4 opacity-30">{"\u269B"}</div>
              <h3 className="text-sm font-medium text-content-muted mb-2">
                Start a conversation
              </h3>
              <p className="text-xs text-content-faint mb-4">
                Ask about your pages, request summaries, generate content, or
                explore your knowledge graph.
              </p>
              <div className="space-y-2">
                {[
                  "Summarize my recent notes",
                  "What topics are most connected?",
                  "Help me write about...",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setInput(suggestion)}
                    className="block w-full px-3 py-2 text-xs text-left text-content-muted border border-content-border rounded-md hover:border-accent hover:text-accent-light hover:bg-content-tertiary transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-4 flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            } animate-fade-in`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                msg.role === "user"
                  ? "bg-accent text-white"
                  : "bg-content-secondary border border-content-border text-content-text"
              }`}
            >
              {msg.role === "assistant" ? (
                <div className="text-sm">
                  <MarkdownRenderer content={msg.content} />
                </div>
              ) : (
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start mb-4 animate-fade-in">
            <div className="bg-content-secondary border border-content-border rounded-lg px-4 py-3">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-content-muted animate-bounce" />
                <div
                  className="w-2 h-2 rounded-full bg-content-muted animate-bounce"
                  style={{ animationDelay: "0.1s" }}
                />
                <div
                  className="w-2 h-2 rounded-full bg-content-muted animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-4 px-4 py-3 bg-red-900/20 border border-red-800/40 rounded-lg text-sm text-red-400 animate-fade-in">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-content-border bg-content-secondary">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything... (Enter to send, Shift+Enter for newline)"
              rows={1}
              className="w-full px-4 py-2.5 text-sm border border-content-border rounded-lg bg-content text-content-text placeholder-content-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent resize-none min-h-[40px] max-h-[120px]"
              style={{
                height: "auto",
                minHeight: "40px",
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = "auto";
                target.style.height =
                  Math.min(target.scrollHeight, 120) + "px";
              }}
              disabled={loading}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="px-4 py-2.5 bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M14 2L2 8l4 2m8-8l-6 12-2-4m8-8l-8 8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
