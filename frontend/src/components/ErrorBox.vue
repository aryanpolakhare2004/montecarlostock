<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ error: unknown }>();
const message = computed(() => (props.error instanceof Error ? props.error.message : String(props.error)));
</script>

<template>
  <p class="error">{{ message }}</p>
</template>
