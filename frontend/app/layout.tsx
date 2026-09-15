import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { QueryProvider } from "@/providers/query-provider";
import {
  DEFAULT_THEME,
  THEME_STORAGE_KEY,
  ThemeProvider,
} from "@/providers/theme-provider";

const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Financial Analyst",
  description: "Enterprise AI Financial Platform",
};

/**
 * Applies the persisted theme before first paint so the workspace never
 * flashes the wrong palette. Mirrors `ThemeProvider`'s storage key and default.
 */
const themeScript = `(function(){try{var k=${JSON.stringify(
  THEME_STORAGE_KEY
)};var s=window.localStorage.getItem(k);var t=s==="light"||s==="dark"?s:${JSON.stringify(
  DEFAULT_THEME
)};var r=document.documentElement;r.classList.toggle("dark",t==="dark");r.style.colorScheme=t;}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={[
        geistSans.variable,
        geistMono.variable,
        DEFAULT_THEME === "dark" ? "dark" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>

      <body>
        <ThemeProvider>
          <QueryProvider>
            {children}
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}