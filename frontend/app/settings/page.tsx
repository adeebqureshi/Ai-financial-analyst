import { AppShell } from "@/components/layout/app-shell";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl">
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Settings
        </h1>

        <p className="mt-3 text-zinc-400">
          Configure your workspace preferences.
        </p>
      </div>
    </AppShell>
  );
}