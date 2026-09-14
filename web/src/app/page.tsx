import { getHealth } from "@/lib/api-client";

export default async function HomePage() {
  let status: "ok" | "unreachable" = "unreachable";

  try {
    const health = await getHealth();
    status = health.status === "ok" ? "ok" : "unreachable";
  } catch {
    // The API being down is an expected, handled state — not a crash.
    // Mirrors the graceful-degradation principle from the HLD failure table.
    status = "unreachable";
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-950 text-slate-100">
      <h1 className="text-2xl font-semibold">SentinelAI</h1>
      <p
        data-testid="api-status"
        className={status === "ok" ? "text-emerald-400" : "text-rose-400"}
      >
        API: {status === "ok" ? "healthy" : "unreachable"}
      </p>
    </main>
  );
}
