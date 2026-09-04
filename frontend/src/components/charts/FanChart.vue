<script setup lang="ts">
import { computed } from 'vue';
import { Line } from 'vue-chartjs';
import type { ChartData, ChartOptions, TooltipItem } from 'chart.js';
import { cssVar, hexToRgba } from '../../utils/cssVar';
import { useThemeVersion } from '../../composables/useThemeVersion';
import type { BandPoint } from '../../types';

const props = withDefaults(defineProps<{ data: BandPoint[]; yLabel?: string }>(), { yLabel: 'Value' });

const themeVersion = useThemeVersion();

function fmt(v: number): string {
  return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

// dataset order: [p5, p95(fills to p5), p25, p75(fills to p25), median]
const TOOLTIP_RANK = [4, 0, 3, 1, 2]; // rank per datasetIndex: p95,p75,median,p25,p5

const chartData = computed<ChartData<'line'>>(() => {
  void themeVersion.value;
  const seriesColor = cssVar('--series-1');
  const border = cssVar('--border');
  return {
    labels: props.data.map((d) => String(d.step)),
    datasets: [
      { label: 'p5', data: props.data.map((d) => d.p5), borderWidth: 0, pointRadius: 0, fill: false, borderColor: border },
      { label: 'p95', data: props.data.map((d) => d.p95), borderWidth: 0, pointRadius: 0, backgroundColor: hexToRgba(seriesColor, 0.12), fill: 0 },
      { label: 'p25', data: props.data.map((d) => d.p25), borderWidth: 0, pointRadius: 0, fill: false, borderColor: border },
      { label: 'p75', data: props.data.map((d) => d.p75), borderWidth: 0, pointRadius: 0, backgroundColor: hexToRgba(seriesColor, 0.28), fill: 2 },
      { label: 'median', data: props.data.map((d) => d.p50), borderColor: seriesColor, borderWidth: 2, pointRadius: 0, fill: false },
    ],
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
      legend: { display: false },
      tooltip: {
        backgroundColor: panelRaised,
        titleColor: muted,
        bodyColor: text,
        borderColor: border,
        borderWidth: 1,
        itemSort: (a: TooltipItem<'line'>, b: TooltipItem<'line'>) =>
          TOOLTIP_RANK[a.datasetIndex] - TOOLTIP_RANK[b.datasetIndex],
        callbacks: {
          title: (items: TooltipItem<'line'>[]) => `Day ${items[0]?.label ?? ''}`,
          label: (item: TooltipItem<'line'>) => `${item.dataset.label}: ${fmt(item.parsed.y ?? 0)}`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: muted, font: { size: 11 } },
        title: { display: true, text: 'Trading day', color: muted, font: { size: 11 } },
      },
      y: {
        grid: { color: border },
        ticks: { color: muted, font: { size: 11 } },
        title: { display: true, text: props.yLabel, color: muted, font: { size: 11 } },
      },
    },
  };
});
</script>

<template>
  <div class="chart-card">
    <div class="chart-legend">
      <span><i class="legend-swatch" style="background: var(--series-1); opacity: 0.15" /> 5th-95th percentile</span>
      <span><i class="legend-swatch" style="background: var(--series-1); opacity: 0.3" /> 25th-75th percentile</span>
      <span><i class="legend-swatch line" style="background: var(--series-1)" /> median</span>
    </div>
    <div style="height: 280px">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
