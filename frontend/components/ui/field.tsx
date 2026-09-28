"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

const controlClassName = [
  "w-full rounded-lg border border-input bg-card",
  "text-body text-foreground placeholder:text-subtle-foreground",
  "transition-[border-color,box-shadow,background-color]",
  "hover:border-border-strong",
  "focus-visible:border-ring focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/25",
  "disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground",
  "aria-[invalid=true]:border-loss",
].join(" ");

export function Input({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      data-slot="input"
      className={cn(controlClassName, "h-10 px-3.5 text-label", className)}
      {...props}
    />
  );
}

export function Textarea({
  className,
  ...props
}: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(controlClassName, "resize-y px-3.5 py-2.5 text-label leading-6", className)}
      {...props}
    />
  );
}

export function Select({ className, ...props }: React.ComponentProps<"select">) {
  return (
    <select
      data-slot="select"
      className={cn(controlClassName, "h-10 px-3.5 pr-8 text-label", className)}
      {...props}
    />
  );
}

type FieldProps = {
  label: React.ReactNode;
  htmlFor: string;
  hint?: React.ReactNode;
  error?: React.ReactNode;
  required?: boolean;
  className?: string;
  children: React.ReactNode;
};

export function Field({
  label,
  htmlFor,
  hint,
  error,
  required = false,
  className,
  children,
}: FieldProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <label
        htmlFor={htmlFor}
        className="block text-caption font-semibold uppercase tracking-[0.08em] text-subtle-foreground"
      >
        {label}
        {required && (
          <span className="ml-1 text-loss" aria-hidden="true">
            *
          </span>
        )}
      </label>

      {children}

      {hint && !error && (
        <p
          id={`${htmlFor}-hint`}
          className="text-caption leading-relaxed text-muted-foreground"
        >
          {hint}
        </p>
      )}

      {error && (
        <p
          id={`${htmlFor}-error`}
          role="alert"
          className="text-caption font-medium text-loss"
        >
          {error}
        </p>
      )}
    </div>
  );
}

type TickerInputProps = Omit<
  React.ComponentProps<"input">,
  "value" | "onChange" | "maxLength"
> & {
  value: string;
  onValueChange: (value: string) => void;
  maxLength?: number;
};

export function TickerInput({
  value,
  onValueChange,
  maxLength = 5,
  className,
  ...props
}: TickerInputProps) {
  return (
    <Input
      value={value}
      onChange={(event) => onValueChange(event.target.value.toUpperCase())}
      maxLength={maxLength}
      autoCapitalize="characters"
      autoComplete="off"
      spellCheck={false}
      inputMode="text"
      className={cn("font-mono tracking-[0.06em]", className)}
      {...props}
    />
  );
}
