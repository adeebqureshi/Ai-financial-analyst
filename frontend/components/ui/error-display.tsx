"use client";

import { RefreshCw, AlertTriangle, AlertCircle, WifiOff, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { ApiError } from "@/services/api";

import { Button } from "./button";

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
        title: "Not Authenticated",
        message: "Please refresh the page to continue.",
        isRetryable: true,
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
        message: "Our servers are having trouble. Please wait a moment and retry.",
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
        "rounded-lg border border-loss/30 bg-loss-subtle text-center",
        compact ? "p-4" : "p-6",
        className
      )}
      role="alert"
    >
      <Icon
        className={cn("mx-auto text-loss", compact ? "size-6" : "size-9")}
        aria-hidden="true"
      />

      <h2
        className={cn(
          "mt-3 text-foreground",
          compact ? "text-body font-semibold" : "text-title"
        )}
      >
        {title ?? defaultTitle}
      </h2>

      <p
        className={cn(
          "mt-1.5 text-muted-foreground",
          compact ? "text-caption" : "text-label"
        )}
      >
        {message}
      </p>

      {isRetryable && onRetry && (
        <div className="mt-4 flex justify-center">
          <Button variant="secondary" size={compact ? "sm" : "md"} onClick={onRetry}>
            <RefreshCw className="size-3.5" aria-hidden="true" />
            Try again
          </Button>
        </div>
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
        "inline-flex flex-wrap items-center gap-2 rounded-md border border-loss/30 bg-loss-subtle px-3 py-2 text-label text-loss",
        className
      )}
      role="alert"
    >
      <Icon
        className="size-4 shrink-0"
        aria-hidden="true"
      />
      <span className="min-w-0">{message}</span>
      {isRetryable && onRetry && (
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onRetry}
          className="text-loss hover:bg-loss/10 hover:text-loss"
          aria-label="Retry"
        >
          <RefreshCw className="size-3.5" aria-hidden="true" />
        </Button>
      )}
    </div>
  );
}