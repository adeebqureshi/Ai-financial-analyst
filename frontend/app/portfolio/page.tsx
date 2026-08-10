import { AppShell } from "@/components/layout/app-shell";

export default function PortfolioPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl">
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Portfolio
        </h1>

        <p className="mt-3 text-zinc-400">
          Track positions, allocation and performance.
        </p>
      </div>
    </AppShell>
  );
}