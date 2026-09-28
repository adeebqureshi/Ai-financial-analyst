import { PageHeader } from "@/components/ui/page-header";
import { ComparisonWorkspace } from "@/components/comparison/comparison-workspace";

export default function ComparePage() {
  return (
    <div className="mx-auto max-w-7xl space-y-8 pb-8">
      <PageHeader
        eyebrow="Markets & Compare"
        title="Company comparison"
        description="Compare multiple companies using AI valuation, financial health, risk analysis and intrinsic value."
      />

      <ComparisonWorkspace />
    </div>
  );
}
