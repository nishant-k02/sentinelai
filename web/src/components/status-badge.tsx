import type { Health } from "@/lib/health";

// Full class names written out (not assembled from fragments) so Tailwind's
// source scan can see every one of them.
export const HEALTH_STYLES: Record<
  Health,
  { label: string; dot: string; text: string; pill: string }
> = {
  healthy: {
    label: "Healthy",
    dot: "bg-emerald-400",
    text: "text-emerald-400",
    pill: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  },
  degraded: {
    label: "Degraded",
    dot: "bg-amber-400",
    text: "text-amber-400",
    pill: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  },
  critical: {
    label: "Critical",
    dot: "bg-rose-500",
    text: "text-rose-400",
    pill: "border-rose-500/30 bg-rose-500/10 text-rose-300",
  },
};

export function StatusBadge({ health }: { health: Health }) {
  const style = HEALTH_STYLES[health];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${style.pill}`}
    >
      <span className={`size-1.5 rounded-full ${style.dot}`} aria-hidden />
      {style.label}
    </span>
  );
}
