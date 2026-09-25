import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReportViewer } from "../report-viewer";

const markdownMock = vi.hoisted(() => vi.fn());

vi.mock("@/components/ui/markdown", () => ({
  Markdown: ({ children }: { children: React.ReactNode }) => {
    markdownMock();
    return <div data-testid="markdown">{children}</div>;
  },
}));

describe("ReportViewer", () => {
  beforeEach(() => {
    markdownMock.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders a report normally", () => {
    render(<ReportViewer report="Revenue increased" />);
    expect(screen.getByTestId("markdown")).toHaveTextContent("Revenue increased");
    expect(screen.getByRole("button", { name: "Copy report" })).toBeInTheDocument();
  });

  it("contains child rendering errors, hides details, and retries", () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => undefined);
    let shouldThrow = true;
    markdownMock.mockImplementation(() => {
      if (shouldThrow) throw new Error("secret-api-key");
    });

    render(<ReportViewer report="Confidential report" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Unable to display this report.");
    expect(screen.queryByText("secret-api-key")).not.toBeInTheDocument();
    expect(error).toHaveBeenCalled();

    shouldThrow = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(screen.getByTestId("markdown")).toHaveTextContent("Confidential report");
  });
});
