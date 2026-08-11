"use client";

import { useRef, useState } from "react";
import { Bot, Loader2, Send, Sparkles, User } from "lucide-react";

import { api } from "@/services/api";

import type { ChatData } from "@/types/analysis";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type Props = {
  ticker: string;
};

export function AIChat({ ticker }: Props) {
  // A stable per-widget session id lets the backend resolve follow-ups like
  // "what about its valuation?" against the previous turn's company. It is
  // generated lazily on first send (an event handler, not render).
  const sessionIdRef = useRef<string | null>(null);

  function getSessionId(): string {
    if (sessionIdRef.current === null) {
      sessionIdRef.current = `chat-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    }

    return sessionIdRef.current;
  }

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  async function send() {
    const text = input.trim();

    if (!text || sending) return;

    const userMessage: Message = {
      role: "user",
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSending(true);

    try {
      const response = await api.chat({
        message: text,
        ticker,
        session_id: getSessionId(),
      });

      const reply =
        (response as unknown as {
          data?: ChatData | null;
        }).data?.message ??
        "No response generated.";

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: reply,
        },
      ]);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again.";

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${message}`,
        },
      ]);
    } finally {
      setSending(false);

      requestAnimationFrame(() => {
        listRef.current?.scrollTo({
          top: listRef.current.scrollHeight,
          behavior: "smooth",
        });
      });
    }
  }

  return (
    <section className="rounded-[36px] border border-white/10 bg-white/[0.03] backdrop-blur-xl">

      <div className="flex items-center justify-between border-b border-white/10 p-6">

        <div className="flex items-center gap-3">

          <div className="rounded-2xl bg-blue-500/10 p-3">
            <Sparkles
              size={20}
              className="text-blue-400"
            />
          </div>

          <div>

            <h2 className="text-xl font-bold text-white">
              Ask AI Assistant
            </h2>

            <p className="mt-1 text-sm text-zinc-500">
              Ask questions about {ticker}
            </p>

          </div>

        </div>

      </div>

      <div
        ref={listRef}
        className="flex max-h-[420px] min-h-[240px] flex-col gap-4 overflow-y-auto p-6"
      >

        {messages.length === 0 && (

          <div className="m-auto max-w-sm text-center">

            <Bot
              size={40}
              className="mx-auto text-zinc-600"
            />

            <p className="mt-4 text-sm leading-6 text-zinc-500">
              Ask me anything about {ticker} —
              valuation, financials, risk or
              investment outlook.
            </p>

          </div>

        )}

        {messages.map((message, index) => {

          const isUser = message.role === "user";

          return (
            <div
              key={index}
              className={`flex ${
                isUser
                  ? "justify-end"
                  : "justify-start"
              }`}
            >

              <div
                className={`flex max-w-[85%] gap-3 ${
                  isUser
                    ? "flex-row-reverse"
                    : ""
                }`}
              >

                <div
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl ${
                    isUser
                      ? "bg-emerald-500/10"
                      : "bg-blue-500/10"
                  }`}
                >
                  {isUser ? (
                    <User
                      size={16}
                      className="text-emerald-400"
                    />
                  ) : (
                    <Bot
                      size={16}
                      className="text-blue-400"
                    />
                  )}
                </div>

                <div
                  className={`whitespace-pre-wrap rounded-3xl px-5 py-4 text-sm leading-6 ${
                    isUser
                      ? "rounded-tr-sm bg-blue-600 text-white"
                      : "rounded-tl-sm bg-white/5 text-zinc-300"
                  }`}
                >
                  {message.content}
                </div>

              </div>

            </div>
          );
        })}

        {sending && (

          <div className="flex justify-start">

            <div className="flex items-center gap-3 rounded-3xl rounded-tl-sm bg-white/5 px-5 py-4 text-sm text-zinc-400">

              <Loader2
                size={16}
                className="animate-spin text-blue-400"
              />

              AI is thinking...

            </div>

          </div>

        )}

      </div>

      <div className="flex items-center gap-3 border-t border-white/10 p-4">

        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder={`Ask about ${ticker}...`}
          className="flex-1 rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-sm text-white outline-none placeholder:text-zinc-500 focus:border-blue-500/40"
        />

        <button
          onClick={send}
          disabled={sending || !input.trim()}
          className="rounded-2xl bg-blue-600 p-4 text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {sending ? (
            <Loader2
              size={18}
              className="animate-spin"
            />
          ) : (
            <Send size={18} />
          )}
        </button>

      </div>

    </section>
  );
}
