"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", icon: "dashboard", label: "Dashboard" },
  { href: "/creative-automation", icon: "auto_awesome", label: "Creative Automation" },
  { href: "/ivr-automation", icon: "settings_phone", label: "IVR Automation" },
  { href: "/asset-library", icon: "folder_open", label: "Asset Library" },
  { href: "/projects", icon: "tactic", label: "Projects" },
  { href: "/history", icon: "history", label: "History" },
  { href: "/settings", icon: "settings", label: "Settings" },
] as const;

// Only /ivr-automation is a real route in Phase 1 -- the rest are future
// modules (Creative Automation, Asset Library, Localization, Campaign
// Automation) and keep their placeholder href, same as the static mockup.
const IMPLEMENTED_ROUTES = new Set(["/ivr-automation"]);

export function SideNav() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen z-40 w-64 border-r minimal-divider flex flex-col bg-surface">
      <div className="px-gutter py-md">
        <h1 className="font-title-md text-title-md font-bold tracking-tight text-on-surface">Automation Hub</h1>
      </div>
      <nav className="flex-1 px-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const isImplemented = IMPLEMENTED_ROUTES.has(item.href);
          return (
            <Link
              key={item.href}
              href={isImplemented ? item.href : "#"}
              className={
                isActive
                  ? "flex items-center gap-3 px-3 py-2 text-on-surface bg-white/5 border border-white/5 rounded-lg font-medium"
                  : "flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:text-on-surface transition-colors rounded-lg group"
              }
            >
              <span className={`material-symbols-outlined ${isActive ? "text-primary" : ""}`}>{item.icon}</span>
              <span className="font-body-sm">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
