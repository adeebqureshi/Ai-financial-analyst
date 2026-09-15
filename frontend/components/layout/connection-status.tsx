"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/services/api";

type HealthState =
  | { status: "checking" }
  | {
      status: "healthy";
      demoMode: boolean;
      version: string;
      degradedComponents: string[];
    }
  | { status: "degraded"; demoMode: boolean; degradedComponents: string[] }
  | { status: "unavailable"; message: string };

function toComponentNames(value: unknown): string[] {
  if (!Array.isArray(value)) return [];

  return value
    .map((component) => {
      if (
        typeof component === "object" &&
        component !== null &&
        "status" in component &&
        (component as { status?: unknown }).status !== "healthy" &&
        "name" in component &&
        typeof (component as { name?: unknown }).name === "string"
      ) {
        return (component as { name: string }).name;
      }

      return null;
    })
    .filter((name): name is string => name !== null);
}

type Props = {
  defaultTicker?: string;
};

/**
 * Real backend connection indicator.
 *
 * Combines `GET /health` (service status) with `GET /version` (app version
 * and demo-mode flag). Each state — connected, degraded, unavailable, and
 * loading — is rendered explicitly so the shell never invents status.
 */
export function ConnectionStatus({ defaultTicker = "AAPL" }: Props) {
  const router = useRouter();
  const [state, setState] = useState<HealthState>({ status: "checking" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      // Health first, because it carries per-component status for the
      // degraded case. If health is unreachable, the backend is unavailable.
      let health: {
        status?: unknown;
        components?: unknown;
      } | null = null;

      try {
        const response = await api.health();
        health = (response?.data ?? null) as typeof health;
      } catch (err) {
        if (!cancelled) {
          setState({
            status: "unavailable",
            message:
              err instanceof Error ? err.message : "Backend is unreachable.",
          });
        }

        return;
      }

      // Version is auxiliary (display + demo badge); it must not downgrade a
      // healthy backend to unavailable when it alone fails.
      let demoMode = false;
      let version: string | null = null;

      try {
        const response = await api.version();
        const data = (response?.data ?? null) as {
          demo_mode?: unknown;
          app_version?: unknown;
        } | null;

        demoMode = data?.demo_mode === true;
        version =
          typeof data?.app_version === "string" ? data.app_version : null;
      } catch {
        // Keep the health-derived state below; version details stay unknown.
      }

      if (cancelled) return;

      const status =
        typeof health?.status === "string" ? health.status : "unknown";
      const degradedComponents = toComponentNames(health?.components);

      if (status === "healthy") {
        setState({
          status: "healthy",
          demoMode,
          version: version ?? "unknown",
          degradedComponents,
        });
        return;
      }

      if (status === "degraded") {
        setState({ status: "degraded", demoMode, degradedComponents });
        return;
      }

      setState({
        status: "unavailable",
        message: `Backend reported status "${status}".`,
      });
    }

    void check();

    return () => {
      cancelled = true;
    };
  }, [attempt]);

  const retry = () => setAttempt((count) => count + 1);

  if (state.status === "checking") {
    return (
      <span
        role="status"
        className="inline-flex items-center gap-2 rounded-full border border-border bg-muted px-3 py-1.5 text-caption text-muted-foreground"
      >
        <span
          className="h-1.5 w-1.5 animate-pulse rounded-full bg-subtle-foreground"
          aria-hidden="true"
        />
        Checking backend…
      </span>
    );
  }

  if (state.status === "unavailable") {
    return (
      <span
        role="alert"
        className="inline-flex items-center gap-1.5 rounded-full border border-loss/30 bg-loss-subtle px-3 py-1.5 text-caption"
      >
        <span className="font-medium text-loss">Backend unavailable</span>
        <span className="max-w-56 truncate text-loss/80" title={state.message}>
          {state.message}
        </span>
        <button
          type="button"
          onClick={retry}
          className="rounded-sm font-medium text-loss underline underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background"
        >
          Retry
        </button>
      </span>
    );
  }

  const degraded = state.status === "degraded";
  const detail = degraded
    ? `Degraded: ${
        state.degradedComponents.length > 0
          ? state.degradedComponents.join(", ")
          : "a component needs attention"
      }`
    : `Healthy · v${state.version}`;

  return (
    <span
      role="status"
      title={detail}
      className="inline-flex items-center gap-2 rounded-full border border-border bg-muted px-3 py-1.5 text-caption text-muted-foreground"
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          degraded ? "bg-warning" : "bg-gain"
        }`}
        aria-hidden="true"
      />
      <span className="font-medium text-foreground">
        Backend {degraded ? "degraded" : "connected"}
      </span>
      <span className="hidden sm:inline">{detail}</span>

      {state.demoMode && (
        <span
          role="status"
          className="rounded-full border border-warning/30 bg-warning-subtle px-2 py-0.5 text-[11px] font-medium text-warning"
        >
          DEMO MODE
        </span>
      )}

      <Button
        type="button"
        variant="ghost"
        size="icon-sm"
        onClick={() => router.push(`/analysis/${defaultTicker}`)}
        aria-label={`Open analysis for ${defaultTicker}`}
        title={`Open analysis for ${defaultTicker}`}
        className="-mr-1 text-muted-foreground hover:text-foreground"
      >
        <Search size={14} aria-hidden="true" />
      </Button>
    </span>
  );
}