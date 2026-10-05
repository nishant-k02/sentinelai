import type { components } from "@/lib/api-types.gen";

export type HealthResponse = components["schemas"]["HealthResponse"];
export type Service = components["schemas"]["ServiceRead"];
export type ServiceList = components["schemas"]["ServiceList"];
export type MetricSample = components["schemas"]["MetricSampleRead"];
export type MetricSampleList = components["schemas"]["MetricSampleList"];

// Server-only — never prefix with NEXT_PUBLIC_. These fetches run inside the
// Next.js server process, never in the browser, so the API's internal URL
// never needs to reach client JavaScript.
const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

// TEMPORARY. Until the UI has login (UI-2), the dashboard needs to be told
// which organization to show. `make seed` creates the demo organization
// with this fixed id. After UI-2 the organization comes from the signed-in
// user's session and this constant is deleted.
export const DEMO_ORGANIZATION_ID =
  process.env.DEMO_ORGANIZATION_ID ?? "00000000-0000-4000-8000-00000000d3a0";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type Params = Record<string, string | number | undefined>;

async function apiGet<T>(path: string, params: Params = {}): Promise<T> {
  const url = new URL(path, API_BASE_URL);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }
  // no-store: this is live operational data. Serving a cached "healthy" for
  // a service that has since fallen over is worse than being slow.
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    throw new ApiError(res.status, `GET ${path} responded ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/healthz");
}

export function listServices(organizationId: string): Promise<ServiceList> {
  return apiGet<ServiceList>("/v1/services", {
    organization_id: organizationId,
    limit: 200, // the API's maximum page size
  });
}

export function getService(id: string): Promise<Service> {
  return apiGet<Service>(`/v1/services/${id}`);
}

/**
 * The most recent `limit` samples of one metric, oldest first (the API
 * returns newest first; charts read left to right).
 */
export async function getMetricSeries(
  serviceId: string,
  metricName: string,
  limit: number,
): Promise<MetricSample[]> {
  const page = await apiGet<MetricSampleList>(
    `/v1/services/${serviceId}/metrics`,
    { metric_name: metricName, limit },
  );
  return [...page.items].reverse();
}
