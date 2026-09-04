<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{ values: number[]; width?: number; height?: number; positive: boolean }>(),
  { width: 100, height: 28 },
);

const points = computed(() => {
  if (props.values.length < 2) return '';
  const lo = Math.min(...props.values);
  const hi = Math.max(...props.values);
  const span = hi - lo || 1;
  const step = props.width / (props.values.length - 1);
  return props.values
    .map((v, i) => `${(i * step).toFixed(1)},${(props.height - ((v - lo) / span) * props.height).toFixed(1)}`)
    .join(' ');
});
</script>

<template>
  <svg v-if="values.length < 2" :width="width" :height="height" />
  <svg v-else :width="width" :height="height" class="sparkline">
    <polyline :points="points" fill="none" :stroke="positive ? 'var(--good)' : 'var(--bad)'" stroke-width="1.5" />
  </svg>
</template>
