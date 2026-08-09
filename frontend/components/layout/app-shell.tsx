import type { ReactNode } from "react";
import Sidebar from "./sidebar";
import Topbar from "./topbar";

export default function AppShell({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#07080b] text-white">
      <Sidebar />

      <div className="lg:pl-[250px]">
        <Topbar />

        <main className="min-h-[calc(100vh-76px)]">
          {children}
        </main>
      </div>
    </div>
  );
}