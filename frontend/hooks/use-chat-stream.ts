"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  api,
  type ChatStreamDoneData,
  type ChatStreamPlanData,
} from "@/services/api";
import type { DocumentCitation } from "@/types/analysis";

export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  role: ChatRole;
  content: string;

  model?: string | null;
  ticker?: string | null;
  sources?: DocumentCitation[];

  error?: string | null;
};

export type SendOptions = {

  ticker?: string;

  documentId?: string;

  asOfDate?: string;
};

type Props = {

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

  const ensureSessionId = useCallback((): string => {
    if (sessionIdRef.current === null) {
      sessionIdRef.current = newSessionId();
      setSessionId(sessionIdRef.current);
      try {
        window.localStorage.setItem(storageKey(scope), sessionIdRef.current);
      } catch {

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
              // Only the resolved ticker is surfaced. Execution steps and tool
              // names are server-side implementation detail.
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


              partial.content = data.message || partial.content;
              partial.model = data.model ?? null;
              partial.ticker =
                partial.ticker ??
                (data.tickers?.length ? data.tickers[0] : null);
              partial.sources = data.sources ?? undefined;
              setMessages((prev) => {
                const next = [...prev];
                next[next.length - 1] = { ...partial };
                return next;
              });
            },
            onError: (message) => {
              if (!isCurrent()) return;

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


  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);


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

    }
  }, [scope]);


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

          try {
            window.localStorage.removeItem(storageKey(scope));
          } catch {

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


      }
    },
    [isStreaming, scope]
  );


  const mountedRef = useRef(false);
  useEffect(() => {
    if (mountedRef.current) return;
    mountedRef.current = true;
    void restoreSession();

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
