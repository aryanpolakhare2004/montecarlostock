<script setup lang="ts">
import Spinner from './Spinner.vue';

withDefaults(defineProps<{ busy: boolean; busyLabel?: string }>(), { busyLabel: 'Running…' });
</script>

<template>
  <button type="submit" :disabled="busy" class="submit-btn">
    <template v-if="busy">
      <Spinner :size="14" /> {{ busyLabel }}
    </template>
    <slot v-else />
  </button>
</template>
