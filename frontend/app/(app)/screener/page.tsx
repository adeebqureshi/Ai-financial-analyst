import { PageHeader } from "@/components/ui/page-header";
import { CriteriaCheck } from "@/components/screener/criteria-check";

export default function ScreenerPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <PageHeader
        title="Financial Criteria Check"
        description="Evaluate one candidate company against screening criteria using real analysis data and your own valuation assumptions."
      />

      <CriteriaCheck />
    </div>
  );
}
