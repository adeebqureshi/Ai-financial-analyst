import { vi, describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import GlobalError from "@/app/global-error";

describe("GlobalError fallback component", () => {
  const mockReset = vi.fn();
  const mockError = new Error("Something went wrong");

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders error UI with title and message", () => {
    render(<GlobalError error={mockError} reset={mockReset} />);

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("An unexpected error occurred. Our team has been notified.")).toBeInTheDocument();
  });

  it("renders retry button with correct label", () => {
    render(<GlobalError error={mockError} reset={mockReset} />);

    const button = screen.getByText("Try again");
    expect(button).toBeInTheDocument();
  });

  it("calls reset function when retry button is clicked", () => {
    render(<GlobalError error={mockError} reset={mockReset} />);

    fireEvent.click(screen.getByText("Try again"));
    expect(mockReset).toHaveBeenCalledTimes(1);
  });

  it("displays error digest when available", () => {
    const errorWithDigest = Object.assign(new Error("Test error"), { digest: "abc123" });
    render(<GlobalError error={errorWithDigest} reset={mockReset} />);

    expect(screen.getByText("Error ID: abc123")).toBeInTheDocument();
  });

  it("does not display error digest when not available", () => {
    render(<GlobalError error={mockError} reset={mockReset} />);

    expect(screen.queryByText(/Error ID:/)).not.toBeInTheDocument();
  });

  it("does not expose stack traces", () => {
    const errorWithStack = new Error("Test error");
    errorWithStack.stack = "Error: Test error\n    at Component.render (/app/page.tsx:10:5)\n    at processError (/app/error.tsx:5:1)";
    render(<GlobalError error={errorWithStack} reset={mockReset} />);

    expect(screen.queryByText(/Component\.render/)).not.toBeInTheDocument();
    expect(screen.queryByText(/page\.tsx/)).not.toBeInTheDocument();
    expect(screen.queryByText(/at Component/)).not.toBeInTheDocument();
    expect(screen.queryByText(/processError/)).not.toBeInTheDocument();
  });

  it("renders with proper styling classes", () => {
    render(<GlobalError error={mockError} reset={mockReset} />);

    const container = screen.getByText("Something went wrong").closest("div.min-h-screen");
    expect(container).toHaveClass("min-h-screen");
    expect(container).toHaveClass("bg-[#05060A]");
    expect(container).toHaveClass("text-white");
  });

  it("logs error to console on mount", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(<GlobalError error={mockError} reset={mockReset} />);

    expect(consoleSpy).toHaveBeenCalledWith("Global error caught:", mockError);
    consoleSpy.mockRestore();
  });
});