"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  BarChart3,
  Bot,
  Building2,
  FileText,
  Home,
  Settings,
  Wallet,
} from "lucide-react";

import { cn } from "@/lib/utils";

const items = [
  {
    title: "Dashboard",
    icon: Home,
    href: "/",
  },
  {
    title: "Companies",
    icon: Building2,
    href: "/companies",
  },
  {
    title: "AI Analysis",
    icon: Bot,
    href: "/analysis",
  },
  {
    title: "Portfolio",
    icon: Wallet,
    href: "/portfolio",
  },
  {
    title: "Reports",
    icon: FileText,
    href: "/reports",
  },
  {
    title: "Market",
    icon: BarChart3,
    href: "/market",
  },
];

export function Sidebar() {
  return (
    <div className="flex h-full flex-col">
      {/* Logo */}

      <div className="px-6 py-8">
        <motion.div
          initial={{
            opacity: 0,
            y: 10,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          className="space-y-1"
        >
          <h1 className="text-xl font-semibold tracking-tight text-white">
            FinPilot AI
          </h1>

          <p className="text-xs text-zinc-500">
            Enterprise Financial Intelligence
          </p>
        </motion.div>
      </div>

      {/* Navigation */}

      <nav className="flex-1 px-3">
        <div className="space-y-1">
          {items.map((item, index) => (
            <motion.div
              key={item.title}
              initial={{
                opacity: 0,
                x: -20,
              }}
              animate={{
                opacity: 1,
                x: 0,
              }}
              transition={{
                delay: index * 0.05,
              }}
            >
              <Link
                href={item.href}
                className={cn(
                  "group flex items-center gap-3",
                  "rounded-2xl px-4 py-3",
                  "text-zinc-400",
                  "transition-all duration-300",
                  "hover:bg-white/5",
                  "hover:text-white"
                )}
              >
                <item.icon
                  size={20}
                  className="transition-transform duration-300 group-hover:scale-110"
                />

                <span className="text-sm font-medium">
                  {item.title}
                </span>
              </Link>
            </motion.div>
          ))}
        </div>
      </nav>

      {/* Footer */}

      <div className="border-t border-white/5 p-4">
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-2xl px-4 py-3 text-zinc-400 transition-all hover:bg-white/5 hover:text-white"
        >
          <Settings size={20} />

          <span className="text-sm">
            Settings
          </span>
        </Link>
      </div>
    </div>
  );
}