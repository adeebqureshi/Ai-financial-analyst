"use client";

import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  Bot,
  Check,
  Loader2,
  RotateCcw,
  Send,
  Sparkles,
  X,
} from "lucide-react";

import { Markdown } from "@/components/ui/markdown";
import { Button } from "@/components/ui/button";
import { useChatStream, type SendOptions } from "@/hooks/use-chat-stream";
import { cn } from "@/lib/utils";
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

  /**
   * Layout variant. `"research"` renders the panel without its own header (the
   * caller supplies one) and lays the suggestions out as full-width rows.
   * Defaults to the original self-contained panel used by the copilot drawer.
   */
  variant?: "default" | "research";

  /** Whether to list what the assistant can cover in the empty state. */
  showCapabilities?: boolean;

  /** Keyboard hint under the composer; defaults to the full Enter/Shift hint. */
  composerHint?: string;
};

/** Shown in the copilot's empty state to make its remit concrete. */
const capabilities = [
  "Financial performance",
  "Risks & uncertainties",
  "Management commentary",
  "Outlook and guidance",
  "Key financial metrics",
];

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
  variant = "default",
  showCapabilities = true,
  composerHint,
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
  const idBase = "ai-chat-suggestions";

  return (
    <section
      data-testid="ai-chat"
      aria-label="AI financial analyst chat"
      className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-border bg-card shadow-card"
    >
      <header
        className={cn(
          "flex shrink-0 items-center justify-between gap-3 border-b border-border bg-surface/40 px-4 py-3",
          // The research card supplies its own heading, so only the New/Stop
          // controls survive here — right-aligned in a slim bar.
          variant === "research" &&
            "justify-end border-b-0 bg-transparent px-0 py-0"
        )}
      >
        <div className={cn("flex min-w-0 items-center gap-3", variant === "research" && "sr-only")}>
          <span
            className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand text-brand-foreground"
            aria-hidden="true"
          >
            <Bot size={18} />
          </span>
          <div className="min-w-0">
            <h2 className="truncate text-label font-semibold tracking-[-0.01em] text-foreground">
              AI Financial Analyst
            </h2>
            <p className="mt-0.5 flex items-center gap-1.5 truncate text-caption text-muted-foreground">
              {isStreaming ? (
                <>
                  <Loader2
                    size={11}
                    className="motion-safe:animate-spin"
                    aria-hidden="true"
                  />
                  Researching…
                </>
              ) : (
                <>
                  <span className="size-1.5 shrink-0 rounded-full bg-gain" aria-hidden="true" />
                  Research Copilot
                </>
              )}
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
        {/* The empty state uses `my-auto` rather than `justify-center` so it
            stays centred when it fits and top-aligned when it overflows; that
            keeps the heading reachable on short viewports instead of clipping
            it above the scroll area. */}
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-1 flex-col overflow-y-auto py-6 text-center">
            <div className="my-auto flex w-full flex-col items-center gap-2.5">
            {suggestions && suggestions.length > 0 ? (
              <>
                {/* The research card already renders the heading, so the inner
                    icon + title block is only shown in the default variant. */}
                {variant === "default" && (
                  <>
                    <span
                      className="flex size-11 items-center justify-center rounded-xl bg-brand-subtle text-brand ring-1 ring-brand/15"
                      aria-hidden="true"
                    >
                      <Sparkles size={20} />
                    </span>

                    <div className="space-y-1.5">
                      <p className="text-subtitle font-semibold tracking-[-0.01em] text-foreground">
                        {emptyTitle}
                      </p>
                      <p className="mx-auto max-w-md text-caption leading-relaxed text-muted-foreground">
                        {emptyDescription}
                      </p>
                    </div>
                  </>
                )}

                {showCapabilities && (
                  <ul className="w-full max-w-lg space-y-1.5 text-left text-caption text-muted-foreground">
                    {capabilities.map((item) => (
                      <li key={item} className="flex items-center gap-2">
                        <Check
                          size={12}
                          className="shrink-0 text-brand"
                          aria-hidden="true"
                        />
                        {item}
                      </li>
                    ))}
                  </ul>
                )}

                <div className="mt-1 w-full max-w-lg">
                  <p
                    id={`${idBase}-suggestions-label`}
                    className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-subtle-foreground"
                  >
                    Try asking
                  </p>
                  <ul
                    aria-labelledby={`${idBase}-suggestions-label`}
                    className={cn(
                      "grid gap-1.5",
                      variant === "research" ? "max-w-none space-y-2" : "sm:grid-cols-2"
                    )}
                  >
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
                          className={cn(
                            "group flex h-full w-full items-center gap-2 rounded-lg border border-border bg-background px-2.5 py-2 text-left text-caption text-muted-foreground transition-colors hover:border-brand/40 hover:bg-brand-subtle/50 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                            variant === "research" && "px-3.5 py-2.5 text-label"
                          )}
                        >
                          {variant === "default" && (
                            <Sparkles
                              size={12}
                              className="shrink-0 text-brand"
                              aria-hidden="true"
                            />
                          )}
                          <span className="min-w-0 flex-1">{question}</span>
                          <ArrowRight
                            size={14}
                            className="shrink-0 text-subtle-foreground transition-transform duration-150 group-hover:translate-x-0.5"
                            aria-hidden="true"
                          />
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
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
        <footer className="shrink-0 border-t border-border bg-surface/40 p-3">
          <div className="flex items-end gap-2 rounded-xl border border-input bg-background p-1.5 transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20">
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
                className="max-h-44 min-h-[3.5rem] w-full resize-none rounded-lg border-0 bg-transparent px-2.5 py-2 text-body text-foreground outline-none placeholder:text-subtle-foreground focus-visible:outline-none focus-visible:ring-0"
              />
            </label>

            <Button
              type="button"
              variant="primary"
              size="icon"
              onClick={submit}
              disabled={!input.trim() || isStreaming}
              aria-label="Send message"
              className="size-10 rounded-lg"
            >
              {isStreaming ? (
                <Loader2
                  size={18}
                  className="motion-safe:animate-spin"
                  aria-hidden="true"
                />
              ) : (
                <Send size={18} aria-hidden="true" />
              )}
            </Button>
          </div>

          <p className="mt-1.5 px-1 text-caption text-subtle-foreground">
            {composerHint ?? "Enter to send · Shift + Enter for a new line"}
          </p>
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
