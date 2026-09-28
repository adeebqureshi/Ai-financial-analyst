"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/services/api";

export type WorkspaceStatus = {
  status: "checking" | "healthy" | "degraded" | "unavailable";
  detail: string;
  demoMode: boolean;
  version: string | null;
  degradedComponents: string[];
};

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

export function useWorkspaceStatus() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
    retry: false,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const version = useQuery({
    queryKey: ["version"],
    queryFn: () => api.version(),
    retry: false,
    staleTime: 60_000,
  });

  const documents = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.listDocuments(),
    retry: false,
    staleTime: 30_000,
  });

  if (health.isPending) {
    return {
      status: "checking" as const,
      detail: "Checking backend…",
      demoMode: false,
      version: null,
      degradedComponents: [],
      documentCount: null,
      documentsPending: true,
    };
  }

  if (health.isError) {
    return {
      status: "unavailable" as const,
      detail: "Backend unreachable",
      demoMode: false,
      version: null,
      degradedComponents: [],
      documentCount: null,
      documentsPending: documents.isPending,
    };
  }

  const payload = (health.data?.data ?? null) as {
    status?: unknown;
    components?: unknown;
  } | null;

  const status = typeof payload?.status === "string" ? payload.status : "unknown";
  const degradedComponents = toComponentNames(payload?.components);

  const versionPayload = (version.data?.data ?? null) as {
    demo_mode?: unknown;
    app_version?: unknown;
  } | null;

  const demoMode = versionPayload?.demo_mode === true;
  const appVersion =
    typeof versionPayload?.app_version === "string"
      ? versionPayload.app_version
      : null;

  const documentCount = documents.data?.data?.total ?? null;

  if (status === "healthy") {
    return {
      status: "healthy" as const,
      detail: appVersion ? `API v${appVersion}` : "All services operational",
      demoMode,
      version: appVersion,
      degradedComponents,
      documentCount,
      documentsPending: documents.isPending,
    };
  }

  if (status === "degraded") {
    return {
      status: "degraded" as const,
      detail:
        degradedComponents.length > 0
          ? `Attention: ${degradedComponents.join(", ")}`
          : "A component needs attention",
      demoMode,
      version: appVersion,
      degradedComponents,
      documentCount,
      documentsPending: documents.isPending,
    };
  }

  return {
    status: "unavailable" as const,
    detail: `Backend reported “${status}”`,
    demoMode,
    version: appVersion,
    degradedComponents,
    documentCount,
    documentsPending: documents.isPending,
  };
}
