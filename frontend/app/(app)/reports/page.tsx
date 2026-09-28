import { PageHeader } from "@/components/ui/page-header";
import { ReportWorkspace } from "@/components/reports/report-workspace";

export default function ReportsPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-8">
      <PageHeader
        eyebrow="Research & Reports"
        title="AI investment reports"
        description="Generate an LLM-powered research report for any public company, grounded in the same market data and documents the rest of the workspace uses."
      />

      <ReportWorkspace />
    </div>
  );
}
