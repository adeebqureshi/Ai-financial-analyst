import { AppShell } from "@/components/layout/app-shell";
import { ComparisonWorkspace } from "@/components/comparison/comparison-workspace";

export default function ComparePage() {
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

        <ComparisonWorkspace />

      </div>
    </AppShell>
  );
}