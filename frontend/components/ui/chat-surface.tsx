"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUpRight, Bot, Loader2, RotateCcw, Send, Sparkles, X } from "lucide-react";

import { Markdown } from "@/components/ui/markdown";
import { Button } from "@/components/ui/button";
import { useChatStream, type SendOptions } from "@/hooks/use-chat-stream";
import type { AgentToolExecution } from "@/types/analysis";

type Props = {

  scope?: string;

  ticker?: string;

  documentId?: string;

  asOfDate?: string;

  inputLabel?: string;

  placeholder?: string;

  autoPrompt?: string | null;
  /**
   * Optional example questions rendered in the empty state. Clicking one sends
   * it through the same `send()` path the composer uses. Omit to keep the
   * original minimal empty state.
   */
  suggestions?: string[];
  /** Title/description for the empty state when suggestions are supplied. */
  emptyTitle?: string;
  emptyDescription?: string;

  sessionId?: string | null;

  readOnly?: boolean;
};

const toolStatusTone: Record<AgentToolExecution["status"], string> = {
  done: "text-gain",
  running: "text-brand",
  error: "text-loss",
  skipped: "text-muted-foreground",
};


export function ChatSurface({
  scope = "default",
  ticker,
  documentId,
  asOfDate,
  inputLabel = "Message the AI financial analyst",
  placeholder = "Ask a research question…",
  autoPrompt = null,
  suggestions,
  emptyTitle = "Ask about your documents",
  emptyDescription = "Ask questions about financial filings, management commentary, performance, risks, or other indexed research.",
  sessionId = null,
  readOnly = false,
}: Props) {
  const { messages, isStreaming, error, send, retry, cancel, reset, restoreSession } =
    useChatStream({ scope });

  const [input, setInput] = useState("");
  const listRef = useRef<HTMLDivElement>(null);
  const followRef = useRef(true);
  const sentPromptRef = useRef<string | null>(null);
  const restoredSessionRef = useRef<string | null>(null);


  useEffect(() => {
    if (!listRef.current || !followRef.current) return;
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages]);

  function onScroll() {
    const el = listRef.current;

    if (!el) return;
    followRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 48;
  }

  function submit() {
    const text = input.trim();

    if (!text || isStreaming) return;

    send(text, { ticker, documentId, asOfDate } satisfies SendOptions);
    setInput("");
  }

  useEffect(() => {
    const prompt = autoPrompt?.trim();

    if (!prompt || isStreaming) return;
    if (sentPromptRef.current === prompt) return;

    sentPromptRef.current = prompt;
    send(prompt, { ticker, documentId, asOfDate } satisfies SendOptions);
  }, [asOfDate, autoPrompt, documentId, isStreaming, send, ticker]);

  useEffect(() => {
    const target = sessionId?.trim();

    if (!target || isStreaming) return;
    if (restoredSessionRef.current === target) return;

    restoredSessionRef.current = target;
    void restoreSession(target);
  }, [isStreaming, restoreSession, sessionId]);

  const canRetry = Boolean(error) && !isStreaming;

  return (
    <section
      data-testid="ai-chat"
      aria-label="AI financial analyst chat"
      className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-border bg-card shadow-card"
    >
      <header className="flex shrink-0 items-center justify-between gap-2 border-b border-border px-4 py-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-brand text-brand-foreground">
            <Bot size={17} aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <h2 className="truncate text-label font-semibold text-foreground">
              AI Financial Analyst
            </h2>
            <p className="truncate text-caption text-muted-foreground">
              {isStreaming ? "Researching…" : "Research assistant"}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-1">
          {isStreaming && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={cancel}
              aria-label="Stop generating"
            >
              <X size={15} aria-hidden="true" />
              Stop
            </Button>
          )}

          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={reset}
            aria-label="Start a new chat session"
          >
            <RotateCcw size={15} aria-hidden="true" />
            New
          </Button>
        </div>
      </header>

      <div
        ref={listRef}
        onScroll={onScroll}
        className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4"
      >
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-1 flex-col items-center justify-center gap-2.5 py-6 text-center">
            {suggestions && suggestions.length > 0 ? (
              <>
                <span
                  className="flex size-10 items-center justify-center rounded-xl bg-brand-subtle text-brand"
                  aria-hidden="true"
                >
                  <Sparkles size={18} />
                </span>
                <p className="text-label font-semibold text-foreground">
                  {emptyTitle}
                </p>
                <p className="max-w-sm text-caption leading-relaxed text-muted-foreground">
                  {emptyDescription}
                </p>
                <ul className="mt-1.5 grid w-full max-w-md gap-1.5">
                  {suggestions.map((question) => (
                    <li key={question}>
                      <button
                        type="button"
                        onClick={() => {
                          if (isStreaming) return;
                          setInput("");
                          send(question, {
                            ticker,
                            documentId,
                            asOfDate,
                          } satisfies SendOptions);
                        }}
                        className="group flex w-full items-center gap-2 rounded-lg border border-border bg-background px-3 py-1.5 text-left text-caption text-muted-foreground transition-colors hover:border-border-strong hover:bg-surface hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        <Sparkles
                          size={13}
                          className="shrink-0 text-brand"
                          aria-hidden="true"
                        />
                        <span className="min-w-0 flex-1">{question}</span>
                        <ArrowUpRight
                          size={13}
                          className="shrink-0 text-subtle-foreground transition-transform duration-150 group-hover:-translate-y-0.5 group-hover:translate-x-0.5"
                          aria-hidden="true"
                        />
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <>
                <p className="text-label font-medium text-foreground">
                  Ask a research question
                </p>
                <p className="max-w-xs text-caption text-muted-foreground">
                  Grounded in SEC filings, uploaded documents and financial
                  statements.
                </p>
              </>
            )}
          </div>
        )}

        {messages.map((message, index) => (
          <ChatMessageRow
            key={index}
            message={message}
            isStreaming={isStreaming}
            isLast={index === messages.length - 1}
          />
        ))}
      </div>

      {canRetry && (
        <div className="shrink-0 border-t border-border px-4 py-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => retry()}
            aria-label="Retry the last message"
          >
            <RotateCcw size={14} aria-hidden="true" />
            Retry
          </Button>
        </div>
      )}

      {!readOnly && (
        <footer className="shrink-0 border-t border-border p-3">
          <div className="flex items-end gap-2">
            <label className="min-w-0 flex-1">
              <span className="sr-only">{inputLabel}</span>
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    submit();
                  }
                }}
                rows={2}
                placeholder={placeholder}
                aria-label={inputLabel}
                className="max-h-40 min-h-[3.25rem] w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-label text-foreground placeholder:text-subtle-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>

            <Button
              type="button"
              variant="primary"
              size="icon"
              onClick={submit}
              disabled={!input.trim() || isStreaming}
              aria-label="Send message"
            >
              {isStreaming ? (
                <Loader2
                  size={17}
                  className="motion-safe:animate-spin"
                  aria-hidden="true"
                />
              ) : (
                <Send size={17} aria-hidden="true" />
              )}
            </Button>
          </div>
        </footer>
      )}
    </section>
  );
}
type RowProps = {
  message: ReturnType<typeof useChatStream>["messages"][number];
  isStreaming: boolean;
  isLast: boolean;
};

function ChatMessageRow({ message, isStreaming, isLast }: RowProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="whitespace-pre-wrap rounded-xl rounded-tr-sm bg-primary px-4 py-3 text-label text-primary-foreground">
          {message.content}
        </div>
      </div>
    );
  }

  const waiting =
    isStreaming && isLast && !message.content && !message.error;

  return (
    <div className="flex justify-start">
      <div className="flex max-w-[85%] gap-2.5">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-brand text-brand-foreground">
          <Bot size={14} aria-hidden="true" />
        </div>

        <div className="min-w-0 flex-1 rounded-xl rounded-tl-sm border border-border bg-surface px-4 py-3">
          {message.content ? (
            <Markdown>{message.content}</Markdown>
          ) : waiting ? (
            <p className="inline-flex items-center gap-2 text-caption text-muted-foreground">
              <Loader2
                size={13}
                className="motion-safe:animate-spin"
                aria-hidden="true"
              />
              Researching…
            </p>
          ) : null}

          {message.error && (
            <div
              role="alert"
              className="mt-2 rounded-md border border-loss/25 bg-loss-subtle px-3 py-2 text-caption text-loss"
            >
              <p className="font-medium">Generation failed</p>
              <p className="mt-0.5">{message.error}</p>
              {message.content && (
                <p className="mt-1 text-muted-foreground">
                  Partial response preserved above.
                </p>
              )}
            </div>
          )}

          {message.sources && message.sources.length > 0 && (
            <div className="mt-3 border-t border-border pt-2">
              <p className="text-caption font-medium text-muted-foreground">
                Sources
              </p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {message.sources.map((source, sourceIndex) => (
                  <span
                    key={sourceIndex}
                    className="inline-flex items-center gap-1 rounded-full border border-border bg-muted px-2 py-0.5 text-[11px] text-muted-foreground"
                  >
                    {source.filename}
                    {source.page != null && ` · p.${source.page}`}
                  </span>
                ))}
              </div>
            </div>
          )}

          {message.plan && message.plan.length > 0 && (
            <div className="mt-3 border-t border-border pt-2">
              <p className="text-caption font-medium text-muted-foreground">
                Research plan
              </p>
              <ol className="mt-1.5 space-y-1">
                {message.plan.map((step, stepIndex) => (
                  <li
                    key={stepIndex}
                    className="text-caption text-muted-foreground"
                  >
                    {stepIndex + 1}. {step}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {message.tools_used && message.tools_used.length > 0 && (
            <div className="mt-3 border-t border-border pt-2">
              <p className="text-caption font-medium text-muted-foreground">
                Tools used
              </p>
              <ul className="mt-1.5 space-y-1">
                {message.tools_used.map((tool, toolIndex) => (
                  <li
                    key={toolIndex}
                    className="text-caption text-muted-foreground"
                  >
                    <span
                      className={`font-medium ${toolStatusTone[tool.status]}`}
                    >
                      {tool.tool}
                    </span>
                    {tool.detail && ` — ${tool.detail}`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
