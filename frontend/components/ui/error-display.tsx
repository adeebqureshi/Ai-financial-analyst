"use client";

import { RefreshCw, AlertTriangle, AlertCircle, WifiOff, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { ApiError } from "@/services/api";

type ErrorDisplayProps = {
  error: unknown;
  onRetry?: () => void;
  title?: string;
  className?: string;
  compact?: boolean;
};

function getErrorInfo(error: unknown) {
  if (error instanceof ApiError) {
    if (error.isAuthError()) {
      return {
        icon: Lock,
        title: "Authentication Required",
        message: "Your session has expired. Please sign in again.",
        isRetryable: false,
      };
    }
    if (error.isNotFound()) {
      return {
        icon: AlertCircle,
        title: "Not Found",
        message: "The requested resource could not be found.",
        isRetryable: false,
      };
    }
    if (error.isClientError()) {
      return {
        icon: AlertTriangle,
        title: "Request Failed",
        message: error.message,
        isRetryable: false,
      };
    }
    if (error.isServerError()) {
      return {
        icon: WifiOff,
        title: "Server Error",
        message: "Our servers are having trouble. Please try again in a moment.",
        isRetryable: true,
      };
    }
    return {
      icon: AlertTriangle,
      title: "Error",
      message: error.message,
      isRetryable: error.isRetryable(),
    };
  }

  if (error instanceof TypeError && error.message.includes("fetch")) {
    return {
      icon: WifiOff,
      title: "Connection Failed",
      message: "Unable to connect to the server. Please check your internet connection.",
      isRetryable: true,
    };
  }

  if (error instanceof Error) {
    return {
      icon: AlertTriangle,
      title: "Error",
      message: error.message,
      isRetryable: true,
    };
  }

  return {
    icon: AlertTriangle,
    title: "Unknown Error",
    message: "An unexpected error occurred.",
    isRetryable: true,
  };
}

export function ErrorDisplay({
  error,
  onRetry,
  title,
  className,
  compact = false,
}: ErrorDisplayProps) {
  const { icon: Icon, title: defaultTitle, message, isRetryable } = getErrorInfo(error);

  return (
    <div
      className={cn(
        "rounded-2xl border p-6 text-center transition-colors",
        compact
          ? "border-white/10 bg-white/[0.02] p-4"
          : "border-red-500/20 bg-red-500/10",
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <Icon
        size={compact ? 24 : 40}
        className={cn(
          "mx-auto text-red-400",
          compact && "text-red-400"
        )}
        aria-hidden="true"
      />

      <h2 className={cn("mt-4 font-bold", compact ? "text-lg" : "text-2xl")} style={{ color: "white" }}>
        {title ?? defaultTitle}
      </h2>

      <p className={cn("mt-2 text-zinc-300", compact ? "text-sm" : "text-base")}>
        {message}
      </p>

      {isRetryable && onRetry && (
        <button
          onClick={onRetry}
          className={cn(
            "mt-4 inline-flex items-center gap-2 rounded-xl font-medium transition focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-[#05060A]",
            compact
              ? "px-4 py-2 text-sm border border-white/10 bg-white/5 text-zinc-300 hover:bg-white/10"
              : "px-6 py-3 bg-white text-black hover:bg-blue-100"
          )}
          aria-label="Retry the failed operation"
        >
          <RefreshCw size={16} aria-hidden="true" />
          Try again
        </button>
      )}
    </div>
  );
}

export function ErrorInline({
  error,
  onRetry,
  className,
}: {
  error: unknown;
  onRetry?: () => void;
  className?: string;
}) {
  const { icon: Icon, message, isRetryable } = getErrorInfo(error);

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-red-400 text-sm",
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <Icon size={16} aria-hidden="true" />
      <span>{message}</span>
      {isRetryable && onRetry && (
        <button
          onClick={onRetry}
          className="ml-2 px-3 py-1 text-xs font-medium rounded-lg border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 transition"
          aria-label="Retry"
        >
          <RefreshCw size={12} aria-hidden="true" />
        </button>
      )}
    </div>
  );
}