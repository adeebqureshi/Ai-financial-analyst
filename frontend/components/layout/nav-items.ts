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


export const navigationDestinations: NavDestination[] = navigationGroups.flatMap(
  (group) =>
    group.items.map((item) => ({ ...item, group: group.label }))
);


export function isActivePath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(href + "/");
}


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
