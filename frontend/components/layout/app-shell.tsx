import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

type Props = {
  children: React.ReactNode;
};

export function AppShell({
  children,
}: Props) {
  return (
    <div className="min-h-screen bg-[#05060A] text-white">

      <Sidebar />

      <div className="ml-72">

        <Topbar />

        <main className="mx-auto max-w-[1700px] p-8">

          {children}

        </main>

      </div>

    </div>
  );
}