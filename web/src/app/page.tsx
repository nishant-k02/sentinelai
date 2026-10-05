import { ApiUnavailable } from "@/components/api-unavailable";
import { ServiceCard } from "@/components/service-card";
import { HEALTH_STYLES } from "@/components/status-badge";
import { DEMO_ORGANIZATION_ID } from "@/lib/api-client";
import { getServiceSnapshots, type ServiceSnapshot } from "@/lib/dashboard";
import { HEALTH_ORDER, type Health } from "@/lib/health";

export const metadata = { title: "Overview" };

async function load(): Promise<ServiceSnapshot[] | null> {
  try {
    return await getServiceSnapshots(DEMO_ORGANIZATION_ID);
  } catch {
    return null;
  }
}

function Tile({
  label,
  value,
  valueClass = "text-white",
}: {
  label: string;
  value: number;
  valueClass?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 px-5 py-4">
      <p className="text-xs tracking-wide text-slate-500 uppercase">{label}</p>
      <p className={`mt-1 text-3xl font-semibold tabular-nums ${valueClass}`}>
        {value}
      </p>
    </div>
  );
}

export default async function OverviewPage() {
  const snapshots = await load();
  if (snapshots === null) return <ApiUnavailable />;

  const counts = (health: Health) =>
    snapshots.filter((s) => s.health === health).length;

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="text-xl font-semibold text-white">Overview</h1>
      <p className="mt-1 text-sm text-slate-500">
        Services that need attention are listed first.
      </p>

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Tile label="Services" value={snapshots.length} />
        {HEALTH_ORDER.map((health) => (
          <Tile
            key={health}
            label={HEALTH_STYLES[health].label}
            value={counts(health)}
            valueClass={
              counts(health) > 0 ? HEALTH_STYLES[health].text : "text-slate-600"
            }
          />
        ))}
      </div>

      {snapshots.length === 0 ? (
        <p className="mt-10 text-center text-sm text-slate-500">
          No services yet. Load the demo fleet with{" "}
          <code className="rounded bg-slate-800 px-1.5 py-0.5 text-xs">
            make seed
          </code>
          .
        </p>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {snapshots.map((snapshot) => (
            <ServiceCard key={snapshot.service.id} snapshot={snapshot} />
          ))}
        </div>
      )}
    </div>
  );
}
