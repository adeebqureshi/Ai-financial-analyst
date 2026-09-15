import { AgentWorkspace } from "@/features/agent";
import { ConnectionStatus } from "@/components/layout/connection-status";

export default function HomePage() {
  return <AgentWorkspace connection={<ConnectionStatus />} />;
}
