"use client";

import { useQuery } from "@tanstack/react-query";

import { api, ApiError } from "@/services/api";
import type { DocumentData } from "@/types/analysis";

/**
 * Indexed-document rows, shared by the research library and the other
 * document surfaces.
 *
 * Uses the same `["documents"]` query key as `useWorkspaceStatus` and
 * `DocumentLibrary`, so mounting it adds no extra network traffic — React Query
 * serves every consumer from one cache entry.
 *
 * `total` is deliberately `number | null`: a failed request must render as
 * "unavailable", never as a misleading zero.
 */
export function useDocuments() {
  const query = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.listDocuments(),
    retry: false,
    staleTime: 30_000,
  });

  const documents: DocumentData[] = query.data?.data?.documents ?? [];

  return {
    documents,
    total: query.data?.data?.total ?? null,
    isPending: query.isPending,
    isError: query.isError,
    error: query.error,
    /**
     * A throttled request is not an outage. Callers must not tell the user the
     * document service is down when the backend simply refused the call for a
     * moment — the two states need very different wording.
     */
    isRateLimited:
      query.isError && query.error instanceof ApiError && query.error.status === 429,
    refetch: query.refetch,
    /** Newest first — the backend already sorts by `created_at` desc. */
    latest: documents[0] ?? null,
  };
}

export function formatDocumentExtent(
  pages: number | null | undefined,
  chunks: number | null | undefined
): string {
  if (pages == null || chunks == null) return "—";

  return `${pages} ${pages === 1 ? "page" : "pages"} · ${chunks} ${
    chunks === 1 ? "chunk" : "chunks"
  }`;
}