"use client";

import { GlassCard } from "@/components/ui/glass-card";

const prompts = [
  "Analyze Apple using DCF",
  "Compare Apple vs Microsoft",
  "Summarize latest 10-K filing",
  "Explain Piotroski Score",
  "Estimate intrinsic value of NVIDIA",
  "Show bankruptcy risk for Tesla",
];

export function PromptSuggestions() {
  return (
    <GlassCard className="p-6">
      <h2 className="mb-6 text-xl font-semibold">
        Suggested Prompts
      </h2>

      <div className="flex flex-wrap gap-3">
        {prompts.map((prompt) => (
          <button
            key={prompt}
            className="
              rounded-full
              border
              border-white/10
              bg-white/5
              px-4
              py-2.5
              text-sm
              text-zinc-300
              transition-all
              duration-300
              hover:border-blue-500/30
              hover:bg-blue-500/10
              hover:text-white
            "
          >
            {prompt}
          </button>
        ))}
      </div>
    </GlassCard>
  );
}