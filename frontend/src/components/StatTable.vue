<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ summary: object }>();
const entries = computed(() => Object.entries(props.summary as Record<string, unknown>));

function fmtValue(value: unknown): string {
  return typeof value === 'number' ? value.toFixed(4) : String(value);
}
</script>

<template>
  <table class="stat-table">
    <tbody>
      <tr v-for="[key, value] in entries" :key="key">
        <td>{{ key }}</td>
        <td>{{ fmtValue(value) }}</td>
      </tr>
    </tbody>
  </table>
</template>
