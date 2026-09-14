import type { components } from "@/lib/api-types.gen";

type HealthResponse = components["schemas"]["HealthResponse"];

// Server-only — never prefix with NEXT_PUBLIC_. This fetch runs inside the
// Next.js server process, never in the browser, so the API's internal URL
// never needs to reach client JavaScript.
const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/healthz`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`GET /healthz responded ${res.status}`);
  }
  return res.json() as Promise<HealthResponse>;
}
