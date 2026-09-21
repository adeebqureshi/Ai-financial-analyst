"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  api,
  type ChatStreamDoneData,
  type ChatStreamPlanData,
} from "@/services/api";
import type { AgentToolExecution, DocumentCitation } from "@/types/analysis";

export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  role: ChatRole;
  content: string;
  /** Present only when the backend actually returned these values. */
  model?: string | null;
  ticker?: string | null;
  sources?: DocumentCitation[];
  plan?: string[];
  tools_used?: AgentToolExecution[];
  /** Set when the turn ended in an error; partial content is preserved. */
  error?: string | null;
};

export type SendOptions = {
  /** Optional ticker context forwarded to the backend verbatim. */
  ticker?: string;
  /** Optional uploaded-document scope forwarded to the backend verbatim. */
  documentId?: string;
  /**
   * Optional historical date (YYYY-MM-DD) forwarded to the backend verbatim.
   * The hook never invents a value; it only forwards what the caller provides.
   */
  asOfDate?: string;
};

type Props = {
  /** Stable storage scope so concurrent surfaces keep separate sessions. */
  scope?: string;
};

const SESSION_PREFIX = "afa-chat-session";

function storageKey(scope: string) {
  return `${SESSION_PREFIX}-${scope}`;
}

function newSessionId() {
  return `chat-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export function useChatStream({ scope = "default" }: Props = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sessionIdRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const lastInputRef = useRef<string | null>(null);
  const lastOptionsRef = useRef<SendOptions>({});
  const revisionRef = useRef(0);
  /**
   * Resolve (or lazily create) the session id. Generation happens in event
   * handlers only, never during render.
   */
  const ensureSessionId = useCallback((): string => {
    if (sessionIdRef.current === null) {
      sessionIdRef.current = newSessionId();
      setSessionId(sessionIdRef.current);
      try {
        window.localStorage.setItem(storageKey(scope), sessionIdRef.current);
      } catch {
        // Storage is best-effort; the in-memory id still works.
      }
    }
    return sessionIdRef.current;
  }, [scope]);

  const runTurn = useCallback(
    async (input: string, opts: SendOptions) => {
      abortRef.current?.abort();

      const controller = new AbortController();
      abortRef.current = controller;
      revisionRef.current += 1;
      const isCurrent = () =>
        abortRef.current === controller && !controller.signal.aborted;

      setError(null);
      setIsStreaming(true);

      // The assistant bubble starts empty and accumulates streamed tokens,
      // so an interrupted stream keeps whatever partial text arrived.
      const partial: ChatMessage = {
        role: "assistant",
        content: "",
        error: null,
      };

      setMessages((prev) => [
        ...prev,
        { role: "user", content: input },
        partial,
      ]);

      try {
        await api.chatStream(
          {
            message: input,
            session_id: ensureSessionId(),
            ...(opts.ticker ? { ticker: opts.ticker } : {}),
            ...(opts.documentId ? { document_id: opts.documentId } : {}),
            ...(opts.asOfDate ? { as_of_date: opts.asOfDate } : {}),
          },
          {
            onPlan: (data: ChatStreamPlanData) => {
              if (!isCurrent()) return;
              if (data.steps?.length) partial.plan = data.steps;
              if (data.tools_used?.length) {
                partial.tools_used = data.tools_used;
              }
              if (data.tickers?.length && !partial.ticker) {
                partial.ticker = data.tickers[0];
              }
              setMessages((prev) => {
                const next = [...prev];
                next[next.length - 1] = { ...partial };
                return next;
              });
            },
            onDelta: (delta) => {
              if (!isCurrent()) return;
              partial.content += delta;
              setMessages((prev) => {
                const next = [...prev];
                next[next.length - 1] = { ...partial };
                return next;
              });
            },
            onDone: (data: ChatStreamDoneData) => {
              if (!isCurrent()) return;
              // Only trust what the backend returned; keep the streamed
              // partial when the done frame carries no final message.
              partial.content = data.message || partial.content;
              partial.model = data.model ?? null;
              partial.ticker =
                partial.ticker ??
                (data.tickers?.length ? data.tickers[0] : null);
              partial.sources = data.sources ?? undefined;
              if (data.steps?.length) partial.plan = data.steps;
              if (data.tools_used?.length) partial.tools_used = data.tools_used;
              setMessages((prev) => {
                const next = [...prev];
                next[next.length - 1] = { ...partial };
                return next;
              });
            },
            onError: (message) => {
              if (!isCurrent()) return;
              // Preserve the partial content and surface the error inline.
              partial.error = message;
              setError(message);
              setMessages((prev) => {
                const next = [...prev];
                next[next.length - 1] = { ...partial };
                return next;
              });
            },
          },
          controller.signal
        );
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          // Cancelled by the user: keep the partial content as-is.
        } else {
          const message =
            err instanceof Error
              ? err.message
              : "Something went wrong while researching your question. Please try again.";
          partial.error = message;
          setError(message);
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = { ...partial };
            return next;
          });
        }
      } finally {
        // Only the latest turn may clear the streaming flag; a superseded
        // request's finally must not end a newer in-flight stream.
        if (abortRef.current === controller) {
          abortRef.current = null;
          setIsStreaming(false);
        }
      }
    },
    [ensureSessionId]
  );

  const send = useCallback(
    (input: string, opts: SendOptions = {}) => {
      const trimmed = input.trim();

      if (!trimmed || isStreaming) return;

      lastInputRef.current = trimmed;
      lastOptionsRef.current = opts;
      void runTurn(trimmed, opts);
    },
    [isStreaming, runTurn]
  );

  /** Retry the last user message with its original options. */
  const retry = useCallback(
    (opts: SendOptions = {}) => {
      if (isStreaming || lastInputRef.current === null) return;
      void runTurn(
        lastInputRef.current,
        Object.keys(opts).length ? opts : lastOptionsRef.current
      );
    },
    [isStreaming, runTurn]
  );

  /** Abort the in-flight stream; partial content is preserved. */
  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  /** Start a fresh session; any in-flight stream is cancelled. */
  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    lastInputRef.current = null;
    sessionIdRef.current = null;
    setSessionId(null);
    setError(null);
    setMessages([]);
    try {
      window.localStorage.removeItem(storageKey(scope));
    } catch {
      // Best-effort only.
    }
  }, [scope]);

  /**
   * Restore a previously persisted session using the real endpoints:
   * `GET /chat/sessions` confirms ownership, then
   * `GET /chat/sessions/{id}/messages` loads the transcript. A stored id
   * that no longer exists (or belongs to nobody) is forgotten silently.
   */
  const restoreSession = useCallback(
    async (storedId?: string | null) => {
      if (isStreaming) return;

      let candidate = storedId ?? null;

      if (!candidate) {
        try {
          candidate = window.localStorage.getItem(storageKey(scope));
        } catch {
          return;
        }
      }

      if (!candidate) return;

      try {
        const listed = await api.listChatSessions();
        const exists =
          (listed?.data?.sessions ?? []).some(
            (session) => session.session_id === candidate
          ) ?? false;

        if (!exists) {
          // Stale id: forget it so the next send starts a fresh session.
          try {
            window.localStorage.removeItem(storageKey(scope));
          } catch {
            // Best-effort only.
          }
          return;
        }

        const history = await api.listChatSessionMessages(candidate);
        const rows = history?.data?.messages ?? [];

        sessionIdRef.current = candidate;
        setSessionId(candidate);
        setMessages(
          rows.map((row) => ({
            role: row.role,
            content: row.content,
          }))
        );
        setError(null);
      } catch {
        // History is unavailable (e.g. backend down); start empty rather
        // than inventing a transcript.
      }
    },
    [isStreaming, scope]
  );

  // Restore the persisted session once on mount; abort on unmount.
  const mountedRef = useRef(false);
  useEffect(() => {
    if (mountedRef.current) return;
    mountedRef.current = true;
    void restoreSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  return {
    messages,
    isStreaming,
    error,
    sessionId,
    send,
    retry,
    cancel,
    reset,
    restoreSession,
  };
}
