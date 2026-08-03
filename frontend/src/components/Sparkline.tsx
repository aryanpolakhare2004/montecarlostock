interface Props {
  values: number[];
  width?: number;
  height?: number;
  positive: boolean;
}

export function Sparkline({ values, width = 100, height = 28, positive }: Props) {
  if (values.length < 2) return <svg width={width} height={height} />;

  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const span = hi - lo || 1;
  const step = width / (values.length - 1);

  const points = values
    .map((v, i) => `${(i * step).toFixed(1)},${(height - ((v - lo) / span) * height).toFixed(1)}`)
    .join(' ');

  return (
    <svg width={width} height={height} className="sparkline">
      <polyline points={points} fill="none" stroke={positive ? 'var(--good)' : 'var(--bad)'} strokeWidth={1.5} />
    </svg>
  );
}
