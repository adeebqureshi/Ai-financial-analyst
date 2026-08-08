"use client";

import { useState } from "react";
import { Paperclip, Mic, ArrowUp } from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";

export function ChatInput() {
  const [value, setValue] = useState("");

  return (
    <GlassCard className="p-4">
      <textarea
        rows={4}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask anything about a company, valuation, SEC filing or portfolio..."
        className="
          w-full
          resize-none
          bg-transparent
          text-lg
          outline-none
          placeholder:text-zinc-500
        "
      />

      <div className="mt-4 flex items-center justify-between">

        <div className="flex gap-2">

          <button className="rounded-xl border border-white/10 p-2 hover:bg-white/5">
            <Paperclip size={18} />
          </button>

          <button className="rounded-xl border border-white/10 p-2 hover:bg-white/5">
            <Mic size={18} />
          </button>

        </div>

        <button
          className="
            flex
            items-center
            gap-2
            rounded-xl
            bg-blue-600
            px-5
            py-3
            font-medium
            transition-all
            hover:bg-blue-500
          "
        >
          Analyze

          <ArrowUp size={18} />
        </button>

      </div>
    </GlassCard>
  );
}