import { Database } from "lucide-react";

import { DocumentLibrary } from "@/features/documents/document-library";
import { PageHeader } from "@/components/ui/page-header";
import { TextAction } from "@/components/ui/button";

export default function ResearchPage() {
  return (
    <div className="space-y-4 pb-8">
      <PageHeader
        eyebrow="Research & Reports"
        title="Research"
        description="Upload financial documents, build a searchable knowledge base, and ask grounded questions."
        actions={
          <TextAction href="/search" icon={<Database size={14} aria-hidden="true" />}>
            Search knowledge base
          </TextAction>
        }
      />

      <DocumentLibrary />
    </div>
  );
}
