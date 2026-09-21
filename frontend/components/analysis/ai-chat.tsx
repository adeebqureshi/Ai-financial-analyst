"use client";

import { ChatSurface } from "@/components/ui/chat-surface";

type Props = {
  ticker: string;
};

/**
 * Analysis-page chat.
 *
 * A thin adapter over the shared {@link ChatSurface}: all streaming, session,
 * abort, retry and rendering behavior lives there now. The `ai-chat` test id
 * is provided by ChatSurface so existing Playwright coverage is unaffected.
 */
export function AIChat({ ticker }: Props) {
  return (
    <ChatSurface
      scope={`analysis-${ticker}`}
      ticker={ticker}
      placeholder={`Ask about ${ticker}…`}
    />
  );
}
