import {
  BookOpenText,
  GitCompare,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  title: string;
  href: string;
  icon: LucideIcon;
  description?: string;
  keywords?: string;
};

export type NavGroup = {
  label: string;
  items: NavItem[];
};

export const navigationGroups: NavGroup[] = [
  {
    label: "Company Analysis",
    items: [
      {
        title: "Analyze",
        href: "/analysis",
        icon: Sparkles,
        description: "Full AI pipeline for one ticker",
        keywords: "valuation intrinsic value dcf risk health company profile report",
      },
    ],
  },
  {
    label: "Markets & Compare",
    items: [
      {
        title: "Compare",
        href: "/compare",
        icon: GitCompare,
        description: "Side-by-side valuation and health",
        keywords: "comparison peer relative",
      },
    ],
  },
  {
    label: "Research",
    items: [
      {
        title: "Research",
        href: "/research",
        icon: BookOpenText,
        description: "Upload filings and query the knowledge base",
        keywords: "documents upload pdf rag ingest search knowledge base retrieval",
      },
    ],
  },
];

export type NavDestination = NavItem & { group: string };

export const navigationDestinations: NavDestination[] =
  navigationGroups.flatMap((group) =>
    group.items.map((item) => ({ ...item, group: group.label }))
  );

export function isActivePath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(href + "/");
}

/**
 * Routes that stay reachable but are no longer primary navigation
 * destinations. Search is reached through Research; Settings only holds the
 * theme picker, which also lives in the topbar. Both keep a truthful topbar
 * breadcrumb.
 */
const secondaryRoutes: Record<string, { title: string; section: string }> = {
  "/search": { title: "Search knowledge base", section: "Research" },
  "/settings": { title: "Settings", section: "Workspace" },
};

export function titleForPathname(pathname: string): string {
  const href = "/" + pathname.split("/").filter(Boolean)[0];

  const destination = navigationDestinations.find((item) => item.href === href);
  if (destination) return destination.title;

  return secondaryRoutes[href]?.title ?? "Workspace";
}

export function sectionForPathname(pathname: string): string {
  const href = "/" + pathname.split("/").filter(Boolean)[0];

  return (
    navigationGroups.find((group) =>
      group.items.some((item) => item.href === href)
    )?.label ??
    secondaryRoutes[href]?.section ??
    "Workspace"
  );
}
