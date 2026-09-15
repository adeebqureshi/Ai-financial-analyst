"use client";

import { Moon, Sun } from "lucide-react";

import { useTheme } from "@/providers/theme-provider";
import { Button } from "./button";

/**
 * Light/dark switch.
 *
 * Icons are chosen with the `dark` variant rather than React state so the
 * rendered icon always matches the CSS-applied theme (and SSR output is
 * unambiguous during hydration).
 */
export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();

  const label =
    theme === "dark" ? "Switch to light theme" : "Switch to dark theme";

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className={className}
      aria-label={label}
      title={label}
    >
      <Moon className="size-4 dark:hidden" aria-hidden="true" />
      <Sun className="hidden size-4 dark:block" aria-hidden="true" />
    </Button>
  );
}