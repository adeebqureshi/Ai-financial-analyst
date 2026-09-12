"use client";

import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { ReactNode, useState } from "react";
import { ApiError } from "@/services/api";

type Props = {
  children: ReactNode;
};

function shouldRetry(
  failureCount: number,
  error: unknown
): boolean {
  if (failureCount >= 3) return false;

  if (error instanceof ApiError) {
    return error.isRetryable();
  }

  if (error instanceof TypeError && error.message.includes("fetch")) {
    return true;
  }

  return false;
}

export function QueryProvider({
  children,
}: Props) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60,
            retry: shouldRetry,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: shouldRetry,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={client}>
      {children}
    </QueryClientProvider>
  );
}