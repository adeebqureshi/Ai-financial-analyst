"use client";

import { cn } from "@/lib/utils";

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-white/10",
        className
      )}
      {...props}
    />
  );
}

export function SkeletonCard({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl space-y-6",
        className
      )}
      {...props}
    >
      <Skeleton className="h-6 w-1/4 rounded" />
      <Skeleton className="h-8 w-1/2 rounded" />
      <div className="space-y-3">
        <Skeleton className="h-4 w-full rounded" />
        <Skeleton className="h-4 w-3/4 rounded" />
        <Skeleton className="h-4 w-1/2 rounded" />
      </div>
    </div>
  );
}

export function SkeletonMetricCard({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl space-y-4",
        className
      )}
      {...props}
    >
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32 rounded" />
        <Skeleton className="h-10 w-10 rounded-full" />
      </div>
      <Skeleton className="h-12 w-24 rounded" />
      <div className="flex items-center gap-2">
        <Skeleton className="h-4 w-20 rounded-full" />
        <Skeleton className="h-4 w-16 rounded" />
      </div>
    </div>
  );
}

export function SkeletonTable({
  rows = 5,
  cols = 4,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  rows?: number;
  cols?: number;
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
                <Skeleton className="h-4 w-20 rounded" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <tr key={rowIndex} className="border-b border-white/5">
              {Array.from({ length: cols }).map((_, colIndex) => (
                <td key={colIndex} className="p-6 text-center">
                  <Skeleton className="h-6 w-24 mx-auto rounded" />
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
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  height?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl",
        className
      )}
      {...props}
    >
      <div className="mb-8">
        <Skeleton className="h-4 w-32 rounded mb-2" />
        <Skeleton className="h-8 w-48 rounded" />
      </div>
      <div className="h-[400px]" style={{ height }}>
        <div className="h-full flex items-center justify-center">
          <Skeleton className="w-full h-full max-w-md rounded-lg" />
        </div>
      </div>
    </div>
  );
}

export function SkeletonText({
  lines = 3,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  lines?: number;
}) {
  return (
    <div
      className={cn("space-y-2", className)}
      {...props}
    >
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
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
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  items?: number;
}) {
  return (
    <div
      className={cn("space-y-3", className)}
      {...props}
    >
      {Array.from({ length: items }).map((_, i) => (
        <div
          key={i}
          className="flex items-center justify-between rounded-2xl border border-white/5 bg-white/[0.02] px-5 py-4"
        >
          <div className="flex items-center gap-4">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div>
              <Skeleton className="h-5 w-24 rounded mb-1" />
              <Skeleton className="h-4 w-32 rounded" />
            </div>
          </div>
          <Skeleton className="h-6 w-20 rounded" />
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
    <div className={cn("space-y-10", className)} {...props}>
      <SkeletonCard className="max-w-4xl" />
      <SkeletonCard className="max-w-4xl" />
      <SkeletonChart />
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonChart height="500px" />
      <SkeletonCard />
    </div>
  );
}