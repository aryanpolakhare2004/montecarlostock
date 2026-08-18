import {
  Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import type { HistogramBin } from '../../types';

function defaultFormat(v: number): string {
  return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

interface TooltipProps {
  active?: boolean;
  payload?: { payload: HistogramBin & { mid: number } }[];
  formatValue: (v: number) => string;
}

function HistTooltip({ active, payload, formatValue }: TooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const bin = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">
        {formatValue(bin.bin_start)} to {formatValue(bin.bin_end)}
      </div>
      <div className="chart-tooltip-row"><span>count</span><strong>{bin.count.toLocaleString()}</strong></div>
    </div>
  );
}

interface Props {
  data: HistogramBin[];
  xLabel?: string;
  referenceValue?: number;
  formatValue?: (v: number) => string;
}

export function Histogram({ data, xLabel = 'Value', referenceValue, formatValue }: Props) {
  const fmt = formatValue || defaultFormat;
  const chartData = data.map((d) => ({ ...d, mid: (d.bin_start + d.bin_end) / 2 }));

  return (
    <div className="chart-card">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={chartData} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="var(--border)" vertical={false} />
          <XAxis
            dataKey="mid" type="number" domain={['dataMin', 'dataMax']} tickFormatter={fmt}
            stroke="var(--muted)" tick={{ fill: 'var(--muted)', fontSize: 11 }}
            label={{ value: xLabel, position: 'insideBottom', offset: -4, fill: 'var(--muted)', fontSize: 11 }}
          />
          <YAxis stroke="var(--muted)" tick={{ fill: 'var(--muted)', fontSize: 11 }} width={40} allowDecimals={false} />
          <Tooltip content={<HistTooltip formatValue={fmt} />} cursor={{ fill: 'var(--border)', opacity: 0.3 }} />
          {referenceValue !== undefined && (
            <ReferenceLine x={referenceValue} stroke="var(--muted)" strokeDasharray="4 4" />
          )}
          <Bar dataKey="count" fill="var(--series-1)" radius={[3, 3, 0, 0]} maxBarSize={24} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
