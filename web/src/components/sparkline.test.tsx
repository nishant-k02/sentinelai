import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Sparkline } from "./sparkline";

describe("Sparkline", () => {
  it("draws an accessible chart for a series", () => {
    const { container } = render(
      <Sparkline values={[1, 3, 2, 5]} label="error rate" />,
    );
    expect(screen.getByRole("img", { name: "error rate" })).toBeInTheDocument();
    expect(container.querySelectorAll("path")).toHaveLength(2); // area + line
  });

  it("survives a flat series (no divide-by-zero NaN in the path)", () => {
    const { container } = render(<Sparkline values={[4, 4, 4]} label="flat" />);
    for (const path of container.querySelectorAll("path")) {
      expect(path.getAttribute("d")).not.toContain("NaN");
    }
  });

  it("says so when there is not enough data", () => {
    render(<Sparkline values={[1]} label="too short" />);
    expect(screen.getByText("no data")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
