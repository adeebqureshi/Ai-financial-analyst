import { vi, describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorDisplay, ErrorInline } from "@/components/ui/error-display";
import { ApiError } from "@/services/api";

describe("ErrorDisplay", () => {
  const mockOnRetry = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders authentication error correctly", () => {
    const error = new ApiError("Unauthorized", 401, "/api/test");
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} />);

    expect(screen.getByText("Authentication Required")).toBeInTheDocument();
    expect(screen.getByText("Your session has expired. Please sign in again.")).toBeInTheDocument();
    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("renders not found error correctly", () => {
    const error = new ApiError("Not Found", 404, "/api/test");
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} />);

    expect(screen.getByText("Not Found")).toBeInTheDocument();
    expect(screen.getByText("The requested resource could not be found.")).toBeInTheDocument();
    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
  });

  it("renders client error with custom message", () => {
    const error = new ApiError("Invalid ticker symbol", 400, "/api/test");
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} />);

    expect(screen.getByText("Request Failed")).toBeInTheDocument();
    expect(screen.getByText("Invalid ticker symbol")).toBeInTheDocument();
    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
  });

  it("renders server error as retryable", () => {
    const error = new ApiError("Internal Server Error", 500, "/api/test");
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} />);

    expect(screen.getByText("Server Error")).toBeInTheDocument();
    expect(screen.getByText("Our servers are having trouble. Please wait a moment and retry.")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("renders network error as retryable", () => {
    const error = new TypeError("Failed to fetch");
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} />);

    expect(screen.getByText("Connection Failed")).toBeInTheDocument();
    expect(screen.getByText("Unable to connect to the server. Please check your internet connection.")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("renders generic error as retryable", () => {
    const error = new Error("Something went wrong");
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} />);

    expect(screen.getByText("Error")).toBeInTheDocument();
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("renders unknown error for non-Error objects", () => {
    render(<ErrorDisplay error="string error" onRetry={mockOnRetry} />);

    expect(screen.getByText("Unknown Error")).toBeInTheDocument();
    expect(screen.getByText("An unexpected error occurred.")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("calls onRetry when retry button is clicked", () => {
    const error = new ApiError("Server Error", 500, "/api/test");
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} />);

    fireEvent.click(screen.getByText("Try again"));
    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it("does not render retry button when onRetry is not provided", () => {
    const error = new ApiError("Server Error", 500, "/api/test");
    render(<ErrorDisplay error={error} />);

    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
  });

  it("uses custom title when provided", () => {
    const error = new ApiError("Server Error", 500, "/api/test");
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} title="Custom Title" />);

    expect(screen.getByText("Custom Title")).toBeInTheDocument();
    expect(screen.queryByText("Server Error")).not.toBeInTheDocument();
  });

  it("renders in compact mode", () => {
    const error = new ApiError("Server Error", 500, "/api/test");
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} compact />);

    expect(screen.getByText("Server Error")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("does not expose stack traces", () => {
    const error = new Error("Test error");
    error.stack = "Error: Test error\n    at Object.<anonymous> (/test.js:1:1)";
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} />);

    expect(screen.queryByText(/at Object/)).not.toBeInTheDocument();
    expect(screen.queryByText(/test\.js/)).not.toBeInTheDocument();
  });

  it("has correct ARIA attributes", () => {
    const error = new ApiError("Server Error", 500, "/api/test");
    render(<ErrorDisplay error={error} onRetry={mockOnRetry} />);

    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();
  });
});

describe("ErrorInline", () => {
  const mockOnRetry = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders authentication error inline", () => {
    const error = new ApiError("Unauthorized", 401, "/api/test");
    render(<ErrorInline error={error} onRetry={mockOnRetry} />);

    expect(screen.getByText("Your session has expired. Please sign in again.")).toBeInTheDocument();
    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("renders server error with retry button", () => {
    const error = new ApiError("Server Error", 500, "/api/test");
    render(<ErrorInline error={error} onRetry={mockOnRetry} />);

    expect(screen.getByText("Our servers are having trouble. Please wait a moment and retry.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("calls onRetry when inline retry is clicked", () => {
    const error = new ApiError("Server Error", 500, "/api/test");
    render(<ErrorInline error={error} onRetry={mockOnRetry} />);

    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it("does not show retry button when error is not retryable", () => {
    const error = new ApiError("Bad Request", 400, "/api/test");
    render(<ErrorInline error={error} onRetry={mockOnRetry} />);

    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
  });

  it("does not show retry button when onRetry not provided", () => {
    const error = new ApiError("Server Error", 500, "/api/test");
    render(<ErrorInline error={error} />);

    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
  });

  it("does not expose stack traces", () => {
    const error = new Error("Test error");
    error.stack = "Error: Test error\n    at Object.<anonymous> (/test.js:1:1)";
    render(<ErrorInline error={error} onRetry={mockOnRetry} />);

    expect(screen.queryByText(/at Object/)).not.toBeInTheDocument();
  });
});