"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  ArrowRight,
  Bot,
  Check,
  FileText,
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
   * Layout variant. `"research"` renders the panel without its own chrome (the
   * caller supplies the container) and adopts the Research layout: suggestions
   * become chips above the composer and the send control is a round accent
   * button. Defaults to the original self-contained panel used by the copilot
   * drawer and the analysis chat.
   */
  variant?: "default" | "research";

  /** Whether to list what the assistant can cover in the empty state. */
  showCapabilities?: boolean;

  /** Keyboard hint under the composer; defaults to the full Enter/Shift hint. */
  composerHint?: string;

  /**
   * Research-only header content. When `variant="research"` these drive the
   * panel header so it can reflect live state (streaming, errors, document
   * loading) that lives in this component, without reimplementing a chat.
   */
  headerIcon?: ReactNode;
  headerTitle?: string;
  /** Static suffix rendered after the live status, e.g. "· 1 document". */
  headerMeta?: string;
  /** Parent-owned loading state (e.g. the documents query) for the status dot. */
  statusPending?: boolean;
  /** Parent-owned error state for the status dot. */
  statusError?: boolean;

  /**
   * Research-only control rendered at the bottom-left of the composer (the
   * document scope switcher). Purely presentational — the parent owns the
   * selected-document state.
   */
  scopeControl?: ReactNode;

  /**
   * How many messages may exist before the suggestion chips disappear. Only
   * consulted by the research variant. `0` keeps them for the empty chat only,
   * which is what the reference layout shows.
   */
  suggestionsThreshold?: number;
};

/** Shown in the copilot's empty state to make its remit concrete. */
const capabilities = [
  "Financial performance",
  "Risks & uncertainties",
  "Management commentary",
  "Outlook and guidance",
  "Key financial metrics",
];

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
  headerIcon,
  headerTitle = "AI Research Assistant",
  headerMeta,
  statusPending = false,
  statusError = false,
  scopeControl,
  suggestionsThreshold = 0,
}: Props) {
  const { messages, isStreaming, error, send, retry, cancel, reset, restoreSession } =
    useChatStream({ scope });

  const [input, setInput] = useState("");
  const listRef = useRef<HTMLDivElement>(null);
  const followRef = useRef(true);
  const sentPromptRef = useRef<string | null>(null);
  const restoredSessionRef = useRef<string | null>(null);

  const isResearch = variant === "research";

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

  function ask(question: string) {
    if (isStreaming) return;

    setInput("");
    send(question, { ticker, documentId, asOfDate } satisfies SendOptions);
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
  const hasSuggestions = Boolean(suggestions && suggestions.length > 0);
  const showChips =
    isResearch &&
    hasSuggestions &&
    !isStreaming &&
    messages.length <= suggestionsThreshold;
  const showEmptyState =
    !isResearch &&
    messages.length === 0 &&
    !isStreaming &&
    hasSuggestions;

  return (
    <section
      data-testid="ai-chat"
      aria-label="AI financial analyst chat"
      className={cn(
        "flex min-h-0 flex-1 flex-col overflow-hidden",
        !isResearch &&
          "rounded-xl border border-border bg-card shadow-card"
      )}
    >
      <header
        className={cn(
          "flex shrink-0 items-center justify-between gap-3 border-b border-border bg-surface/40 px-4 py-3"
        )}
      >
        <div className="flex min-w-0 items-center gap-3">
          {isResearch ? (
            <span
              className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-brand-subtle text-brand ring-1 ring-brand/15"
              aria-hidden="true"
            >
              {headerIcon ?? <Sparkles size={18} />}
            </span>
          ) : (
            <span
              className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand text-brand-foreground"
              aria-hidden="true"
            >
              <Bot size={18} />
            </span>
          )}

          <div className="min-w-0">
            <h2 className="truncate text-label font-semibold tracking-[-0.01em] text-foreground">
              {isResearch ? headerTitle : "AI Financial Analyst"}
            </h2>
            <ChatStatusLine
              isResearch={isResearch}
              isStreaming={isStreaming}
              error={error}
              statusPending={statusPending}
              statusError={statusError}
              headerMeta={headerMeta}
            />
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
            {isResearch ? "New chat" : "New"}
          </Button>
        </div>
      </header>

      <div
        ref={listRef}
        onScroll={onScroll}
        className={cn(
          "flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto",
          isResearch ? "px-5 py-5" : "p-4"
        )}
      >
        {/* The empty state uses `my-auto` rather than `justify-center` so it
            stays centred when it fits and top-aligned when it overflows; that
            keeps the heading reachable on short viewports instead of clipping
            it above the scroll area. */}
        {showEmptyState && (
          <div className="flex flex-1 flex-col overflow-y-auto py-6 text-center">
            <div className="my-auto flex w-full flex-col items-center gap-2.5">
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
                <SuggestionList
                  idBase="ai-chat-suggestions"
                  label="Try asking"
                  questions={suggestions ?? []}
                  onPick={ask}
                />
              </div>
            </div>
          </div>
        )}

        {!showEmptyState &&
          messages.length === 0 &&
          !isStreaming &&
          !isResearch && (
            <div className="flex flex-1 flex-col items-center justify-center gap-2 py-6 text-center">
              <p className="text-label font-medium text-foreground">
                Ask a research question
              </p>
              <p className="max-w-xs text-caption text-muted-foreground">
                Grounded in SEC filings, uploaded documents and financial
                statements.
              </p>
            </div>
          )}

        {messages.map((message, index) => (
          <ChatMessageRow
            key={index}
            message={message}
            isStreaming={isStreaming}
            isLast={index === messages.length - 1}
            isResearch={isResearch}
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

      {/* Research keeps suggestions as compact chips pinned above the composer
          so the message area itself stays free for answers. */}
      {showChips && suggestions && (
        <div className="shrink-0 px-5 pb-3">
          <SuggestionList
            idBase="ai-chat-suggestion-chips"
            label="Suggested questions"
            questions={suggestions}
            onPick={ask}
            variant="chips"
          />
        </div>
      )}

      {!readOnly && (
        <footer
          className={cn(
            "shrink-0 border-t border-border bg-surface/40",
            isResearch ? "px-5 pb-4 pt-3.5" : "p-3"
          )}
        >
          <div
            className={cn(
              "flex items-end gap-2 border border-input bg-background transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20",
              isResearch
                ? "flex-col items-stretch rounded-2xl p-2"
                : "rounded-xl p-1.5"
            )}
          >
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
                className={cn(
                  "max-h-44 w-full resize-none border-0 bg-transparent text-body text-foreground outline-none placeholder:text-subtle-foreground focus-visible:outline-none focus-visible:ring-0",
                  isResearch
                    ? "min-h-[3.25rem] rounded-xl px-2.5 py-1.5"
                    : "min-h-[3.5rem] rounded-lg px-2.5 py-2"
                )}
              />
            </label>

            {isResearch ? (
              <div className="flex items-center justify-between gap-2 px-0.5 pb-0.5">
                <div className="flex min-w-0 items-center gap-1.5">
                  {scopeControl}
                </div>

                <Button
                  type="button"
                  variant="primary"
                  size="icon"
                  onClick={submit}
                  disabled={!input.trim() || isStreaming}
                  aria-label="Send message"
                  className="size-10 rounded-full"
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
            ) : (
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
            )}
          </div>

          <p className="mt-2 px-1 text-caption text-subtle-foreground">
            {composerHint ?? "Enter to send · Shift + Enter for a new line"}
          </p>
        </footer>
      )}
    </section>
  );
}

/**
 * Live service state. Deliberately derived from real state — the streaming
 * flag, the stream error, and the caller's document query — so the header never
 * claims "Ready" while work is in flight.
 */
function ChatStatusLine({
  isResearch,
  isStreaming,
  error,
  statusPending,
  statusError,
  headerMeta,
}: {
  isResearch: boolean;
  isStreaming: boolean;
  error: string | null;
  statusPending: boolean;
  statusError: boolean;
  headerMeta?: string;
}) {
  let dot: ReactNode;
  let label: string;

  if (isStreaming) {
    dot = (
      <Loader2
        size={11}
        className="shrink-0 motion-safe:animate-spin"
        aria-hidden="true"
      />
    );
    label = "Searching";
  } else if (error || statusError) {
    dot = <span className="size-1.5 shrink-0 rounded-full bg-loss" aria-hidden="true" />;
    label = "Error";
  } else if (statusPending) {
    dot = (
      <span
        className="size-1.5 shrink-0 animate-pulse rounded-full bg-muted-foreground"
        aria-hidden="true"
      />
    );
    label = "Checking";
  } else {
    dot = <span className="size-1.5 shrink-0 rounded-full bg-gain" aria-hidden="true" />;
    label = "Ready";
  }

  return (
    <p
      className="mt-0.5 flex items-center gap-1.5 truncate text-caption text-muted-foreground"
      role="status"
      aria-live="polite"
    >
      {dot}
      {label}
      {isResearch && headerMeta ? (
        <span className="tnum truncate">{headerMeta}</span>
      ) : null}
    </p>
  );
}

function SuggestionList({
  idBase,
  label,
  questions,
  onPick,
  variant = "rows",
}: {
  idBase: string;
  label: string;
  questions: string[];
  onPick: (question: string) => void;
  variant?: "rows" | "chips";
}) {
  const chips = variant === "chips";

  return (
    <div>
      <p
        id={`${idBase}-suggestions-label`}
        className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-subtle-foreground"
      >
        {label}
      </p>

      <ul
        aria-labelledby={`${idBase}-suggestions-label`}
        className={cn(chips ? "flex flex-wrap gap-1.5" : "grid gap-1.5 sm:grid-cols-2")}
      >
        {questions.map((question) => (
          <li key={question} className={cn(chips && "max-w-full")}>
            <button
              type="button"
              onClick={() => onPick(question)}
              className={cn(
                "group flex w-full items-center gap-2 rounded-lg border border-border bg-background text-left text-caption text-muted-foreground transition-colors hover:border-brand/40 hover:bg-brand-subtle/50 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                chips ? "rounded-full px-3 py-1.5" : "h-full px-3 py-2.5"
              )}
            >
              {!chips && (
                <Sparkles
                  size={12}
                  className="shrink-0 text-brand"
                  aria-hidden="true"
                />
              )}
              <span className="min-w-0 flex-1">{question}</span>
              {!chips && (
                <ArrowRight
                  size={14}
                  className="shrink-0 text-subtle-foreground transition-transform duration-150 group-hover:translate-x-0.5"
                  aria-hidden="true"
                />
              )}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

type RowProps = {
  message: ReturnType<typeof useChatStream>["messages"][number];
  isStreaming: boolean;
  isLast: boolean;
  isResearch: boolean;
};

function ChatMessageRow({ message, isStreaming, isLast, isResearch }: RowProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div
          className={cn(
            "whitespace-pre-wrap bg-primary text-label text-primary-foreground",
            isResearch
              ? "max-w-[85%] rounded-2xl rounded-tr-md px-3.5 py-2.5"
              : "rounded-xl rounded-tr-sm px-4 py-3"
          )}
        >
          {message.content}
        </div>
      </div>
    );
  }

  const waiting =
    isStreaming && isLast && !message.content && !message.error;

  return (
    <div className="flex justify-start">
      <div className={cn("flex gap-2.5", isResearch ? "w-full" : "max-w-[85%]")}>
        {!isResearch && (
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-brand text-brand-foreground">
            <Bot size={14} aria-hidden="true" />
          </div>
        )}

        <div
          className={cn(
            "min-w-0 flex-1",
            isResearch
              ? "rounded-2xl rounded-tl-md bg-surface px-4 py-3 text-body text-foreground"
              : "rounded-xl rounded-tl-sm border border-border bg-surface px-4 py-3"
          )}
        >
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

          {/* Citations stay small chips directly under the answer. Internal
              execution detail (plan, tools, retrieval steps) is deliberately
              absent — it is server-side implementation detail. */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-subtle-foreground">
                Sources
              </p>
              <ul className="mt-1.5 flex flex-wrap gap-1.5">
                {message.sources.map((source, sourceIndex) => (
                  <li key={sourceIndex}>
                    <span
                      title={source.filename}
                      className="inline-flex max-w-full items-center gap-1 rounded-md border border-border bg-card px-1.5 py-0.5 text-[11px] text-muted-foreground"
                    >
                      <FileText
                        size={10}
                        className="shrink-0 text-subtle-foreground"
                        aria-hidden="true"
                      />
                      <span className="truncate">{source.filename}</span>
                      {source.page != null && (
                        <span className="tnum shrink-0 text-subtle-foreground">
                          · p. {source.page}
                        </span>
                      )}
                    </span>
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