import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export interface FundamentalsTrendRow {
  fiscal_year: number;
  revenue?: number | null;
  net_income?: number | null;
  free_cash_flow?: number | null;
}

const SERIES = [
  { key: 'revenue', label: 'Revenue', color: 'var(--series-1)' },
  { key: 'net_income', label: 'Net income', color: 'var(--series-2)' },
  { key: 'free_cash_flow', label: 'Free cash flow', color: 'var(--series-3)' },
] as const;

function fmt(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  return `$${v.toFixed(0)}`;
}

interface TooltipEntry {
  dataKey: string;
  value: number;
}

function TrendTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipEntry[]; label?: number }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">FY{label}</div>
      {SERIES.map((s) => {
        const entry = payload.find((p) => p.dataKey === s.key);
        if (!entry || entry.value == null) return null;
        return (
          <div className="chart-tooltip-row" key={s.key}>
            <span><i className="legend-swatch line" style={{ background: s.color }} /> {s.label}</span>
            <strong>{fmt(entry.value)}</strong>
          </div>
        );
      })}
    </div>
  );
}

export function TrendLineChart({ data }: { data: FundamentalsTrendRow[] }) {
  return (
    <div className="chart-card">
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 8, bottom: 8 }}>
          <CartesianGrid stroke="var(--border)" vertical={false} />
          <XAxis dataKey="fiscal_year" stroke="var(--muted)" tick={{ fill: 'var(--muted)', fontSize: 11 }} />
          <YAxis stroke="var(--muted)" tick={{ fill: 'var(--muted)', fontSize: 11 }} tickFormatter={fmt} width={56} />
          <Tooltip content={<TrendTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: 'var(--muted)' }} />
          {SERIES.map((s) => (
            <Line
              key={s.key} dataKey={s.key} name={s.label} stroke={s.color} strokeWidth={2} dot={false}
              connectNulls isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
