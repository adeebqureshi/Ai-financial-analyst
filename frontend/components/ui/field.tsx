"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

const controlClassName = [
  "w-full rounded-md border border-input bg-card",
  "text-body text-foreground placeholder:text-subtle-foreground",
  "transition-colors",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
  "focus-visible:ring-offset-2 focus-visible:ring-offset-background",
  "disabled:cursor-not-allowed disabled:opacity-50",
  "aria-[invalid=true]:border-destructive",
].join(" ");

export function Input({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      data-slot="input"
      className={cn(controlClassName, "h-9 px-3", className)}
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
      className={cn(controlClassName, "resize-y px-3 py-2 leading-6", className)}
      {...props}
    />
  );
}

export function Select({ className, ...props }: React.ComponentProps<"select">) {
  return (
    <select
      data-slot="select"
      className={cn(controlClassName, "h-9 px-3 pr-8", className)}
      {...props}
    />
  );
}

type FieldProps = {
  label: React.ReactNode;
  /** Id of the control this label describes. */
  htmlFor: string;
  hint?: React.ReactNode;
  error?: React.ReactNode;
  required?: boolean;
  className?: string;
  children: React.ReactNode;
};

/**
 * Label + control + hint/error wrapper.
 *
 * The hint id is `${htmlFor}-hint` and the error id `${htmlFor}-error` so
 * callers can wire `aria-describedby` on the control.
 */
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
        className="block text-label font-medium text-foreground"
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
        <p id={`${htmlFor}-hint`} className="text-caption text-subtle-foreground">
          {hint}
        </p>
      )}

      {error && (
        <p id={`${htmlFor}-error`} role="alert" className="text-caption text-loss">
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
  /** Symbols are 1-5 characters server-side; enforced here too. */
  maxLength?: number;
};

/** Ticker entry that normalises to uppercase as the user types. */
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
      className={cn("font-mono tracking-wide", className)}
      {...props}
    />
  );
}