"use client";

import Link from "next/link";
import { Database, FileSearch, Loader2, Upload } from "lucide-react";

import { useWorkspaceStatus } from "@/hooks/use-workspace-status";
import { SectionHeading } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";

/**
 * Knowledge-base summary for the Command Hub.
 *
 * Every number here comes from the existing `/health` and `/documents`
 * responses via `useWorkspaceStatus` — nothing is invented, and no new
 * endpoint is called. When the document service cannot be reached the panel
 * shows an explicit unavailable state rather than a fake zero.
 */
export function KnowledgeBase() {
  const status = useWorkspaceStatus();

  const unavailable = !status.documentsPending && status.documentCount === null;
  const count = status.documentCount;

  return (
    <section aria-labelledby="knowledge-base-heading" className="space-y-4">
      <SectionHeading
        id="knowledge-base-heading"
        title="Knowledge base"
        description="Documents indexed for AI retrieval."
      />

      <div className="space-y-4 rounded-xl border border-border bg-card p-4">
        <div className="flex items-center gap-3">
          <span
            className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-subtle text-brand"
            aria-hidden="true"
          >
            <Database size={17} />
          </span>

          <div className="min-w-0 flex-1">
            {status.documentsPending ? (
              <p className="flex items-center gap-2 text-label font-medium text-muted-foreground">
                <Loader2
                  size={14}
                  className="motion-safe:animate-spin"
                  aria-hidden="true"
                />
                Checking indexed documents…
              </p>
            ) : unavailable ? (
              <>
                <p className="text-label font-medium text-foreground">
                  Document service unavailable
                </p>
                <p className="mt-0.5 text-caption text-muted-foreground">
                  The backend did not respond, so the indexed document count is
                  unknown.
                </p>
              </>
            ) : count === 0 ? (
              <>
                <p className="text-label font-medium text-foreground">
                  No documents indexed yet
                </p>
                <p className="mt-0.5 text-caption text-muted-foreground">
                  Upload a filing or annual report to make it searchable by the
                  AI.
                </p>
              </>
            ) : (
              <>
                <p className="text-label font-medium text-foreground">
                  {count} document{count === 1 ? "" : "s"} indexed
                </p>
                <p className="mt-0.5 text-caption text-muted-foreground">
                  Available for retrieval, citation and research answers.
                </p>
              </>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 border-t border-border pt-4">
          <Button asChild variant="primary" size="sm">
            <Link href="/search">
              <FileSearch size={14} aria-hidden="true" />
              Search knowledge base
            </Link>
          </Button>

          <Button asChild variant="secondary" size="sm">
            <Link href="/research">
              <Upload size={14} aria-hidden="true" />
              Manage documents
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
