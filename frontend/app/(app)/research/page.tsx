import { Database } from "lucide-react";
import Link from "next/link";

import { DocumentLibrary } from "@/features/documents/document-library";
import { PageHeader } from "@/components/ui/page-header";

export default function ResearchPage() {
  return (
    // Full-height column on desktop: the sticky topbar is h-14 (3.5rem) and the
    // shell pads the page by ~1.5rem top and bottom. Pinning the height here
    // keeps the chat composer visible and makes the message list the only
    // scrolling region. Below `lg` the layout stacks and heights fall back to
    // content flow.
    <div className="mx-auto flex w-full max-w-[100rem] flex-col gap-5 pb-8 lg:h-[calc(100dvh-3.5rem-4.75rem)]">
      <PageHeader
        compact
        eyebrow="Research"
        title="Research"
        description="Upload financial documents, build a searchable knowledge base, and ask grounded questions."
        titleProps={{ className: "text-title" }}
        actions={
          // Knowledge-base retrieval is a Research capability, not a separate
          // top-level destination. This hands off to the existing hybrid
          // vector + keyword search route rather than duplicating it.
          <Link
            href="/search"
            className="inline-flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3.5 text-label font-medium text-foreground shadow-soft transition-colors hover:border-border-strong hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            <Database size={15} className="text-brand" aria-hidden="true" />
            Search knowledge base
          </Link>
        }
      />

      <div className="min-h-0 flex-1">
        <DocumentLibrary />
      </div>
    </div>
  );
}