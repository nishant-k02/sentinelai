import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", () => ({
  getHealth: vi.fn(),
}));

import { getHealth } from "@/lib/api-client";

import HomePage from "./page";

describe("HomePage", () => {
  it("shows healthy when the API responds ok", async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });
    render(await HomePage());
    expect(screen.getByTestId("api-status")).toHaveTextContent("API: healthy");
  });

  it("shows unreachable when the API call fails", async () => {
    vi.mocked(getHealth).mockRejectedValue(new Error("connection refused"));
    render(await HomePage());
    expect(screen.getByTestId("api-status")).toHaveTextContent(
      "API: unreachable",
    );
  });
});
