"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";

export type Theme = "light" | "dark";

/** localStorage key used by the provider and the pre-paint script in `app/layout.tsx`. */
export const THEME_STORAGE_KEY = "afa-theme";

/**
 * Shipped default theme.
 *
 * Kept at ``dark`` while the page-by-page token migration is in flight so the
 * live app keeps its current look at every commit. The final polish phase
 * flips this single constant to ``light``, making the light-first palette the
 * default without touching any component.
 */
export const DEFAULT_THEME: Theme = "dark";

type ThemeContextValue = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
};

const NOOP_CONTEXT: ThemeContextValue = {
  theme: DEFAULT_THEME,
  setTheme: () => undefined,
  toggleTheme: () => undefined,
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function isDarkClassApplied(): boolean {
  if (typeof document === "undefined") return DEFAULT_THEME === "dark";
  return document.documentElement.classList.contains("dark");
}

/** Apply the theme to `document.documentElement` (the Tailwind `dark` class owner). */
export function applyThemeClass(theme: Theme): void {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.style.colorScheme = theme;
}

/**
 * The applied theme lives on `<html>` (written by the pre-paint script in the
 * root layout and by {@link applyThemeClass}), so the DOM is the single source
 * of truth. Subscribing to it keeps React in sync without a mount-time
 * `setState`, which React 19 flags as a cascading render.
 */
function subscribeToTheme(onStoreChange: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;

  const observer = new MutationObserver(onStoreChange);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class"],
  });

  window.addEventListener("storage", onStoreChange);

  return () => {
    observer.disconnect();
    window.removeEventListener("storage", onStoreChange);
  };
}

function getThemeSnapshot(): Theme {
  return isDarkClassApplied() ? "dark" : "light";
}

type Props = {
  children: ReactNode;
  /** Theme assumed during SSR, before the client snapshot is available. */
  defaultTheme?: Theme;
};

export function ThemeProvider({ children, defaultTheme = DEFAULT_THEME }: Props) {
  const theme = useSyncExternalStore(
    subscribeToTheme,
    getThemeSnapshot,
    () => defaultTheme
  );

  const setTheme = useCallback((next: Theme) => {
    applyThemeClass(next);

    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch {
      // Persisting is best-effort; the applied class is the source of truth.
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(getThemeSnapshot() === "dark" ? "light" : "dark");
  }, [setTheme]);

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, setTheme, toggleTheme }),
    [setTheme, theme, toggleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * Access the current theme.
 *
 * Returns a no-op context when used outside {@link ThemeProvider} so isolated
 * component tests never crash.
 */
export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext) ?? NOOP_CONTEXT;
}