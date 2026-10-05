export type Health = "healthy" | "degraded" | "critical";

const RANK: Record<Health, number> = { healthy: 0, degraded: 1, critical: 2 };

export function worst(levels: Health[]): Health {
  return levels.reduce<Health>(
    (a, b) => (RANK[b] > RANK[a] ? b : a),
    "healthy",
  );
}

function byThreshold(
  value: number,
  degraded: number,
  critical: number,
): Health {
  if (value >= critical) return "critical";
  if (value >= degraded) return "degraded";
  return "healthy";
}

/**
 * Rate a single metric against fixed thresholds.
 *
 * PREVIEW ONLY. These are hard-coded numbers standing in for the real thing:
 * anomaly detection (M2) will learn what "normal" is per service and per
 * metric instead of applying one rule to every service. Static thresholds
 * are exactly what that milestone exists to replace: 500ms is an outage for
 * one service and a good day for another.
 */
export function rateMetric(metricName: string, value: number): Health {
  switch (metricName) {
    case "error_rate_percent":
      return byThreshold(value, 1.5, 5);
    case "latency_p95_ms":
      return byThreshold(value, 500, 1000);
    case "cpu_percent":
      return byThreshold(value, 75, 90);
    default:
      return "healthy";
  }
}

export interface Vitals {
  errorRate: number;
  latencyP95: number;
  cpu: number;
}

/** A service is as unhealthy as its unhealthiest vital sign. */
export function assessHealth(v: Vitals): Health {
  return worst([
    rateMetric("error_rate_percent", v.errorRate),
    rateMetric("latency_p95_ms", v.latencyP95),
    rateMetric("cpu_percent", v.cpu),
  ]);
}

export const HEALTH_ORDER: Health[] = ["critical", "degraded", "healthy"];

export function compareHealthDesc(a: Health, b: Health): number {
  return RANK[b] - RANK[a];
}
