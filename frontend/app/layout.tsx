import type { Metadata } from "next";
import Script from "next/script";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { QueryProvider } from "@/providers/query-provider";
import { DEFAULT_THEME, ThemeProvider } from "@/providers/theme-provider";

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
      <body>
        <Script
          id="theme-init"
          src="/theme-init.js"
          strategy="beforeInteractive"
        />
        <ThemeProvider>
          <QueryProvider>
            {children}
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
