"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type ChatSessionSummary } from "@/services/api";

export const CHAT_SESSIONS_QUERY_KEY = ["chat-sessions"] as const;

export function useChatSessions(enabled = true) {
  return useQuery({
    queryKey: CHAT_SESSIONS_QUERY_KEY,
    queryFn: () => api.listChatSessions(),
    enabled,
    retry: false,
    staleTime: 30_000,
  });
}

export function chatSessionRows(
  data: Awaited<ReturnType<typeof api.listChatSessions>> | undefined
): ChatSessionSummary[] {
  return data?.data?.sessions ?? [];
}

/**
 * Delete one persisted research session.
 *
 * On success the session is spliced out of the cached list *and* the query is
 * invalidated, so a refetch cannot resurrect a row the server has already
 * dropped. Both are deliberate: the splice removes the row instantly (no spinner
 * round-trip), and the invalidation is the source of truth that keeps the cache
 * honest if anything else changed the server state in the meantime.
 *
 * A failure is never swallowed — the row stays in the cache and the caller shows
 * the error, because optimistically dropping a row that still exists in the
 * database would be a lie.
 */
export function useDeleteChatSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => api.deleteChatSession(sessionId),

    onSuccess: (_result, sessionId) => {
      queryClient.setQueryData<Awaited<ReturnType<typeof api.listChatSessions>>>(
        CHAT_SESSIONS_QUERY_KEY,
        (previous) => {
          const sessions = previous?.data?.sessions;

          // Nothing cached yet — the invalidation below is the whole update.
          if (!sessions) return previous;

          return {
            ...previous,
            data: {
              ...previous.data,
              sessions: sessions.filter(
                (session) => session.session_id !== sessionId
              ),
              total: Math.max((previous.data?.total ?? 0) - 1, 0),
            },
          };
        }
      );

      void queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY });
    },
  });
}