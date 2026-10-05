"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  href: string;
  label: string;
  /** Milestone that makes this page real. Items with one render disabled. */
  soon?: string;
}

// Disabled entries are deliberate: they show where the product is going and
// which milestone delivers each piece.
const ITEMS: NavItem[] = [
  { href: "/", label: "Overview" },
  { href: "/services", label: "Services" },
  { href: "#", label: "Incidents", soon: "M3" },
  { href: "#", label: "Runbooks", soon: "M6" },
  { href: "#", label: "Remediation", soon: "M8" },
  { href: "#", label: "Postmortems", soon: "M15" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Nav({ layout }: { layout: "vertical" | "horizontal" }) {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Main"
      className={
        layout === "vertical"
          ? "flex flex-col gap-0.5 px-3"
          : "flex gap-1 overflow-x-auto px-4 py-2"
      }
    >
      {ITEMS.map((item) => {
        const base =
          "flex shrink-0 items-center justify-between gap-3 rounded-md px-3 py-2 text-sm";

        if (item.soon) {
          return (
            <span
              key={item.label}
              aria-disabled="true"
              className={`${base} cursor-not-allowed text-slate-600`}
            >
              {item.label}
              <span className="rounded bg-slate-800/80 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                {item.soon}
              </span>
            </span>
          );
        }

        const active = isActive(pathname, item.href);
        return (
          <Link
            key={item.label}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`${base} ${
              active
                ? "bg-slate-800 text-white"
                : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
