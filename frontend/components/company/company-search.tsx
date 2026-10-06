"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Building2, Search } from "lucide-react";

import { CompanyLogo } from "@/components/company/company-logo";
import { cn } from "@/lib/utils";
import { resolveCompany, searchCompanies } from "@/lib/companies";
import type { CompanyInfo } from "@/lib/companies";

export type { CompanyInfo };

type Props = {
  value: string;
  onValueChange: (value: string) => void;
  onSelect: (company: CompanyInfo) => void;
  placeholder?: string;
  ariaLabel?: string;
  autoFocus?: boolean;
  id?: string;
  limit?: number;
  className?: string;
  inputClassName?: string;
  disabled?: boolean;
};


export function CompanySearch({
  value,
  onValueChange,
  onSelect,
  placeholder = "Search company or ticker (e.g. NVIDIA or NVDA)",
  ariaLabel = "Search company or ticker",
  autoFocus = false,
  id,
  limit = 8,
  className,
  inputClassName,
  disabled = false,
}: Props) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const listboxId = `${inputId}-listbox`;
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [touched, setTouched] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  const results = useMemo(() => searchCompanies(value, limit), [value, limit]);
  const showDropdown = open && touched && value.trim().length >= 1;
  const resolved = useMemo(() => resolveCompany(value), [value]);
  const safeActive = results.length ? active % results.length : 0;

  useEffect(() => {
    function onDown(event: MouseEvent) {
      if (!wrapRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  function choose(company: CompanyInfo) {
    setOpen(false);
    onSelect(company);
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
      return;
    }
    if (!showDropdown) {
      if (event.key === "ArrowDown" && value.trim()) {
        event.preventDefault();
        setOpen(true);
      }
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((i) => (results.length ? (i + 1) % results.length : 0));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((i) => (results.length ? (i - 1 + results.length) % results.length : 0));
    } else if (event.key === "Enter" && results[safeActive]) {
      event.preventDefault();
      choose(results[safeActive]);
    }
  }

  const activeId = results.length ? `${listboxId}-option-${safeActive}` : undefined;
  const showNoResults = showDropdown && results.length === 0;
  const showHint = touched && value.trim().length > 0 && !resolved && !showDropdown;

  return (
    <div ref={wrapRef} className={cn("relative min-w-0 flex-1", className)}>
      <div className="flex min-w-0 flex-1 items-center gap-2.5">
        <Search size={18} className="shrink-0 text-brand" aria-hidden="true" />
        <input
          id={inputId}
          type="text"
          role="combobox"
          aria-expanded={showDropdown}
          aria-controls={listboxId}
          aria-activedescendant={activeId}
          aria-autocomplete="list"
          aria-label={ariaLabel}
          value={value}
          disabled={disabled}
          autoFocus={autoFocus}
          autoComplete="off"
          spellCheck={false}
          placeholder={placeholder}
          onChange={(e) => {
            onValueChange(e.target.value);
            setTouched(true);
            setOpen(true);
            setActive(0);
          }}
          onFocus={() => {
            setTouched(true);
            if (value.trim()) setOpen(true);
          }}
          onKeyDown={onKeyDown}
          className={cn("min-w-0 flex-1 bg-transparent text-body text-foreground placeholder:text-subtle-foreground focus:outline-none", inputClassName)}
        />
      </div>
      {showHint && (
        <p role="alert" className="mt-1 text-caption font-medium text-loss">
          No matching company found. Select a company from the suggestions.
        </p>
      )}
      {showDropdown && results.length > 0 && (
        <ul
          id={listboxId}
          role="listbox"
          aria-label="Matching companies"
          className="absolute left-0 right-0 top-full z-50 mt-2 overflow-hidden rounded-xl border border-border bg-popover shadow-overlay"
        >
          {results.map((company, index) => (
            <li key={company.ticker} role="presentation">
              <button
                type="button"
                id={`${listboxId}-option-${index}`}
                role="option"
                aria-selected={index === safeActive}
                onMouseEnter={() => setActive(index)}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => choose(company)}
                className={cn(
                  "flex w-full items-center gap-3 px-3.5 py-2.5 text-left transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring",
                  index === safeActive ? "bg-accent text-accent-foreground" : "text-foreground hover:bg-muted",
                )}
              >
                <CompanyLogo ticker={company.ticker} size="xs" decorative />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-label font-medium">{company.name}</span>
                  {company.exchange && (
                    <span className="block truncate text-caption text-muted-foreground">{company.exchange}</span>
                  )}
                </span>
                <span className="tnum shrink-0 rounded-md border border-border bg-surface px-2 py-0.5 font-mono text-caption font-semibold tracking-[0.05em] text-muted-foreground">
                  {company.ticker}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {showNoResults && (
        <div className="absolute left-0 right-0 top-full z-50 mt-2 rounded-xl border border-border bg-popover px-4 py-3 shadow-overlay">
          <p className="flex items-center gap-2 text-label text-muted-foreground">
            <Building2 size={15} aria-hidden="true" />
            No companies found
          </p>
        </div>
      )}
    </div>
  );
}
