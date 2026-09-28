"use client";

import { Moon, Settings2, Sun } from "lucide-react";

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { useTheme } from "@/providers/theme-provider";
import { cn } from "@/lib/utils";

const OPTIONS = [
  {
    value: "light" as const,
    label: "Light",
    hint: "Warm ivory surfaces with deep brown text",
    icon: Sun,
  },
  {
    value: "dark" as const,
    label: "Dark",
    hint: "Deep warm charcoal with cream text",
    icon: Moon,
  },
];

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="mx-auto max-w-3xl space-y-8 pb-8">
      <PageHeader
        eyebrow="Workspace"
        title="Settings"
        description="Configure your workspace preferences."
      />

      <Card>
        <CardHeader>
          <div>
            <CardTitle as="h2">Appearance</CardTitle>
            <p className="mt-1 text-label text-muted-foreground">
              Both themes are designed independently — not a simple inversion.
            </p>
          </div>
        </CardHeader>

        <CardBody>
          <div
            role="radiogroup"
            aria-label="Theme"
            className="grid gap-3 sm:grid-cols-2"
          >
            {OPTIONS.map((option) => {
              const Icon = option.icon;
              const active = theme === option.value;

              return (
                <button
                  key={option.value}
                  type="button"
                  role="radio"
                  aria-checked={active}
                  onClick={() => setTheme(option.value)}
                  className={cn(
                    "flex items-start gap-3 rounded-xl border px-4 py-3.5 text-left transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    active
                      ? "border-brand/50 bg-brand-subtle"
                      : "border-border bg-card hover:border-border-strong hover:bg-muted"
                  )}
                >
                  <span
                    className={cn(
                      "flex size-9 shrink-0 items-center justify-center rounded-lg",
                      active
                        ? "bg-brand text-brand-foreground"
                        : "bg-muted text-muted-foreground"
                    )}
                    aria-hidden="true"
                  >
                    <Icon size={16} />
                  </span>

                  <span className="min-w-0">
                    <span className="block text-label font-semibold text-foreground">
                      {option.label}
                    </span>
                    <span className="mt-1 block text-caption leading-relaxed text-muted-foreground">
                      {option.hint}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>

          <p className="mt-4 text-caption text-muted-foreground">
            Your choice is saved on this device and applied before the app paints.
          </p>
        </CardBody>
      </Card>

      <p className="flex items-center gap-2 text-caption text-muted-foreground">
        <Settings2 size={14} aria-hidden="true" />
        Additional workspace settings will appear here as they become available.
      </p>
    </div>
  );
}
