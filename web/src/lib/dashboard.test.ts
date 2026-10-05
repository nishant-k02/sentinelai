import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", () => ({
  listServices: vi.fn(),
  getService: vi.fn(),
  getMetricSeries: vi.fn(),
}));

import {
  getMetricSeries,
  getService,
  listServices,
  type Service,
} from "@/lib/api-client";

import { getServiceDetail, getServiceSnapshots } from "./dashboard";

const NOW = Date.parse("2026-01-01T12:00:00Z");

function service(name: string): Service {
  return {
    id: `id-${name}`,
    organization_id: "org",
    name,
    environment: "production",
    created_at: "2026-01-01T00:00:00Z",
  };
}

/** A one-sample series, recorded `minutesAgo` before NOW. */
function sample(value: number, minutesAgo = 0) {
  return [
    {
      id: "m",
      service_id: "s",
      metric_name: "x",
      value,
      recorded_at: new Date(NOW - minutesAgo * 60_000).toISOString(),
      created_at: "2026-01-01T00:00:00Z",
    },
  ];
}

/** Stub metric values per (service, metric). */
function stubMetrics(table: Record<string, Record<string, number>>) {
  vi.mocked(getMetricSeries).mockImplementation(async (serviceId, metric) =>
    sample(table[serviceId]?.[metric] ?? 0, 2),
  );
}

beforeEach(() => vi.resetAllMocks());

describe("getServiceSnapshots", () => {
  it("lists services needing attention first, then alphabetically", async () => {
    vi.mocked(listServices).mockResolvedValue({
      items: [service("alpha"), service("zulu"), service("bravo")],
      total: 3,
      limit: 200,
      offset: 0,
    });
    stubMetrics({
      "id-alpha": {
        error_rate_percent: 0.2,
        latency_p95_ms: 100,
        cpu_percent: 20,
      },
      "id-zulu": {
        error_rate_percent: 9,
        latency_p95_ms: 1500,
        cpu_percent: 85,
      },
      "id-bravo": {
        error_rate_percent: 2,
        latency_p95_ms: 100,
        cpu_percent: 20,
      },
    });

    const result = await getServiceSnapshots("org", NOW);

    expect(result.map((s) => [s.service.name, s.health])).toEqual([
      ["zulu", "critical"],
      ["bravo", "degraded"],
      ["alpha", "healthy"],
    ]);
  });

  it("reports how stale the newest sample is", async () => {
    vi.mocked(listServices).mockResolvedValue({
      items: [service("alpha")],
      total: 1,
      limit: 200,
      offset: 0,
    });
    stubMetrics({});

    const [snapshot] = await getServiceSnapshots("org", NOW);
    expect(snapshot.ageMinutes).toBe(2);
  });
});

describe("getServiceDetail", () => {
  it("builds one panel per metric and rates the service from them", async () => {
    vi.mocked(getService).mockResolvedValue(service("alpha"));
    stubMetrics({
      "id-alpha": {
        error_rate_percent: 9,
        latency_p95_ms: 100,
        cpu_percent: 20,
      },
    });

    const detail = await getServiceDetail("id-alpha", NOW);

    expect(detail.panels).toHaveLength(5);
    expect(detail.health).toBe("critical");
    const errors = detail.panels.find(
      (p) => p.definition.name === "error_rate_percent",
    );
    expect(errors?.health).toBe("critical");
    expect(errors?.latest).toBe(9);
  });
});
