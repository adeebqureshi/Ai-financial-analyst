
import { Briefcase } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";

export default function PortfolioPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <PageHeader
        eyebrow="Workspace"
        title="Portfolio"
        description="Track positions, allocation and performance."
      />

      <EmptyState
        icon={<Briefcase size={28} aria-hidden="true" />}
        title="No portfolio connected yet"
        description="Portfolio tracking is not connected to a data source in this workspace. Connect a brokerage or import holdings to see positions, allocation and performance here."
      />
    </div>
  );
}