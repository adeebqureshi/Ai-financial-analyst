import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  Skeleton,
  SkeletonCard,
  SkeletonMetricCard,
  SkeletonTable,
  SkeletonChart,
  SkeletonText,
  SkeletonList,
  SkeletonAnalysisView,
} from "@/components/ui/skeleton";

describe("Skeleton components", () => {
  describe("Skeleton", () => {
    it("renders a div with pulse animation and base classes", () => {
      render(<Skeleton data-testid="test-skeleton" />);
      const skeleton = screen.getByTestId("test-skeleton");
      expect(skeleton).toHaveClass("animate-pulse");
      expect(skeleton).toHaveClass("rounded-md");
      expect(skeleton).toHaveClass("bg-white/10");
    });

    it("applies custom className", () => {
      render(<Skeleton data-testid="test-skeleton" className="custom-class" />);
      expect(screen.getByTestId("test-skeleton")).toHaveClass("custom-class");
    });

    it("passes through additional props", () => {
      render(<Skeleton data-testid="test-skeleton" />);
      expect(screen.getByTestId("test-skeleton")).toBeInTheDocument();
    });
  });

  describe("SkeletonCard", () => {
    it("renders card structure with title and content skeletons", () => {
      render(<SkeletonCard />);
      const card = screen.getByTestId("skeleton-card");
      expect(card).toHaveClass("rounded-[32px]");
      expect(card).toHaveClass("border");
      expect(card).toHaveClass("bg-white/[0.03]");
      expect(card).toHaveClass("p-8");
      expect(card).toHaveClass("space-y-6");
    });
  });

  describe("SkeletonMetricCard", () => {
    it("renders metric card structure", () => {
      render(<SkeletonMetricCard data-testid="metric-card" />);
      const card = screen.getByTestId("metric-card");
      expect(card).toHaveClass("rounded-[32px]");
      expect(card).toHaveClass("space-y-4");
    });
  });

  describe("SkeletonTable", () => {
    it("renders table with default rows and columns", () => {
      render(<SkeletonTable />);
      const table = screen.getByRole("table");
      expect(table).toBeInTheDocument();
    });

    it("renders correct number of header cells for default cols", () => {
      render(<SkeletonTable />);
      const headers = screen.getAllByRole("columnheader");
      expect(headers.length).toBe(4);
    });

    it("renders correct number of rows for default", () => {
      render(<SkeletonTable />);
      const rows = screen.getAllByRole("row");
      expect(rows.length).toBe(6);
    });

    it("accepts custom rows and cols", () => {
      render(<SkeletonTable rows={3} cols={5} />);
      const headers = screen.getAllByRole("columnheader");
      expect(headers.length).toBe(5);

      const rows = screen.getAllByRole("row");
      expect(rows.length).toBe(4);
    });
  });

  describe("SkeletonChart", () => {
    it("renders chart container with title area", () => {
      render(<SkeletonChart />);
      const container = screen.getByTestId("skeleton-chart");
      expect(container).toHaveClass("rounded-[32px]");
    });

    it("applies custom height", () => {
      render(<SkeletonChart height="300px" />);
      const chartArea = screen.getByTestId("skeleton-chart");
      const heightDiv = chartArea.querySelector('div[style*="height: 300px"]');
      expect(heightDiv).toBeInTheDocument();
    });
  });

  describe("SkeletonText", () => {
    it("renders default number of lines", () => {
      render(<SkeletonText data-testid="text-skeleton" />);
      const container = screen.getByTestId("text-skeleton");
      const lines = container.querySelectorAll("div > div");
      expect(lines.length).toBe(3);
    });

    it("renders custom number of lines", () => {
      render(<SkeletonText lines={5} data-testid="text-skeleton" />);
      const container = screen.getByTestId("text-skeleton");
      const lines = container.querySelectorAll("div > div");
      expect(lines.length).toBe(5);
    });
  });

  describe("SkeletonList", () => {
    it("renders default number of items", () => {
      render(<SkeletonList />);
      const items = screen.getAllByTestId("skeleton-list-item");
      expect(items.length).toBe(5);
    });

    it("renders custom number of items", () => {
      render(<SkeletonList items={3} />);
      const items = screen.getAllByTestId("skeleton-list-item");
      expect(items.length).toBe(3);
    });

    it("each item has avatar, text, and action skeletons", () => {
      render(<SkeletonList items={1} />);
      const items = screen.getAllByTestId("skeleton-list-item");
      expect(items.length).toBe(1);
    });
  });

  describe("SkeletonAnalysisView", () => {
    it("renders complete analysis view structure", () => {
      render(<SkeletonAnalysisView />);
      const container = screen.getByTestId("skeleton-analysis-view");
      expect(container).toHaveClass("space-y-10");
    });

    it("contains multiple SkeletonCard components", () => {
      render(<SkeletonAnalysisView />);
      const cards = screen.getAllByTestId("skeleton-card");
      expect(cards.length).toBeGreaterThanOrEqual(6);
    });

    it("contains SkeletonChart components", () => {
      render(<SkeletonAnalysisView />);
      const charts = screen.getAllByTestId("skeleton-chart");
      expect(charts.length).toBeGreaterThanOrEqual(2);
    });
  });
});