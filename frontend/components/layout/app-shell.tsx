"use client";

import { useEffect, useState } from "react";

import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { CopilotDrawer, CopilotFab, CopilotProvider } from "./ai-copilot";

const TABLET_QUERY = "(min-width: 768px) and (max-width: 1279px)";

type Props = {
  children: React.ReactNode;
};

function Shell({ children }: Props) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;

    const query = window.matchMedia(TABLET_QUERY);

    function sync(event: MediaQueryList | MediaQueryListEvent) {
      if (event.matches) setCollapsed(true);
    }

    sync(query);
    query.addEventListener("change", sync);

    return () => query.removeEventListener("change", sync);
  }, []);

  return (
    <div className="min-h-dvh bg-background text-foreground">
      <a
        href="#workspace-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[60] focus:rounded-lg focus:border focus:border-border focus:bg-card focus:px-4 focus:py-2 focus:text-label focus:text-foreground focus:shadow-overlay"
      >
        Skip to main content
      </a>

      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        collapsed={collapsed}
        onToggleCollapsed={() => setCollapsed((current) => !current)}
      />

      <div
        className={
          collapsed
            ? "md:pl-[4.75rem] transition-[padding] duration-200 ease-out"
            : "md:pl-[4.75rem] lg:pl-[17rem] transition-[padding] duration-200 ease-out"
        }
      >
        <Topbar onMenu={() => setSidebarOpen(true)} />

        <main
          id="workspace-main"
          tabIndex={-1}
          className="mx-auto w-full max-w-[120rem] px-4 py-5 pb-24 sm:px-6 sm:py-6 sm:pb-24 lg:px-8 lg:py-6 lg:pb-10"
        >
          {children}
        </main>
      </div>

      <CopilotFab />
      <CopilotDrawer />
    </div>
  );
}

export function AppShell({ children }: Props) {
  return (
    <CopilotProvider>
      <Shell>{children}</Shell>
    </CopilotProvider>
  );
}
