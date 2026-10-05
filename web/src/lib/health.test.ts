import { describe, expect, it } from "vitest";

import { assessHealth, rateMetric, worst } from "./health";

describe("rateMetric", () => {
  it("rates error rate against 1.5% / 5%", () => {
    expect(rateMetric("error_rate_percent", 0.4)).toBe("healthy");
    expect(rateMetric("error_rate_percent", 1.5)).toBe("degraded");
    expect(rateMetric("error_rate_percent", 5)).toBe("critical");
  });

  it("rates latency against 500ms / 1000ms", () => {
    expect(rateMetric("latency_p95_ms", 499)).toBe("healthy");
    expect(rateMetric("latency_p95_ms", 500)).toBe("degraded");
    expect(rateMetric("latency_p95_ms", 1000)).toBe("critical");
  });

  it("does not rate metrics it has no opinion about", () => {
    expect(rateMetric("requests_per_second", 1_000_000)).toBe("healthy");
    expect(rateMetric("something_unknown", 1e9)).toBe("healthy");
  });
});

describe("assessHealth", () => {
  const calm = { errorRate: 0.3, latencyP95: 200, cpu: 30 };

  it("is healthy when every vital is calm", () => {
    expect(assessHealth(calm)).toBe("healthy");
  });

  it("is as unhealthy as its unhealthiest vital", () => {
    expect(assessHealth({ ...calm, cpu: 80 })).toBe("degraded");
    expect(assessHealth({ ...calm, cpu: 80, errorRate: 9 })).toBe("critical");
  });
});

describe("worst", () => {
  it("returns healthy for an empty list", () => {
    expect(worst([])).toBe("healthy");
  });
});
