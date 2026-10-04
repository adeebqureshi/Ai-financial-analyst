import { Database } from "lucide-react";
import Link from "next/link";

import { DocumentLibrary } from "@/features/documents/document-library";
import { PageHeader } from "@/components/ui/page-header";

export default function ResearchPage() {
  return (
    <div className="mx-auto w-full max-w-[78rem] space-y-5 pb-8">
      <PageHeader
        eyebrow="Research"
        title="Research"
        description="Upload financial documents, build a searchable knowledge base, and ask grounded questions."
        actions={
          // Knowledge-base retrieval is a Research capability, not a separate
          // top-level destination. This hands off to the existing hybrid
          // vector + keyword search route rather than duplicating it.
          <Link
            href="/search"
            className="inline-flex h-10 items-center gap-2 rounded-xl border border-border bg-card px-4 text-label font-medium text-foreground shadow-soft transition-colors hover:border-border-strong hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            <Database size={15} className="text-brand" aria-hidden="true" />
            Search knowledge base
          </Link>
        }
      />

      <DocumentLibrary />
    </div>
  );
}