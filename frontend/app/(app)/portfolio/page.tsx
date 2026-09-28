import Link from "next/link";
import { ArrowRight, Briefcase, Sparkles } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";

export default function PortfolioPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-8 pb-8">
      <PageHeader
        eyebrow="Workspace"
        title="Portfolio"
        description="Track positions, allocation and performance."
      />

      <EmptyState
        icon={<Briefcase size={20} aria-hidden="true" />}
        title="No portfolio connected yet"
        description="Portfolio tracking is not connected to a data source in this workspace. Until it is, this page stays intentionally empty rather than showing invented numbers."
        action={
          <Link
            href="/analysis"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3.5 py-2 text-label font-medium text-foreground shadow-soft transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Sparkles size={15} aria-hidden="true" />
            Analyze a company instead
            <ArrowRight size={15} aria-hidden="true" />
          </Link>
        }
      />
    </div>
  );
}
