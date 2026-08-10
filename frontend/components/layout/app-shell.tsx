"use client";

import { useState } from "react";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

type Props = {
  children: React.ReactNode;
};

export function AppShell({ children }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#05060A] text-white">
      <Sidebar
        open={open}
        onClose={() => setOpen(false)}
      />

      <div className="lg:ml-72">
        <Topbar onMenu={() => setOpen(true)} />

        <main className="mx-auto max-w-[1700px] p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
