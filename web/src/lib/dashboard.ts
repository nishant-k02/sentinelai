import {
  getMetricSeries,
  getService,
  listServices,
  type MetricSample,
  type Service,
} from "@/lib/api-client";
import {
  assessHealth,
  compareHealthDesc,
  rateMetric,
  type Health,
} from "@/lib/health";
import { METRICS, type MetricDefinition } from "@/lib/metrics";

const CARD_WINDOW = 60; // minutes of history behind each overview sparkline
const DETAIL_WINDOW = 180;

function values(samples: MetricSample[]): number[] {
  return samples.map((s) => s.value);
}

function last(samples: MetricSample[]): number {
  return samples.at(-1)?.value ?? 0;
}

function ageMinutes(samples: MetricSample[], nowMs: number): number | null {
  const newest = samples.at(-1);
  if (!newest) return null;
  return Math.max(
    0,
    Math.round((nowMs - new Date(newest.recorded_at).getTime()) / 60_000),
  );
}

export interface ServiceSnapshot {
  service: Service;
  health: Health;
  errorRate: number;
  latencyP95: number;
  cpu: number;
  errorSeries: number[];
  ageMinutes: number | null;
}

/**
 * Everything the overview needs, per service.
 *
 * KNOWN N+1: three metric requests per service, in parallel. Fine for a
 * handful of services on localhost; for a real fleet this wants a single
 * "latest values" endpoint (or a summary endpoint) on the backend. Noted
 * here rather than built now: it is exactly the kind of thing you fix once
 * you can measure it (M14), not before.
 */
export async function getServiceSnapshots(
  organizationId: string,
  nowMs: number = Date.now(),
): Promise<ServiceSnapshot[]> {
  const { items } = await listServices(organizationId);

  const snapshots = await Promise.all(
    items.map(async (service): Promise<ServiceSnapshot> => {
      const [errors, latency, cpu] = await Promise.all([
        getMetricSeries(service.id, "error_rate_percent", CARD_WINDOW),
        getMetricSeries(service.id, "latency_p95_ms", CARD_WINDOW),
        getMetricSeries(service.id, "cpu_percent", CARD_WINDOW),
      ]);
      const vitals = {
        errorRate: last(errors),
        latencyP95: last(latency),
        cpu: last(cpu),
      };
      return {
        service,
        health: assessHealth(vitals),
        ...vitals,
        errorSeries: values(errors),
        ageMinutes: ageMinutes(errors, nowMs),
      };
    }),
  );

  // Needs-attention first, then alphabetical: the list answers "what should
  // I look at?" before "what exists?".
  return snapshots.sort(
    (a, b) =>
      compareHealthDesc(a.health, b.health) ||
      a.service.name.localeCompare(b.service.name),
  );
}

export interface MetricPanel {
  definition: MetricDefinition;
  values: number[];
  latest: number;
  min: number;
  max: number;
  health: Health;
}

export interface ServiceDetail {
  service: Service;
  health: Health;
  panels: MetricPanel[];
  ageMinutes: number | null;
}

export async function getServiceDetail(
  id: string,
  nowMs: number = Date.now(),
): Promise<ServiceDetail> {
  const service = await getService(id);
  const series = await Promise.all(
    METRICS.map((m) => getMetricSeries(id, m.name, DETAIL_WINDOW)),
  );

  const panels = METRICS.map((definition, i): MetricPanel => {
    const vals = values(series[i]);
    const latest = last(series[i]);
    return {
      definition,
      values: vals,
      latest,
      min: vals.length ? Math.min(...vals) : 0,
      max: vals.length ? Math.max(...vals) : 0,
      health: rateMetric(definition.name, latest),
    };
  });

  const byName = (name: string) =>
    panels.find((p) => p.definition.name === name)?.latest ?? 0;

  return {
    service,
    health: assessHealth({
      errorRate: byName("error_rate_percent"),
      latencyP95: byName("latency_p95_ms"),
      cpu: byName("cpu_percent"),
    }),
    panels,
    ageMinutes: ageMinutes(series[0], nowMs),
  };
}
