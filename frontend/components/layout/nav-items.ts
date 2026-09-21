import {
  BookOpenText,
  Building2,
  Crosshair,
  FileText,
  GitCompare,
  Search,
  SlidersHorizontal,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  title: string;
  href: string;
  icon: LucideIcon;
};

export type NavGroup = {
  label: string;
  items: NavItem[];
};

/**
 * Single source of truth for the workspace information architecture.
 *
 * Consumed by the sidebar, the topbar (page title) and the command palette so
 * a destination can never be added, renamed or duplicated in one place only.
 * Every href here is a real route in `app/(app)`.
 */
export const navigationGroups: NavGroup[] = [
  {
    label: "CO-PILOT",
    items: [
      { title: "Ask AI", href: "/dashboard", icon: Sparkles },
      { title: "Reports", href: "/reports", icon: FileText },
    ],
  },
  {
    label: "RESEARCH",
    items: [
      { title: "Documents", href: "/research", icon: BookOpenText },
      { title: "Search", href: "/search", icon: Search },
    ],
  },
  {
    label: "MARKETS",
    items: [
      { title: "Screener", href: "/screener", icon: SlidersHorizontal },
      { title: "Compare", href: "/compare", icon: GitCompare },
    ],
  },
  {
    label: "COMPANY",
    items: [
      { title: "Analyze", href: "/analysis", icon: Crosshair },
      { title: "Profile", href: "/company", icon: Building2 },
    ],
  },
];

export type NavDestination = NavItem & { group: string };

/** Flattened destinations, used by the command palette. */
export const navigationDestinations: NavDestination[] = navigationGroups.flatMap(
  (group) =>
    group.items.map((item) => ({ ...item, group: group.label }))
);

/** True when `pathname` is the href itself or a nested route beneath it. */
export function isActivePath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(href + "/");
}

/**
 * Title shown in the topbar for a pathname (first segment), taken from the
 * navigation config. Routes outside the primary navigation (e.g. `/watchlist`)
 * fall back to a local map, then to "Workspace".
 */
const secondaryTitles: Record<string, string> = {
  "/portfolio": "Portfolio",
  "/watchlist": "Watchlist",
  "/settings": "Settings",
};

export function titleForPathname(pathname: string): string {
  const href = "/" + pathname.split("/").filter(Boolean)[0];

  const destination = navigationDestinations.find((item) => item.href === href);
  if (destination) return destination.title;

  return secondaryTitles[href] ?? "Workspace";
}
