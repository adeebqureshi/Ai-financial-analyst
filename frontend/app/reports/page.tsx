import { AppShell } from "@/components/layout/app-shell";
import { ReportWorkspace } from "@/components/reports/report-workspace";

export default function ReportsPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl">

        <div className="mb-12">

          <h1 className="text-5xl font-bold tracking-tight text-white">
            AI Investment Reports
          </h1>

          <p className="mt-4 text-lg text-zinc-400">
            Generate comprehensive, LLM-powered
            research reports for any public company.
          </p>

        </div>

        <ReportWorkspace />

      </div>
    </AppShell>
  );
}
