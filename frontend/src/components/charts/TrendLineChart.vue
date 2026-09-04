<script setup lang="ts">
import { computed } from 'vue';
import { Line } from 'vue-chartjs';
import type { ChartData, ChartOptions, TooltipItem } from 'chart.js';
import { cssVar } from '../../utils/cssVar';
import { useThemeVersion } from '../../composables/useThemeVersion';

export interface FundamentalsTrendRow {
  fiscal_year: number;
  revenue?: number | null;
  net_income?: number | null;
  free_cash_flow?: number | null;
}

const SERIES = [
  { key: 'revenue', label: 'Revenue', color: '--series-1' },
  { key: 'net_income', label: 'Net income', color: '--series-2' },
  { key: 'free_cash_flow', label: 'Free cash flow', color: '--series-3' },
] as const;

const props = defineProps<{ data: FundamentalsTrendRow[] }>();

const themeVersion = useThemeVersion();

function fmt(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  return `$${v.toFixed(0)}`;
}

const chartData = computed<ChartData<'line'>>(() => {
  void themeVersion.value;
  return {
    labels: props.data.map((d) => String(d.fiscal_year)),
    datasets: SERIES.map((s) => ({
      label: s.label,
      data: props.data.map((d) => d[s.key] ?? null),
      borderColor: cssVar(s.color),
      borderWidth: 2,
      pointRadius: 0,
      spanGaps: true,
      fill: false,
    })),
  };
});

const chartOptions = computed<ChartOptions<'line'>>(() => {
  void themeVersion.value;
  const muted = cssVar('--muted');
  const border = cssVar('--border');
  const panelRaised = cssVar('--panel-raised');
  const text = cssVar('--text');
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: true, labels: { color: muted, font: { size: 12 } } },
      tooltip: {
        backgroundColor: panelRaised,
        titleColor: muted,
        bodyColor: text,
        borderColor: border,
        borderWidth: 1,
        callbacks: {
          title: (items: TooltipItem<'line'>[]) => `FY${items[0]?.label ?? ''}`,
          label: (item: TooltipItem<'line'>) => `${item.dataset.label}: ${fmt(item.parsed.y ?? 0)}`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: muted, font: { size: 11 } },
      },
      y: {
        grid: { color: border },
        ticks: { color: muted, font: { size: 11 }, callback: (v) => fmt(Number(v)) },
      },
    },
  };
});
</script>

<template>
  <div class="chart-card">
    <div style="height: 260px">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
