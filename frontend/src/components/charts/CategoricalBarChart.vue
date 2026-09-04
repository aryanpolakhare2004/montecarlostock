<script setup lang="ts">
import { computed } from 'vue';
import { Bar } from 'vue-chartjs';
import type { ChartData, ChartOptions, Plugin, TooltipItem } from 'chart.js';
import { cssVar } from '../../utils/cssVar';
import { useThemeVersion } from '../../composables/useThemeVersion';

const SERIES_VARS = [
  '--series-1', '--series-2', '--series-3', '--series-4',
  '--series-5', '--series-6', '--series-7', '--series-8',
];

export interface BarDatum {
  name: string;
  value: number;
  extra?: { label: string; value: string }[];
}

const props = withDefaults(
  defineProps<{ data: BarDatum[]; yLabel?: string; formatValue?: (v: number) => string }>(),
  { yLabel: 'Value' },
);

const themeVersion = useThemeVersion();

function defaultFormat(v: number): string {
  return v.toLocaleString(undefined, { maximumFractionDigits: 4 });
}

const fmt = computed(() => props.formatValue || defaultFormat);
const chartHeight = computed(() => Math.max(220, props.data.length * 44));

const chartData = computed<ChartData<'bar'>>(() => {
  void themeVersion.value;
  const colors = props.data.map((_, i) => cssVar(SERIES_VARS[i % SERIES_VARS.length]));
  return {
    labels: props.data.map((d) => d.name),
    datasets: [{
      label: 'value',
      data: props.data.map((d) => d.value),
      backgroundColor: colors,
      borderRadius: 4,
      maxBarThickness: 24,
    }],
  };
});

const dataLabelsPlugin = computed<Plugin<'bar'>>(() => {
  void themeVersion.value;
  const text = cssVar('--text');
  return {
    id: 'valueLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      const meta = chart.getDatasetMeta(0);
      ctx.save();
      ctx.fillStyle = text;
      ctx.font = '11px sans-serif';
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'left';
      meta.data.forEach((bar, i) => {
        const value = chart.data.datasets[0]?.data[i];
        if (typeof value !== 'number') return;
        ctx.fillText(fmt.value(value), bar.x + 6, bar.y);
      });
      ctx.restore();
    },
  };
});

const chartOptions = computed<ChartOptions<'bar'>>(() => {
  void themeVersion.value;
  const muted = cssVar('--muted');
  const text = cssVar('--text');
  const border = cssVar('--border');
  const panelRaised = cssVar('--panel-raised');
  return {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { right: 48 } },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: panelRaised,
        titleColor: muted,
        bodyColor: text,
        borderColor: border,
        borderWidth: 1,
        callbacks: {
          title: (items: TooltipItem<'bar'>[]) => props.data[items[0]?.dataIndex ?? 0]?.name ?? '',
          label: (item: TooltipItem<'bar'>) => `value: ${fmt.value(item.parsed.x ?? 0)}`,
          afterLabel: (item: TooltipItem<'bar'>) => {
            const extra = props.data[item.dataIndex]?.extra;
            return extra ? extra.map((row) => `${row.label}: ${row.value}`) : [];
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: border },
        ticks: { color: muted, font: { size: 11 }, callback: (v) => fmt.value(Number(v)) },
        title: { display: true, text: props.yLabel, color: muted, font: { size: 11 } },
      },
      y: {
        grid: { display: false },
        ticks: { color: text, font: { size: 11 } },
      },
    },
  };
});
</script>

<template>
  <div class="chart-card">
    <div :style="{ height: chartHeight + 'px' }">
      <Bar :data="chartData" :options="chartOptions" :plugins="[dataLabelsPlugin]" />
    </div>
  </div>
</template>
