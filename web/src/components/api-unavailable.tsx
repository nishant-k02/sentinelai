export function ApiUnavailable() {
  return (
    <div
      role="alert"
      className="mx-auto mt-16 max-w-md rounded-xl border border-rose-500/30 bg-rose-500/5 p-6 text-center"
    >
      <h2 className="text-base font-semibold text-rose-300">
        Can&apos;t reach the SentinelAI API
      </h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-400">
        The dashboard could not load data. Check that the API is running (
        <code className="rounded bg-slate-800 px-1.5 py-0.5 text-xs">
          uv run uvicorn sentinelai.main:app
        </code>
        ) and that the demo data is loaded (
        <code className="rounded bg-slate-800 px-1.5 py-0.5 text-xs">
          make seed
        </code>
        ), then refresh.
      </p>
    </div>
  );
}
