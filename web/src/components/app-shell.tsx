import { Suspense, type ReactNode } from "react";

import { ApiStatus, ApiStatusSkeleton } from "@/components/api-status";
import { Nav } from "@/components/nav";

function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <svg
        viewBox="0 0 24 24"
        className="size-6 text-emerald-400"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.75}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
      >
        <path d="M12 3 4 6v6c0 4.5 3.4 8.3 8 9 4.6-.7 8-4.5 8-9V6l-8-3Z" />
        <path d="M7.5 12h2.2l1.6-3.5 2.2 7 1.5-3.5h1.5" />
      </svg>
      <span className="text-[15px] font-semibold tracking-tight text-white">
        SentinelAI
      </span>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-slate-800 bg-slate-950/60 md:flex">
        <div className="flex h-14 items-center border-b border-slate-800 px-6">
          <Logo />
        </div>
        <div className="flex-1 py-4">
          <Nav layout="vertical" />
        </div>
        <p className="border-t border-slate-800 px-6 py-4 text-[11px] leading-relaxed text-slate-600">
          Milestone 1.5 · early preview
          <br />
          Health ratings use fixed thresholds until anomaly detection (M2).
        </p>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-slate-800 px-6">
          <div className="md:hidden">
            <Logo />
          </div>
          <div className="ml-auto">
            <Suspense fallback={<ApiStatusSkeleton />}>
              <ApiStatus />
            </Suspense>
          </div>
        </header>
        <div className="border-b border-slate-800 md:hidden">
          <Nav layout="horizontal" />
        </div>
        <main className="flex-1 p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
