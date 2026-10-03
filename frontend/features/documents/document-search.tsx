"use client";

import { useEffect, useRef, useState } from "react";
import {
  BookOpenText,
  Clock,
  FileText,
  Layers,
  Loader2,
  Quote,
  Search,
  Sparkles,
} from "lucide-react";
import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Badge, TickerBadge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorDisplay } from "@/components/ui/error-display";
import { SkeletonList } from "@/components/ui/skeleton";
import { SectionHeading } from "@/components/ui/page-header";
import { useCopilot } from "@/components/layout/ai-copilot";
import { api } from "@/services/api";
import type { SearchResultData } from "@/types/analysis";

const RETRIEVAL_STEPS = [
  {
    icon: Layers,
    title: "Hybrid retrieval",
    description:
      "Queries run against both the vector index and keyword search, then the results are merged.",
  },
  {
    icon: Quote,
    title: "Page-level citations",
    description:
      "Every hit carries its document, page and relevance score so you can verify the evidence.",
  },
  {
    icon: BookOpenText,
    title: "Same corpus as the copilot",
    description:
      "These documents are the knowledge the AI analyst retrieves from when it answers a question.",
  },
];

const EXAMPLE_QUERIES = [
  "What are the key risks disclosed in the latest filing?",
  "Summarise revenue growth and margin trends",
  "Which segment drives the majority of profit?",
];

export function DocumentSearch({ initialQuery = "" }: { initialQuery?: string }) {
  const copilot = useCopilot();

  const [query, setQuery] = useState(initialQuery);
  const [submittedQuery, setSubmittedQuery] = useState(initialQuery);
  const autoRanRef = useRef(false);

  const searchMutation = useMutation({ mutationFn: api.search });

  const result: SearchResultData | null = searchMutation.data?.data ?? null;

  useEffect(() => {
    const trimmed = initialQuery.trim();

    if (!trimmed || autoRanRef.current) return;

    autoRanRef.current = true;
    searchMutation.mutate(trimmed);
  }, [initialQuery, searchMutation]);

  function handleSearch() {
    const trimmed = query.trim();

    if (!trimmed) return;

    setSubmittedQuery(trimmed);
    searchMutation.mutate(trimmed);
  }

  return (
    <div className="space-y-6">
      <section
        aria-labelledby="search-heading"
        className="overflow-hidden rounded-2xl border border-border bg-card shadow-card"
      >
        <div className="px-5 py-6 sm:px-7 sm:py-7">
          <h2 id="search-heading" className="text-subtitle text-foreground">
            Query the knowledge base
          </h2>
          <p className="mt-1.5 max-w-2xl text-label text-muted-foreground">
            Hybrid vector + keyword retrieval across every indexed filing,
            report and note. The copilot uses this same retrieval layer to
            ground its answers.
          </p>

          <form
            className="mt-5"
            onSubmit={(event) => {
              event.preventDefault();
              handleSearch();
            }}
          >
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="flex min-w-0 flex-1 items-center gap-3 rounded-xl border border-input bg-background px-4 transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20">
                <Search
                  size={18}
                  className="shrink-0 text-brand"
                  aria-hidden="true"
                />

                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="e.g. What were the key risks disclosed this quarter?"
                  aria-label="Search query"
                  className="h-12 min-w-0 flex-1 bg-transparent text-body text-foreground outline-none placeholder:text-subtle-foreground"
                />
              </div>

              <Button
                type="submit"
                disabled={!query.trim() || searchMutation.isPending}
              >
                {searchMutation.isPending ? (
                  <Loader2
                    size={16}
                    className="motion-safe:animate-spin"
                    aria-hidden="true"
                  />
                ) : (
                  <Search size={16} aria-hidden="true" />
                )}
                {searchMutation.isPending ? "Searching…" : "Search"}
              </Button>
            </div>
          </form>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-caption text-subtle-foreground">Examples</span>

            {EXAMPLE_QUERIES.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => setQuery(example)}
                className="max-w-full truncate rounded-md border border-border bg-surface px-2.5 py-1.5 text-caption text-muted-foreground transition-colors hover:border-border-strong hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </section>

      {searchMutation.isPending && (
        <div role="status" aria-busy="true">
          <SkeletonList items={3} />
          <span className="sr-only">Searching documents…</span>
        </div>
      )}

      {searchMutation.isError && (
        <ErrorDisplay
          error={searchMutation.error}
          onRetry={() => submittedQuery && searchMutation.mutate(submittedQuery)}
          title="Search failed"
        />
      )}

      {result && (
        <div className="space-y-4">
          <SectionHeading
            title={`${result.total} result${result.total === 1 ? "" : "s"}`}
            description={
              <>
                Retrieved for{" "}
                <span className="text-foreground">“{submittedQuery}”</span>
              </>
            }
            actions={
              <>
                <Badge variant="neutral">
                  <Clock size={12} aria-hidden="true" />
                  {result.retrieval_time_ms.toFixed(1)} ms
                </Badge>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => copilot.open({ prompt: submittedQuery })}
                >
                  <Sparkles size={14} aria-hidden="true" />
                  Ask the copilot
                </Button>
              </>
            }
          />

          {result.hits.length === 0 && (
            <EmptyState
              tone="brand"
              icon={<FileText size={20} aria-hidden="true" />}
              title="No matches found"
              description="Try different wording, or upload more documents to the knowledge base."
            />
          )}

          {result.hits.map((hit, index) => (
            <article
              key={hit.id}
              className="rounded-xl border border-border bg-card px-5 py-4 shadow-card transition-colors hover:border-border-strong"
            >
              <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
                <div className="flex min-w-0 items-center gap-3">
                  <span
                    className="tnum flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted text-caption font-medium text-muted-foreground"
                    aria-hidden="true"
                  >
                    {index + 1}
                  </span>

                  <span className="min-w-0">
                    <span className="block truncate text-label font-semibold text-foreground">
                      {hit.filename ?? hit.source ?? "Document chunk"}
                    </span>
                    <span className="mt-0.5 block text-caption text-muted-foreground">
                      {hit.page != null ? `Page ${hit.page}` : "Page unknown"}
                      {hit.section ? ` · ${hit.section}` : ""}
                    </span>
                  </span>
                </div>

                <span className="shrink-0 rounded-full border border-border bg-surface px-2.5 py-0.5 text-caption text-muted-foreground">
                  Relevance{" "}
                  <span className="tnum font-medium text-foreground">
                    {hit.score.toFixed(3)}
                  </span>
                </span>
              </div>

              <p className="mt-3.5 whitespace-pre-wrap text-body leading-relaxed text-muted-foreground">
                {hit.text}
              </p>

              {(hit.ticker ||
                hit.filing_type ||
                hit.filing_date ||
                hit.document_id) && (
                <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border pt-3">
                  {hit.ticker && (
                    /* Reuse the shared badge rather than a fourth hand-rolled
                       ticker pill — it brings the logo and the one visual
                       language with it. */
                    <TickerBadge symbol={hit.ticker} />
                  )}

                  {hit.filing_type && (
                    <Badge variant="neutral">{hit.filing_type}</Badge>
                  )}

                  {hit.filing_date && (
                    <Badge variant="neutral">Filed {hit.filing_date}</Badge>
                  )}

                  {hit.document_id && (
                    <span className="truncate text-caption text-subtle-foreground">
                      {hit.document_id}
                    </span>
                  )}
                </div>
              )}
            </article>
          ))}
        </div>
      )}

      {!result && !searchMutation.isPending && !searchMutation.isError && (
        <>
          <EmptyState
            compact
            icon={<Search size={20} aria-hidden="true" />}
            title="No query yet"
            description="Enter a question above to search the indexed knowledge base."
          />

          <ol className="grid gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-3">
            {RETRIEVAL_STEPS.map((step) => {
              const Icon = step.icon;

              return (
                <li key={step.title} className="bg-card px-4 py-4">
                  <span
                    className="flex size-8 items-center justify-center rounded-lg bg-brand-subtle text-brand"
                    aria-hidden="true"
                  >
                    <Icon size={15} />
                  </span>
                  <p className="mt-3 text-label font-semibold text-foreground">
                    {step.title}
                  </p>
                  <p className="mt-1 text-caption leading-relaxed text-muted-foreground">
                    {step.description}
                  </p>
                </li>
              );
            })}
          </ol>
        </>
      )}
    </div>
  );
}
