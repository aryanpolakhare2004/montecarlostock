<script setup lang="ts" generic="T extends object">
import { ref } from 'vue';
import { DownloadIcon } from './icons';
import { useToast } from '../composables/useToast';
import { downloadBlob, toCsv } from '../utils/csv';

const props = defineProps<{
  runId: number;
  csvFilename: string;
  csvRows: T[];
}>();

const busy = ref<'png' | 'pdf' | null>(null);
const { showToast } = useToast();

function onCsv() {
  try {
    downloadBlob(props.csvFilename, toCsv(props.csvRows), 'text/csv');
  } catch (err) {
    showToast(`CSV export failed: ${err instanceof Error ? err.message : String(err)}`, 'error');
  }
}

async function onDownload(kind: 'png' | 'pdf') {
  busy.value = kind;
  try {
    const resp = await fetch(`/api/runs/${props.runId}/${kind}`);
    if (!resp.ok) throw new Error(`request failed (${resp.status})`);
    const blob = await resp.blob();
    downloadBlob(`run-${props.runId}.${kind}`, blob, kind === 'png' ? 'image/png' : 'application/pdf');
  } catch (err) {
    showToast(`${kind.toUpperCase()} export failed: ${err instanceof Error ? err.message : String(err)}`, 'error');
  } finally {
    busy.value = null;
  }
}
</script>

<template>
  <div class="export-buttons">
    <button type="button" :disabled="csvRows.length === 0" @click="onCsv">
      <DownloadIcon :size="14" /> CSV
    </button>
    <button type="button" :disabled="busy !== null" @click="onDownload('png')">
      <DownloadIcon :size="14" /> PNG
    </button>
    <button type="button" :disabled="busy !== null" @click="onDownload('pdf')">
      <DownloadIcon :size="14" /> PDF
    </button>
  </div>
</template>
