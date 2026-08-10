import Link from "next/link";
import { ArrowRight, BookOpen, Bot, Database } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { DocumentLibrary } from "@/features/documents/document-library";

const pipeline = [
  { label: "Uploaded Documents", icon: BookOpen },
  { label: "RAG Knowledge Base", icon: Database },
  { label: "AI Financial Agent", icon: Bot },
];

export default function ResearchPage() {
  return (
    <AppShell>
      <section className="mb-10">
        <p className="text-sm uppercase tracking-widest text-zinc-500">
          Research
        </p>

        <h1 className="mt-3 text-4xl font-bold tracking-tight text-white lg:text-5xl">
          Upload and analyze financial documents with grounded AI
        </h1>

        <p className="mt-4 max-w-3xl text-lg text-zinc-400">
          PDFs you upload here are parsed, chunked, embedded and indexed into
          the knowledge base. The AI financial agent then retrieves and cites
          them with page-level evidence.
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          {pipeline.map((step, index) => {
            const Icon = step.icon;

            return (
              <div key={step.label} className="flex items-center gap-3">
                <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-3">
                  <Icon size={18} className="text-blue-400" />
                  <span className="text-sm font-medium text-zinc-200">
                    {step.label}
                  </span>
                </div>

                {index < pipeline.length - 1 && (
                  <ArrowRight size={18} className="text-zinc-600" />
                )}
              </div>
            );
          })}

          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-2xl border border-blue-500/20 bg-blue-500/10 px-5 py-3 text-sm font-medium text-blue-300 transition hover:bg-blue-500/20"
          >
            Ask AI about a document
            <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      <DocumentLibrary />
    </AppShell>
  );
}
