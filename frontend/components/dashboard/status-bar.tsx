"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";

interface VersionInfo {
  app_name: string;
  app_version: string;
  demo_mode: boolean;
}

export function StatusBar() {
  const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null);

  useEffect(() => {
    async function fetchVersion() {
      try {
        const response = await api.version();
        if (response?.data) {
          setVersionInfo(response.data as VersionInfo);
        }
      } catch {
        // Silently fail - status bar is non-critical
      }
    }
    fetchVersion();
  }, []);

  const isDemoMode = versionInfo?.demo_mode ?? false;

  return (
    <footer
      className="
        mt-10
        flex
        items-center
        justify-between
        rounded-3xl
        border
        border-white/5
        bg-white/[0.03]
        px-6
        py-4
      "
    >
      <span className="text-sm text-zinc-500">
        AI Financial Analyst Enterprise Edition
      </span>

      <div className="flex items-center gap-6 text-sm text-zinc-500">
        <span>Backend Connected</span>

        <span>RAG Ready</span>

        <span>LLM Ready</span>

        {isDemoMode && (
          <span
            className="flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-400"
          >
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-amber-500" />
            </span>
            DEMO MODE
          </span>
        )}
      </div>
    </footer>
  );
}