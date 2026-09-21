
import { Eye } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";

export default function WatchlistPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <PageHeader
        eyebrow="Workspace"
        title="Watchlist"
        description="Monitor companies you are tracking."
      />

      <EmptyState
        icon={<Eye size={28} aria-hidden="true" />}
        title="Your watchlist is empty"
        description="Symbols you follow will appear here. Run an analysis or company lookup, then add the ticker to your watchlist to track it."
      />
    </div>
  );
}