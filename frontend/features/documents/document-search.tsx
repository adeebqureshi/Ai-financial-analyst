"use client";

import { useState } from "react";
import {
  Search,
  FileText,
  Loader2,
  Sparkles,
  Clock,
  Hash,
} from "lucide-react";
import { useMutation } from "@tanstack/react-query";

import { GlassCard } from "@/components/ui/glass-card";
import { PremiumButton } from "@/components/ui/premium-button";
import { api } from "@/services/api";

export function DocumentSearch() {
  const [query, setQuery] = useState("");

  const [submittedQuery, setSubmittedQuery] = useState("");

  const searchMutation = useMutation({
    mutationFn: api.search,
  });

  const result = searchMutation.data?.data ?? null;

  function handleSearch() {
    const trimmed = query.trim();

    if (!trimmed) return;

    setSubmittedQuery(trimmed);

    searchMutation.mutate(trimmed);
  }

  return (
    <div className="space-y-8">
      <header>
        <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-4 py-2 text-sm text-violet-300">
          <Sparkles size={16} />
          Semantic Search
        </div>

        <h1 className="mt-6 text-4xl font-bold text-white">
          Search Every Indexed Document
        </h1>

        <p className="mt-3 max-w-2xl text-zinc-400">
          Query across all uploaded filings, reports and notes using
          hybrid vector + keyword retrieval. Results include scores
          and page-level provenance.
        </p>
      </header>

      {/* Query input */}
      <GlassCard glow className="p-6">
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="flex flex-1 items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4">
            <Search size={20} className="shrink-0 text-zinc-500" />

            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSearch();
              }}
              placeholder="e.g. What were the key risks disclosed this quarter?"
              className="w-full bg-transparent py-4 text-white outline-none placeholder:text-zinc-500"
            />
          </div>

          <PremiumButton
            disabled={!query.trim() || searchMutation.isPending}
            onClick={handleSearch}
          >
            {searchMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Searching…
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                Search
              </>
            )}
          </PremiumButton>
        </div>
      </GlassCard>

      {searchMutation.isError && (
        <p className="rounded-2xl border border-red-400/20 bg-red-500/10 p-4 text-sm text-red-400">
          Search failed. Please make sure documents are uploaded, then try again.
        </p>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <p className="flex flex-wrap items-center gap-3 text-sm text-zinc-500">
            <span>
              {result.total} result{result.total === 1 ? "" : "s"} for{" "}
              <span className="font-medium text-white">
                “{submittedQuery}”
              </span>
            </span>

            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.02] px-3 py-1">
              <Clock size={14} className="text-zinc-400" />
              {result.retrieval_time_ms.toFixed(1)} ms
            </span>
          </p>

          {result.hits.length === 0 && (
            <p className="rounded-2xl border border-white/5 bg-white/[0.02] p-8 text-center text-sm text-zinc-500">
              No matches found. Try different wording or upload more documents.
            </p>
          )}

          {result.hits.map((hit) => (
            <GlassCard key={hit.id} className="p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="rounded-xl bg-white/5 p-3">
                    <FileText size={20} className="text-violet-300" />
                  </div>

                  <div className="min-w-0">
                    <p className="truncate font-medium text-white">
                      {hit.filename ?? hit.source ?? "Document chunk"}
                    </p>

                    <p className="mt-0.5 text-sm text-zinc-500">
                      {hit.page != null
                        ? `Page ${hit.page}`
                        : "Unknown page"}
                    </p>
                  </div>
                </div>

                <span className="rounded-full border border-violet-400/20 bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-300">
                  {(hit.score * 100).toFixed(1)}% match
                </span>
              </div>

              <p className="mt-4 line-clamp-5 whitespace-pre-wrap leading-relaxed text-zinc-300">
                {hit.text}
              </p>

              {(hit.section ||
                hit.ticker ||
                hit.filing_type ||
                hit.filing_date) && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {hit.ticker && (
                    <span className="rounded-full border border-white/10 bg-white/[0.02] px-3 py-1 text-xs text-zinc-400">
                      {hit.ticker}
                    </span>
                  )}

                  {hit.section && (
                    <span className="rounded-full border border-white/10 bg-white/[0.02] px-3 py-1 text-xs text-zinc-400">
                      {hit.section}
                    </span>
                  )}

                  {hit.filing_type && (
                    <span className="rounded-full border border-white/10 bg-white/[0.02] px-3 py-1 text-xs text-zinc-400">
                      {hit.filing_type}
                    </span>
                  )}

                  {hit.filing_date && (
                    <span className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/[0.02] px-3 py-1 text-xs text-zinc-400">
                      <Hash size={12} />
                      {hit.filing_date}
                    </span>
                  )}
                </div>
              )}
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}
