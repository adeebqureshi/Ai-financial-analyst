import { AppShell } from "@/components/layout/app-shell";

export default function ComparePage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl">
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Compare
        </h1>

        <p className="mt-3 text-zinc-400">
          Side-by-side company comparison and valuation analysis.
        </p>
      </div>
    </AppShell>
  );
}