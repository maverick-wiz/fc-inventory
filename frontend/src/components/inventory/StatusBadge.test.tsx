import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders In Stock correctly", () => {
    render(<StatusBadge status="in_stock" />);
    expect(screen.getByText("In Stock")).toBeTruthy();
  });

  it("renders Low Stock with amber styling", () => {
    render(<StatusBadge status="low_stock" />);
    const badge = screen.getByText("Low Stock");
    expect(badge).toBeTruthy();
    expect(badge.className).toContain("amber");
  });

  it("renders Out of Stock with red styling", () => {
    render(<StatusBadge status="out_of_stock" />);
    expect(screen.getByText("Out of Stock")).toBeTruthy();
  });

  it("renders On Order with blue styling", () => {
    render(<StatusBadge status="on_order" />);
    expect(screen.getByText("On Order")).toBeTruthy();
  });

  it("has correct aria-label for accessibility", () => {
    render(<StatusBadge status="low_stock" />);
    expect(screen.getByLabelText("Stock status: Low Stock")).toBeTruthy();
  });
});
