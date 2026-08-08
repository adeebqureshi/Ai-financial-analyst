"use client";

import { ReactNode } from "react";
import { PanelLeft, Search, Bell } from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";
import { PremiumButton } from "@/components/ui/premium-button";

interface AppShellProps {
  sidebar: ReactNode;
  children: ReactNode;
  insights?: ReactNode;
}

export function AppShell({
  sidebar,
  children,
  insights,
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-[#05060A] text-white">
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <aside className="w-72 shrink-0 border-r border-white/5 bg-[#090B11]/80 backdrop-blur-3xl">
          {sidebar}
        </aside>

        {/* Main */}
        <main className="flex min-w-0 flex-1 flex-col">
          {/* Top Navigation */}
          <header className="sticky top-0 z-30 border-b border-white/5 bg-[#05060A]/70 backdrop-blur-3xl">
            <div className="flex h-16 items-center justify-between px-6">
              <div className="flex items-center gap-4">
                <PremiumButton
                  variant="ghost"
                  size="sm"
                >
                  <PanelLeft className="h-5 w-5" />
                </PremiumButton>

                <GlassCard className="flex h-11 w-[420px] items-center gap-3 px-4">
                  <Search className="h-4 w-4 text-zinc-500" />

                  <input
                    placeholder="Search companies, filings, reports..."
                    className="flex-1 bg-transparent text-sm outline-none placeholder:text-zinc-500"
                  />
                </GlassCard>
              </div>

              <div className="flex items-center gap-3">
                <PremiumButton
                  variant="secondary"
                  size="sm"
                >
                  <Bell className="h-4 w-4" />
                </PremiumButton>
              </div>
            </div>
          </header>

          {/* Workspace */}
          <div className="flex flex-1 overflow-hidden">
            {/* Center */}
            <section className="flex-1 overflow-y-auto p-6">
              {children}
            </section>

            {/* AI Insights */}
            <aside className="hidden w-[380px] border-l border-white/5 bg-[#090B11]/60 p-6 xl:block">
              {insights}
            </aside>
          </div>
        </main>
      </div>
    </div>
  );
}