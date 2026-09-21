"use client";

import { useState } from "react";
import { Clock, FileText, Loader2, Search } from "lucide-react";
import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorDisplay } from "@/components/ui/error-display";
import { SkeletonList } from "@/components/ui/skeleton";
import { api } from "@/services/api";
import type { SearchResultData } from "@/types/analysis";

export function DocumentSearch() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");

  const searchMutation = useMutation({ mutationFn: api.search });

  const result: SearchResultData | null = searchMutation.data?.data ?? null;

  function handleSearch() {
    const trimmed = query.trim();

    if (!trimmed) return;

    setSubmittedQuery(trimmed);
    searchMutation.mutate(trimmed);
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div>
            <CardTitle as="h2">Query the knowledge base</CardTitle>
            <p className="mt-1 text-label text-muted-foreground">
              Hybrid vector + keyword retrieval over every indexed document.
            </p>
          </div>
        </CardHeader>

        <CardBody>
          <form
            className="flex flex-col gap-3 sm:flex-row"
            onSubmit={(event) => {
              event.preventDefault();
              handleSearch();
            }}
          >
            <div className="flex min-w-0 flex-1 items-center gap-2 rounded-md border border-input bg-card px-3 focus-within:border-border-strong focus-within:ring-2 focus-within:ring-ring">
              <Search
                size={16}
                className="shrink-0 text-muted-foreground"
                aria-hidden="true"
              />

              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="e.g. What were the key risks disclosed this quarter?"
                aria-label="Search query"
                className="h-9 min-w-0 flex-1 bg-transparent text-body text-foreground outline-none placeholder:text-subtle-foreground"
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
          </form>
        </CardBody>
      </Card>

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
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3 text-label text-muted-foreground">
            <span>
              {result.total} result{result.total === 1 ? "" : "s"} for{" "}
              <span className="font-medium text-foreground">
                “{submittedQuery}”
              </span>
            </span>

            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted px-2.5 py-0.5 text-caption">
              <Clock size={12} aria-hidden="true" />
              {result.retrieval_time_ms.toFixed(1)} ms
            </span>
          </div>

          {result.hits.length === 0 && (
            <EmptyState
              icon={<FileText size={20} aria-hidden="true" />}
              title="No matches found"
              description="Try different wording, or upload more documents to the knowledge base."
            />
          )}

          {result.hits.map((hit) => (
            <Card key={hit.id}>
              <CardBody>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
                      <FileText size={18} aria-hidden="true" />
                    </span>

                    <span className="min-w-0">
                      <span className="block truncate text-label font-medium text-foreground">
                        {hit.filename ?? hit.source ?? "Document chunk"}
                      </span>
                      <span className="mt-0.5 block text-caption text-muted-foreground">
                        {hit.page != null ? `Page ${hit.page}` : "Unknown page"}
                      </span>
                    </span>
                  </div>

                  {/* `score` is the retriever's raw relevance score (reciprocal
                      rank fusion, or a cross-encoder logit when reranking is
                      enabled). It is not a percentage, so it is shown as-is. */}
                  <span className="inline-flex items-center rounded-full border border-border bg-muted px-2.5 py-0.5 text-caption text-muted-foreground">
                    Relevance {hit.score.toFixed(3)}
                  </span>
                </div>

                <p className="mt-3 line-clamp-5 whitespace-pre-wrap text-body text-muted-foreground">
                  {hit.text}
                </p>

                {(hit.section ||
                  hit.ticker ||
                  hit.filing_type ||
                  hit.filing_date) && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {hit.ticker && (
                      <span className="rounded-full border border-border bg-muted px-2.5 py-0.5 font-mono text-caption text-muted-foreground">
                        {hit.ticker}
                      </span>
                    )}

                    {hit.section && (
                      <span className="rounded-full border border-border bg-muted px-2.5 py-0.5 text-caption text-muted-foreground">
                        {hit.section}
                      </span>
                    )}

                    {hit.filing_type && (
                      <span className="rounded-full border border-border bg-muted px-2.5 py-0.5 text-caption text-muted-foreground">
                        {hit.filing_type}
                      </span>
                    )}

                    {hit.filing_date && (
                      <span className="inline-flex items-center gap-1 rounded-full border border-border bg-muted px-2.5 py-0.5 text-caption text-muted-foreground">
                        <span aria-hidden="true">#</span>
                        {hit.filing_date}
                      </span>
                    )}
                  </div>
                )}
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
