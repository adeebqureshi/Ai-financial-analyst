import { PageHeader } from "@/components/ui/page-header";
import { DocumentSearch } from "@/features/documents/document-search";

type Props = {
  searchParams: Promise<{ q?: string | string[] }>;
};

export default async function SearchPage({ searchParams }: Props) {
  const params = await searchParams;
  const raw = params.q;
  const initialQuery = Array.isArray(raw) ? (raw[0] ?? "") : (raw ?? "");

  return (
    <div className="space-y-8 pb-8">
      <PageHeader
        eyebrow="Research"
        title="Search the knowledge base"
        description="Query every indexed filing, report and note using hybrid vector + keyword retrieval — the same knowledge the AI copilot uses to ground its research."
      />

      <DocumentSearch initialQuery={initialQuery} />
    </div>
  );
}
