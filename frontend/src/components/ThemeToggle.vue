<script setup lang="ts">
import { computed } from 'vue';
import { useTheme } from '../composables/useTheme';
import { MonitorIcon, MoonIcon, SunIcon } from './icons';

const LABELS = { system: 'System', light: 'Light', dark: 'Dark' } as const;

const { theme, cycleTheme } = useTheme();
const Icon = computed(() => (theme.value === 'light' ? SunIcon : theme.value === 'dark' ? MoonIcon : MonitorIcon));
const label = computed(() => LABELS[theme.value]);
</script>

<template>
  <button type="button" class="theme-toggle" title="Cycle theme (System / Light / Dark)" @click="cycleTheme">
    <component :is="Icon" :size="14" />
    <span>{{ label }}</span>
  </button>
</template>
