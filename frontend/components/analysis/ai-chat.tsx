"use client";

import { ChatSurface } from "@/components/ui/chat-surface";

type Props = {
  ticker: string;
};


export function AIChat({ ticker }: Props) {
  return (
    <ChatSurface
      scope={`analysis-${ticker}`}
      ticker={ticker}
      placeholder={`Ask about ${ticker}…`}
    />
  );
}
