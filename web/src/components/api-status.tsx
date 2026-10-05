import { getHealth } from "@/lib/api-client";

export function ApiStatusSkeleton() {
  return (
    <span className="inline-flex items-center gap-2 text-xs text-slate-500">
      <span className="size-2 rounded-full bg-slate-600" aria-hidden />
      API: checking…
    </span>
  );
}

/**
 * Async Server Component: it fetches during render, on the server. The shell
 * wraps it in <Suspense>, so the page paints immediately and this chip
 * streams in when the API answers (or fails to).
 */
export async function ApiStatus() {
  let healthy = false;
  try {
    healthy = (await getHealth()).status === "ok";
  } catch {
    // The API being down is an expected, handled state, not a crash.
    healthy = false;
  }

  return (
    <span
      data-testid="api-status"
      className={`inline-flex items-center gap-2 text-xs ${
        healthy ? "text-emerald-400" : "text-rose-400"
      }`}
    >
      <span
        className={`size-2 rounded-full ${healthy ? "bg-emerald-400" : "bg-rose-500"}`}
        aria-hidden
      />
      API: {healthy ? "healthy" : "unreachable"}
    </span>
  );
}
