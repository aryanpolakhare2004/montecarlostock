<script setup lang="ts">
import { provide, ref } from 'vue';
import { ToastKey, type ToastKind } from '../composables/useToast';

interface Toast {
  id: number;
  message: string;
  kind: ToastKind;
}

const toasts = ref<Toast[]>([]);
let nextId = 0;

function dismissToast(id: number) {
  toasts.value = toasts.value.filter((t) => t.id !== id);
}

function showToast(message: string, kind: ToastKind = 'info') {
  const id = nextId++;
  toasts.value = [...toasts.value, { id, message, kind }];
  setTimeout(() => {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }, 4000);
}

provide(ToastKey, { showToast, dismissToast });
</script>

<template>
  <slot />
  <div class="toast-stack" role="status" aria-live="polite">
    <div v-for="t in toasts" :key="t.id" :class="`toast toast-${t.kind}`">
      <span>{{ t.message }}</span>
      <button type="button" class="toast-close" aria-label="Dismiss" @click="dismissToast(t.id)">×</button>
    </div>
  </div>
</template>
