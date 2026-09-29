import { ArrowRight, BookOpen, Bot, Database, Search } from "lucide-react";

import { DocumentLibrary } from "@/features/documents/document-library";
import { PageHeader } from "@/components/ui/page-header";
import { TextAction } from "@/components/ui/button";

const pipeline = [
  {
    label: "Uploaded documents",
    hint: "PDF filings and reports",
    icon: BookOpen,
  },
  {
    label: "RAG knowledge base",
    hint: "Parsed, chunked and embedded",
    icon: Database,
  },
  {
    label: "AI financial agent",
    hint: "Retrieves and cites evidence",
    icon: Bot,
  },
];

export default function ResearchPage() {
  return (
    <div className="space-y-8 pb-8">
      <PageHeader
        eyebrow="Research & Reports"
        title="Research workspace"
        description="Upload financial PDFs, then question them with the copilot. Documents are parsed, chunked, embedded and cited with page-level evidence."
        actions={
          <TextAction href="/search" icon={<Search size={14} aria-hidden="true" />}>
            Search knowledge base
          </TextAction>
        }
      />

      <ol className="grid gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-3">
        {pipeline.map((step, index) => {
          const Icon = step.icon;

          return (
            <li
              key={step.label}
              className="flex items-center gap-3 bg-card px-4 py-3.5"
            >
              <span
                className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-subtle text-brand"
                aria-hidden="true"
              >
                <Icon size={15} />
              </span>

              <span className="min-w-0">
                <span className="block truncate text-label font-medium text-foreground">
                  <span className="tnum mr-1.5 text-subtle-foreground">
                    {index + 1}.
                  </span>
                  {step.label}
                </span>
                <span className="mt-0.5 block truncate text-caption text-muted-foreground">
                  {step.hint}
                </span>
              </span>

              {index < pipeline.length - 1 && (
                <ArrowRight
                  size={14}
                  className="ml-auto hidden shrink-0 text-border-strong sm:block"
                  aria-hidden="true"
                />
              )}
            </li>
          );
        })}
      </ol>

      <DocumentLibrary />
    </div>
  );
}
