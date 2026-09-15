"use client";

import * as React from "react";
import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { EmptyState } from "./empty-state";

export type SortDirection = "asc" | "desc";

export type DataTableColumn<T> = {
  key: string;
  header: React.ReactNode;
  align?: "left" | "center" | "right";
  /** Set together with `sortValue` to make the column sortable. */
  sortable?: boolean;
  sortValue?: (row: T) => string | number | null | undefined;
  render: (row: T) => React.ReactNode;
  headerClassName?: string;
  cellClassName?: string;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  getRowKey: (row: T, index: number) => string;
  /** Required: describes the table for screen readers. */
  caption: string;
  initialSortKey?: string;
  initialSortDirection?: SortDirection;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
  testId?: string;
  /** Prefer real links in cells; use only for tables of non-navigable rows. */
  onRowClick?: (row: T) => void;
};

const alignClassNames = {
  left: "text-left",
  center: "text-center",
  right: "text-right",
} as const;

/** Missing values always sort last, regardless of direction. */
function compareValues(
  a: string | number | null | undefined,
  b: string | number | null | undefined
): number {
  const aMissing = a === null || a === undefined;
  const bMissing = b === null || b === undefined;

  if (aMissing && bMissing) return 0;
  if (aMissing) return 1;
  if (bMissing) return -1;

  if (typeof a === "number" && typeof b === "number") return a - b;

  return String(a).localeCompare(String(b));
}

export function DataTable<T>({
  columns,
  rows,
  getRowKey,
  caption,
  initialSortKey,
  initialSortDirection = "asc",
  emptyTitle = "Nothing to show yet",
  emptyDescription,
  className,
  testId,
  onRowClick,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = React.useState<string | undefined>(initialSortKey);
  const [sortDirection, setSortDirection] =
    React.useState<SortDirection>(initialSortDirection);

  const sortedRows = React.useMemo(() => {
    const column = columns.find((candidate) => candidate.key === sortKey);
    const readValue = column?.sortValue;

    if (!column?.sortable || !readValue) return rows;

    const direction = sortDirection === "desc" ? -1 : 1;

    return [...rows].sort(
      (a, b) => direction * compareValues(readValue(a), readValue(b))
    );
  }, [columns, rows, sortDirection, sortKey]);

  function toggleSort(column: DataTableColumn<T>) {
    if (sortKey === column.key) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }

    setSortKey(column.key);
    setSortDirection("asc");
  }

  const isEmpty = sortedRows.length === 0;

  return (
    <div
      data-testid={testId}
      className={cn(
        "overflow-hidden rounded-lg border border-border bg-card shadow-card",
        className
      )}
    >
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-label">
          <caption className="sr-only">{caption}</caption>

          <thead>
            <tr className="border-b border-border bg-muted/60">
              {columns.map((column) => {
                const isSorted = sortKey === column.key;
                const canSort =
                  column.sortable === true && Boolean(column.sortValue);

                return (
                  <th
                    key={column.key}
                    scope="col"
                    aria-sort={
                      isSorted
                        ? sortDirection === "asc"
                          ? "ascending"
                          : "descending"
                        : undefined
                    }
                    className={cn(
                      "px-4 py-2.5 font-medium text-muted-foreground",
                      alignClassNames[column.align ?? "left"],
                      column.headerClassName
                    )}
                  >
                    {canSort ? (
                      <button
                        type="button"
                        onClick={() => toggleSort(column)}
                        aria-label={`Sort by ${
                          typeof column.header === "string"
                            ? column.header
                            : column.key
                        }`}
                        className={cn(
                          "inline-flex items-center gap-1.5 rounded-sm transition-colors",
                          "hover:text-foreground",
                          "focus-visible:outline-none focus-visible:ring-2",
                          "focus-visible:ring-ring focus-visible:ring-offset-2",
                          "focus-visible:ring-offset-background",
                          isSorted && "text-foreground"
                        )}
                      >
                        {column.header}

                        {isSorted ? (
                          sortDirection === "asc" ? (
                            <ArrowUp className="size-3.5" aria-hidden="true" />
                          ) : (
                            <ArrowDown className="size-3.5" aria-hidden="true" />
                          )
                        ) : (
                          <ChevronsUpDown
                            className="size-3.5 opacity-50"
                            aria-hidden="true"
                          />
                        )}
                      </button>
                    ) : (
                      column.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>

          <tbody>
            {isEmpty ? (
              <tr>
                <td colSpan={columns.length} className="p-4">
                  <EmptyState
                    title={emptyTitle}
                    description={emptyDescription}
                  />
                </td>
              </tr>
            ) : (
              sortedRows.map((row, index) => (
                <tr
                  key={getRowKey(row, index)}
                  tabIndex={onRowClick ? 0 : undefined}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  onKeyDown={
                    onRowClick
                      ? (event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            onRowClick(row);
                          }
                        }
                      : undefined
                  }
                  className={cn(
                    "border-b border-border last:border-0",
                    onRowClick &&
                      "cursor-pointer transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
                  )}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={cn(
                        "px-4 py-3 text-foreground",
                        alignClassNames[column.align ?? "left"],
                        column.cellClassName
                      )}
                    >
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
