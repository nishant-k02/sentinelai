import { HEALTH_STYLES } from "@/components/status-badge";
import { Sparkline } from "@/components/sparkline";
import type { MetricPanel as Panel } from "@/lib/dashboard";
import { formatMetric } from "@/lib/metrics";

export function MetricPanel({ panel }: { panel: Panel }) {
  const { definition, health } = panel;
  const style = HEALTH_STYLES[health];

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-medium text-slate-300">
          {definition.label}
        </h3>
        <p className={`text-xl font-semibold tabular-nums ${style.text}`}>
          {formatMetric(panel.latest, definition)}
        </p>
      </div>

      <Sparkline
        values={panel.values}
        label={`${definition.label}, last 3 hours`}
        height={110}
        className={`mt-4 ${style.text}`}
      />

      <div className="mt-2 flex justify-between text-[11px] text-slate-600">
        <span>3h ago</span>
        <span>
          min {formatMetric(panel.min, definition)} · max{" "}
          {formatMetric(panel.max, definition)}
        </span>
        <span>now</span>
      </div>
    </section>
  );
}
