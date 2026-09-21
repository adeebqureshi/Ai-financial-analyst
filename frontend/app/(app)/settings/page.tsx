
import { Settings2 } from "lucide-react";

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <PageHeader
        eyebrow="Workspace"
        title="Settings"
        description="Configure your workspace preferences."
      />

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle as="h2">Appearance</CardTitle>
        </CardHeader>
        <CardBody className="flex items-center justify-between gap-4">
          <div>
            <p className="text-label font-medium text-foreground">
              Theme
            </p>
            <p className="mt-1 text-caption text-muted-foreground">
              Switch between light and dark mode. The choice is saved on this
              device.
            </p>
          </div>
          <ThemeToggle />
        </CardBody>
      </Card>

      <p className="flex items-center gap-2 text-caption text-muted-foreground">
        <Settings2 size={14} aria-hidden="true" />
        Additional workspace settings will appear here as they become available.
      </p>
    </div>
  );
}