<script setup lang="ts">
import { computed } from 'vue';
import { Chart } from 'vue-chartjs';
import type { ChartData, ChartOptions, TooltipItem } from 'chart.js';
import { cssVar } from '../../utils/cssVar';
import { useThemeVersion } from '../../composables/useThemeVersion';
import type { HistogramBin } from '../../types';

const props = withDefaults(
  defineProps<{
    data: HistogramBin[];
    xLabel?: string;
    referenceValue?: number;
    formatValue?: (v: number) => string;
  }>(),
  { xLabel: 'Value' },
);

const themeVersion = useThemeVersion();

function defaultFormat(v: number): string {
  return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

const fmt = computed(() => props.formatValue || defaultFormat);
const mids = computed(() => props.data.map((d) => (d.bin_start + d.bin_end) / 2));
const maxCount = computed(() => Math.max(0, ...props.data.map((d) => d.count)));

const chartData = computed<ChartData<'bar' | 'line'>>(() => {
  void themeVersion.value;
  const seriesColor = cssVar('--series-1');
  const muted = cssVar('--muted');
  const datasets: ChartData<'bar' | 'line'>['datasets'] = [
    {
      type: 'bar',
      label: 'count',
      data: props.data.map((d, i) => ({ x: mids.value[i], y: d.count })),
      backgroundColor: seriesColor,
      borderRadius: 3,
      maxBarThickness: 24,
    },
  ];
  if (props.referenceValue !== undefined) {
    datasets.push({
      type: 'line',
      label: 'reference',
      data: [{ x: props.referenceValue, y: 0 }, { x: props.referenceValue, y: maxCount.value }],
      borderColor: muted,
      borderDash: [4, 4],
      borderWidth: 1,
      pointRadius: 0,
    });
  }
  return { datasets };
});

const chartOptions = computed<ChartOptions<'bar'>>(() => {
  void themeVersion.value;
  const muted = cssVar('--muted');
  const border = cssVar('--border');
  const panelRaised = cssVar('--panel-raised');
  const text = cssVar('--text');
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: panelRaised,
        titleColor: muted,
        bodyColor: text,
        borderColor: border,
        borderWidth: 1,
        filter: (item: TooltipItem<'bar'>) => item.dataset.label === 'count',
        callbacks: {
          title: (items: TooltipItem<'bar'>[]) => {
            const bin = props.data[items[0]?.dataIndex ?? 0];
            return bin ? `${fmt.value(bin.bin_start)} to ${fmt.value(bin.bin_end)}` : '';
          },
          label: (item: TooltipItem<'bar'>) => `count: ${(item.parsed.y ?? 0).toLocaleString()}`,
        },
      },
    },
    scales: {
      x: {
        type: 'linear',
        grid: { display: false },
        ticks: { color: muted, font: { size: 11 }, callback: (v) => fmt.value(Number(v)) },
        title: { display: true, text: props.xLabel, color: muted, font: { size: 11 } },
      },
      y: {
        grid: { color: border },
        ticks: { color: muted, font: { size: 11 }, precision: 0 },
      },
    },
  };
});
</script>

<template>
  <div class="chart-card">
    <div style="height: 240px">
      <Chart type="bar" :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
