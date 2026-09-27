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


export const THEME_STORAGE_KEY = "afa-theme";


export const DEFAULT_THEME: Theme = "light";

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


export function applyThemeClass(theme: Theme): void {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.style.colorScheme = theme;
}


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


export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext) ?? NOOP_CONTEXT;
}
