import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiUnavailable } from "@/components/api-unavailable";
import { MetricPanel } from "@/components/metric-panel";
import { StatusBadge } from "@/components/status-badge";
import { ApiError } from "@/lib/api-client";
import { getServiceDetail, type ServiceDetail } from "@/lib/dashboard";
import { formatAge } from "@/lib/metrics";

export const metadata = { title: "Service" };

async function load(
  id: string,
): Promise<ServiceDetail | "not-found" | "unavailable"> {
  try {
    return await getServiceDetail(id);
  } catch (error) {
    // 422: the id wasn't even a valid UUID. Either way, there's no such page.
    if (
      error instanceof ApiError &&
      (error.status === 404 || error.status === 422)
    ) {
      return "not-found";
    }
    return "unavailable";
  }
}

export default async function ServicePage(props: PageProps<"/services/[id]">) {
  const { id } = await props.params;
  const detail = await load(id);

  if (detail === "not-found") notFound();
  if (detail === "unavailable") return <ApiUnavailable />;

  const { service, health, panels } = detail;

  return (
    <div className="mx-auto max-w-6xl">
      <Link
        href="/services"
        className="text-xs text-slate-500 hover:text-slate-300"
      >
        ← All services
      </Link>

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold text-white">{service.name}</h1>
        <StatusBadge health={health} />
        <span className="rounded-md border border-slate-800 px-2 py-0.5 text-xs text-slate-400">
          {service.environment}
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-500">
        Last 3 hours · updated {formatAge(detail.ageMinutes)}
      </p>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {panels.map((panel) => (
          <MetricPanel key={panel.definition.name} panel={panel} />
        ))}
      </div>

      <p className="mt-6 rounded-xl border border-dashed border-slate-800 p-5 text-sm text-slate-500">
        Recent deployments and error logs for this service will appear here once
        the API exposes them (next UI step). They are already being collected.
      </p>
    </div>
  );
}
