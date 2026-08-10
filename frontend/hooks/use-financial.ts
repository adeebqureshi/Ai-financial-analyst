"use client";

import { useQuery } from "@tanstack/react-query";

import { getFinancialStatements } from "@/services/financial";

export function useFinancial(
  ticker: string
) {
  return useQuery({
    queryKey: ["financial", ticker],

    queryFn: () =>
      getFinancialStatements(ticker),
  });
}