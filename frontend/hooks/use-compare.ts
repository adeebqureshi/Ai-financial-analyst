"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

export function useCompare(tickers: string[]) {
  return useQuery({
    queryKey: ["compare", tickers],

    enabled: tickers.length >= 2,

    queryFn: () =>
      api.compare(tickers),
  });
}
