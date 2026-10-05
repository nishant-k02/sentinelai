export interface MetricDefinition {
  name: string;
  label: string;
  unit: string;
  digits: number;
}

// The five series the demo fleet (and, later, real services) report.
export const METRICS: MetricDefinition[] = [
  { name: "error_rate_percent", label: "Error rate", unit: "%", digits: 2 },
  { name: "latency_p95_ms", label: "Latency p95", unit: "ms", digits: 0 },
  { name: "cpu_percent", label: "CPU", unit: "%", digits: 0 },
  { name: "memory_percent", label: "Memory", unit: "%", digits: 0 },
  {
    name: "requests_per_second",
    label: "Throughput",
    unit: "req/s",
    digits: 0,
  },
];

export function formatMetric(value: number, def: MetricDefinition): string {
  return `${value.toFixed(def.digits)}${def.unit === "%" ? "%" : ` ${def.unit}`}`;
}

export function formatAge(minutes: number | null): string {
  if (minutes === null) return "no data";
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m ago`;
}
