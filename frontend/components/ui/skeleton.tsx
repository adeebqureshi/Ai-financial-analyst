"use client";

import { cn } from "@/lib/utils";

export function Skeleton({
  className,
  animate = true,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { animate?: boolean }) {
  return (
    <div
      className={cn(
        animate ? "animate-pulse" : "",
        "rounded-md bg-white/10",
        className
      )}
      {...props}
    />
  );
}

export function SkeletonWrapper({
  className,
  animate = true,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { animate?: boolean }) {
  return (
    <div
      className={cn(animate ? "animate-pulse" : "", "rounded-md bg-white/10", className)}
      {...props}
    />
  );
}

export function SkeletonCard({
  className,
  animate = true,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { animate?: boolean }) {
  return (
    <div
      data-testid="skeleton-card"
      className={cn(
        "rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl space-y-6",
        className
      )}
      {...props}
    >
      <Skeleton animate={animate} className="h-6 w-1/4 rounded" />
      <Skeleton animate={animate} className="h-8 w-1/2 rounded" />
      <div className="space-y-3">
        <Skeleton animate={animate} className="h-4 w-full rounded" />
        <Skeleton animate={animate} className="h-4 w-3/4 rounded" />
        <Skeleton animate={animate} className="h-4 w-1/2 rounded" />
      </div>
    </div>
  );
}

export function SkeletonMetricCard({
  className,
  animate = true,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { animate?: boolean }) {
  return (
    <div
      className={cn(
        "rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl space-y-4",
        className
      )}
      {...props}
    >
      <div className="flex items-center justify-between">
        <Skeleton animate={animate} className="h-4 w-32 rounded" />
        <Skeleton animate={animate} className="h-10 w-10 rounded-full" />
      </div>
      <Skeleton animate={animate} className="h-12 w-24 rounded" />
      <div className="flex items-center gap-2">
        <Skeleton animate={animate} className="h-4 w-20 rounded-full" />
        <Skeleton animate={animate} className="h-4 w-16 rounded" />
      </div>
    </div>
  );
}

export function SkeletonTable({
  rows = 5,
  cols = 4,
  className,
  animate = true,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  rows?: number;
  cols?: number;
  animate?: boolean;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-[32px] border border-white/10 bg-white/[0.03]",
        className
      )}
      {...props}
    >
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/10">
            {Array.from({ length: cols }).map((_, i) => (
              <th key={i} className="p-6 text-left">
                <Skeleton animate={animate} className="h-4 w-20 rounded" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <tr key={rowIndex} className="border-b border-white/5">
              {Array.from({ length: cols }).map((_, colIndex) => (
                <td key={colIndex} className="p-6 text-center">
                  <Skeleton animate={animate} className="h-6 w-24 mx-auto rounded" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SkeletonChart({
  className,
  height = "400px",
  animate = true,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  height?: string;
  animate?: boolean;
}) {
  return (
    <div
      data-testid="skeleton-chart"
      className={cn(
        "rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl",
        className
      )}
      {...props}
    >
      <div className="mb-8">
        <Skeleton animate={animate} className="h-4 w-32 rounded mb-2" />
        <Skeleton animate={animate} className="h-8 w-48 rounded" />
      </div>
      <div className="h-[400px]" style={{ height }}>
        <div className="h-full flex items-center justify-center">
          <Skeleton animate={animate} className="w-full h-full max-w-md rounded-lg" />
        </div>
      </div>
    </div>
  );
}

export function SkeletonText({
  lines = 3,
  className,
  animate = true,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  lines?: number;
  animate?: boolean;
}) {
  return (
    <div
      className={cn("space-y-2", className)}
      {...props}
    >
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          animate={animate}
          className={`h-4 rounded ${
            i === lines - 1 ? "w-3/4" : "w-full"
          }`}
        />
      ))}
    </div>
  );
}

export function SkeletonList({
  items = 5,
  className,
  animate = true,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  items?: number;
  animate?: boolean;
}) {
  return (
    <div
      className={cn("space-y-3", className)}
      {...props}
    >
      {Array.from({ length: items }).map((_, i) => (
        <div
          key={i}
          data-testid="skeleton-list-item"
          className="flex items-center justify-between rounded-2xl border border-white/5 bg-white/[0.02] px-5 py-4"
        >
          <div className="flex items-center gap-4">
            <Skeleton animate={animate} className="h-10 w-10 rounded-full" />
            <div>
              <Skeleton animate={animate} className="h-5 w-24 rounded mb-1" />
              <Skeleton animate={animate} className="h-4 w-32 rounded" />
            </div>
          </div>
          <Skeleton animate={animate} className="h-6 w-20 rounded" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonAnalysisView({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div data-testid="skeleton-analysis-view" className={cn("animate-pulse space-y-10", className)} {...props}>
      <SkeletonCard animate={false} className="max-w-4xl" />
      <SkeletonCard animate={false} className="max-w-4xl" />
      <SkeletonChart animate={false} />
      <SkeletonCard animate={false} />
      <SkeletonCard animate={false} />
      <SkeletonCard animate={false} />
      <SkeletonChart animate={false} height="500px" />
      <SkeletonCard animate={false} />
    </div>
  );
}