"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

type Section = { id: string; label: string };

export function AnalysisSectionNav({ sections }: { sections: Section[] }) {
  const [active, setActive] = useState(sections[0]?.id ?? "");

  useEffect(() => {
    const elements = sections
      .map((section) => document.getElementById(section.id))
      .filter((element): element is HTMLElement => Boolean(element));

    if (elements.length === 0) return;
    if (typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

        const first = visible[0];
        if (first) setActive(first.target.id);
      },
      { rootMargin: "-140px 0px -55% 0px", threshold: [0, 0.2, 0.6] }
    );

    elements.forEach((element) => observer.observe(element));

    return () => observer.disconnect();
  }, [sections]);

  return (
    <nav
      aria-label="Analysis sections"
      className="sticky top-16 z-20 -mx-4 border-y border-border bg-background/90 px-4 backdrop-blur-md sm:mx-0 sm:rounded-xl sm:border sm:px-2 sm:py-1.5"
    >
      <ul className="flex gap-1 overflow-x-auto">
        {sections.map((section) => {
          const isActive = active === section.id;

          return (
            <li key={section.id}>
              <a
                href={`#${section.id}`}
                aria-current={isActive ? "true" : undefined}
                className={cn(
                  "inline-flex whitespace-nowrap rounded-lg px-3 py-1.5 text-caption font-medium transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  isActive
                    ? "bg-brand-subtle text-brand"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                {section.label}
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
