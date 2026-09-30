import { describe, expect, it } from "vitest";

import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";

describe("cn / tailwind-merge configuration", () => {
  it("keeps a text colour alongside a custom type-scale size", () => {
    // Regression guard: the design system's `text-label`/`text-caption` sizes
    // are custom `@theme` utilities. tailwind-merge used to treat them as text
    // *colours* and silently drop an earlier `text-primary-foreground`, which
    // rendered primary buttons as dark text on a dark background (~1.7:1).
    const merged = cn(
      "bg-primary text-primary-foreground shadow-soft",
      "h-9 rounded-lg px-3.5 text-label",
    );

    expect(merged).toContain("bg-primary");
    expect(merged).toContain("text-primary-foreground");
    expect(merged).toContain("text-label");
  });

  it("still lets a later explicit colour win the conflict", () => {
    expect(cn("text-primary-foreground text-label", "text-white")).toBe(
      "text-label text-white",
    );
  });

  it("still removes genuinely conflicting colours", () => {
    expect(cn("text-foreground text-muted-foreground")).toBe(
      "text-muted-foreground",
    );
  });
});

describe("buttonVariants", () => {
  it("emits a high-contrast colour pair for the primary variant", () => {
    for (const size of ["sm", "md", "lg", "icon"] as const) {
      const classes = buttonVariants({ variant: "primary", size });

      expect(classes, `size=${size}`).toContain("bg-primary");
      expect(classes, `size=${size}`).toContain("text-primary-foreground");
    }
  });

  it("emits a readable colour pair for the danger variant", () => {
    const classes = buttonVariants({ variant: "danger", size: "md" });

    expect(classes).toContain("bg-destructive");
    expect(classes).toContain("text-destructive-foreground");
  });

  it("survives cn() with no colour classes dropped", () => {
    const classes = cn(buttonVariants({ variant: "primary", size: "md" }));

    expect(classes).toContain("text-primary-foreground");
    expect(classes).toContain("text-label");
  });
});
