import { PageHeader } from "@/components/ui/page-header";
import { CriteriaCheck } from "@/components/screener/criteria-check";

export default function ScreenerPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-8 pb-8">
      <PageHeader
        eyebrow="Markets & Compare"
        title="Financial criteria check"
        description="Evaluate one candidate company against screening criteria using real analysis data and your own valuation assumptions."
      />

      <CriteriaCheck />
    </div>
  );
}
