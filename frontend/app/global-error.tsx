"use client";

import { useEffect } from "react";
import { RefreshCw, AlertTriangle } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global error caught:", error);
  }, [error]);

  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-[#05060A] text-white flex items-center justify-center p-4">
          <div className="max-w-md w-full text-center">
            <div className="mx-auto mb-6 h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center">
              <AlertTriangle size={48} className="text-red-400" />
            </div>

            <h1 className="text-3xl font-bold text-white mb-4">
              Something went wrong
            </h1>

            <p className="text-zinc-400 mb-8">
              An unexpected error occurred. Our team has been notified.
            </p>

            <button
              onClick={reset}
              className="inline-flex items-center gap-2 rounded-2xl bg-white px-6 py-3 font-medium text-black transition hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-[#05060A]"
            >
              <RefreshCw size={18} />
              Try again
            </button>

            <p className="mt-6 text-xs text-zinc-600">
              {error.digest ? `Error ID: ${error.digest}` : ""}
            </p>
          </div>
        </div>
      </body>
    </html>
  );
}