import { AppShell } from "@/components/layout/app-shell";
import { DocumentSearch } from "@/features/documents/document-search";

export default function SearchPage() {
  return (
    <AppShell>
      <section className="mb-10">
        <p className="text-sm uppercase tracking-widest text-zinc-500">
          Research
        </p>

        <h1 className="mt-3 text-4xl font-bold tracking-tight text-white lg:text-5xl">
          Search your financial knowledge base
        </h1>

        <p className="mt-4 max-w-3xl text-lg text-zinc-400">
          Query every indexed filing, report and note using hybrid vector +
          keyword retrieval. These documents are the same knowledge the AI
          financial agent uses to ground its research.
        </p>
      </section>

      <DocumentSearch />
    </AppShell>
  );
}
