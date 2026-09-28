"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Sparkles, X } from "lucide-react";

import { ChatSurface } from "@/components/ui/chat-surface";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type CopilotOpenOptions = {
  prompt?: string;
  sessionId?: string | null;
};

type CopilotContextValue = {
  isOpen: boolean;
  hasOpened: boolean;
  prompt: string | null;
  sessionId: string | null;
  open: (options?: CopilotOpenOptions) => void;
  close: () => void;
  toggle: () => void;
};

const CopilotContext = createContext<CopilotContextValue | null>(null);

export function CopilotProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [hasOpened, setHasOpened] = useState(false);
  const [prompt, setPrompt] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const open = useCallback((options?: CopilotOpenOptions) => {
    setPrompt(options?.prompt ?? null);
    setSessionId(options?.sessionId ?? null);
    setHasOpened(true);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => setIsOpen(false), []);

  const toggle = useCallback(() => {
    setHasOpened(true);
    setIsOpen((current) => {
      if (current) {
        setPrompt(null);
        setSessionId(null);
      }

      return !current;
    });
  }, []);

  const value = useMemo<CopilotContextValue>(
    () => ({ isOpen, hasOpened, prompt, sessionId, open, close, toggle }),
    [close, hasOpened, isOpen, open, prompt, sessionId, toggle]
  );

  return (
    <CopilotContext.Provider value={value}>{children}</CopilotContext.Provider>
  );
}

export function useCopilot(): CopilotContextValue {
  return (
    useContext(CopilotContext) ?? {
      isOpen: false,
      hasOpened: false,
      prompt: null,
      sessionId: null,
      open: () => undefined,
      close: () => undefined,
      toggle: () => undefined,
    }
  );
}

export function CopilotDrawer() {
  const { isOpen, hasOpened, prompt, sessionId, close } = useCopilot();

  return (
    <>
      {isOpen && (
        <button
          type="button"
          aria-label="Close AI copilot"
          onClick={close}
          className="fixed inset-0 z-40 bg-foreground/25 backdrop-blur-[2px] motion-safe:animate-in motion-safe:fade-in sm:hidden"
        />
      )}

      <aside
        aria-label="AI copilot"
        aria-hidden={!isOpen}
        className={cn(
          "fixed inset-x-0 bottom-0 z-50 flex h-[82vh] flex-col",
          "border-t border-border bg-card shadow-overlay",
          "transition-[transform,visibility] duration-200 ease-out",
          isOpen ? "visible translate-y-0" : "invisible translate-y-full",
          "sm:inset-y-0 sm:left-auto sm:right-0 sm:h-full sm:w-[26rem]",
          "sm:border-l sm:border-t-0 sm:rounded-none",
          isOpen
            ? "sm:translate-x-0 sm:translate-y-0"
            : "invisible sm:translate-x-full sm:translate-y-0"
        )}
      >
        <header className="flex shrink-0 items-center justify-between gap-3 border-b border-border px-4 py-3">
          <div className="flex min-w-0 items-center gap-2.5">
            <span
              className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-brand-subtle text-brand"
              aria-hidden="true"
            >
              <Sparkles size={15} />
            </span>

            <div className="min-w-0">
              <h2 className="truncate text-label font-semibold text-foreground">
                AI Copilot
              </h2>
              <p className="truncate text-caption text-muted-foreground">
                Grounded in filings, documents and statements
              </p>
            </div>
          </div>

          <Button
            variant="ghost"
            size="icon-sm"
            onClick={close}
            aria-label="Close AI copilot"
          >
            <X size={16} aria-hidden="true" />
          </Button>
        </header>

        <div className="min-h-0 flex-1 p-3">
          {hasOpened && (
          <ChatSurface
            key="copilot-drawer"
            scope="copilot-drawer"
            autoPrompt={prompt}
            sessionId={sessionId}
            inputLabel="Ask the AI copilot a financial research question"
            placeholder="e.g. Compare NVDA and AMD on valuation and risk…"
          />
          )}
        </div>
      </aside>
    </>
  );
}

export function CopilotFab() {
  const { isOpen, open } = useCopilot();

  return (
    <button
      type="button"
      onClick={() => open()}
      aria-label="Open AI copilot"
      title="Ask the AI copilot (Ctrl+K)"
      className={cn(
        "fixed bottom-5 right-5 z-30 inline-flex h-12 items-center gap-2 rounded-full",
        "border border-border bg-primary px-4 text-label font-medium text-primary-foreground",
        "shadow-overlay transition-[transform,opacity] duration-150",
        "hover:scale-[1.02] active:scale-[0.99]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        isOpen ? "pointer-events-none scale-95 opacity-0" : "opacity-100"
      )}
    >
      <Sparkles size={17} aria-hidden="true" />
      <span className="hidden sm:inline">Ask AI</span>
    </button>
  );
}
