import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { RecentAnalyses } from "@/components/analysis/recent-analyses";
import { ApiError } from "@/services/api";

/**
 * Delete-a-research-session coverage.
 *
 * The list runs against a real `QueryClient` seeded with a `["chat-sessions"]`
 * payload, and `fetch` is stubbed by a small *stateful* fake server: a
 * successful DELETE really removes the session from what `GET /chat/sessions`
 * returns afterwards. That matters — the mutation invalidates the query, so a
 * stub that ignored deletions would just re-add the row and hide a real bug.
 *
 * `fireEvent` matches the convention used by the other suites.
 */

type Session = {
  session_id: string;
  title: string | null;
  updated_at: string;
};

const INITIAL: Session[] = [
  {
    session_id: "sess-nvda",
    title: "Is NVDA overvalued?",
    updated_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
  },
  {
    session_id: "sess-aapl",
    title: "Compare AAPL and MSFT",
    updated_at: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(),
  },
  {
    session_id: "sess-untitled",
    title: null,
    updated_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
  },
];

function listPayload(sessions: Session[]) {
  return {
    success: true,
    message: `${sessions.length} chat sessions`,
    data: { sessions, total: sessions.length },
  };
}

let queryClient: QueryClient;
/** The fake server's persisted state. */
let serverSessions: Session[];
let deleteCalls: string[];
let deleteResponder: (id: string) => Promise<Response>;

function renderList() {
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return render(<RecentAnalyses />, { wrapper });
}

/** Text of the session list only, so dialog copy can't create false matches. */
function listText(): string {
  return screen.queryByRole("list")?.textContent ?? "";
}

function actionsButton(label: string) {
  return screen.getByRole("button", { name: `Actions for ${label}` });
}

/** Open a row's overflow menu, then choose Delete. Leaves the dialog open. */
function openDeleteDialog(label: string) {
  fireEvent.click(actionsButton(label));
  fireEvent.click(
    within(screen.getByRole("menu")).getByRole("menuitem", { name: /Delete/ })
  );
  return screen.getByRole("dialog");
}

function confirmInDialog() {
  fireEvent.click(
    within(screen.getByRole("dialog")).getByRole("button", { name: "Delete" })
  );
}

describe("RecentAnalyses delete", () => {
  beforeEach(() => {
    deleteCalls = [];
    serverSessions = INITIAL.map((s) => ({ ...s }));
    deleteResponder = async () => new Response(null, { status: 204 });

    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: 0 },
        mutations: { retry: false },
      },
    });

    queryClient.setQueryData(["chat-sessions"], listPayload(serverSessions));

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const method = init?.method ?? "GET";
        const isCollection =
          url.includes("/chat/sessions") && !url.includes("/messages");

        if (method === "DELETE" && isCollection) {
          const id = decodeURIComponent(
            url.split("/chat/sessions/")[1].split("?")[0]
          );
          deleteCalls.push(id);

          const response = await deleteResponder(id);

          // Only drop it server-side when the delete actually succeeded.
          if (response.status === 204) {
            serverSessions = serverSessions.filter((s) => s.session_id !== id);
          }

          return response;
        }

        if (isCollection) {
          return new Response(JSON.stringify(listPayload(serverSessions)), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }

        return new Response("{}", {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("renders a delete control for every session", async () => {
    renderList();

    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    expect(actionsButton("Is NVDA overvalued?")).toBeInTheDocument();
    expect(actionsButton("Compare AAPL and MSFT")).toBeInTheDocument();
    // An untitled session keeps the honest fallback, not an invented title.
    expect(actionsButton("Research session")).toBeInTheDocument();
    expect(listText()).toContain("Research session");
  });

  it("does not delete on the first click — confirmation is required", async () => {
    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    const dialog = openDeleteDialog("Is NVDA overvalued?");

    expect(within(dialog).getByText("Delete research session?")).toBeInTheDocument();
    expect(dialog).toHaveAccessibleDescription(/permanently delete/i);

    // Untouched until the dialog is confirmed.
    expect(listText()).toContain("Is NVDA overvalued?");
    expect(deleteCalls).toHaveLength(0);
  });

  it("cancel keeps the session and sends no request", async () => {
    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    fireEvent.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Cancel" })
    );

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
    );
    expect(listText()).toContain("Is NVDA overvalued?");
    expect(deleteCalls).toHaveLength(0);
    expect(serverSessions).toHaveLength(3);
  });

  it("confirming sends exactly one DELETE for that session and removes the row", async () => {
    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    confirmInDialog();

    await waitFor(() => expect(listText()).not.toContain("Is NVDA overvalued?"));

    expect(deleteCalls).toEqual(["sess-nvda"]);

    // Other sessions are untouched.
    expect(listText()).toContain("Compare AAPL and MSFT");
    expect(listText()).toContain("Research session");

    // The cache no longer holds it, so a refetch cannot bring it back.
    const cached = queryClient.getQueryData<ReturnType<typeof listPayload>>([
      "chat-sessions",
    ]);
    expect(cached?.data.sessions.map((s) => s.session_id)).not.toContain(
      "sess-nvda"
    );
  });

  it("stays deleted after the cache refetches", async () => {
    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    confirmInDialog();
    await waitFor(() => expect(listText()).not.toContain("Is NVDA overvalued?"));

    // Force a fresh read from the (stateful) fake server.
    await queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    await waitFor(() => expect(listText()).not.toContain("Is NVDA overvalued?"));

    expect(deleteCalls).toEqual(["sess-nvda"]);
  });

  it("shows the pending label and refuses duplicate DELETEs", async () => {
    let release: () => void = () => {};
    deleteResponder = () =>
      new Promise<Response>((resolve) => {
        release = () => resolve(new Response(null, { status: 204 }));
      });

    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    confirmInDialog();

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Deleting..." })).toBeInTheDocument()
    );
    expect(screen.getByRole("button", { name: "Deleting..." })).toBeDisabled();

    // Keep hammering the now-disabled control and the dialog itself.
    fireEvent.click(screen.getByRole("button", { name: "Deleting..." }));
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Enter" });
    fireEvent.keyDown(screen.getByRole("dialog"), { key: " " });

    expect(deleteCalls).toHaveLength(1);

    release();
    await waitFor(() => expect(listText()).not.toContain("Is NVDA overvalued?"));
    expect(deleteCalls).toHaveLength(1);
  });

  it("cannot be dismissed while the delete is in flight", async () => {
    let release: () => void = () => {};
    deleteResponder = () =>
      new Promise<Response>((resolve) => {
        release = () => resolve(new Response(null, { status: 204 }));
      });

    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    confirmInDialog();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Deleting..." })).toBeInTheDocument()
    );

    // Escape, backdrop and Cancel must not orphan an in-flight request.
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    fireEvent.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Cancel" })
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    release();
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
    );
    expect(deleteCalls).toHaveLength(1);
  });

  it("keeps the session visible and explains the failure when delete fails", async () => {
    deleteResponder = async () =>
      new Response(JSON.stringify({ detail: "kaboom: db exploded" }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });

    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    confirmInDialog();

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Couldn't delete this research session\. Please try again\./
      )
    );

    // A failed delete is never a client-side hide.
    expect(listText()).toContain("Is NVDA overvalued?");
    expect(deleteCalls).toHaveLength(1);
    expect(serverSessions).toHaveLength(3);

    // No backend detail leaks into the UI.
    expect(screen.queryByText(/kaboom/)).not.toBeInTheDocument();
    expect(screen.getByRole("alert").textContent ?? "").not.toMatch(
      /traceback|db exploded/i
    );
  });

  it("treats 404 as a failure rather than silently succeeding", async () => {
    deleteResponder = async () =>
      new Response(JSON.stringify({ detail: "Session not found." }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      });

    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    confirmInDialog();

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(listText()).toContain("Is NVDA overvalued?");
    expect(screen.queryByText(/Session not found/)).not.toBeInTheDocument();
  });

  it("surfaces a 401 without dropping the row", async () => {
    deleteResponder = async () =>
      new Response(JSON.stringify({ detail: "Not authenticated." }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });

    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    confirmInDialog();

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(listText()).toContain("Is NVDA overvalued?");
  });

  it("survives a network failure without dropping the row", async () => {
    deleteResponder = async () => {
      throw new ApiError("network down", 0, "/chat/sessions/sess-nvda");
    };

    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    confirmInDialog();

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(listText()).toContain("Is NVDA overvalued?");
  });

  it("retries after a failure and succeeds", async () => {
    deleteResponder = async () => {
      throw new ApiError("network down", 0, "/chat/sessions/sess-nvda");
    };

    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    confirmInDialog();
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());

    deleteResponder = async () => new Response(null, { status: 204 });
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    await waitFor(() => expect(listText()).not.toContain("Is NVDA overvalued?"));
    expect(deleteCalls).toEqual(["sess-nvda", "sess-nvda"]);
  });

  it("shows the empty state after the final session is deleted", async () => {
    queryClient.setQueryData(
      ["chat-sessions"],
      listPayload([
        {
          session_id: "only",
          title: "Is NVDA overvalued?",
          updated_at: new Date().toISOString(),
        },
      ])
    );
    serverSessions = [
      {
        session_id: "only",
        title: "Is NVDA overvalued?",
        updated_at: new Date().toISOString(),
      },
    ];

    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    openDeleteDialog("Is NVDA overvalued?");
    confirmInDialog();

    await waitFor(() => expect(listText()).not.toContain("Is NVDA overvalued?"));

    // Honest empty state: no leftover rows, no fake records.
    expect(screen.getByText(/No research sessions yet\./)).toBeInTheDocument();
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
    expect(deleteCalls).toEqual(["only"]);
    expect(serverSessions).toEqual([]);
  });

  it("still offers navigation from the menu without deleting", async () => {
    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    fireEvent.click(actionsButton("Is NVDA overvalued?"));

    const openLink = within(screen.getByRole("menu")).getByRole("menuitem", {
      name: /Open session/,
    });
    expect(openLink).toHaveAttribute("href", "/analysis");
    expect(deleteCalls).toHaveLength(0);
  });

  it("closes the menu on Escape", async () => {
    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    const trigger = actionsButton("Is NVDA overvalued?");
    fireEvent.click(trigger);
    expect(screen.getByRole("menu")).toBeInTheDocument();

    fireEvent.keyDown(trigger, { key: "Escape" });
    await waitFor(() =>
      expect(screen.queryByRole("menu")).not.toBeInTheDocument()
    );
  });

  it("exposes accessible names and menu state on the delete controls", async () => {
    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    const trigger = actionsButton("Is NVDA overvalued?");
    expect(trigger).toHaveAttribute("aria-haspopup", "menu");
    expect(trigger).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("menu")).toHaveAccessibleName(
      "Actions for Is NVDA overvalued?"
    );
  });

  it("gives the dialog an accessible name and description", async () => {
    renderList();
    await waitFor(() => expect(listText()).toContain("Is NVDA overvalued?"));

    const dialog = openDeleteDialog("Is NVDA overvalued?");

    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAccessibleName("Delete research session?");
    expect(dialog).toHaveAccessibleDescription(/conversation history/i);
    expect(dialog).toHaveAccessibleDescription(/cannot be undone/i);
  });
});