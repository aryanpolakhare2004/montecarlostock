import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const SERIES_COLORS = [
  'var(--series-1)', 'var(--series-2)', 'var(--series-3)', 'var(--series-4)',
  'var(--series-5)', 'var(--series-6)', 'var(--series-7)', 'var(--series-8)',
];

export interface BarDatum {
  name: string;
  value: number;
  extra?: { label: string; value: string }[];
}

function defaultFormat(v: number): string {
  return v.toLocaleString(undefined, { maximumFractionDigits: 4 });
}

interface TooltipProps {
  active?: boolean;
  payload?: { payload: BarDatum }[];
  formatValue: (v: number) => string;
}

function BarTooltip({ active, payload, formatValue }: TooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const item = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">{item.name}</div>
      <div className="chart-tooltip-row"><span>value</span><strong>{formatValue(item.value)}</strong></div>
      {item.extra?.map((row) => (
        <div className="chart-tooltip-row" key={row.label}>
          <span>{row.label}</span><strong>{row.value}</strong>
        </div>
      ))}
    </div>
  );
}

interface Props {
  data: BarDatum[];
  yLabel?: string;
  formatValue?: (v: number) => string;
}

export function CategoricalBarChart({ data, yLabel = 'Value', formatValue }: Props) {
  const fmt = formatValue || defaultFormat;
  return (
    <div className="chart-card">
      <ResponsiveContainer width="100%" height={Math.max(220, data.length * 44)}>
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 48, left: 8, bottom: 8 }}>
          <CartesianGrid stroke="var(--border)" horizontal={false} />
          <XAxis
            type="number" stroke="var(--muted)" tick={{ fill: 'var(--muted)', fontSize: 11 }} tickFormatter={fmt}
            label={{ value: yLabel, position: 'insideBottom', offset: -4, fill: 'var(--muted)', fontSize: 11 }}
          />
          <YAxis
            type="category" dataKey="name" stroke="var(--muted)" width={160}
            tick={{ fill: 'var(--text)', fontSize: 11 }}
          />
          <Tooltip content={<BarTooltip formatValue={fmt} />} cursor={{ fill: 'var(--border)', opacity: 0.3 }} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={24} isAnimationActive={false}>
            {data.map((entry, i) => (
              <Cell key={entry.name} fill={SERIES_COLORS[i % SERIES_COLORS.length]} />
            ))}
            <LabelList
              dataKey="value" position="right" fill="var(--text)" fontSize={11}
              formatter={(v: unknown) => (typeof v === 'number' ? fmt(v) : '')}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
