interface SparklineProps {
  values: number[];
  label: string;
  className?: string;
  height?: number;
}

const WIDTH = 300;

/**
 * A dependency-free SVG line chart. The line takes its color from
 * `currentColor`, so callers style it with an ordinary text-color class.
 * `preserveAspectRatio="none"` stretches it to its container;
 * `vector-effect: non-scaling-stroke` keeps the line from stretching with it.
 */
export function Sparkline({
  values,
  label,
  className = "",
  height = 48,
}: SparklineProps) {
  if (values.length < 2) {
    return (
      <div
        className={`flex items-center justify-center text-xs text-slate-500 ${className}`}
        style={{ height }}
      >
        no data
      </div>
    );
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1; // a flat series draws a flat line, not NaN
  const pad = 3;

  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * WIDTH;
    const y = pad + (1 - (v - min) / span) * (height - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const line = `M${points.join(" L")}`;
  const area = `${line} L${WIDTH},${height} L0,${height} Z`;

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${height}`}
      preserveAspectRatio="none"
      role="img"
      aria-label={label}
      className={`w-full ${className}`}
      style={{ height }}
    >
      <path d={area} fill="currentColor" opacity={0.12} />
      <path
        d={line}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.75}
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
