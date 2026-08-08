"use client";

import { Search, Sparkles } from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";
import { PremiumButton } from "@/components/ui/premium-button";

export function AISearchBox() {
  return (
    <GlassCard
      glow
      className="p-5"
    >
      <div className="flex items-center gap-4">

        <Search
          className="text-zinc-500"
          size={22}
        />

        <input
          placeholder="Ask anything about Apple..."
          className="
            h-14
            flex-1
            bg-transparent
            text-lg
            outline-none
            placeholder:text-zinc-500
          "
        />

        <PremiumButton size="lg">
          <Sparkles className="mr-2 h-4 w-4" />
          Analyze
        </PremiumButton>

      </div>
    </GlassCard>
  );
}