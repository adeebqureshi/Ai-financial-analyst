"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "@/services/api";
import type {
  AnalyzeData,
  ApiResponse,
} from "@/types/analysis";

export function useAnalysis(ticker?: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["analysis", ticker],
    queryFn: () =>
      api.analyze(ticker as string),
    enabled: Boolean(ticker),
  });

  const mutation = useMutation({
    mutationFn: (symbol: string) =>
      api.analyze(symbol),
    onSuccess: (
      data: ApiResponse<AnalyzeData>,
      symbol: string
    ) => {
      queryClient.setQueryData(
        ["analysis", symbol],
        data
      );
    },
  });

  return {
    ...mutation,
    query,
  };
}
