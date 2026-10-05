import Link from "next/link";

import { ApiUnavailable } from "@/components/api-unavailable";
import {
  DEMO_ORGANIZATION_ID,
  listServices,
  type Service,
} from "@/lib/api-client";

export const metadata = { title: "Services" };

async function load(): Promise<Service[] | null> {
  try {
    return (await listServices(DEMO_ORGANIZATION_ID)).items;
  } catch {
    return null;
  }
}

export default async function ServicesPage() {
  const services = await load();
  if (services === null) return <ApiUnavailable />;

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="text-xl font-semibold text-white">Services</h1>
      <p className="mt-1 text-sm text-slate-500">
        Everything registered with SentinelAI.
      </p>

      <div className="mt-6 overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900/70 text-xs tracking-wide text-slate-500 uppercase">
            <tr>
              <th className="px-5 py-3 font-medium">Name</th>
              <th className="px-5 py-3 font-medium">Environment</th>
              <th className="px-5 py-3 font-medium">Registered</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {services.map((service) => (
              <tr key={service.id} className="hover:bg-slate-900/50">
                <td className="px-5 py-3">
                  <Link
                    href={`/services/${service.id}`}
                    className="font-medium text-white hover:underline"
                  >
                    {service.name}
                  </Link>
                </td>
                <td className="px-5 py-3 text-slate-400">
                  {service.environment}
                </td>
                <td className="px-5 py-3 text-slate-500">
                  {new Date(service.created_at).toLocaleString("en-US", {
                    dateStyle: "medium",
                    timeStyle: "short",
                    timeZone: "UTC",
                  })}{" "}
                  UTC
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
