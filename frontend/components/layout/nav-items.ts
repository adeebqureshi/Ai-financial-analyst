import {
  BookOpenText,
  Building2,
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
  description?: string;
  keywords?: string;
};

export type NavGroup = {
  label: string;
  items: NavItem[];
};

export const navigationGroups: NavGroup[] = [
  {
    label: "Company & Valuation",
    items: [
      {
        title: "Analyze",
        href: "/analysis",
        icon: Sparkles,
        description: "Full AI pipeline for one ticker",
        keywords: "valuation intrinsic value dcf risk health",
      },
      {
        title: "Company",
        href: "/company",
        icon: Building2,
        description: "Company profiles and sector context",
        keywords: "profile sector industry lookup",
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
    label: "Research & Reports",
    items: [
      {
        title: "Research",
        href: "/research",
        icon: BookOpenText,
        description: "Upload filings and query the knowledge base",
        keywords: "documents upload pdf rag ingest",
      },
      {
        title: "Search",
        href: "/search",
        icon: Search,
        description: "Hybrid vector and keyword retrieval",
        keywords: "search retrieval query knowledge base",
      },
      {
        title: "Reports",
        href: "/reports",
        icon: FileText,
        description: "Generate an LLM research report",
        keywords: "report generate research memo",
      },
    ],
  },
];

export const workspaceItems: NavItem[] = [
  {
    title: "Settings",
    href: "/settings",
    icon: SlidersHorizontal,
    keywords: "settings preferences theme",
  },
];

export type NavDestination = NavItem & { group: string };

export const navigationDestinations: NavDestination[] = [
  ...navigationGroups.flatMap((group) =>
    group.items.map((item) => ({ ...item, group: group.label }))
  ),
  ...workspaceItems.map((item) => ({ ...item, group: "Workspace" })),
];

export function isActivePath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(href + "/");
}

const secondaryTitles: Record<string, string> = {
  "/settings": "Settings",
};

export function titleForPathname(pathname: string): string {
  const href = "/" + pathname.split("/").filter(Boolean)[0];

  const destination = navigationDestinations.find((item) => item.href === href);
  if (destination) return destination.title;

  return secondaryTitles[href] ?? "Workspace";
}

export function sectionForPathname(pathname: string): string {
  const href = "/" + pathname.split("/").filter(Boolean)[0];

  return (
    navigationGroups.find((group) =>
      group.items.some((item) => item.href === href)
    )?.label ?? "Workspace"
  );
}
