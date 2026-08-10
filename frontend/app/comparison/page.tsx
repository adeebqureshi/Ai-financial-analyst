import { AppShell } from "@/components/layout/app-shell";
import { ComparisonToolbar } from "@/components/comparison/comparison-toolbar";
import { ComparisonTable } from "@/components/comparison/comparison-table";

export default function ComparisonPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl">

        <div className="mb-12">

          <h1 className="text-5xl font-bold tracking-tight text-white">
            Company Comparison
          </h1>

          <p className="mt-4 text-lg text-zinc-400">
            Compare multiple companies using AI valuation,
            financial health, risk analysis and intrinsic value.
          </p>

        </div>

        <ComparisonToolbar />

        <div className="mt-10">
          <ComparisonTable />
        </div>

      </div>
    </AppShell>
  );
}