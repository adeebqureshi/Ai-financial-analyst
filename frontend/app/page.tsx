import { AppShell } from "@/components/layout/app-shell";
import { Sidebar } from "@/components/layout/sidebar";
import { AIInsight } from "@/components/dashboard/ai-insight";
import { WorkspaceHero } from "@/components/dashboard/workspace-hero";

export default function HomePage() {
  return (
    <AppShell
      sidebar={<Sidebar />}
      insights={<AIInsight />}
    >
      <WorkspaceHero />
    </AppShell>
  );
}