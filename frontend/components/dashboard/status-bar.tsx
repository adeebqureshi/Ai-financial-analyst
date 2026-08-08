"use client";

export function StatusBar() {
  return (
    <footer
      className="
        mt-10
        flex
        items-center
        justify-between
        rounded-3xl
        border
        border-white/5
        bg-white/[0.03]
        px-6
        py-4
      "
    >
      <span className="text-sm text-zinc-500">
        AI Financial Analyst Enterprise Edition
      </span>

      <div className="flex items-center gap-6 text-sm text-zinc-500">
        <span>Backend Connected</span>

        <span>RAG Ready</span>

        <span>LLM Ready</span>
      </div>
    </footer>
  );
}