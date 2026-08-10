"use client";

import * as React from "react";
import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

type GlassCardProps = {
  hover?: boolean;
  glow?: boolean;
  children?: React.ReactNode;
} & Omit<HTMLMotionProps<"div">, "ref" | "children">;

export function GlassCard({
  hover = true,
  glow = false,
  children,
  className,
  ...props
}: GlassCardProps) {
  return (
    <motion.div
      whileHover={
        hover
          ? {
              y: -4,
              scale: 1.01,
            }
          : undefined
      }
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 20,
      }}
      className={cn(
        "relative overflow-hidden rounded-3xl",
        "border border-white/10",
        "bg-white/[0.04]",
        "backdrop-blur-2xl",
        "shadow-2xl",
        glow &&
          "shadow-[0_0_40px_rgba(79,124,255,0.15)] border-blue-400/20",
        className
      )}
      {...props}
    >
      {/* Gradient Border */}
      <div
        className="
          pointer-events-none
          absolute
          inset-0
          rounded-3xl
          bg-gradient-to-br
          from-white/10
          via-transparent
          to-blue-400/10
        "
      />

      {/* Soft Highlight */}
      <div
        className="
          pointer-events-none
          absolute
          -top-20
          left-1/2
          h-40
          w-40
          -translate-x-1/2
          rounded-full
          bg-white/10
          blur-3xl
        "
      />

      <div className="relative z-10">
        {children}
      </div>
    </motion.div>
  );
}