import {
  Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import type { BandPoint } from '../../types';

interface TooltipProps {
  active?: boolean;
  payload?: { payload: BandPoint }[];
  label?: number;
}

function fmt(v: number): string {
  return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function FanTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const point = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">Day {label}</div>
      <div className="chart-tooltip-row"><span>p95</span><strong>{fmt(point.p95)}</strong></div>
      <div className="chart-tooltip-row"><span>p75</span><strong>{fmt(point.p75)}</strong></div>
      <div className="chart-tooltip-row"><span>median</span><strong>{fmt(point.p50)}</strong></div>
      <div className="chart-tooltip-row"><span>p25</span><strong>{fmt(point.p25)}</strong></div>
      <div className="chart-tooltip-row"><span>p5</span><strong>{fmt(point.p5)}</strong></div>
    </div>
  );
}

export function FanChart({ data, yLabel = 'Value' }: { data: BandPoint[]; yLabel?: string }) {
  const chartData = data.map((d) => ({ ...d, band90: [d.p5, d.p95], band50: [d.p25, d.p75] }));

  return (
    <div className="chart-card">
      <div className="chart-legend">
        <span><i className="legend-swatch" style={{ background: 'var(--series-1)', opacity: 0.15 }} /> 5th-95th percentile</span>
        <span><i className="legend-swatch" style={{ background: 'var(--series-1)', opacity: 0.3 }} /> 25th-75th percentile</span>
        <span><i className="legend-swatch line" style={{ background: 'var(--series-1)' }} /> median</span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={chartData} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="var(--border)" vertical={false} />
          <XAxis
            dataKey="step" stroke="var(--muted)" tick={{ fill: 'var(--muted)', fontSize: 11 }}
            label={{ value: 'Trading day', position: 'insideBottom', offset: -4, fill: 'var(--muted)', fontSize: 11 }}
          />
          <YAxis
            stroke="var(--muted)" tick={{ fill: 'var(--muted)', fontSize: 11 }} width={64}
            label={{ value: yLabel, angle: -90, position: 'insideLeft', fill: 'var(--muted)', fontSize: 11 }}
          />
          <Tooltip content={<FanTooltip />} />
          <Area dataKey="band90" stroke="none" fill="var(--series-1)" fillOpacity={0.12} isAnimationActive={false} />
          <Area dataKey="band50" stroke="none" fill="var(--series-1)" fillOpacity={0.28} isAnimationActive={false} />
          <Line dataKey="p50" stroke="var(--series-1)" strokeWidth={2} dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
