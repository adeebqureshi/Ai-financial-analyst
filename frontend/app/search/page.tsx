import { AppShell } from "@/components/layout/app-shell";
import { DocumentSearch } from "@/features/documents/document-search";

export default function SearchPage() {
  return (
    <AppShell>
      <DocumentSearch />
    </AppShell>
  );
}
