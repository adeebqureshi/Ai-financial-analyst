"use client";

import ReactMarkdown, { type Components } from "react-markdown";

import { cn } from "@/lib/utils";

/**
 * Shared markdown renderer.
 *
 * Extracted from the agent workspace so the chat transcript and the generated
 * investment report render identically. Replaces the previous `prose` classes
 * on the report viewer, which had no effect because `@tailwindcss/typography`
 * is not installed.
 */
export const markdownComponents: Components = {
  h1: (props) => (
    <h1 {...props} className="mb-3 mt-6 text-title text-foreground first:mt-0" />
  ),
  h2: (props) => (
    <h2 {...props} className="mb-3 mt-6 text-title text-foreground first:mt-0" />
  ),
  h3: (props) => (
    <h3
      {...props}
      className="mb-2 mt-5 text-body font-semibold text-foreground first:mt-0"
    />
  ),
  p: (props) => (
    <p {...props} className="mb-3 text-body leading-7 text-muted-foreground" />
  ),
  strong: (props) => (
    <strong {...props} className="font-semibold text-foreground" />
  ),
  em: (props) => <em {...props} className="italic text-foreground" />,
  a: (props) => (
    <a
      {...props}
      target="_blank"
      rel="noreferrer"
      className="text-brand underline underline-offset-2 hover:text-brand/80"
    />
  ),
  ul: (props) => (
    <ul {...props} className="mb-3 list-disc space-y-1.5 pl-5 text-body" />
  ),
  ol: (props) => (
    <ol {...props} className="mb-3 list-decimal space-y-1.5 pl-5 text-body" />
  ),
  li: (props) => (
    <li {...props} className="leading-7 text-muted-foreground" />
  ),
  blockquote: (props) => (
    <blockquote
      {...props}
      className="mb-3 border-l-2 border-border-strong pl-4 text-muted-foreground"
    />
  ),
  code: (props) => (
    <code
      {...props}
      className="rounded-sm bg-muted px-1.5 py-0.5 font-mono text-caption text-foreground"
    />
  ),
  pre: (props) => (
    <pre
      {...props}
      className="mb-3 overflow-x-auto rounded-md border border-border bg-muted p-4 font-mono text-caption text-foreground"
    />
  ),
  hr: () => <hr className="my-6 border-border" />,
  table: (props) => (
    <div className="mb-3 overflow-x-auto">
      <table {...props} className="tnum w-full border-collapse text-label" />
    </div>
  ),
  th: (props) => (
    <th
      {...props}
      className="border border-border bg-muted px-3 py-2 text-left font-medium text-foreground"
    />
  ),
  td: (props) => (
    <td
      {...props}
      className="border border-border px-3 py-2 text-muted-foreground"
    />
  ),
};

export function Markdown({
  children,
  className,
  components,
}: {
  children: string;
  className?: string;
  components?: Components;
}) {
  return (
    <div className={cn("text-body text-foreground", className)}>
      <ReactMarkdown components={components ?? markdownComponents}>
        {children}
      </ReactMarkdown>
    </div>
  );
}