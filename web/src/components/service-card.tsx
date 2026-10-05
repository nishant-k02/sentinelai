import Link from "next/link";

import { HEALTH_STYLES, StatusBadge } from "@/components/status-badge";
import { Sparkline } from "@/components/sparkline";
import type { ServiceSnapshot } from "@/lib/dashboard";
import { rateMetric } from "@/lib/health";
import { formatAge } from "@/lib/metrics";

function Stat({
  label,
  value,
  health,
}: {
  label: string;
  value: string;
  health: "healthy" | "degraded" | "critical";
}) {
  return (
    <div>
      <dt className="text-[11px] tracking-wide text-slate-500 uppercase">
        {label}
      </dt>
      <dd
        className={`mt-0.5 text-sm font-medium ${HEALTH_STYLES[health].text}`}
      >
        {value}
      </dd>
    </div>
  );
}

export function ServiceCard({ snapshot }: { snapshot: ServiceSnapshot }) {
  const { service, health } = snapshot;

  return (
    <Link
      href={`/services/${service.id}`}
      className="group block rounded-xl border border-slate-800 bg-slate-900/50 p-5 transition-colors hover:border-slate-700 hover:bg-slate-900"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-[15px] font-semibold text-white">
            {service.name}
          </h3>
          <p className="mt-0.5 text-xs text-slate-500">{service.environment}</p>
        </div>
        <StatusBadge health={health} />
      </div>

      <Sparkline
        values={snapshot.errorSeries}
        label={`${service.name} error rate, last hour`}
        className={`mt-4 ${HEALTH_STYLES[health].text}`}
      />
      <p className="mt-1 text-[11px] text-slate-600">
        Error rate · last hour · updated {formatAge(snapshot.ageMinutes)}
      </p>

      <dl className="mt-4 grid grid-cols-3 gap-3 border-t border-slate-800 pt-4">
        <Stat
          label="Errors"
          value={`${snapshot.errorRate.toFixed(2)}%`}
          health={rateMetric("error_rate_percent", snapshot.errorRate)}
        />
        <Stat
          label="p95"
          value={`${snapshot.latencyP95.toFixed(0)} ms`}
          health={rateMetric("latency_p95_ms", snapshot.latencyP95)}
        />
        <Stat
          label="CPU"
          value={`${snapshot.cpu.toFixed(0)}%`}
          health={rateMetric("cpu_percent", snapshot.cpu)}
        />
      </dl>
    </Link>
  );
}
