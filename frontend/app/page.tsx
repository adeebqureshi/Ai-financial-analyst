import { AppShell } from "@/components/layout/app-shell";
import { AgentWorkspace } from "@/features/agent";

export default function HomePage() {
  return (
    <AppShell>
      <AgentWorkspace />
    </AppShell>
  );
}
