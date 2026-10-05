import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ServiceSnapshot } from "@/lib/dashboard";

import { ServiceCard } from "./service-card";

const snapshot: ServiceSnapshot = {
  service: {
    id: "11111111-1111-4111-8111-111111111111",
    organization_id: "22222222-2222-4222-8222-222222222222",
    name: "checkout-api",
    environment: "production",
    created_at: "2026-01-01T00:00:00Z",
  },
  health: "critical",
  errorRate: 9.4,
  latencyP95: 1380,
  cpu: 83,
  errorSeries: [0.4, 0.5, 4, 9.4],
  ageMinutes: 0,
};

describe("ServiceCard", () => {
  it("links to the service detail page", () => {
    render(<ServiceCard snapshot={snapshot} />);
    expect(screen.getByRole("link")).toHaveAttribute(
      "href",
      `/services/${snapshot.service.id}`,
    );
  });

  it("shows the name, health, and vitals", () => {
    render(<ServiceCard snapshot={snapshot} />);
    expect(screen.getByText("checkout-api")).toBeInTheDocument();
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("9.40%")).toBeInTheDocument();
    expect(screen.getByText("1380 ms")).toBeInTheDocument();
    expect(screen.getByText("83%")).toBeInTheDocument();
  });
});
