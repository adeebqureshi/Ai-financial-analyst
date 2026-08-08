"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { motion } from "framer-motion";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  [
    "relative inline-flex items-center justify-center",
    "overflow-hidden whitespace-nowrap",
    "rounded-2xl",
    "font-medium",
    "transition-all duration-300",
    "focus-visible:outline-none",
    "focus-visible:ring-2",
    "focus-visible:ring-blue-500/60",
    "disabled:pointer-events-none",
    "disabled:opacity-50",
    "select-none",
  ].join(" "),
  {
    variants: {
      variant: {
        primary: [
          "bg-gradient-to-r",
          "from-blue-600",
          "to-indigo-500",
          "text-white",
          "shadow-lg",
          "shadow-blue-500/20",
          "hover:shadow-blue-500/30",
        ].join(" "),

        secondary: [
          "border",
          "border-white/10",
          "bg-white/5",
          "backdrop-blur-xl",
          "text-white",
          "hover:bg-white/10",
        ].join(" "),

        ghost: [
          "bg-transparent",
          "text-zinc-300",
          "hover:bg-white/5",
          "hover:text-white",
        ].join(" "),
      },

      size: {
        sm: "h-9 px-4 text-sm",

        md: "h-11 px-6",

        lg: "h-12 px-8 text-base",

        xl: "h-14 px-10 text-lg",
      },
    },

    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export interface PremiumButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function PremiumButton({
  className,
  variant,
  size,
  asChild = false,
  children,
  ...props
}: PremiumButtonProps) {
  const Comp = asChild ? Slot : "button";

  return (
    <motion.div
      whileHover={{
        scale: 1.03,
        y: -1,
      }}
      whileTap={{
        scale: 0.98,
      }}
      transition={{
        type: "spring",
        stiffness: 320,
        damping: 20,
      }}
      className="inline-flex"
    >
      <Comp
        className={cn(
          buttonVariants({
            variant,
            size,
          }),
          className
        )}
        {...props}
      >
        <span className="relative z-10">
          {children}
        </span>

        <span
          className="
            absolute
            inset-0
            opacity-0
            transition-opacity
            duration-300
            hover:opacity-100
            bg-gradient-to-r
            from-white/10
            to-transparent
          "
        />
      </Comp>
    </motion.div>
  );
}