"use client";

import { useQuery } from "@tanstack/react-query";

import { api, type ChatSessionSummary } from "@/services/api";

export function useChatSessions(enabled = true) {
  return useQuery({
    queryKey: ["chat-sessions"],
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
